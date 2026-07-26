#!/usr/bin/env python3
import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BT709_FLAGS = [
    "-color_range",
    "tv",
    "-colorspace",
    "bt709",
    "-color_trc",
    "bt709",
    "-color_primaries",
    "bt709",
]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def find_font(bold: bool) -> str:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError("No supported Arial or DejaVu font found")


def fitted_font(draw: ImageDraw.ImageDraw, text: str, bold: bool, size: int, max_width: int) -> ImageFont.FreeTypeFont:
    font_path = find_font(bold)
    while size > 18:
        candidate = ImageFont.truetype(font_path, size)
        box = draw.textbbox((0, 0), text, font=candidate)
        if box[2] - box[0] <= max_width:
            return candidate
        size -= 2
    return ImageFont.truetype(font_path, 18)


def base_card(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), "#0b0b0d")
    draw = ImageDraw.Draw(image)
    left = round(width * 0.061)
    top = round(height * 0.17)
    bottom = round(height * 0.84)
    draw.rectangle((left, top, left + 18, bottom), fill="#ef3e2f")
    draw.rectangle((left, bottom - 10, round(width * 0.31), bottom), fill="#ef3e2f")
    return image, draw


def render_title(path: Path, config: dict, width: int, height: int) -> None:
    image, draw = base_card(width, height)
    x = round(width * 0.105)
    max_width = round(width * 0.79)
    headline = str(config.get("headline", "IGNITION"))
    subhead = str(config.get("subhead", "OPEN ANIMATION MIX"))
    strapline = str(config.get("strapline", ""))
    draw.text((x, round(height * 0.31)), headline, font=fitted_font(draw, headline, True, 148, max_width), fill="#f4f4f2")
    draw.text((x, round(height * 0.49)), subhead, font=fitted_font(draw, subhead, True, 56, max_width), fill="#ef3e2f")
    if strapline:
        draw.text((x, round(height * 0.57)), strapline, font=fitted_font(draw, strapline, False, 30, max_width), fill="#a8a8aa")
    image.save(path)


def render_credits(path: Path, config: dict, width: int, height: int) -> None:
    image, draw = base_card(width, height)
    x = round(width * 0.105)
    max_width = round(width * 0.79)
    heading = str(config.get("heading", "SOURCE / LICENSE"))
    draw.text((x, round(height * 0.21)), heading, font=fitted_font(draw, heading, True, 72, max_width), fill="#f4f4f2")
    y = round(height * 0.34)
    for line in config.get("lines", [])[:6]:
        text = str(line)
        draw.text((x, y), text, font=fitted_font(draw, text, True, 46, max_width), fill="#ef3e2f")
        y += round(height * 0.065)
    audio_line = str(config.get("audio_line", ""))
    license_line = str(config.get("license_line", ""))
    if audio_line:
        draw.text((x, round(height * 0.58)), audio_line, font=fitted_font(draw, audio_line, False, 30, max_width), fill="#f4f4f2")
    if license_line:
        draw.text((x, round(height * 0.66)), license_line, font=fitted_font(draw, license_line, False, 28, max_width), fill="#a8a8aa")
    image.save(path)


def video_flags(crf: int) -> list[str]:
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), *BT709_FLAGS]


def frame_count(duration: float, fps: int, label: str) -> int:
    frames = round(duration * fps)
    if duration <= 0 or frames <= 0:
        raise ValueError(f"{label} must be at least one output frame")
    return frames


def card_clip(image: Path, output: Path, duration: float, fps: int, crf: int) -> None:
    total_frames = frame_count(duration, fps, "card duration")
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(fps),
            "-t",
            str(duration),
            "-i",
            str(image),
            "-an",
            "-vf",
            f"fps={fps},format=yuv420p,setsar=1",
            "-frames:v",
            str(total_frames),
            *video_flags(crf),
            str(output),
        ]
    )


def action_clip(config: dict, output: Path, width: int, height: int, fps: int, crf: int) -> None:
    source = Path(config["path"]).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    start = float(config.get("start", 0))
    duration = float(config["duration"])
    speed = float(config.get("speed", 1.0))
    if duration <= 0 or speed <= 0:
        raise ValueError("clip duration and speed must be positive")
    total_frames = frame_count(duration, fps, "clip duration")
    source_duration = duration * speed + 0.08
    filter_graph = (
        f"setpts=PTS/{speed},trim=duration={duration},setpts=PTS-STARTPTS,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={fps},eq=contrast=1.06:saturation=1.12:brightness=-0.01,"
        "format=yuv420p,setsar=1"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-t",
            str(source_duration),
            "-i",
            str(source),
            "-an",
            "-vf",
            filter_graph,
            "-frames:v",
            str(total_frames),
            *video_flags(crf),
            str(output),
        ]
    )


def probe(path: Path) -> dict:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,r_frame_rate,nb_frames,duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    return json.loads(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a normalized animation montage from a JSON manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    for executable in ("ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise SystemExit(f"{executable} is required")

    config = json.loads(args.manifest.read_text(encoding="utf-8"))
    output = Path(config["output"]).expanduser().resolve()
    work_dir = Path(config.get("work_dir", output.parent / ".cc-animation-montage-work")).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    target = float(config.get("duration", 30))
    video = config.get("video", {})
    width = int(video.get("width", 1920))
    height = int(video.get("height", 1080))
    fps = int(video.get("fps", 30))
    crf = int(video.get("crf", 18))
    if target <= 0 or fps <= 0 or width <= 0 or height <= 0:
        raise SystemExit("duration, fps, width, and height must be positive")

    total_frames = round(target * fps)
    timeline = []
    if config.get("title_card"):
        timeline.append(("title card", float(config["title_card"].get("duration", 0.8))))
    timeline.extend(
        (f"clip {index}", float(clip["duration"]))
        for index, clip in enumerate(config.get("clips", []), start=1)
    )
    if config.get("credits_card"):
        timeline.append(("credits card", float(config["credits_card"].get("duration", 2.0))))
    planned_frames = sum(frame_count(duration, fps, label) for label, duration in timeline)
    if planned_frames != total_frames:
        raise SystemExit(
            f"timeline has {planned_frames} rounded frames; expected exactly {total_frames}"
        )

    segments = []
    title = config.get("title_card")
    if title:
        title_png = work_dir / "title.png"
        render_title(title_png, title, width, height)
        title_clip = work_dir / "clip_000.mp4"
        card_clip(title_png, title_clip, float(title.get("duration", 0.8)), fps, crf)
        segments.append(title_clip)

    for index, clip in enumerate(config.get("clips", []), start=1):
        clip_path = work_dir / f"clip_{index:03d}.mp4"
        action_clip(clip, clip_path, width, height, fps, crf)
        segments.append(clip_path)

    credits = config.get("credits_card")
    if credits:
        credits_png = work_dir / "credits.png"
        render_credits(credits_png, credits, width, height)
        credits_clip = work_dir / f"clip_{len(segments):03d}.mp4"
        card_clip(credits_png, credits_clip, float(credits.get("duration", 2.0)), fps, crf)
        segments.append(credits_clip)

    if not segments:
        raise SystemExit("manifest contains no title, clips, or credits")

    concat_list = work_dir / "concat.txt"
    concat_list.write_text("".join(f"file '{path}'\n" for path in segments), encoding="utf-8")
    silent = work_dir / "video_silent.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(silent)])

    silent_duration = float(probe(silent)["format"]["duration"])
    if silent_duration + 1 / fps < target:
        raise SystemExit(f"timeline is too short: {silent_duration:.3f}s for {target:.3f}s target")

    exact_video = work_dir / "video_exact.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(silent),
            "-an",
            "-vf",
            f"fps={fps},setpts=PTS-STARTPTS,format=yuv420p",
            "-frames:v",
            str(total_frames),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            *BT709_FLAGS,
            str(exact_video),
        ]
    )

    exact_audio = work_dir / "audio_exact.m4a"
    audio = config.get("audio")
    if audio:
        audio_path = Path(audio["path"]).expanduser()
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        fade_in = float(audio.get("fade_in", 0.2))
        fade_out = float(audio.get("fade_out", 1.6))
        fade_out_start = max(0.0, target - fade_out)
        volume_db = float(audio.get("volume_db", -3))
        audio_filter = (
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out},"
            f"volume={volume_db}dB,apad=pad_dur=1,atrim=duration={target},aresample=48000"
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(float(audio.get("start", 0))),
                "-t",
                str(target),
                "-i",
                str(audio_path),
                "-vn",
                "-af",
                audio_filter,
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-b:a",
                "256k",
                str(exact_audio),
            ]
        )
    else:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=48000:cl=stereo",
                "-t",
                str(target),
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(exact_audio),
            ]
        )

    metadata = config.get("metadata", {})
    mux = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(exact_video),
        "-i",
        str(exact_audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c",
        "copy",
        "-t",
        str(target),
    ]
    if metadata.get("title"):
        mux.extend(["-metadata", f"title={metadata['title']}"])
    if metadata.get("comment"):
        mux.extend(["-metadata", f"comment={metadata['comment']}"])
    mux.extend(
        [
            "-bsf:v",
            (
                "h264_metadata=video_full_range_flag=0:colour_primaries=1:"
                "transfer_characteristics=1:matrix_coefficients=1"
            ),
        ]
    )
    mux.extend(["-movflags", "+faststart", str(output)])
    run(mux)

    result = probe(output)
    video_stream = next(stream for stream in result["streams"] if stream["codec_type"] == "video")
    actual_frames = int(video_stream.get("nb_frames", 0))
    actual_duration = float(result["format"]["duration"])
    if actual_frames != total_frames or not math.isclose(actual_duration, target, abs_tol=1 / fps):
        raise SystemExit(
            f"verification failed: duration={actual_duration}, frames={actual_frames}, expected={total_frames}"
        )
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(output), "-f", "null", "-"])
    print(json.dumps({"output": str(output), "duration": actual_duration, "frames": actual_frames}, indent=2))


if __name__ == "__main__":
    main()
