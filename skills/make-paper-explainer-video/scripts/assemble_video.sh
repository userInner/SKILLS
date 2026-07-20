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

ffmpeg -hide_banner -loglevel error -y \
  -framerate "$fps" -i "$frames/frame_%05d.jpg" -i "$audio" \
  -filter_complex "[1:a]highpass=f=65,lowpass=f=12000,acompressor=threshold=-20dB:ratio=2:attack=10:release=180,alimiter=limit=.94[a]" \
  -map 0:v -map '[a]' -c:v libx264 -preset medium -crf 20 \
  -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart \
  -shortest "$output"
