/* Code Graph 4D - JavaScript */

// Update stats
document.getElementById('stat-files').textContent = graphData.nodes.length;
document.getElementById('stat-deps').textContent = graphData.links.length;
document.getElementById('stat-headers').textContent = graphData.nodes.filter(n => n.isHeader).length;
document.getElementById('stat-sources').textContent = graphData.nodes.filter(n => !n.isHeader).length;
document.getElementById('stat-communities').textContent = graphData.metadata.numCommunities;
document.getElementById('stat-levels').textContent = graphData.metadata.maxLevel;

// ============================================================================
// State & Configuration
// ============================================================================

const communityColors = [
    '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3',
    '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#cddc39',
    '#ffeb3b', '#ffc107', '#ff9800', '#ff5722', '#795548'
];

let useHierarchy = false;
let useCommunityColors = true;
let isLightMode = false;
let flyMode = false;
let boundaryVisible = false;
let highlightedNode = null;
let highlightedLinks = new Set();
let highlightedNodes = new Set();

const themes = {
    dark: {
        bg: '#0a0a0f',
        panelBg: 'rgba(20, 20, 30, 0.9)',
        panelBorder: '#333',
        text: '#fff',
        textMuted: '#888',
        header: '#4fc3f7',
        source: '#81c784',
        link: 'rgba(255,180,100,0.6)',
        arrow: 'rgba(255,200,120,0.8)'
    },
    light: {
        bg: '#f5f5f5',
        panelBg: 'rgba(255, 255, 255, 0.95)',
        panelBorder: '#ddd',
        text: '#333',
        textMuted: '#666',
        header: '#1976d2',
        source: '#388e3c',
        link: 'rgba(150,100,50,0.7)',
        arrow: 'rgba(180,120,60,0.9)'
    }
};


// ============================================================================
// Helper Functions
// ============================================================================

function getNodeColor(node) {
    const theme = isLightMode ? themes.light : themes.dark;
    if (useCommunityColors) {
        return communityColors[node.community % communityColors.length];
    }
    return node.isHeader ? theme.header : theme.source;
}

function getNodeSize(node) {
    return node.radius || 5;
}

function getLinkWidth(link) {
    const weight = link.weight || 1;
    const baseWidth = highlightedLinks.has(link) ? 4 : 1;
    return baseWidth + Math.min(weight, 10) * 0.3;
}

function getLinkColor(link) {
    const theme = isLightMode ? themes.light : themes.dark;
    if (highlightedLinks.has(link)) {
        return '#ff6b6b';
    }
    return theme.link;
}

function updateHighlight(node) {
    highlightedLinks.clear();
    highlightedNodes.clear();
    
    if (node) {
        highlightedNodes.add(node.id);
        graphData.links.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            if (srcId === node.id || tgtId === node.id) {
                highlightedLinks.add(link);
                highlightedNodes.add(srcId);
                highlightedNodes.add(tgtId);
            }
        });
    }
    highlightedNode = node;
}

function applyTheme() {
    const theme = isLightMode ? themes.light : themes.dark;
    document.body.style.background = theme.bg;
    document.body.style.color = theme.text;
    
    document.querySelectorAll('#info-panel, #node-info, #controls, #file-tree').forEach(el => {
        el.style.background = theme.panelBg;
        el.style.borderColor = theme.panelBorder;
    });
    document.querySelectorAll('.stat-label').forEach(el => {
        el.style.color = theme.textMuted;
    });
    
    Graph.backgroundColor(theme.bg)
        .linkColor(() => theme.link)
        .linkDirectionalArrowColor(() => theme.arrow)
        .nodeColor(getNodeColor);
}

function updateList(listId, sectionId, items) {
    const list = document.getElementById(listId);
    const section = document.getElementById(sectionId);
    list.innerHTML = '';
    if (items && items.length > 0) {
        section.style.display = 'block';
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
    } else {
        section.style.display = 'none';
    }
}


// ============================================================================
// Graph Initialization
// ============================================================================

const Graph = ForceGraph3D()
    (document.getElementById('graph-container'))
    .graphData(graphData)
    .nodeLabel('path')
    .nodeColor(node => {
        if (highlightedNode && !highlightedNodes.has(node.id)) {
            return 'rgba(100,100,100,0.3)';
        }
        return getNodeColor(node);
    })
    .nodeVal(getNodeSize)
    .nodeOpacity(0.9)
    .nodeThreeObject(node => {
        const lines = node.lineCount || 10;
        const colorStr = getNodeColor(node);
        const color = colorStr.startsWith('#') ? parseInt(colorStr.slice(1), 16) : 0x4fc3f7;
        
        let geometry;
        if (node.isHeader) {
            const edge = Math.max(3, lines / 10);
            geometry = new THREE.BoxGeometry(edge, edge, edge);
        } else {
            const radius = Math.max(2, lines / 40);
            geometry = new THREE.SphereGeometry(radius, 16, 12);
        }
        
        const material = new THREE.MeshLambertMaterial({
            color: color,
            transparent: true,
            opacity: 0.9
        });
        return new THREE.Mesh(geometry, material);
    })
    .nodeThreeObjectExtend(false)
    .linkColor(getLinkColor)
    .linkWidth(getLinkWidth)
    .linkDirectionalArrowLength(6)
    .linkDirectionalArrowRelPos(1)
    .linkDirectionalArrowColor(link => highlightedLinks.has(link) ? '#ff6b6b' : 'rgba(255,200,120,0.8)')
    .linkOpacity(link => highlightedLinks.has(link) ? 1 : 0.5)
    .backgroundColor('#0a0a0f')
    .onNodeClick(node => {
        if (highlightedNode === node) {
            updateHighlight(null);
        } else {
            updateHighlight(node);
        }
        
        Graph.nodeColor(Graph.nodeColor())
            .linkColor(getLinkColor)
            .linkWidth(getLinkWidth);
        
        const panel = document.getElementById('node-info');
        panel.style.display = 'block';
        
        document.getElementById('node-name').textContent = node.path;
        document.getElementById('node-type').textContent = node.isHeader ? 'Header (■)' : 'Source (●)';
        document.getElementById('node-type').className = node.isHeader ? 'header-node' : 'source-node';
        document.getElementById('node-lines').textContent = node.lineCount;
        document.getElementById('node-radius').textContent = node.radius;
        document.getElementById('node-complexity').textContent = node.complexity;
        document.getElementById('node-level').textContent = node.level;
        document.getElementById('node-community').textContent = node.community;
        
        updateList('node-classes', 'classes-section', node.classes);
        updateList('node-structs', 'structs-section', node.structs);
        updateList('node-functions', 'functions-section', node.functions);
        
        const cam = Graph.camera();
        const dx = cam.position.x - node.x;
        const dy = cam.position.y - node.y;
        const dz = cam.position.z - node.z;
        const currentDist = Math.hypot(dx, dy, dz);
        const targetDist = Math.max(200, currentDist * 0.5);
        const scale = targetDist / currentDist;
        
        Graph.cameraPosition(
            { x: node.x + dx * scale, y: node.y + dy * scale, z: node.z + dz * scale },
            node,
            1000
        );
    })
    .onBackgroundClick(() => {
        updateHighlight(null);
        Graph.nodeColor(Graph.nodeColor())
            .linkColor(getLinkColor)
            .linkWidth(getLinkWidth);
    });


// ============================================================================
// Controls Event Listeners
// ============================================================================

document.getElementById('show-labels').addEventListener('change', (e) => {
    Graph.nodeLabel(e.target.checked ? 'path' : null);
});

document.getElementById('show-arrows').addEventListener('change', (e) => {
    Graph.linkDirectionalArrowLength(e.target.checked ? 6 : 0);
});

document.getElementById('use-hierarchy').addEventListener('change', (e) => {
    useHierarchy = e.target.checked;
    if (useHierarchy) {
        const levelSpacing = 50;
        graphData.nodes.forEach(node => {
            node.fy = node.level * levelSpacing;
        });
    } else {
        graphData.nodes.forEach(node => {
            node.fy = undefined;
        });
    }
    Graph.graphData(graphData);
});

document.getElementById('color-community').addEventListener('change', (e) => {
    useCommunityColors = e.target.checked;
    Graph.nodeColor(getNodeColor);
});

document.getElementById('light-mode').addEventListener('change', (e) => {
    isLightMode = e.target.checked;
    applyTheme();
    if (boundaryVisible) drawBoundary();
});

// ============================================================================
// Boundary Canvas
// ============================================================================

const boundaryCanvas = document.createElement('canvas');
boundaryCanvas.id = 'boundary-overlay';
boundaryCanvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;display:none;';
document.body.appendChild(boundaryCanvas);

function drawBoundary() {
    if (!boundaryVisible) return;
    const ctx = boundaryCanvas.getContext('2d');
    const w = window.innerWidth;
    const h = window.innerHeight;
    boundaryCanvas.width = w;
    boundaryCanvas.height = h;
    
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = isLightMode ? 'rgba(100,100,100,0.4)' : 'rgba(100,150,200,0.3)';
    ctx.lineWidth = 1;
    
    const gridSize = 100;
    const centerX = w / 2;
    const centerY = h / 2;
    
    for (let i = -5; i <= 5; i++) {
        ctx.beginPath();
        ctx.moveTo(0, centerY + i * gridSize);
        ctx.lineTo(w, centerY + i * gridSize);
        ctx.stroke();
    }
    for (let i = -5; i <= 5; i++) {
        ctx.beginPath();
        ctx.moveTo(centerX + i * gridSize, 0);
        ctx.lineTo(centerX + i * gridSize, h);
        ctx.stroke();
    }
    
    ctx.strokeStyle = isLightMode ? 'rgba(80,80,80,0.6)' : 'rgba(100,180,255,0.4)';
    ctx.lineWidth = 2;
    const margin = 50;
    ctx.strokeRect(margin, margin, w - margin * 2, h - margin * 2);
}

document.getElementById('show-boundary').addEventListener('change', (e) => {
    boundaryVisible = e.target.checked;
    boundaryCanvas.style.display = boundaryVisible ? 'block' : 'none';
    if (boundaryVisible) drawBoundary();
});

window.addEventListener('resize', () => {
    if (boundaryVisible) drawBoundary();
});


// ============================================================================
// Fly Mode
// ============================================================================

const flySpeed = 5;
const keys = {};

document.addEventListener('keydown', (e) => { keys[e.key.toLowerCase()] = true; });
document.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });

document.getElementById('fly-mode').addEventListener('change', (e) => {
    flyMode = e.target.checked;
    Graph.controls().screenSpacePanning = flyMode;
});

(function flyLoop() {
    if (flyMode) {
        const ctrl = Graph.controls();
        if (keys['w']) ctrl.target.z -= flySpeed;
        if (keys['s']) ctrl.target.z += flySpeed;
        if (keys['a']) ctrl.target.x -= flySpeed;
        if (keys['d']) ctrl.target.x += flySpeed;
        if (keys['q'] || keys[' ']) ctrl.target.y += flySpeed;
        if (keys['e']) ctrl.target.y -= flySpeed;
        ctrl.update();
    }
    requestAnimationFrame(flyLoop);
})();

// ============================================================================
// File Tree
// ============================================================================

function buildFileTree() {
    const tree = {};
    graphData.nodes.forEach(node => {
        const parts = node.path.split('/');
        let current = tree;
        parts.forEach((part, i) => {
            if (i === parts.length - 1) {
                if (!current._files) current._files = [];
                current._files.push({ name: part, node: node });
            } else {
                if (!current[part]) current[part] = {};
                current = current[part];
            }
        });
    });
    return tree;
}

function renderTree(tree, container) {
    Object.keys(tree).filter(k => k !== '_files').sort().forEach(folder => {
        const folderDiv = document.createElement('div');
        folderDiv.className = 'tree-folder';
        
        const folderName = document.createElement('span');
        folderName.className = 'tree-folder-name';
        folderName.textContent = '📁 ' + folder;
        folderName.onclick = () => {
            const content = folderDiv.querySelector('.tree-folder-content');
            if (content) content.classList.toggle('tree-collapsed');
        };
        folderDiv.appendChild(folderName);
        
        const content = document.createElement('div');
        content.className = 'tree-folder-content';
        renderTree(tree[folder], content);
        folderDiv.appendChild(content);
        
        container.appendChild(folderDiv);
    });
    
    if (tree._files) {
        tree._files.sort((a, b) => a.name.localeCompare(b.name)).forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'tree-file ' + (file.node.isHeader ? 'header' : 'source');
            fileDiv.textContent = (file.node.isHeader ? '📄 ' : '📝 ') + file.name;
            fileDiv.onclick = () => {
                const node = graphData.nodes.find(n => n.id === file.node.id);
                if (node && node.x !== undefined) {
                    Graph.cameraPosition(
                        { x: node.x + 150, y: node.y + 150, z: node.z + 150 },
                        node,
                        1000
                    );
                    updateHighlight(node);
                    Graph.nodeColor(Graph.nodeColor())
                        .linkColor(getLinkColor)
                        .linkWidth(getLinkWidth);
                }
            };
            container.appendChild(fileDiv);
        });
    }
}

document.getElementById('show-tree').addEventListener('change', (e) => {
    const treePanel = document.getElementById('file-tree');
    treePanel.style.display = e.target.checked ? 'block' : 'none';
    if (e.target.checked && !treePanel.dataset.built) {
        const tree = buildFileTree();
        renderTree(tree, document.getElementById('tree-content'));
        treePanel.dataset.built = 'true';
    }
});

// Build tree on load
setTimeout(() => {
    const tree = buildFileTree();
    renderTree(tree, document.getElementById('tree-content'));
    document.getElementById('file-tree').dataset.built = 'true';
}, 100);
