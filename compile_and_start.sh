#!/bin/bash
# Code-Graph-4D: Setup, run, and visualize

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="code_graph_314"
TARGET_PATH="${1:-../unreal_project/Source}"
OUTPUT_FILE="$SCRIPT_DIR/code_graph_output.html"

# Initialize conda
source "$(conda info --base)/etc/profile.d/conda.sh"

# Create environment if not exists
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "🔧 Creating conda environment: $ENV_NAME (Python 3.14)"
    conda create -n $ENV_NAME python=3.14 -y
fi

# Activate environment
echo "🐍 Activating environment: $ENV_NAME"
conda activate $ENV_NAME

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Run analysis
echo "🔍 Analyzing: $TARGET_PATH"
cd "$SCRIPT_DIR"
python -m code_graph_4d.main "$TARGET_PATH" -o "$OUTPUT_FILE" --no-open

# Open in browser
echo "🌐 Opening visualization..."
open "$OUTPUT_FILE"

echo "✅ Done!"
