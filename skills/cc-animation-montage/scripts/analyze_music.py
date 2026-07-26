#!/usr/bin/env python3
import argparse
import array
import json
import math
import shutil
import statistics
import subprocess
import sys
from pathlib import Path


def decode_audio(path: Path, start: float, duration: float, sample_rate: int) -> array.array:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-t",
        str(duration),
        "-i",
        str(path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "f32le",
        "-",
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    samples = array.array("f")
    samples.frombytes(completed.stdout)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def frame_energies(samples: array.array, frame_size: int, hop_size: int) -> list[float]:
    energies = []
    for start in range(0, max(0, len(samples) - frame_size + 1), hop_size):
        total = 0.0
        end = start + frame_size
        previous = samples[start - 1] if start else samples[0]
        for index in range(start, end):
            current = samples[index]
            emphasized = current - 0.97 * previous
            total += emphasized * emphasized
            previous = current
        energies.append(math.log10(total / frame_size + 1e-12))
    return energies


def onset_strengths(energies: list[float], history: int = 8) -> list[float]:
    strengths = [0.0] * len(energies)
    for index in range(1, len(energies)):
        baseline_start = max(0, index - history)
        baseline = statistics.median(energies[baseline_start:index])
        strengths[index] = max(0.0, energies[index] - baseline)
    return strengths


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def select_peaks(
    strengths: list[float],
    count: int,
    minimum_gap_frames: int,
    local_radius: int = 2,
) -> list[int]:
    threshold = percentile([value for value in strengths if value > 0], 0.65)
    candidates = []
    for index in range(local_radius, len(strengths) - local_radius):
        value = strengths[index]
        neighborhood = strengths[index - local_radius : index + local_radius + 1]
        if value >= threshold and value == max(neighborhood):
            candidates.append(index)

    selected = []
    for index in sorted(candidates, key=lambda item: strengths[item], reverse=True):
        if all(abs(index - other) >= minimum_gap_frames for other in selected):
            selected.append(index)
        if len(selected) == count:
            break
    return sorted(selected)


def energy_windows(
    energies: list[float],
    frame_seconds: float,
    duration: float,
    window_seconds: float = 1.0,
) -> list[dict]:
    count = max(1, math.ceil(duration / window_seconds))
    raw = []
    for index in range(count):
        first = math.floor(index * window_seconds / frame_seconds)
        last = math.ceil((index + 1) * window_seconds / frame_seconds)
        values = energies[first:last]
        raw.append(statistics.mean(values) if values else min(energies, default=-12.0))
    low = min(raw, default=0.0)
    high = max(raw, default=1.0)
    span = high - low or 1.0
    return [
        {
            "relative_seconds": round(index * window_seconds, 3),
            "normalized_energy": round((value - low) / span, 3),
        }
        for index, value in enumerate(raw)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find frame-aligned energy changes and salient audio onsets without assuming a fixed BPM."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--min-gap", type=float, default=0.18)
    parser.add_argument("--sample-rate", type=int, default=22050)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required")
    if not args.input.is_file():
        raise SystemExit(f"input not found: {args.input}")
    if args.start < 0 or args.duration <= 0 or args.fps <= 0:
        raise SystemExit("start must be non-negative; duration and fps must be positive")
    if args.count <= 0 or args.min_gap <= 0 or args.sample_rate <= 0:
        raise SystemExit("count, min-gap, and sample-rate must be positive")

    frame_size = 1024
    hop_size = 256
    samples = decode_audio(args.input, args.start, args.duration, args.sample_rate)
    if len(samples) < frame_size:
        raise SystemExit("selected audio window is too short")

    energies = frame_energies(samples, frame_size, hop_size)
    strengths = onset_strengths(energies)
    frame_seconds = hop_size / args.sample_rate
    minimum_gap_frames = max(1, round(args.min_gap / frame_seconds))
    peaks = select_peaks(strengths, args.count, minimum_gap_frames)
    strongest = max((strengths[index] for index in peaks), default=1.0) or 1.0

    result = {
        "source": str(args.input.resolve()),
        "analysis_start": args.start,
        "analysis_duration": args.duration,
        "sample_rate": args.sample_rate,
        "timeline_fps": args.fps,
        "energy_by_second": energy_windows(energies, frame_seconds, args.duration),
        "salient_onsets": [
            {
                "absolute_seconds": round(args.start + index * frame_seconds, 3),
                "relative_seconds": round(index * frame_seconds, 3),
                "timeline_frame": round(index * frame_seconds * args.fps),
                "strength": round(strengths[index] / strongest, 3),
            }
            for index in peaks
        ],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
