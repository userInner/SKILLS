#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 CLEAN_9X16_FRAME OUTPUT_PREFIX" >&2
  exit 2
fi

input=$1
prefix=$2
mkdir -p "$(dirname "$prefix")"

dimensions=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height -of csv=s=x:p=0 "$input")
if [[ "$dimensions" != "1080x1920" ]]; then
  echo "expected a 1080x1920 clean cover frame, got $dimensions" >&2
  exit 1
fi

ffmpeg -hide_banner -loglevel error -y -i "$input" \
  -frames:v 1 -q:v 2 "${prefix}_9x16.jpg"
ffmpeg -hide_banner -loglevel error -y -i "$input" \
  -vf "crop=1080:1440:0:0" -frames:v 1 -q:v 2 "${prefix}_3x4.jpg"

echo "cover_9x16=${prefix}_9x16.jpg"
echo "cover_3x4=${prefix}_3x4.jpg"
