"""Generate 3D visualization HTML using 3d-force-graph."""

import json
import math
import webbrowser
from pathlib import Path
from typing import Any

import networkx as nx


def _calc_radius(line_count: int) -> float:
    """Calculate node size: lines / 2 = diameter = box edge length."""
    lines = max(10, line_count)
    return round(lines / 2, 2)  # 100 lines = 50 (diameter/edge)


def graph_to_json(G: nx.DiGraph) -> dict[str, Any]:
    """Convert NetworkX graph to 3d-force-graph JSON format."""
    # Get max level for normalization
    max_level = max((attrs.get('level', 0) for _, attrs in G.nodes(data=True)), default=1)
    max_level = max(max_level, 1)
    
    # Get number of communities
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
    
    metadata = {
        'maxLevel': max_level,
        'numCommunities': num_communities,
    }
    
    # Calculate in-degree for each node (how many times it's included)
    in_degrees = dict(G.in_degree())
    max_in_degree = max(in_degrees.values()) if in_degrees else 1
    
    links = []
    for src, dst, attrs in G.edges(data=True):
        # Edge width based on target's in-degree
        target_in_degree = in_degrees.get(dst, 1)
        links.append({
            'source': src,
            'target': dst,
            'type': attrs.get('type', 'include'),
            'weight': target_in_degree,
        })
    
    metadata['maxInDegree'] = max_in_degree
    
    return {'nodes': nodes, 'links': links, 'metadata': metadata}


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
        #file-tree {{
            position: absolute;
            top: 200px;
            left: 10px;
            background: rgba(20, 20, 30, 0.9);
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #333;
            max-width: 280px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 12px;
            display: block;
        }}
        #file-tree h4 {{
            margin: 0 0 8px 0;
            color: #4fc3f7;
            cursor: pointer;
        }}
        .tree-folder {{
            margin-left: 12px;
        }}
        .tree-folder-name {{
            color: #ffc107;
            cursor: pointer;
            user-select: none;
        }}
        .tree-folder-name:hover {{
            color: #ffeb3b;
        }}
        .tree-file {{
            margin-left: 12px;
            cursor: pointer;
            padding: 2px 0;
        }}
        .tree-file:hover {{
            color: #4fc3f7;
        }}
        .tree-file.header {{
            color: #81c784;
        }}
        .tree-file.source {{
            color: #aaa;
        }}
        .tree-collapsed {{
            display: none;
        }}
    </style>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
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
        <div class="stat"><span class="stat-label">Communities:</span> <span id="stat-communities">0</span></div>
        <div class="stat"><span class="stat-label">Max Level:</span> <span id="stat-levels">0</span></div>
        <div style="margin-top: 10px; color: #666; font-size: 11px;">
            Click node for details<br>
            Drag to rotate • Scroll to zoom
        </div>
    </div>
    
    <div id="node-info">
        <h4 id="node-name"></h4>
        <div class="stat"><span class="stat-label">Type:</span> <span id="node-type"></span></div>
        <div class="stat"><span class="stat-label">Lines:</span> <span id="node-lines"></span></div>
        <div class="stat"><span class="stat-label">Radius:</span> <span id="node-radius"></span></div>
        <div class="stat"><span class="stat-label">Complexity:</span> <span id="node-complexity"></span></div>
        <div class="stat"><span class="stat-label">Level:</span> <span id="node-level"></span></div>
        <div class="stat"><span class="stat-label">Community:</span> <span id="node-community"></span></div>
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
        <label><input type="checkbox" id="show-labels" checked> Labels</label>
        <label><input type="checkbox" id="show-arrows" checked> Arrows</label>
        <label><input type="checkbox" id="use-hierarchy"> Hierarchy Y</label>
        <label><input type="checkbox" id="color-community" checked> Community Colors</label>
        <label><input type="checkbox" id="show-boundary"> Boundary</label>
        <label><input type="checkbox" id="light-mode"> Light Mode</label>
        <label><input type="checkbox" id="fly-mode"> Fly Mode</label>
        <label><input type="checkbox" id="show-tree" checked> Tree</label>
    </div>
    
    <div id="file-tree">
        <h4>📁 File Tree</h4>
        <div id="tree-content"></div>
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
        document.getElementById('stat-communities').textContent = graphData.metadata.numCommunities;
        document.getElementById('stat-levels').textContent = graphData.metadata.maxLevel;
        
        // Community color palette
        const communityColors = [
            '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3',
            '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#cddc39',
            '#ffeb3b', '#ffc107', '#ff9800', '#ff5722', '#795548'
        ];
        
        let useHierarchy = false;
        let useCommunityColors = true;
        let isLightMode = false;
        
        // Theme colors
        const themes = {{
            dark: {{
                bg: '#0a0a0f',
                panelBg: 'rgba(20, 20, 30, 0.9)',
                panelBorder: '#333',
                text: '#fff',
                textMuted: '#888',
                header: '#4fc3f7',
                source: '#81c784',
                link: 'rgba(255,180,100,0.6)',
                arrow: 'rgba(255,200,120,0.8)'
            }},
            light: {{
                bg: '#f5f5f5',
                panelBg: 'rgba(255, 255, 255, 0.95)',
                panelBorder: '#ddd',
                text: '#333',
                textMuted: '#666',
                header: '#1976d2',
                source: '#388e3c',
                link: 'rgba(150,100,50,0.7)',
                arrow: 'rgba(180,120,60,0.9)'
            }}
        }};
        
        function getNodeColor(node) {{
            const theme = isLightMode ? themes.light : themes.dark;
            if (useCommunityColors) {{
                return communityColors[node.community % communityColors.length];
            }}
            return node.isHeader ? theme.header : theme.source;
        }}
        
        function applyTheme() {{
            const theme = isLightMode ? themes.light : themes.dark;
            document.body.style.background = theme.bg;
            document.body.style.color = theme.text;
            
            document.querySelectorAll('#info-panel, #node-info, #controls').forEach(el => {{
                el.style.background = theme.panelBg;
                el.style.borderColor = theme.panelBorder;
            }});
            document.querySelectorAll('.stat-label').forEach(el => {{
                el.style.color = theme.textMuted;
            }});
            
            Graph.backgroundColor(theme.bg)
                .linkColor(() => theme.link)
                .linkDirectionalArrowColor(() => theme.arrow)
                .nodeColor(getNodeColor);
        }}
        
        // Node size uses pre-calculated radius from Python
        function getNodeSize(node) {{
            return node.radius || 5;
        }}
        
        // Track highlighted node for dependency chain
        let highlightedNode = null;
        let highlightedLinks = new Set();
        let highlightedNodes = new Set();
        
        function updateHighlight(node) {{
            highlightedLinks.clear();
            highlightedNodes.clear();
            
            if (node) {{
                highlightedNodes.add(node.id);
                // Find all connected links
                graphData.links.forEach(link => {{
                    const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                    const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                    if (srcId === node.id || tgtId === node.id) {{
                        highlightedLinks.add(link);
                        highlightedNodes.add(srcId);
                        highlightedNodes.add(tgtId);
                    }}
                }});
            }}
            highlightedNode = node;
        }}
        
        // Link width based on weight (in-degree of target)
        function getLinkWidth(link) {{
            const weight = link.weight || 1;
            const baseWidth = highlightedLinks.has(link) ? 4 : 1;
            return baseWidth + Math.min(weight, 10) * 0.3;
        }}
        
        // Link color with highlight
        function getLinkColor(link) {{
            const theme = isLightMode ? themes.light : themes.dark;
            if (highlightedLinks.has(link)) {{
                return '#ff6b6b';  // Highlight color
            }}
            return theme.link;
        }}
        
        const Graph = ForceGraph3D()
            (document.getElementById('graph-container'))
            .graphData(graphData)
            .nodeLabel('path')
            .nodeColor(node => {{
                if (highlightedNode && !highlightedNodes.has(node.id)) {{
                    return 'rgba(100,100,100,0.3)';  // Dim non-highlighted
                }}
                return getNodeColor(node);
            }})
            .nodeVal(getNodeSize)
            .nodeOpacity(0.9)
            .nodeThreeObject(node => {{
                const lines = node.lineCount || 10;
                const colorStr = getNodeColor(node);
                const color = colorStr.startsWith('#') ? parseInt(colorStr.slice(1), 16) : 0x4fc3f7;
                
                let geometry;
                if (node.isHeader) {{
                    // Header files: Box, edge = lines / 10
                    const edge = Math.max(3, lines / 10);
                    geometry = new THREE.BoxGeometry(edge, edge, edge);
                }} else {{
                    // Source files: Sphere, radius = lines / 40
                    const radius = Math.max(2, lines / 40);
                    geometry = new THREE.SphereGeometry(radius, 16, 12);
                }}
                
                const material = new THREE.MeshLambertMaterial({{
                    color: color,
                    transparent: true,
                    opacity: 0.9
                }});
                return new THREE.Mesh(geometry, material);
            }})
            .nodeThreeObjectExtend(false)
            .linkColor(getLinkColor)
            .linkWidth(getLinkWidth)
            .linkDirectionalArrowLength(6)
            .linkDirectionalArrowRelPos(1)
            .linkDirectionalArrowColor(link => highlightedLinks.has(link) ? '#ff6b6b' : 'rgba(255,200,120,0.8)')
            .linkOpacity(link => highlightedLinks.has(link) ? 1 : 0.5)
            .backgroundColor('#0a0a0f')
            .onNodeClick(node => {{
                // Toggle highlight
                if (highlightedNode === node) {{
                    updateHighlight(null);  // Clear highlight
                }} else {{
                    updateHighlight(node);  // Highlight this node
                }}
                
                // Refresh rendering
                Graph.nodeColor(Graph.nodeColor())
                    .linkColor(getLinkColor)
                    .linkWidth(getLinkWidth);
                
                // Show node info panel
                const panel = document.getElementById('node-info');
                panel.style.display = 'block';
                
                document.getElementById('node-name').textContent = node.path;
                document.getElementById('node-type').textContent = node.isHeader ? 'Header (●)' : 'Source (■)';
                document.getElementById('node-type').className = node.isHeader ? 'header-node' : 'source-node';
                document.getElementById('node-lines').textContent = node.lineCount;
                document.getElementById('node-radius').textContent = node.radius;
                document.getElementById('node-complexity').textContent = node.complexity;
                document.getElementById('node-level').textContent = node.level;
                document.getElementById('node-community').textContent = node.community;
                
                // Update lists
                updateList('node-classes', 'classes-section', node.classes);
                updateList('node-structs', 'structs-section', node.structs);
                updateList('node-functions', 'functions-section', node.functions);
                
                // Focus on node - move 50% closer, but keep minimum distance of 200
                const cam = Graph.camera();
                const dx = cam.position.x - node.x;
                const dy = cam.position.y - node.y;
                const dz = cam.position.z - node.z;
                const currentDist = Math.hypot(dx, dy, dz);
                const targetDist = Math.max(200, currentDist * 0.5);
                
                // Calculate new camera position at targetDist from node
                const scale = targetDist / currentDist;
                Graph.cameraPosition(
                    {{ x: node.x + dx * scale, y: node.y + dy * scale, z: node.z + dz * scale }},
                    node,
                    1000
                );
            }})
            .onBackgroundClick(() => {{
                // Clear highlight when clicking background
                updateHighlight(null);
                Graph.nodeColor(Graph.nodeColor())
                    .linkColor(getLinkColor)
                    .linkWidth(getLinkWidth);
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
            Graph.linkDirectionalArrowLength(e.target.checked ? 6 : 0);
        }});
        
        // Hierarchy layout toggle
        document.getElementById('use-hierarchy').addEventListener('change', (e) => {{
            useHierarchy = e.target.checked;
            if (useHierarchy) {{
                // Fix Y position based on level
                const levelSpacing = 50;
                graphData.nodes.forEach(node => {{
                    node.fy = node.level * levelSpacing;
                }});
            }} else {{
                // Release Y constraint
                graphData.nodes.forEach(node => {{
                    node.fy = undefined;
                }});
            }}
            Graph.graphData(graphData);
        }});
        
        // Community colors toggle
        document.getElementById('color-community').addEventListener('change', (e) => {{
            useCommunityColors = e.target.checked;
            Graph.nodeColor(getNodeColor);
        }});
        
        // Boundary box toggle - using canvas overlay
        let boundaryVisible = false;
        const boundaryCanvas = document.createElement('canvas');
        boundaryCanvas.id = 'boundary-overlay';
        boundaryCanvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;display:none;';
        document.body.appendChild(boundaryCanvas);
        
        function drawBoundary() {{
            if (!boundaryVisible) return;
            const ctx = boundaryCanvas.getContext('2d');
            const w = window.innerWidth;
            const h = window.innerHeight;
            boundaryCanvas.width = w;
            boundaryCanvas.height = h;
            
            ctx.clearRect(0, 0, w, h);
            ctx.strokeStyle = isLightMode ? 'rgba(100,100,100,0.4)' : 'rgba(100,150,200,0.3)';
            ctx.lineWidth = 1;
            
            // Draw grid lines
            const gridSize = 100;
            const centerX = w / 2;
            const centerY = h / 2;
            
            // Horizontal lines
            for (let i = -5; i <= 5; i++) {{
                ctx.beginPath();
                ctx.moveTo(0, centerY + i * gridSize);
                ctx.lineTo(w, centerY + i * gridSize);
                ctx.stroke();
            }}
            // Vertical lines
            for (let i = -5; i <= 5; i++) {{
                ctx.beginPath();
                ctx.moveTo(centerX + i * gridSize, 0);
                ctx.lineTo(centerX + i * gridSize, h);
                ctx.stroke();
            }}
            
            // Draw border
            ctx.strokeStyle = isLightMode ? 'rgba(80,80,80,0.6)' : 'rgba(100,180,255,0.4)';
            ctx.lineWidth = 2;
            const margin = 50;
            ctx.strokeRect(margin, margin, w - margin * 2, h - margin * 2);
        }}
        
        document.getElementById('show-boundary').addEventListener('change', (e) => {{
            boundaryVisible = e.target.checked;
            boundaryCanvas.style.display = boundaryVisible ? 'block' : 'none';
            if (boundaryVisible) drawBoundary();
        }});
        
        window.addEventListener('resize', () => {{
            if (boundaryVisible) drawBoundary();
        }});
        
        // Light/Dark mode toggle
        document.getElementById('light-mode').addEventListener('change', (e) => {{
            isLightMode = e.target.checked;
            applyTheme();
            if (boundaryVisible) drawBoundary();
        }});
        
        // Fly mode - WASD keyboard navigation
        let flyMode = false;
        const flySpeed = 5;
        const keys = {{}};
        
        document.addEventListener('keydown', (e) => {{ keys[e.key.toLowerCase()] = true; }});
        document.addEventListener('keyup', (e) => {{ keys[e.key.toLowerCase()] = false; }});
        
        document.getElementById('fly-mode').addEventListener('change', (e) => {{
            flyMode = e.target.checked;
            Graph.controls().screenSpacePanning = flyMode;
        }});
        
        // Fly animation loop
        (function flyLoop() {{
            if (flyMode) {{
                const cam = Graph.camera();
                const ctrl = Graph.controls();
                if (keys['w']) ctrl.target.z -= flySpeed;
                if (keys['s']) ctrl.target.z += flySpeed;
                if (keys['a']) ctrl.target.x -= flySpeed;
                if (keys['d']) ctrl.target.x += flySpeed;
                if (keys['q'] || keys[' ']) ctrl.target.y += flySpeed;
                if (keys['e']) ctrl.target.y -= flySpeed;
                ctrl.update();
            }}
            requestAnimationFrame(flyLoop);
        }})();
        
        // File tree
        function buildFileTree() {{
            const tree = {{}};
            graphData.nodes.forEach(node => {{
                const parts = node.path.split('/');
                let current = tree;
                parts.forEach((part, i) => {{
                    if (i === parts.length - 1) {{
                        // File
                        if (!current._files) current._files = [];
                        current._files.push({{ name: part, node: node }});
                    }} else {{
                        // Folder
                        if (!current[part]) current[part] = {{}};
                        current = current[part];
                    }}
                }});
            }});
            return tree;
        }}
        
        function renderTree(tree, container, path = '') {{
            // Render folders first
            Object.keys(tree).filter(k => k !== '_files').sort().forEach(folder => {{
                const folderDiv = document.createElement('div');
                folderDiv.className = 'tree-folder';
                
                const folderName = document.createElement('span');
                folderName.className = 'tree-folder-name';
                folderName.textContent = '📁 ' + folder;
                folderName.onclick = () => {{
                    const content = folderDiv.querySelector('.tree-folder-content');
                    if (content) content.classList.toggle('tree-collapsed');
                }};
                folderDiv.appendChild(folderName);
                
                const content = document.createElement('div');
                content.className = 'tree-folder-content';
                renderTree(tree[folder], content, path + folder + '/');
                folderDiv.appendChild(content);
                
                container.appendChild(folderDiv);
            }});
            
            // Render files
            if (tree._files) {{
                tree._files.sort((a, b) => a.name.localeCompare(b.name)).forEach(file => {{
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'tree-file ' + (file.node.isHeader ? 'header' : 'source');
                    fileDiv.textContent = (file.node.isHeader ? '📄 ' : '📝 ') + file.name;
                    fileDiv.onclick = () => {{
                        // Find and focus on node
                        const node = graphData.nodes.find(n => n.id === file.node.id);
                        if (node && node.x !== undefined) {{
                            Graph.cameraPosition(
                                {{ x: node.x + 150, y: node.y + 150, z: node.z + 150 }},
                                node,
                                1000
                            );
                            updateHighlight(node);
                            Graph.nodeColor(Graph.nodeColor())
                                .linkColor(getLinkColor)
                                .linkWidth(getLinkWidth);
                        }}
                    }};
                    container.appendChild(fileDiv);
                }});
            }}
        }}
        
        // Tree toggle
        document.getElementById('show-tree').addEventListener('change', (e) => {{
            const treePanel = document.getElementById('file-tree');
            treePanel.style.display = e.target.checked ? 'block' : 'none';
            if (e.target.checked && !treePanel.dataset.built) {{
                const tree = buildFileTree();
                renderTree(tree, document.getElementById('tree-content'));
                treePanel.dataset.built = 'true';
            }}
        }});
        
        // Build tree on load (default open)
        setTimeout(() => {{
            const tree = buildFileTree();
            renderTree(tree, document.getElementById('tree-content'));
            document.getElementById('file-tree').dataset.built = 'true';
        }}, 100);
    </script>
</body>
</html>'''
    
    output_path.write_text(html_content, encoding='utf-8')
    return output_path


def open_in_browser(html_path: Path):
    """Open the generated HTML in default browser."""
    webbrowser.open(f'file://{html_path.absolute()}')
