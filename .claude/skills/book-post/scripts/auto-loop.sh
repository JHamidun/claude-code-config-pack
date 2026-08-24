#!/bin/bash
# auto-loop.sh — keeps N parallel book-post passes alive on the chapter queue
#
# Walks chapters/<slug>/DRAFT.md, picks chapters that don't have the target
# output file yet, runs voice-pass / proofread / fact-check on them in parallel.
#
# Usage:
#   PROVIDER=codex PASS=voice ./auto-loop.sh
#   PROVIDER=codex PASS=proofread INPUT=voice-pass ./auto-loop.sh
#   PROVIDER=claude PASS=fact-check INPUT=proofread ./auto-loop.sh
#
# Stop:
#   touch /tmp/book-post.stop
#
# Env:
#   PROVIDER       codex (default) | claude
#   PASS           voice | proofread | fact-check
#   INPUT          (optional) draft | voice-pass | proofread (для proofread/fact-check)
#   PARALLEL       max concurrent runs (default 2 — главы тяжелее новостей)
#   BOOK_ROOT      root of the book directory (default ~/book)

set -e
cd "$(dirname "$0")"

STOP_FILE=/tmp/book-post.stop
PID_FILE=/tmp/book-post-loop.pid
SELF_PID=$$

if [ -f "$PID_FILE" ]; then
  prev=$(cat "$PID_FILE" 2>/dev/null || echo "")
  if [ -n "$prev" ] && kill -0 "$prev" 2>/dev/null; then
    echo "[book-loop] already running as PID $prev — exiting"
    exit 0
  fi
fi
echo "$SELF_PID" > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

PROVIDER=${PROVIDER:-codex}
PASS=${PASS:-voice}
INPUT=${INPUT:-draft}
PARALLEL=${PARALLEL:-2}
BOOK_ROOT=${BOOK_ROOT:-$HOME/book}

# По умолчанию НЕ используем Claude как fallback — бережём лимит на ручную литературную правку.
# Чтобы разрешить fallback на Claude — запускай с BOOK_NO_CLAUDE=0
export BOOK_NO_CLAUDE=${BOOK_NO_CLAUDE:-1}

case "$PASS" in
  voice)      SCRIPT=voice-pass.js; OUT=DRAFT.voice-pass.md ;;
  proofread)  SCRIPT=proofread.js; OUT=DRAFT.proofread.md ;;
  fact-check) SCRIPT=fact-check.js; OUT=FACT-REPORT.md ;;
  web)        SCRIPT=fact-check-web.js; OUT=WEB-FACT-REPORT.md ;;
  *)          echo "Unknown PASS=$PASS (voice|proofread|fact-check|web)"; exit 2 ;;
esac

LOG_DIR=/tmp/book-post-loop
mkdir -p "$LOG_DIR/active"

echo "[book-loop] start: PASS=$PASS PROVIDER=$PROVIDER INPUT=$INPUT PARALLEL=$PARALLEL"
echo "[book-loop] script=$SCRIPT out_file=$OUT book_root=$BOOK_ROOT"

# Find chapters that have DRAFT.md but no OUT yet
list_pending() {
  for chapter_dir in "$BOOK_ROOT"/chapters/*/; do
    [ -f "$chapter_dir/DRAFT.md" ] || continue
    [ -f "$chapter_dir/$OUT" ] && continue
    basename "$chapter_dir"
  done
}

run_one() {
  local slug=$1
  local ts=$(date +%Y%m%d_%H%M%S)
  local lock="$LOG_DIR/active/${slug}_${ts}.lock"
  local logf="$LOG_DIR/${PASS}_${slug}_${ts}.log"
  echo "[$(date -Iseconds)] launching: $slug → $logf"
  (
    if [ "$PASS" = "voice" ]; then
      node "$SCRIPT" --chapter "$slug" --provider "$PROVIDER" > "$logf" 2>&1
    else
      node "$SCRIPT" --chapter "$slug" --provider "$PROVIDER" --input "$INPUT" > "$logf" 2>&1
    fi
    rm -f "$lock"
  ) &
  echo "$!" > "$lock"
}

while true; do
  if [ -f "$STOP_FILE" ]; then
    echo "[$(date -Iseconds)] stop file detected — exiting"
    exit 0
  fi

  # Sweep stale locks (process gone)
  for lock in "$LOG_DIR/active"/*.lock; do
    [ -f "$lock" ] || continue
    pid=$(cat "$lock" 2>/dev/null)
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$lock"
    fi
  done
  active=$(ls "$LOG_DIR/active"/*.lock 2>/dev/null | wc -l || echo 0)

  if [ "$active" -lt "$PARALLEL" ]; then
    pending=$(list_pending | head -1)
    if [ -z "$pending" ]; then
      echo "[$(date -Iseconds)] queue empty (active=$active) — exiting"
      exit 0
    fi
    run_one "$pending"
    sleep 30  # let new run start before re-checking
  else
    sleep 30
  fi
done
