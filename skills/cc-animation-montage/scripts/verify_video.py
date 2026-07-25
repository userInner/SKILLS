#!/usr/bin/env python3
import argparse
import json
import math
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path: Path) -> dict:
    output = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        text=True,
    )
    return json.loads(output)


def audio_metrics(path: Path) -> dict:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-vn",
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    mean_match = re.search(r"mean_volume:\s+(-?[0-9.]+) dB", completed.stdout)
    max_match = re.search(r"max_volume:\s+(-?[0-9.]+) dB", completed.stdout)
    return {
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
        "max_volume_db": float(max_match.group(1)) if max_match else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode and verify a final montage export.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--max-peak-db", type=float, default=0.0)
    args = parser.parse_args()

    for executable in ("ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise SystemExit(f"{executable} is required")
    if not args.input.is_file():
        raise SystemExit(f"input not found: {args.input}")

    data = probe(args.input)
    videos = [stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"]
    audios = [stream for stream in data.get("streams", []) if stream.get("codec_type") == "audio"]
    failures = []
    if len(videos) != 1:
        failures.append(f"expected one video stream, found {len(videos)}")
    if len(audios) != 1:
        failures.append(f"expected one audio stream, found {len(audios)}")

    video = videos[0] if videos else {}
    duration = float(data.get("format", {}).get("duration", 0))
    fps = float(Fraction(video.get("r_frame_rate", "0/1")))
    frames = int(video.get("nb_frames", 0) or 0)
    expected_frames = round(args.duration * args.fps)

    if not math.isclose(duration, args.duration, abs_tol=1 / args.fps):
        failures.append(f"duration {duration:.6f} != {args.duration:.6f}")
    if frames != expected_frames:
        failures.append(f"frame count {frames} != {expected_frames}")
    if not math.isclose(fps, args.fps, abs_tol=0.001):
        failures.append(f"fps {fps} != {args.fps}")
    if video.get("width") != args.width or video.get("height") != args.height:
        failures.append(f"dimensions {video.get('width')}x{video.get('height')} != {args.width}x{args.height}")
    if video.get("codec_name") != "h264":
        failures.append(f"video codec is {video.get('codec_name')}, expected h264")
    if video.get("pix_fmt") != "yuv420p":
        failures.append(f"pixel format is {video.get('pix_fmt')}, expected yuv420p")
    if video.get("color_space") != "bt709" or video.get("color_range") != "tv":
        failures.append("video is not tagged BT.709 limited range")

    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(args.input), "-f", "null", "-"],
        check=True,
    )
    metrics = audio_metrics(args.input) if audios else {}
    if metrics.get("max_volume_db") is not None and metrics["max_volume_db"] > args.max_peak_db:
        failures.append(f"audio peak {metrics['max_volume_db']} dB exceeds {args.max_peak_db} dB")

    result = {
        "path": str(args.input.resolve()),
        "duration": duration,
        "frames": frames,
        "fps": fps,
        "dimensions": [video.get("width"), video.get("height")],
        "video_codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "color_range": video.get("color_range"),
        "color_space": video.get("color_space"),
        "audio": metrics,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
