#!/usr/bin/env bash
# Edit Banana CLI wrapper — run from any directory
# Usage: edit-banana.sh <input_image_path> [output_dir]
#
# Converts diagram image → editable DrawIO XML

set -e

EDIT_BANANA_DIR="${EDIT_BANANA_DIR:-$HOME/Edit-Banana}"

# venv раскладывается по-разному: Windows кладёт интерпретатор в .venv/Scripts/python.exe,
# macOS и Linux — в .venv/bin/python. Скрипт с shebang `#!/usr/bin/env bash` писался как
# раз для *nix, а внутри стоял ТОЛЬКО Windows-путь: на маке и линуксе он честно печатал
# «venv not found» при полностью собранном venv и отправлял переустанавливать то, что уже
# стоит. Проверяем обе раскладки.
# Без переносов строки обратным слэшем: в рабочей копии .sh иногда лежат с CRLF,
# и тогда за `\` идёт возврат каретки — продолжение строки ломается, bash падает
# с syntax error. Одна строка на кандидата надёжнее.
VENV_PYTHON=""
for _cand in "$EDIT_BANANA_DIR/.venv/bin/python" "$EDIT_BANANA_DIR/.venv/bin/python3" "$EDIT_BANANA_DIR/.venv/Scripts/python.exe"; do
    if [ -x "$_cand" ] || [ -f "$_cand" ]; then
        VENV_PYTHON="$_cand"
        break
    fi
done

if [ -z "$VENV_PYTHON" ]; then
    echo "ERROR: не найден интерпретатор venv Edit Banana."
    echo "  Искал:"
    echo "    $EDIT_BANANA_DIR/.venv/bin/python        (macOS, Linux)"
    echo "    $EDIT_BANANA_DIR/.venv/Scripts/python.exe (Windows)"
    echo "  Если Edit-Banana лежит в другом месте — задай EDIT_BANANA_DIR."
    echo "  Установка: ~/.claude/skills/edit-banana/SKILL.md"
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
