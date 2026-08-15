#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 INPUT.pdf OUTPUT_DIR [PAGES_COMMA_SEPARATED]" >&2
  exit 2
fi

input=$1
output=$2
pages=${3:-1}

pdftotext_bin=$(command -v pdftotext || true)
pdftoppm_bin=$(command -v pdftoppm || true)
if [[ -z "$pdftotext_bin" || -z "$pdftoppm_bin" ]]; then
  echo "Poppler tools pdftotext and pdftoppm are required" >&2
  exit 1
fi

mkdir -p "$output/pages"
"$pdftotext_bin" -layout "$input" "$output/paper.txt"

IFS=',' read -r -a page_list <<< "$pages"
for page in "${page_list[@]}"; do
  if [[ ! "$page" =~ ^[0-9]+$ ]] || (( page < 1 )); then
    echo "invalid page: $page" >&2
    exit 2
  fi
  "$pdftoppm_bin" -f "$page" -l "$page" -png -r 220 -singlefile \
    "$input" "$output/pages/page_$page"
done

echo "text=$output/paper.txt"
echo "pages=$output/pages"
