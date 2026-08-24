#!/usr/bin/env bash
# Daily incremental backup of Claude Code transcripts + search index (macOS/Linux).
# Windows twin: backup-transcripts.cmd (same layout, same destination name).
#
# Run it by hand, or from cron:
#   0 21 * * *  bash "$HOME/.claude/scripts/backup-transcripts.sh" >/dev/null
#
# Nothing is ever deleted from the backup (no rsync --delete): an upstream wipe
# (like the July 2026 cleanupPeriodDays regression) cannot propagate here.
# Every step reports its own failure and the script exits non-zero — a backup
# that silently copied nothing is worse than no backup at all.

set -uo pipefail

CLAUDE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$HOME/claude-transcripts-backup"
LOG="$DST/backup.log"
failed=0

if [ ! -d "$CLAUDE_DIR/projects" ]; then
  echo "[backup] FATAL: $CLAUDE_DIR/projects not found - nothing to back up." >&2
  exit 1
fi

mkdir -p "$DST" || { echo "[backup] FATAL: cannot create $DST" >&2; exit 1; }

echo "[backup] source: $CLAUDE_DIR"
echo "[backup] target: $DST"

# 1) Index new sessions into chats.db so the searchable history is always current
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "[backup] WARN: no python on PATH - chats.db index NOT refreshed." >&2
  echo "[$(date '+%F %T')] WARN: python missing, index skipped" >> "$LOG"
  failed=1
else
  PYTHONIOENCODING=utf-8 "$PY" "$CLAUDE_DIR/tools/search_chats.py" index >> "$LOG" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "[backup] WARN: search_chats.py index failed (exit $rc) - see $LOG" >&2
    failed=1
  fi
fi

# 2) Back up transcripts
if command -v rsync >/dev/null 2>&1; then
  if ! rsync -a "$CLAUDE_DIR/projects/" "$DST/projects/" >> "$LOG" 2>&1; then
    echo "[backup] ERROR: rsync of projects/ failed - see $LOG" >&2
    failed=1
  fi
else
  mkdir -p "$DST/projects"
  if ! cp -R "$CLAUDE_DIR/projects/." "$DST/projects/" >> "$LOG" 2>&1; then
    echo "[backup] ERROR: cp of projects/ failed - see $LOG" >&2
    failed=1
  fi
fi

# 3) Back up the search index
if [ -f "$CLAUDE_DIR/chats.db" ]; then
  if ! cp -p "$CLAUDE_DIR/chats.db" "$DST/chats.db" >> "$LOG" 2>&1; then
    echo "[backup] ERROR: copy of chats.db failed - see $LOG" >&2
    failed=1
  fi
else
  echo "[backup] WARN: no chats.db yet - search index not backed up." >&2
fi

if [ "$failed" -ne 0 ]; then
  echo "[$(date '+%F %T')] backup FINISHED WITH ERRORS" >> "$LOG"
  echo "[backup] FINISHED WITH ERRORS - backup is incomplete. Log: $LOG" >&2
  exit 1
fi

echo "[$(date '+%F %T')] backup done" >> "$LOG"
echo "[backup] done."
