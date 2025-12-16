"""Generate 3D visualization HTML using 3d-force-graph."""

import json
import webbrowser
from pathlib import Path
from typing import Any

import networkx as nx


def graph_to_json(G: nx.DiGraph) -> dict[str, Any]:
    """Convert NetworkX graph to 3d-force-graph JSON format."""
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
            # Size based on complexity
            'val': max(1, attrs.get('complexity', 1)),
        }
        nodes.append(node_data)
    
    links = []
    for src, dst, attrs in G.edges(data=True):
        links.append({
            'source': src,
            'target': dst,
            'type': attrs.get('type', 'include'),
        })
    
    return {'nodes': nodes, 'links': links}


def generate_html(G: nx.DiGraph, output_path: Path, title: str = "Code Graph 4D") -> Path:
    """Generate interactive 3D visualization HTML."""
    graph_data = graph_to_json(G)
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            overflow: hidden;
        }}
        #graph-container {{
            width: 100vw;
            height: 100vh;
        }}
        #info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(20, 20, 30, 0.9);
            padding: 15px;
            border-radius: 8px;
            max-width: 300px;
            font-size: 13px;
            border: 1px solid #333;
        }}
        #info-panel h3 {{
            margin: 0 0 10px 0;
            color: #4fc3f7;
        }}
        #node-info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(20, 20, 30, 0.9);
            padding: 15px;
            border-radius: 8px;
            max-width: 350px;
            font-size: 12px;
            border: 1px solid #333;
            display: none;
        }}
        #node-info h4 {{
            margin: 0 0 8px 0;
            color: #81c784;
            word-break: break-all;
        }}
        .stat {{ margin: 5px 0; }}
        .stat-label {{ color: #888; }}
        .list-section {{ margin-top: 8px; }}
        .list-section ul {{
            margin: 4px 0;
            padding-left: 20px;
            max-height: 100px;
            overflow-y: auto;
        }}
        .header-node {{ color: #4fc3f7; }}
        .source-node {{ color: #81c784; }}
        #controls {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(20, 20, 30, 0.9);
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        #controls label {{
            margin-right: 15px;
            cursor: pointer;
        }}
    </style>
    <script src="https://unpkg.com/3d-force-graph@1"></script>
</head>
<body>
    <div id="graph-container"></div>
    
    <div id="info-panel">
        <h3>📊 Code Graph 4D</h3>
        <div class="stat"><span class="stat-label">Files:</span> <span id="stat-files">0</span></div>
        <div class="stat"><span class="stat-label">Dependencies:</span> <span id="stat-deps">0</span></div>
        <div class="stat"><span class="stat-label">Headers:</span> <span id="stat-headers">0</span></div>
        <div class="stat"><span class="stat-label">Sources:</span> <span id="stat-sources">0</span></div>
        <div style="margin-top: 10px; color: #666; font-size: 11px;">
            Click node for details<br>
            Drag to rotate • Scroll to zoom
        </div>
    </div>
    
    <div id="node-info">
        <h4 id="node-name"></h4>
        <div class="stat"><span class="stat-label">Type:</span> <span id="node-type"></span></div>
        <div class="stat"><span class="stat-label">Complexity:</span> <span id="node-complexity"></span></div>
        <div class="list-section" id="classes-section">
            <span class="stat-label">Classes:</span>
            <ul id="node-classes"></ul>
        </div>
        <div class="list-section" id="structs-section">
            <span class="stat-label">Structs:</span>
            <ul id="node-structs"></ul>
        </div>
        <div class="list-section" id="functions-section">
            <span class="stat-label">Functions:</span>
            <ul id="node-functions"></ul>
        </div>
    </div>
    
    <div id="controls">
        <label><input type="checkbox" id="show-labels" checked> Show Labels</label>
        <label><input type="checkbox" id="show-arrows" checked> Show Arrows</label>
    </div>

    <script>
        const graphData = {json.dumps(graph_data)};
        
        // Update stats
        document.getElementById('stat-files').textContent = graphData.nodes.length;
        document.getElementById('stat-deps').textContent = graphData.links.length;
        document.getElementById('stat-headers').textContent = 
            graphData.nodes.filter(n => n.isHeader).length;
        document.getElementById('stat-sources').textContent = 
            graphData.nodes.filter(n => !n.isHeader).length;
        
        const Graph = ForceGraph3D()
            (document.getElementById('graph-container'))
            .graphData(graphData)
            .nodeLabel('path')
            .nodeColor(node => node.isHeader ? '#4fc3f7' : '#81c784')
            .nodeVal(node => Math.max(3, node.complexity * 2))
            .nodeOpacity(0.9)
            .linkColor(() => 'rgba(255,255,255,0.2)')
            .linkWidth(0.5)
            .linkDirectionalArrowLength(3)
            .linkDirectionalArrowRelPos(1)
            .backgroundColor('#0a0a0f')
            .onNodeClick(node => {{
                // Show node info panel
                const panel = document.getElementById('node-info');
                panel.style.display = 'block';
                
                document.getElementById('node-name').textContent = node.path;
                document.getElementById('node-type').textContent = node.isHeader ? 'Header' : 'Source';
                document.getElementById('node-type').className = node.isHeader ? 'header-node' : 'source-node';
                document.getElementById('node-complexity').textContent = node.complexity;
                
                // Update lists
                updateList('node-classes', 'classes-section', node.classes);
                updateList('node-structs', 'structs-section', node.structs);
                updateList('node-functions', 'functions-section', node.functions);
                
                // Focus on node
                const distance = 100;
                const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                Graph.cameraPosition(
                    {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                    node,
                    1000
                );
            }});
        
        function updateList(listId, sectionId, items) {{
            const list = document.getElementById(listId);
            const section = document.getElementById(sectionId);
            list.innerHTML = '';
            if (items && items.length > 0) {{
                section.style.display = 'block';
                items.forEach(item => {{
                    const li = document.createElement('li');
                    li.textContent = item;
                    list.appendChild(li);
                }});
            }} else {{
                section.style.display = 'none';
            }}
        }}
        
        // Controls
        document.getElementById('show-labels').addEventListener('change', (e) => {{
            Graph.nodeLabel(e.target.checked ? 'path' : null);
        }});
        
        document.getElementById('show-arrows').addEventListener('change', (e) => {{
            Graph.linkDirectionalArrowLength(e.target.checked ? 3 : 0);
        }});
    </script>
</body>
</html>'''
    
    output_path.write_text(html_content, encoding='utf-8')
    return output_path


def open_in_browser(html_path: Path):
    """Open the generated HTML in default browser."""
    webbrowser.open(f'file://{html_path.absolute()}')
