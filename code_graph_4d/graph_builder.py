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
    file_lookup: dict[str, FileInfo] = {}
    for f in files:
        # Store by filename and relative path
        file_lookup[f.path.name] = f
        try:
            rel_path = f.path.relative_to(root_path)
            file_lookup[str(rel_path)] = f
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
            target = _resolve_include(include, file_lookup, root_path)
            if target and target in G.nodes:
                G.add_edge(src_path, target, type='include')
    
    return G


def _resolve_include(include: str, lookup: dict[str, FileInfo], root: Path) -> str | None:
    """Resolve an include path to a file in our graph."""
    # Direct filename match
    include_name = Path(include).name
    if include_name in lookup:
        f = lookup[include_name]
        try:
            return str(f.path.relative_to(root))
        except ValueError:
            return str(f.path)
    
    # Try relative path match
    if include in lookup:
        f = lookup[include]
        try:
            return str(f.path.relative_to(root))
        except ValueError:
            return str(f.path)
    
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
