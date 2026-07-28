#!/usr/bin/env python3
"""Safe CLI for Canvas-compatible asynchronous video generation."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE = "https://api.canvas.12646464.xyz"
NONTERMINAL = {"queued", "pending", "processing", "running"}
SUCCESS = {"succeeded", "completed"}
FAILED = {"failed"}


def api_base() -> str:
    return os.environ.get("CANVAS_API_BASE", DEFAULT_BASE).rstrip("/")


def api_key() -> str:
    value = os.environ.get("CANVAS_API_KEY", "").strip()
    if not value:
        raise SystemExit("CANVAS_API_KEY is required")
    return value


def request_json(
    method: str,
    path: str,
    *,
    payload: bytes | None = None,
    content_type: str | None = None,
    timeout: float = 60,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key()}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(
        f"{api_base()}{path}",
        data=payload,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        raw = exc.read()
        try:
            body = json.loads(raw)
        except Exception:
            body = {"error": {"message": raw.decode("utf-8", "replace")}}
        body["_http_status"] = exc.code
        return body
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"request failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("server returned non-JSON data") from exc


def multipart(
    fields: list[tuple[str, str]],
    files: list[tuple[str, Path]],
) -> tuple[bytes, str]:
    boundary = f"----canvas-video-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, path in files:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def prompt_text(args: argparse.Namespace) -> str:
    if getattr(args, "prompt_file", None):
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    return (getattr(args, "prompt", None) or "").strip()


def probe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def collect_files(args: argparse.Namespace) -> list[tuple[str, Path]]:
    output: list[tuple[str, Path]] = []
    mapping = [
        ("reference_images", "reference_image"),
        ("reference_videos", "reference_video"),
        ("reference_audios", "reference_audio"),
    ]
    for field, attr in mapping:
        for value in getattr(args, attr, []) or []:
            output.append((field, Path(value).expanduser().resolve()))
    if getattr(args, "first_frame", None):
        output.append(
            ("first_frame_image", Path(args.first_frame).expanduser().resolve())
        )
    if getattr(args, "last_frame", None):
        output.append(
            ("last_frame_image", Path(args.last_frame).expanduser().resolve())
        )
    return output


def preflight(args: argparse.Namespace) -> dict[str, Any]:
    prompt = prompt_text(args)
    if not prompt:
        raise SystemExit("provide --prompt or --prompt-file")
    files = collect_files(args)
    missing = [str(path) for _, path in files if not path.is_file()]
    if missing:
        raise SystemExit(f"missing reference files: {', '.join(missing)}")

    counts = {
        "images": sum(
            field in {"reference_images", "first_frame_image", "last_frame_image"}
            for field, _ in files
        ),
        "videos": sum(field == "reference_videos" for field, _ in files),
        "audios": sum(field == "reference_audios" for field, _ in files),
        "total": len(files),
    }
    errors: list[str] = []
    warnings: list[str] = []
    if counts["images"] > 9:
        errors.append("more than 9 image references")
    if counts["videos"] > 3:
        errors.append("more than 3 video references")
    if counts["audios"] > 3:
        errors.append("more than 3 audio references")
    if counts["total"] > 12:
        errors.append("more than 12 total references")
    if len(prompt) > 700:
        warnings.append(
            f"prompt has {len(prompt)} characters; consider a compact one-action prompt"
        )

    durations: dict[str, float] = {}
    for field, path in files:
        limit = 30 if "image" in field or "frame" in field else 50
        if field == "reference_audios":
            limit = 15
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > limit:
            warnings.append(f"{path.name} is {size_mb:.1f} MB (common limit {limit} MB)")
        if field in {"reference_videos", "reference_audios"}:
            duration = probe_duration(path)
            if duration is not None:
                durations[path.name] = round(duration, 3)
    video_total = sum(
        durations.get(path.name, 0)
        for field, path in files
        if field == "reference_videos"
    )
    audio_total = sum(
        durations.get(path.name, 0)
        for field, path in files
        if field == "reference_audios"
    )
    if video_total > 15.05:
        warnings.append(f"reference video duration totals {video_total:.3f}s")
    if audio_total > 15.05:
        warnings.append(f"reference audio duration totals {audio_total:.3f}s")

    result = {
        "ok": not errors,
        "model": args.model,
        "seconds": args.seconds,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "prompt_characters": len(prompt),
        "reference_counts": counts,
        "reference_durations": durations,
        "files": [
            {"field": field, "name": path.name, "bytes": path.stat().st_size}
            for field, path in files
        ],
        "warnings": warnings,
        "errors": errors,
    }
    return result


def task_id_from(body: dict[str, Any]) -> str | None:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    task = data.get("task") if isinstance(data.get("task"), dict) else {}
    for source in (data, task, body):
        for key in ("task_id", "taskId", "id"):
            value = source.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def status_from(body: dict[str, Any]) -> str:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    task = data.get("task") if isinstance(data.get("task"), dict) else {}
    for source in (data, task, body):
        value = source.get("status") or source.get("state")
        if isinstance(value, str):
            return value.lower()
    return "unknown"


def result_url_from(body: dict[str, Any]) -> str | None:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    for key in ("video_url", "result_url", "resultVideoUrl", "url"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    urls = data.get("urls")
    if isinstance(urls, list) and urls and isinstance(urls[0], str):
        return urls[0]
    return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt")
    group.add_argument("--prompt-file")
    parser.add_argument("--seconds", type=int)
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--resolution")
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument("--reference-video", action="append", default=[])
    parser.add_argument("--reference-audio", action="append", default=[])
    parser.add_argument("--first-frame")
    parser.add_argument("--last-frame")


def cmd_models(args: argparse.Namespace) -> int:
    body = request_json("GET", "/v1/models")
    models = body.get("data", body)
    if not isinstance(models, list):
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 1
    if args.type:
        models = [item for item in models if item.get("type") == args.type]
    print(json.dumps(models, ensure_ascii=False, indent=2))
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    result = preflight(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def cmd_submit(args: argparse.Namespace) -> int:
    if not args.confirm_submit:
        raise SystemExit("refusing paid request without --confirm-submit")
    check = preflight(args)
    if not check["ok"]:
        print(json.dumps(check, ensure_ascii=False, indent=2))
        return 2

    fields = [("model", args.model), ("prompt", prompt_text(args))]
    for key, value in [
        ("aspect_ratio", args.aspect_ratio),
        ("seconds", str(args.seconds) if args.seconds is not None else None),
        ("resolution", args.resolution),
    ]:
        if value:
            fields.append((key, value))
    payload, content_type = multipart(fields, collect_files(args))
    body = request_json(
        "POST",
        "/v1/videos",
        payload=payload,
        content_type=content_type,
        timeout=args.timeout,
    )
    receipt = {
        "created_at": int(time.time()),
        "request": check,
        "response": body,
        "task_id": task_id_from(body),
        "status": status_from(body),
    }
    write_json(Path(args.receipt).expanduser().resolve(), receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["task_id"] else 3


def cmd_status(args: argparse.Namespace) -> int:
    body = request_json("GET", f"/v1/videos/{args.task_id}", timeout=args.timeout)
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0


def task_from_args(args: argparse.Namespace) -> str:
    if args.task_id:
        return args.task_id
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    task_id = receipt.get("task_id")
    if not task_id:
        raise SystemExit("receipt does not contain a task_id")
    return task_id


def download(url: str, output: Path, timeout: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "canvas-video-producer/1"})
    with urlopen(req, timeout=timeout) as response, output.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def cmd_wait(args: argparse.Namespace) -> int:
    task_id = task_from_args(args)
    deadline = time.monotonic() + args.timeout
    failures = 0
    while True:
        if time.monotonic() >= deadline:
            print(
                json.dumps(
                    {"status": "poll_timeout", "task_id": task_id},
                    ensure_ascii=False,
                )
            )
            return 4
        try:
            body = request_json(
                "GET",
                f"/v1/videos/{task_id}",
                timeout=args.request_timeout,
            )
            status = status_from(body)
            failures = 0
        except RuntimeError as exc:
            failures += 1
            print(
                json.dumps(
                    {
                        "status": "poll_error",
                        "task_id": task_id,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            time.sleep(min(args.interval * max(failures, 1), 90))
            continue

        if body.get("ok") is False and status == "unknown":
            failures += 1
            print(
                json.dumps(
                    {
                        "status": "poll_error",
                        "task_id": task_id,
                        "response": body,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            time.sleep(min(args.interval * max(failures, 1), 90))
            continue

        print(
            json.dumps(
                {
                    "task_id": task_id,
                    "status": status,
                    "progress": (body.get("data") or {}).get("progress"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if status in SUCCESS:
            url = result_url_from(body)
            result = {"task_id": task_id, "status": status, "url": url}
            if args.output and url:
                output = Path(args.output).expanduser().resolve()
                download(url, output, args.download_timeout)
                result["output"] = str(output)
                result["bytes"] = output.stat().st_size
            if args.result:
                write_json(Path(args.result).expanduser().resolve(), body)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if status in FAILED:
            print(json.dumps(body, ensure_ascii=False, indent=2))
            return 5
        if status not in NONTERMINAL:
            print(
                json.dumps(
                    {"status": "unknown_response", "task_id": task_id, "body": body},
                    ensure_ascii=False,
                )
            )
        time.sleep(args.interval)


def cmd_download(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve()
    download(args.url, output, args.timeout)
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    models = sub.add_parser("models")
    models.add_argument("--type")
    models.set_defaults(func=cmd_models)

    pre = sub.add_parser("preflight")
    add_generation_args(pre)
    pre.set_defaults(func=cmd_preflight)

    submit = sub.add_parser("submit")
    add_generation_args(submit)
    submit.add_argument("--confirm-submit", action="store_true")
    submit.add_argument("--receipt", required=True)
    submit.add_argument("--timeout", type=float, default=180)
    submit.set_defaults(func=cmd_submit)

    status = sub.add_parser("status")
    status.add_argument("task_id")
    status.add_argument("--timeout", type=float, default=60)
    status.set_defaults(func=cmd_status)

    wait = sub.add_parser("wait")
    source = wait.add_mutually_exclusive_group(required=True)
    source.add_argument("--task-id")
    source.add_argument("--receipt")
    wait.add_argument("--interval", type=float, default=30)
    wait.add_argument("--timeout", type=float, default=1800)
    wait.add_argument("--request-timeout", type=float, default=60)
    wait.add_argument("--download-timeout", type=float, default=180)
    wait.add_argument("--output")
    wait.add_argument("--result")
    wait.set_defaults(func=cmd_wait)

    fetch = sub.add_parser("download")
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--output", required=True)
    fetch.add_argument("--timeout", type=float, default=180)
    fetch.set_defaults(func=cmd_download)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
