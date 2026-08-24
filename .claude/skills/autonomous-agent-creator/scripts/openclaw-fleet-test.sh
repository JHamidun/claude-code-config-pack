#!/bin/bash
# openclaw-fleet-test.sh — Send test messages to all OpenClaw bots and verify responses.
#
# Requires: tg_client.py (Telethon), Python 3.10+
# Usage: bash openclaw-fleet-test.sh [--bots bot1,bot2,...] [--wait SECONDS]
#
# Default: tests all known bots with 60s wait between send and read.

set -euo pipefail

TG_CLIENT="${TG_CLIENT:-python ~/.claude/tools/tg_client.py}"
WAIT="${WAIT:-60}"

# Свой список ботов: --bots @a,@b  либо BOTS=@a,@b в окружении.
# Дефолта нет намеренно: чужой список молча разошлёт тестовые сообщения не тем ботам.
BOTS="${BOTS:-}"

# Parse --bots and --wait from args
while [[ $# -gt 0 ]]; do
  case $1 in
    --bots) BOTS="$2"; shift 2 ;;
    --wait) WAIT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$BOTS" ]; then
  echo "Укажи ботов: bash openclaw-fleet-test.sh --bots @bot1,@bot2" >&2
  exit 2
fi

IFS=',' read -ra BOT_ARRAY <<< "$BOTS"

echo "=== OpenClaw Fleet Test ==="
echo "Bots: ${BOT_ARRAY[*]}"
echo "Wait: ${WAIT}s"
echo ""

# --- Phase 1: Send test messages ---
echo "[Phase 1] Sending test messages..."
for bot in "${BOT_ARRAY[@]}"; do
  MSYS_NO_PATHCONV=1 $TG_CLIENT send "$bot" "тест — проверка работоспособности $(date +%H:%M)" 2>&1 | tail -1
done

echo ""
echo "[Phase 2] Waiting ${WAIT}s for responses..."
sleep "$WAIT"

echo ""
echo "[Phase 3] Reading responses..."
echo ""

PASS=0
FAIL=0

for bot in "${BOT_ARRAY[@]}"; do
  echo "=== $bot ==="
  RESPONSE=$($TG_CLIENT read-chat "$bot" --limit 1 2>&1 | tail -10)
  echo "$RESPONSE"

  # Check if bot responded (not just our message)
  if echo "$RESPONSE" | grep -qv "^$" && echo "$RESPONSE" | grep -qiE "тест|проверк|работ|привет|OK|✅|готов"; then
    echo "→ ✅ PASS"
    ((PASS++)) || true
  elif echo "$RESPONSE" | grep -qiE "error|failed|rate limit"; then
    echo "→ ❌ FAIL (error in response)"
    ((FAIL++)) || true
  else
    echo "→ ⚠️ UNCLEAR (check manually)"
    ((FAIL++)) || true
  fi
  echo ""
done

echo "=== Results ==="
echo "Pass: $PASS / ${#BOT_ARRAY[@]}"
echo "Fail: $FAIL / ${#BOT_ARRAY[@]}"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "⚠️  Some bots failed. Check AI Gateway:"
  echo "  ssh \$SERVER 'docker logs ai-gateway --since 5m 2>&1 | grep -E \"ERROR|EXHAUSTED\"'"
  exit 1
fi
