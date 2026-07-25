#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


LICENSE_TERMS = (
    "license",
    "licence",
    "creative commons",
    "creativecommons",
    "public domain",
    "copyright",
    "attribution",
    "noncommercial",
    "non-commercial",
    "share alike",
    "sharealike",
)


def run_probe(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    return json.loads(subprocess.check_output(command, text=True))


def digest(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def relevant_metadata(probe: dict) -> list[dict]:
    findings = []
    groups = [("format", probe.get("format", {}).get("tags", {}))]
    groups.extend(
        (f"stream:{stream.get('index')}", stream.get("tags", {}))
        for stream in probe.get("streams", [])
    )
    for scope, tags in groups:
        for key, value in tags.items():
            haystack = f"{key} {value}".lower()
            if any(term in haystack for term in LICENSE_TERMS):
                findings.append({"scope": scope, "key": key, "value": value})
    return findings


def summarize(path: Path, include_hash: bool) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    probe = run_probe(path)
    streams = []
    for stream in probe.get("streams", []):
        streams.append(
            {
                key: stream.get(key)
                for key in (
                    "index",
                    "codec_type",
                    "codec_name",
                    "width",
                    "height",
                    "sample_rate",
                    "channels",
                    "duration",
                    "disposition",
                )
                if stream.get(key) is not None
            }
        )
    result = {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "duration": probe.get("format", {}).get("duration"),
        "format_tags": probe.get("format", {}).get("tags", {}),
        "streams": streams,
        "license_metadata": relevant_metadata(probe),
    }
    if include_hash:
        result["sha256"] = digest(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect media streams and embedded licensing metadata."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--hash", action="store_true", dest="include_hash")
    args = parser.parse_args()

    if shutil.which("ffprobe") is None:
        raise SystemExit("ffprobe is required")

    results = [summarize(path, args.include_hash) for path in args.paths]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
