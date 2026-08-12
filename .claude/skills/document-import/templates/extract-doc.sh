#!/usr/bin/env bash
set -e
file="$1"; out="${2:-extracted}"
mkdir -p "$out"
case "${file##*.}" in
  docx|DOCX) unzip -qo "$file" -d "$out/docx";;
  pptx|PPTX) unzip -qo "$file" -d "$out/pptx";;
  pdf|PDF)
    command -v pdftotext >/dev/null && pdftotext -layout "$file" "$out/text.txt"
    command -v pdfimages >/dev/null && pdfimages -all "$file" "$out/img" || true
    ;;
  *) echo "Не понимаю расширение: $file"; exit 1;;
esac
echo "✓ См. $out/"
