# Code-Graph-4D

A 3D/4D visualization tool for C++ codebase architecture analysis.

![Demo](https://img.shields.io/badge/Python-3.14-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

- 📁 Parse C++ source files (headers, classes, structs, functions)
- 🔗 Analyze file dependencies through `#include` directives
- 🌐 Interactive 3D force-directed graph in browser
- 🎨 Community detection (auto-discover modules)
- 📊 Hierarchy level analysis
- 🔍 Click to highlight dependency chains
- 🌳 File tree panel for navigation
- 🌓 Light/Dark mode
- ✈️ Fly mode (WASD navigation)

## Installation

```bash
# Create conda environment
conda create -n code-graph python=3.14 -y
conda activate code-graph

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Quick start
./compile_and_start.sh /path/to/cpp/project

# Or manually
python -m code_graph_4d.main /path/to/cpp/project
```

## Controls

| Control | Action |
|---------|--------|
| Drag | Rotate view |
| Scroll | Zoom |
| Click node | Highlight dependencies |
| Click background | Clear highlight |
| WASD (Fly mode) | Navigate |
| Q/E (Fly mode) | Up/Down |

## Visualization

- **Node Shape**: Header (.h) = Box ■, Source (.cpp) = Sphere ●
- **Node Size**: Based on line count
- **Node Color**: Community-based (auto-detected modules)
- **Edge Width**: Based on reference count

## Project Structure

```
code-graph-4d/
├── code_graph_4d/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── parser.py            # C++ file parser (tree-sitter)
│   ├── graph_builder.py     # NetworkX graph construction
│   ├── visualizer.py        # HTML generation
│   └── templates/
│       ├── graph.html       # HTML structure
│       ├── styles.css       # CSS styles
│       └── graph.js         # JavaScript logic
├── compile_and_start.sh     # Quick start script
├── requirements.txt
└── README.md
```

## Tech Stack

- Python 3.14 + NetworkX (graph analysis)
- tree-sitter (C++ parsing)
- 3d-force-graph + Three.js (3D visualization)

## Future (4th Dimension)

- ⏱️ Git history timeline visualization
- 🔥 Code complexity heatmap
- 👥 Team ownership overlay

## License

MIT
