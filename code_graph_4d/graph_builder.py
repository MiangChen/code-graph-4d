"""Build NetworkX graph from parsed C++ files."""

from pathlib import Path
from typing import Any

import networkx as nx

from .parser import FileInfo


def build_dependency_graph(files: list[FileInfo], root_path: Path) -> nx.DiGraph:
    """
    Build a directed graph of file dependencies.
    
    Nodes: Each C++ file
    Edges: A -> B means A includes B
    """
    G = nx.DiGraph()
    
    # Build filename lookup for resolving includes
    # Use lists to handle multiple files with same name
    file_lookup: dict[str, list[FileInfo]] = {}
    for f in files:
        # Store by filename
        name = f.path.name
        if name not in file_lookup:
            file_lookup[name] = []
        file_lookup[name].append(f)
        
        # Store by relative path
        try:
            rel_path = str(f.path.relative_to(root_path))
            if rel_path not in file_lookup:
                file_lookup[rel_path] = []
            file_lookup[rel_path].append(f)
        except ValueError:
            pass
    
    # Add nodes with attributes
    for f in files:
        try:
            rel_path = str(f.path.relative_to(root_path))
        except ValueError:
            rel_path = str(f.path)
        
        node_attrs = {
            'path': rel_path,
            'name': f.path.stem,
            'is_header': f.is_header,
            'classes': f.classes,
            'structs': f.structs,
            'functions': f.functions,
            'global_vars': f.global_vars,
            'type': 'header' if f.is_header else 'source',
            # Complexity metric for 4th dimension
            'complexity': len(f.classes) + len(f.structs) + len(f.functions),
        }
        G.add_node(rel_path, **node_attrs)
    
    # Add edges based on includes
    for f in files:
        try:
            src_path = str(f.path.relative_to(root_path))
        except ValueError:
            src_path = str(f.path)
        
        for include in f.includes:
            # Try to resolve include to actual file
            target = _resolve_include(include, file_lookup, root_path, f)
            if target and target in G.nodes:
                G.add_edge(src_path, target, type='include')
    
    return G


def _resolve_include(
    include: str,
    lookup: dict[str, list[FileInfo]],
    root: Path,
    source_file: FileInfo | None = None
) -> str | None:
    """Resolve an include path to a file in our graph."""
    include_name = Path(include).name
    
    def to_rel_path(f: FileInfo) -> str | None:
        try:
            return str(f.path.relative_to(root))
        except ValueError:
            return str(f.path)
    
    # 1. Try relative to source file's directory first
    if source_file:
        source_dir = source_file.path.parent
        candidate = source_dir / include
        if candidate.exists():
            try:
                return str(candidate.relative_to(root))
            except ValueError:
                pass
    
    # 2. Try exact path match
    if include in lookup and lookup[include]:
        return to_rel_path(lookup[include][0])
    
    # 3. Try filename match - prefer file in same directory as source
    if include_name in lookup:
        candidates = lookup[include_name]
        if source_file and len(candidates) > 1:
            # Prefer same directory
            source_dir = source_file.path.parent
            for f in candidates:
                if f.path.parent == source_dir:
                    return to_rel_path(f)
        # Return first match
        if candidates:
            return to_rel_path(candidates[0])
    
    # 4. Try partial path match (e.g., "UI/Widget.h" matches "Source/UI/Widget.h")
    for path_str, files in lookup.items():
        if files and (path_str.endswith(include) or path_str.endswith('/' + include)):
            return to_rel_path(files[0])
    
    return None


def get_graph_stats(G: nx.DiGraph) -> dict[str, Any]:
    """Get statistics about the dependency graph."""
    return {
        'total_files': G.number_of_nodes(),
        'total_dependencies': G.number_of_edges(),
        'headers': sum(1 for _, d in G.nodes(data=True) if d.get('is_header')),
        'sources': sum(1 for _, d in G.nodes(data=True) if not d.get('is_header')),
        'most_depended': _get_most_depended(G, 5),
        'most_dependencies': _get_most_dependencies(G, 5),
    }


def _get_most_depended(G: nx.DiGraph, n: int) -> list[tuple[str, int]]:
    """Get files that are included by the most other files."""
    in_degrees = [(node, G.in_degree(node)) for node in G.nodes()]
    return sorted(in_degrees, key=lambda x: x[1], reverse=True)[:n]


def _get_most_dependencies(G: nx.DiGraph, n: int) -> list[tuple[str, int]]:
    """Get files that include the most other files."""
    out_degrees = [(node, G.out_degree(node)) for node in G.nodes()]
    return sorted(out_degrees, key=lambda x: x[1], reverse=True)[:n]
