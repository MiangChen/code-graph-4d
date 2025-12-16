"""C++ source file parser using tree-sitter."""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    import tree_sitter_cpp as tscpp
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


@dataclass
class FileInfo:
    """Parsed information from a C++ file."""
    path: Path
    includes: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    structs: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    global_vars: list[str] = field(default_factory=list)
    is_header: bool = False


class CppParser:
    """Parser for C++ source files."""
    
    HEADER_EXTENSIONS = {'.h', '.hpp', '.hxx', '.h++', '.hh'}
    SOURCE_EXTENSIONS = {'.cpp', '.cxx', '.cc', '.c++', '.c'}
    
    def __init__(self):
        self.parser: Optional[Parser] = None
        if HAS_TREE_SITTER:
            self._init_tree_sitter()
    
    def _init_tree_sitter(self):
        """Initialize tree-sitter parser."""
        self.parser = Parser(Language(tscpp.language()))
    
    def parse_file(self, filepath: Path) -> Optional[FileInfo]:
        """Parse a single C++ file."""
        if not self._is_cpp_file(filepath):
            return None
        
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None
        
        info = FileInfo(
            path=filepath,
            is_header=filepath.suffix.lower() in self.HEADER_EXTENSIONS
        )
        
        if self.parser and HAS_TREE_SITTER:
            self._parse_with_tree_sitter(content, info)
        else:
            self._parse_with_regex(content, info)
        
        return info
    
    def _is_cpp_file(self, filepath: Path) -> bool:
        """Check if file is a C++ source or header."""
        return filepath.suffix.lower() in (self.HEADER_EXTENSIONS | self.SOURCE_EXTENSIONS)
    
    def _parse_with_tree_sitter(self, content: str, info: FileInfo):
        """Parse using tree-sitter for accurate AST."""
        tree = self.parser.parse(bytes(content, 'utf-8'))
        root = tree.root_node
        
        self._extract_includes_ts(root, content, info)
        self._extract_declarations_ts(root, content, info)
    
    def _extract_includes_ts(self, node, content: str, info: FileInfo):
        """Extract #include directives using tree-sitter."""
        if node.type == 'preproc_include':
            for child in node.children:
                if child.type in ('string_literal', 'system_lib_string'):
                    include_path = content[child.start_byte:child.end_byte]
                    include_path = include_path.strip('"<>')
                    info.includes.append(include_path)
        
        for child in node.children:
            self._extract_includes_ts(child, content, info)
    
    def _extract_declarations_ts(self, node, content: str, info: FileInfo):
        """Extract classes, structs, functions from AST."""
        if node.type == 'class_specifier':
            name = self._get_name_from_node(node, content)
            if name:
                info.classes.append(name)
        
        elif node.type == 'struct_specifier':
            name = self._get_name_from_node(node, content)
            if name:
                info.structs.append(name)
        
        elif node.type == 'function_definition':
            name = self._get_function_name(node, content)
            if name and not self._is_member_function(node):
                info.functions.append(name)
        
        elif node.type == 'declaration':
            if self._is_global_var_declaration(node):
                name = self._get_var_name(node, content)
                if name:
                    info.global_vars.append(name)
        
        for child in node.children:
            self._extract_declarations_ts(child, content, info)
    
    def _get_name_from_node(self, node, content: str) -> Optional[str]:
        """Get name identifier from class/struct node."""
        for child in node.children:
            if child.type == 'type_identifier':
                return content[child.start_byte:child.end_byte]
        return None
    
    def _get_function_name(self, node, content: str) -> Optional[str]:
        """Get function name from function_definition node."""
        for child in node.children:
            if child.type == 'function_declarator':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return content[subchild.start_byte:subchild.end_byte]
                    elif subchild.type == 'qualified_identifier':
                        return content[subchild.start_byte:subchild.end_byte]
        return None
    
    def _is_member_function(self, node) -> bool:
        """Check if function is a class member (has :: in name)."""
        for child in node.children:
            if child.type == 'function_declarator':
                for subchild in child.children:
                    if subchild.type == 'qualified_identifier':
                        return True
        return False
    
    def _is_global_var_declaration(self, node) -> bool:
        """Check if declaration is at global scope."""
        return node.parent and node.parent.type == 'translation_unit'
    
    def _get_var_name(self, node, content: str) -> Optional[str]:
        """Get variable name from declaration."""
        for child in node.children:
            if child.type == 'init_declarator':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return content[subchild.start_byte:subchild.end_byte]
            elif child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
        return None
    
    def _parse_with_regex(self, content: str, info: FileInfo):
        """Fallback regex-based parsing."""
        # Extract includes
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        info.includes = re.findall(include_pattern, content)
        
        # Extract classes
        class_pattern = r'\bclass\s+(\w+)'
        info.classes = re.findall(class_pattern, content)
        
        # Extract structs
        struct_pattern = r'\bstruct\s+(\w+)'
        info.structs = re.findall(struct_pattern, content)
        
        # Extract global functions (simplified)
        func_pattern = r'^(?:[\w:*&<>]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*{'
        info.functions = re.findall(func_pattern, content, re.MULTILINE)


def scan_directory(root_path: Path) -> list[FileInfo]:
    """Scan directory recursively for C++ files."""
    parser = CppParser()
    results = []
    
    for filepath in root_path.rglob('*'):
        if filepath.is_file():
            info = parser.parse_file(filepath)
            if info:
                results.append(info)
    
    return results
