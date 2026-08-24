#!/usr/bin/env bash
# token-rotator.sh — round-robin over several Claude subscription tokens.
#
# Layout it expects (created by the auth procedure in SKILL.md):
#
#   $ACCOUNTS_DIR/            default: /root/.claude-accounts
#     account-1/token.txt     one sk-ant-oat01-... per file, chmod 600
#     account-2/token.txt
#     .active                 index of the account in use (this script writes it)
#
# Override the directory with CLAUDE_ACCOUNTS_DIR=/somewhere/else.
#
# Commands (see SKILL.md "Token Rotation Setup"):
#   status     list accounts and mark the active one
#   get        print the active token, no rotation
#   rotate     advance to the next account, print its token
#   validate   call the API with the active token; exit 0 only if it answers
#   get-valid  print a token that actually works — rotates on failure, up to 3 tries
#   init       re-scan account directories and reset the active pointer if it dangles
#
# Nothing here is Claude-Code-specific: it is plain bash + curl, runs on the server.

set -uo pipefail

ACCOUNTS_DIR="${CLAUDE_ACCOUNTS_DIR:-/root/.claude-accounts}"
ACTIVE_FILE="$ACCOUNTS_DIR/.active"
VALIDATE_MODEL="${CLAUDE_VALIDATE_MODEL:-claude-haiku-4-5-20251001}"

die() { echo "token-rotator: $*" >&2; exit 1; }

# All account dirs that actually hold a non-empty token, sorted, as an array.
list_accounts() {
  local d
  for d in "$ACCOUNTS_DIR"/*/; do
    [ -s "${d}token.txt" ] && basename "$d"
  done | sort
}

accounts_array() {
  mapfile -t ACCOUNTS < <(list_accounts)
  [ "${#ACCOUNTS[@]}" -gt 0 ] || die "no accounts with a token.txt under $ACCOUNTS_DIR — run the auth procedure in SKILL.md first"
}

active_index() {
  local n="${#ACCOUNTS[@]}" i=0
  [ -f "$ACTIVE_FILE" ] && i="$(cat "$ACTIVE_FILE" 2>/dev/null || echo 0)"
  case "$i" in ''|*[!0-9]*) i=0 ;; esac
  [ "$i" -lt "$n" ] || i=0            # pointer past the end (an account was removed)
  echo "$i"
}

set_index() { printf '%s\n' "$1" > "$ACTIVE_FILE"; }

token_of() { cat "$ACCOUNTS_DIR/$1/token.txt"; }

# Exit 0 only when the API answered with this token. Never prints the token.
probe() {
  local token="$1" code
  code="$(curl -sS -o /dev/null -w '%{http_code}' \
    --max-time 30 \
    -X POST https://api.anthropic.com/v1/messages \
    -H "authorization: Bearer $token" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "{\"model\":\"$VALIDATE_MODEL\",\"max_tokens\":4,\"messages\":[{\"role\":\"user\",\"content\":\"OK\"}]}" \
    2>/dev/null)" || return 1
  [ "$code" = "200" ]
}

cmd_status() {
  accounts_array
  local cur; cur="$(active_index)"
  local i
  for i in "${!ACCOUNTS[@]}"; do
    if [ "$i" = "$cur" ]; then printf '* %s (active)\n' "${ACCOUNTS[$i]}"
    else                       printf '  %s\n'          "${ACCOUNTS[$i]}"; fi
  done
}

cmd_get() {
  accounts_array
  token_of "${ACCOUNTS[$(active_index)]}"
}

cmd_rotate() {
  accounts_array
  local cur next
  cur="$(active_index)"
  next=$(( (cur + 1) % ${#ACCOUNTS[@]} ))
  set_index "$next"
  echo "rotated: ${ACCOUNTS[$cur]} -> ${ACCOUNTS[$next]}" >&2
  token_of "${ACCOUNTS[$next]}"
}

cmd_validate() {
  accounts_array
  local acct; acct="${ACCOUNTS[$(active_index)]}"
  if probe "$(token_of "$acct")"; then
    echo "ok: $acct" >&2
  else
    echo "FAILED: $acct" >&2
    exit 1
  fi
}

cmd_get_valid() {
  accounts_array
  local n="${#ACCOUNTS[@]}" tries=3 i acct token
  [ "$tries" -gt "$n" ] && tries="$n"
  i="$(active_index)"
  local attempt
  for (( attempt = 0; attempt < tries; attempt++ )); do
    acct="${ACCOUNTS[$i]}"
    token="$(token_of "$acct")"
    if probe "$token"; then
      set_index "$i"
      printf '%s\n' "$token"
      return 0
    fi
    echo "token-rotator: $acct did not answer, trying the next account" >&2
    i=$(( (i + 1) % n ))
  done
  die "no working token after $tries attempts — re-authenticate (see SKILL.md)"
}

cmd_init() {
  [ -d "$ACCOUNTS_DIR" ] || die "$ACCOUNTS_DIR does not exist"
  accounts_array
  local cur; cur="$(active_index)"
  set_index "$cur"
  echo "found ${#ACCOUNTS[@]} account(s); active: ${ACCOUNTS[$cur]}" >&2
  cmd_status
}

case "${1:-}" in
  status)    cmd_status ;;
  get)       cmd_get ;;
  rotate)    cmd_rotate ;;
  validate)  cmd_validate ;;
  get-valid) cmd_get_valid ;;
  init)      cmd_init ;;
  *) cat >&2 <<USAGE
usage: token-rotator.sh {status|get|rotate|validate|get-valid|init}

  accounts dir: $ACCOUNTS_DIR   (override with CLAUDE_ACCOUNTS_DIR)
  probe model:  $VALIDATE_MODEL (override with CLAUDE_VALIDATE_MODEL)
USAGE
     exit 2 ;;
esac
