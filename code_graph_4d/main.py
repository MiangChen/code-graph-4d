"""Main entry point for Code-Graph-4D."""

import argparse
import sys
from pathlib import Path

from .parser import scan_directory
from .graph_builder import build_dependency_graph, get_graph_stats, enrich_graph_with_analysis
from .visualizer import generate_html, open_in_browser


def main():
    parser = argparse.ArgumentParser(
        description='Code-Graph-4D: 3D visualization for C++ codebase architecture'
    )
    parser.add_argument(
        'path',
        type=Path,
        help='Path to C++ project directory to analyze'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('code_graph.html'),
        help='Output HTML file path (default: code_graph.html)'
    )
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Do not open browser automatically'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed parsing information'
    )
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    if not args.path.is_dir():
        print(f"Error: '{args.path}' is not a directory")
        sys.exit(1)
    
    print(f"🔍 Scanning: {args.path}")
    files = scan_directory(args.path)
    
    if not files:
        print("No C++ files found!")
        sys.exit(1)
    
    print(f"📁 Found {len(files)} C++ files")
    
    if args.verbose:
        for f in files:
            print(f"  - {f.path.name}: {len(f.classes)} classes, {len(f.functions)} functions")
    
    print("🔗 Building dependency graph...")
    graph = build_dependency_graph(files, args.path)
    
    print("🧠 Analyzing hierarchy and communities...")
    graph = enrich_graph_with_analysis(graph)
    
    stats = get_graph_stats(graph)
    print(f"📊 Graph: {stats['total_files']} nodes, {stats['total_dependencies']} edges")
    print(f"   Headers: {stats['headers']}, Sources: {stats['sources']}")
    
    if stats['most_depended']:
        top = stats['most_depended'][0]
        print(f"   Most included: {top[0]} ({top[1]} times)")
    
    print(f"🎨 Generating visualization...")
    output_path = generate_html(graph, args.output, title=f"Code Graph: {args.path.name}")
    print(f"✅ Output: {output_path.absolute()}")
    
    if not args.no_open:
        print("🌐 Opening in browser...")
        open_in_browser(output_path)


if __name__ == '__main__':
    main()
