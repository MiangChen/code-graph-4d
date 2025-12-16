"""Generate 3D visualization HTML using 3d-force-graph."""

import json
import webbrowser
from pathlib import Path
from typing import Any

import networkx as nx


# Template directory
TEMPLATE_DIR = Path(__file__).parent / 'templates'


def _calc_radius(line_count: int) -> float:
    """Calculate node size: lines / 2 = diameter = box edge length."""
    lines = max(10, line_count)
    return round(lines / 2, 2)


def graph_to_json(G: nx.DiGraph) -> dict[str, Any]:
    """Convert NetworkX graph to 3d-force-graph JSON format."""
    max_level = max((attrs.get('level', 0) for _, attrs in G.nodes(data=True)), default=1)
    max_level = max(max_level, 1)
    
    communities = set(attrs.get('community', 0) for _, attrs in G.nodes(data=True))
    num_communities = len(communities)
    
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        node_data = {
            'id': node_id,
            'name': attrs.get('name', node_id),
            'path': attrs.get('path', node_id),
            'type': attrs.get('type', 'source'),
            'isHeader': attrs.get('is_header', False),
            'classes': attrs.get('classes', []),
            'structs': attrs.get('structs', []),
            'functions': attrs.get('functions', []),
            'complexity': attrs.get('complexity', 1),
            'level': attrs.get('level', 0),
            'community': attrs.get('community', 0),
            'lineCount': attrs.get('line_count', 10),
            'radius': _calc_radius(attrs.get('line_count', 10)),
        }
        nodes.append(node_data)
    
    in_degrees = dict(G.in_degree())
    max_in_degree = max(in_degrees.values()) if in_degrees else 1
    
    links = []
    for src, dst, attrs in G.edges(data=True):
        target_in_degree = in_degrees.get(dst, 1)
        links.append({
            'source': src,
            'target': dst,
            'type': attrs.get('type', 'include'),
            'weight': target_in_degree,
        })
    
    metadata = {
        'maxLevel': max_level,
        'numCommunities': num_communities,
        'maxInDegree': max_in_degree,
    }
    
    return {'nodes': nodes, 'links': links, 'metadata': metadata}


def _load_template(name: str) -> str:
    """Load template file content."""
    return (TEMPLATE_DIR / name).read_text(encoding='utf-8')


def generate_html(G: nx.DiGraph, output_path: Path, title: str = "Code Graph 4D") -> Path:
    """Generate interactive 3D visualization HTML."""
    graph_data = graph_to_json(G)
    
    # Load templates
    html_template = _load_template('graph.html')
    css_content = _load_template('styles.css')
    js_content = _load_template('graph.js')
    
    # Replace placeholders
    html_content = html_template.replace('{{TITLE}}', title)
    html_content = html_content.replace('{{CSS}}', css_content)
    html_content = html_content.replace('{{GRAPH_DATA}}', json.dumps(graph_data))
    html_content = html_content.replace('{{JS}}', js_content)
    
    output_path.write_text(html_content, encoding='utf-8')
    return output_path


def open_in_browser(html_path: Path):
    """Open the generated HTML in default browser."""
    webbrowser.open(f'file://{html_path.absolute()}')
