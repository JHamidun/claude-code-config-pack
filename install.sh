#!/usr/bin/env bash
# Claude Code config installer (macOS / Linux)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_CLAUDE="$HERE/.claude"
SRC_CLAUDE_MD="$HERE/CLAUDE.md"
SRC_ENV_TEMPLATE="$HERE/.credentials.template.env"
DST_CLAUDE="$HOME/.claude"
DST_CLAUDE_MD="$HOME/CLAUDE.md"
DST_ENV="$DST_CLAUDE/.credentials.master.env"

BACKUP=0
SKIP_DEPS=0
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --backup) BACKUP=1 ;;
        --skip-deps) SKIP_DEPS=1 ;;
        --force) FORCE=1 ;;
        -h|--help) echo "Usage: ./install.sh [--backup] [--skip-deps] [--force]"; exit 0 ;;
    esac
done

[ ! -d "$SRC_CLAUDE" ] && { echo "ERROR: $SRC_CLAUDE not found." >&2; exit 1; }

if [ "$BACKUP" -eq 1 ] && [ -d "$DST_CLAUDE" ]; then
    stamp=$(date +%Y%m%d-%H%M%S)
    mv "$DST_CLAUDE" "$DST_CLAUDE.backup.$stamp"
fi

mkdir -p "$DST_CLAUDE"
echo "Copying .claude/* ..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a \
        --exclude='.credentials.master.env' \
        --exclude='MEMORY.md' \
        --exclude='chats.db*' \
        --exclude='tg_session.session*' \
        "$SRC_CLAUDE/" "$DST_CLAUDE/"
else
    cp -R "$SRC_CLAUDE/." "$DST_CLAUDE/"
    # Recursive cleanup of files we never want to overwrite
    find "$DST_CLAUDE" -type f \( \
        -name '.credentials.master.env' -o \
        -name 'MEMORY.md' -o \
        -name 'chats.db*' -o \
        -name 'tg_session.session*' \
    \) -delete 2>/dev/null || true
fi

if [ -f "$DST_CLAUDE_MD" ] && [ "$FORCE" -ne 1 ]; then
    cp "$DST_CLAUDE_MD" "$DST_CLAUDE_MD.backup.$(date +%Y%m%d-%H%M%S)"
fi
cp "$SRC_CLAUDE_MD" "$DST_CLAUDE_MD"

if [ ! -f "$DST_ENV" ]; then
    cp "$SRC_ENV_TEMPLATE" "$DST_ENV"
    echo "Created $DST_ENV -- fill in your API keys."
else
    echo "$DST_ENV already exists -- left alone."
fi

if [ "$SKIP_DEPS" -ne 1 ] && [ -f "$HERE/requirements.txt" ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --user --upgrade pip >/dev/null 2>&1 || true
        python3 -m pip install --user -r "$HERE/requirements.txt" || \
            echo "Python deps install failed (skipping)."
    fi
fi

echo
echo "DONE."
echo "Next: edit $DST_ENV  ->  edit $DST_CLAUDE/rules/user-profile.md  ->  run 'claude'"
