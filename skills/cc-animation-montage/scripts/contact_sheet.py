#!/usr/bin/env python3
import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def duration_seconds(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    return float(subprocess.check_output(command, text=True).strip())


def label_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def timestamp(value: float) -> str:
    minutes = int(value // 60)
    seconds = value - minutes * 60
    return f"{minutes:02d}:{seconds:04.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a timestamped video contact sheet.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--columns", type=int, default=6)
    parser.add_argument("--tile-width", type=int, default=320)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    if not args.input.is_file():
        raise SystemExit(f"input not found: {args.input}")
    if args.interval <= 0 or args.columns <= 0:
        raise SystemExit("interval and columns must be positive")

    source_duration = duration_seconds(args.input)
    available = max(0.0, source_duration - args.start)
    window = min(args.duration if args.duration is not None else available, available)
    if window <= 0:
        raise SystemExit("selected time window is empty")

    count = max(1, math.ceil(window / args.interval))
    tile_width = args.tile_width
    frame_height = round(tile_width * 9 / 16)
    label_height = 34
    rows = math.ceil(count / args.columns)

    with tempfile.TemporaryDirectory(prefix="cc-animation-contact-") as temp_name:
        temp_dir = Path(temp_name)
        pattern = temp_dir / "frame_%04d.jpg"
        filter_graph = (
            f"fps=fps=1/{args.interval}:start_time=0,"
            f"scale={tile_width}:{frame_height}:force_original_aspect_ratio=decrease,"
            f"pad={tile_width}:{frame_height}:(ow-iw)/2:(oh-ih)/2:black"
        )
        command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        if args.start:
            command.extend(["-ss", str(args.start)])
        command.extend(["-t", str(window), "-i", str(args.input)])
        command.extend(["-vf", filter_graph, str(pattern)])
        subprocess.run(command, check=True)

        frames = sorted(temp_dir.glob("frame_*.jpg"))[:count]
        if not frames:
            raise SystemExit("ffmpeg produced no contact-sheet frames")

        sheet = Image.new(
            "RGB",
            (args.columns * tile_width, rows * (frame_height + label_height)),
            "#0b0b0d",
        )
        draw = ImageDraw.Draw(sheet)
        font = label_font(20)
        for index, frame_path in enumerate(frames):
            image = Image.open(frame_path).convert("RGB")
            column = index % args.columns
            row = index // args.columns
            x = column * tile_width
            y = row * (frame_height + label_height)
            sheet.paste(image, (x, y))
            sample_time = args.start + index * args.interval
            draw.text((x + 8, y + frame_height + 5), timestamp(sample_time), fill="white", font=font)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.output, quality=92)
        print(args.output.resolve())


if __name__ == "__main__":
    main()
