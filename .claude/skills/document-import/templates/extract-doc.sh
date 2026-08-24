#!/usr/bin/env bash
set -e
file="$1"; out="${2:-extracted}"
mkdir -p "$out"

# Распаковка без внешней программы `unzip`.
# На Windows её нет ни в системе, ни в Git Bash — а docx/pptx/sketch это обычные zip.
# Python в паке обязателен, его zipfile делает ровно то же. Имя интерпретатора
# ищем оба: python3 нет на Windows, python нет на macOS 12.3+ и голой Ubuntu.
PY="$(command -v python3 || command -v python || true)"

unzip_to() {  # $1=архив $2=куда
  if command -v unzip >/dev/null 2>&1; then
    unzip -qo "$1" -d "$2"
  elif [ -n "$PY" ]; then
    "$PY" -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$1" "$2"
  else
    echo "Распаковать нечем: нет ни unzip, ни python/python3 в PATH." >&2
    echo "  Поставь любое из двух — Python нужен паку и так." >&2
    exit 1
  fi
}

case "${file##*.}" in
  docx|DOCX) unzip_to "$file" "$out/docx";;
  pptx|PPTX) unzip_to "$file" "$out/pptx";;
  sketch|SKETCH) unzip_to "$file" "$out/sketch";;
  pdf|PDF)
    if command -v pdftotext >/dev/null 2>&1; then
      pdftotext -layout "$file" "$out/text.txt"
    else
      echo "pdftotext не найден (пакет poppler) — текст из PDF не извлечён." >&2
    fi
    command -v pdfimages >/dev/null 2>&1 && pdfimages -all "$file" "$out/img" || true
    ;;
  *) echo "Не понимаю расширение: $file"; exit 1;;
esac
echo "✓ См. $out/"
