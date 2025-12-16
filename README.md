# Code-Graph-4D

A 3D/4D visualization tool for C++ codebase architecture analysis.

## Features

- 📁 Parse C++ source files (headers, classes, structs, functions, global variables)
- 🔗 Analyze file dependencies through `#include` directives
- 🌐 Generate interactive 3D force-directed graph in browser
- ⏱️ (Future) 4th dimension: Git history timeline visualization

## Installation

```bash
# Create conda environment
conda create -n code-graph python=3.12 -y
conda activate code-graph

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Analyze a C++ project
python -m code_graph_4d.main /path/to/cpp/project

# Output: opens browser with 3D visualization
```

## Tech Stack

- Python 3.12 + NetworkX (graph construction)
- tree-sitter (C++ parsing)
- 3d-force-graph (Three.js based 3D visualization)

## Project Structure

```
code-graph-4d/
├── code_graph_4d/
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── parser.py         # C++ file parser
│   ├── graph_builder.py  # NetworkX graph construction
│   └── visualizer.py     # HTML/JS 3D output
├── templates/
│   └── graph.html        # 3D visualization template
├── requirements.txt
└── README.md
```

## License

MIT
