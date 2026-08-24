#!/usr/bin/env bash
# Portable installer for the "check-skill-solo" Claude Code skill.
# Works on macOS and Linux. No GNU-only tools, no `timeout`, no sudo.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DEST="$HOME/.claude/skills/check-skill-solo"

mkdir -p "$DEST"
cp "$SRC_DIR/SKILL.md" "$DEST/SKILL.md"
[ -f "$SRC_DIR/README.md" ] && cp "$SRC_DIR/README.md" "$DEST/README.md" || true

echo "✅ Installed skill to: $DEST/SKILL.md"
echo ""
echo "Detected cross-check CLIs (optional — skill degrades gracefully if missing):"
for c in codex gemini agy; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "   ✓ $c  -> $(command -v "$c")"
  else
    echo "   · $c  not found (this channel will fall back to an isolated Claude search)"
  fi
done

echo ""
echo "Done. Restart Claude Code, then run:"
echo "   /check-skill-solo <fact or claim to verify>"
echo ""
echo "Optional: for full 3-family verification install the CLIs and log in once:"
echo "   npm install -g @openai/codex      &&  codex   # log in"
echo "   npm install -g @google/gemini-cli &&  gemini  # log in"
