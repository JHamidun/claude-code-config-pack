#!/usr/bin/env bash
# gh-pull.sh — скачать файл или папку из GitHub-репы.
# Usage: ./gh-pull.sh <github-url> [out-dir]

set -euo pipefail

URL="${1:?передай GitHub URL}"
OUT_BASE="${2:-gh-import}"

# Парсим URL
proto="${URL#https://github.com/}"
IFS='/' read -ra parts <<< "$proto"
OWNER="${parts[0]}"
REPO="${parts[1]}"
TYPE="${parts[2]:-tree}"
REF="${parts[3]:-HEAD}"
PATH_IN_REPO=$(IFS=/; echo "${parts[*]:4}")

OUT="${OUT_BASE}/${OWNER}-${REPO}/${PATH_IN_REPO}"
mkdir -p "$OUT"

AUTH=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  AUTH=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

if [[ "$TYPE" == "blob" ]]; then
  echo "→ Один файл: $PATH_IN_REPO"
  raw="https://raw.githubusercontent.com/${OWNER}/${REPO}/${REF}/${PATH_IN_REPO}"
  curl -sL "${AUTH[@]}" "$raw" -o "${OUT_BASE}/${OWNER}-${REPO}/$(basename "$PATH_IN_REPO")"
  echo "✓ ${OUT_BASE}/${OWNER}-${REPO}/$(basename "$PATH_IN_REPO")"
  exit 0
fi

echo "→ Папка: $PATH_IN_REPO (рекурсивно)"
api="https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH_IN_REPO}?ref=${REF}"

walk() {
  local api_url="$1"
  local local_dir="$2"
  mkdir -p "$local_dir"
  curl -sL "${AUTH[@]}" "$api_url" | jq -c '.[]' | while read -r item; do
    name=$(echo "$item" | jq -r .name)
    type=$(echo "$item" | jq -r .type)
    download=$(echo "$item" | jq -r .download_url)
    sub_url=$(echo "$item" | jq -r '.url')
    if [[ "$type" == "file" ]]; then
      curl -sL "${AUTH[@]}" "$download" -o "${local_dir}/${name}"
      echo "  ✓ ${local_dir}/${name}"
    elif [[ "$type" == "dir" ]]; then
      walk "$sub_url" "${local_dir}/${name}"
    fi
  done
}

walk "$api" "$OUT"
echo "Готово. См. $OUT"
