# Code-Graph-4D

English | [中文](README.md)

A 3D/4D visualization tool for C++ codebase architecture analysis.

## Features

| | |
|:---:|:---:|
| ![UI1](asset/ui1.png) | ![UI2](asset/ui2.png) |

- 📁 Parse C++ source files (headers, classes, structs, functions)
- 🔗 Analyze file dependencies through `#include` directives
- 🌐 Interactive 3D force-directed graph in browser
- 🎨 Community detection (auto-discover modules)
- 📊 Hierarchy level analysis
- 🔍 Click to highlight dependency chains
- 🌳 File tree panel for navigation
- 🌓 Light/Dark mode
- ✈️ Fly mode (WASD navigation)

## Quick Start

```bash
./compile_and_start.sh /path/to/cpp/project
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
│   ├── main.py              # CLI entry point
│   ├── parser.py            # C++ parser
│   ├── graph_builder.py     # NetworkX graph construction
│   ├── visualizer.py        # HTML generation
│   └── templates/           # Frontend templates
├── compile_and_start.sh     # Quick start script
└── README.md
```

## Tech Stack

- Python 3.14 + NetworkX
- tree-sitter (C++ parsing)
- 3d-force-graph + Three.js

## Future (4th Dimension)

- ⏱️ Git history timeline visualization
- 🔥 Code complexity heatmap
- 👥 Team ownership overlay

## License

MIT
