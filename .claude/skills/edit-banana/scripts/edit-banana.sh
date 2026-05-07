#!/usr/bin/env bash
# Edit Banana CLI wrapper — run from any directory
# Usage: edit-banana.sh <input_image_path> [output_dir]
#
# Converts diagram image → editable DrawIO XML

set -e

EDIT_BANANA_DIR="$HOME/Edit-Banana"
VENV_PYTHON="$EDIT_BANANA_DIR/.venv/Scripts/python.exe"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Edit Banana venv not found at $VENV_PYTHON"
    echo "See ~/.claude/skills/edit-banana/SKILL.md for installation"
    exit 1
fi

INPUT="${1:-}"
if [ -z "$INPUT" ]; then
    echo "Usage: edit-banana.sh <input_image> [output_dir]"
    echo ""
    echo "Examples:"
    echo "  edit-banana.sh ~/Downloads/flowchart.png"
    echo "  edit-banana.sh ~/Downloads/diagram.jpg ~/Desktop/out/"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "ERROR: Input file not found: $INPUT"
    exit 1
fi

# Absolute path
INPUT_ABS=$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")
OUTPUT_DIR="${2:-$EDIT_BANANA_DIR/output}"
mkdir -p "$OUTPUT_DIR"

# Copy input to Edit-Banana/input/
mkdir -p "$EDIT_BANANA_DIR/input"
cp "$INPUT_ABS" "$EDIT_BANANA_DIR/input/"
BASENAME=$(basename "$INPUT_ABS")

cd "$EDIT_BANANA_DIR"
echo "Processing: $BASENAME"
"$VENV_PYTHON" main.py -i "input/$BASENAME"

# Move output if different dir
if [ "$OUTPUT_DIR" != "$EDIT_BANANA_DIR/output" ]; then
    NAME_NO_EXT="${BASENAME%.*}"
    cp "$EDIT_BANANA_DIR/output/${NAME_NO_EXT}.xml" "$OUTPUT_DIR/" 2>/dev/null || true
fi

echo ""
echo "✅ Done. Open result in https://app.diagrams.net/"
echo "   Output: $OUTPUT_DIR/${BASENAME%.*}.xml"
