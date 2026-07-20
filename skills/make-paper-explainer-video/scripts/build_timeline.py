#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def probe(path: Path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=sample_rate",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"]), int(data["streams"][0]["sample_rate"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("segments_dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--pause", type=float, default=0.12)
    args = parser.parse_args()

    paths = sorted(args.segments_dir.glob("*.wav"))
    if not paths:
        raise SystemExit("no WAV files found")

    durations = []
    sample_rates = []
    for path in paths:
        duration, sample_rate = probe(path)
        durations.append(duration)
        sample_rates.append(sample_rate)
    sample_rate = sample_rates[0]

    cursor = 0.0
    timeline = []
    for index, (path, duration) in enumerate(zip(paths, durations), start=1):
        timeline.append({"index": index, "file": path.name, "start": cursor, "end": cursor + duration})
        cursor += duration + args.pause

    filters = []
    labels = []
    for index in range(len(paths)):
        filters.append(f"[{index}:a]aresample={sample_rate},aformat=sample_fmts=s16:channel_layouts=mono[a{index}]")
        filters.append(f"anullsrc=r={sample_rate}:cl=mono:d={args.pause}[s{index}]")
        labels.extend((f"[a{index}]", f"[s{index}]"))
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for path in paths:
        command.extend(("-i", str(path)))
    command.extend(("-filter_complex", ";".join(filters), "-map", "[out]", str(args.output)))
    subprocess.run(command, check=True)

    args.timeline.write_text(json.dumps({
        "sample_rate": sample_rate,
        "duration": cursor,
        "segments": timeline,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
