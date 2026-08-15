#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 VIDEO.mp4" >&2
  exit 2
fi

video=$1
probe=$(ffprobe -v error -show_entries \
  format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate \
  -of json "$video")
echo "$probe"

width=$(printf '%s' "$probe" | jq -r '.streams[] | select(.codec_type=="video") | .width')
height=$(printf '%s' "$probe" | jq -r '.streams[] | select(.codec_type=="video") | .height')
video_codec=$(printf '%s' "$probe" | jq -r '.streams[] | select(.codec_type=="video") | .codec_name')
audio_codec=$(printf '%s' "$probe" | jq -r '.streams[] | select(.codec_type=="audio") | .codec_name')

[[ "$width" == "1080" && "$height" == "1920" ]] || { echo "expected 1080x1920" >&2; exit 1; }
[[ "$video_codec" == "h264" ]] || { echo "expected H.264" >&2; exit 1; }
[[ "$audio_codec" == "aac" ]] || { echo "expected AAC" >&2; exit 1; }
echo "video validation passed"
