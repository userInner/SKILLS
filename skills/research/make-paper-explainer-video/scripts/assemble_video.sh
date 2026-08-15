#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 FRAMES_DIR AUDIO.wav OUTPUT.mp4 INPUT_FPS" >&2
  exit 2
fi

frames=$1
audio=$2
output=$3
fps=$4
audio_filter=${AUDIO_FILTER:-anull}

ffmpeg -hide_banner -loglevel error -y \
  -framerate "$fps" -i "$frames/frame_%05d.jpg" -i "$audio" \
  -filter_complex "[1:a]${audio_filter}[a]" \
  -map 0:v -map '[a]' -c:v libx264 -preset medium -crf 20 \
  -pix_fmt yuv420p -r 30 -c:a aac -b:a 128k -movflags +faststart \
  -shortest "$output"
