#!/usr/bin/env python3
"""Allow unattended merge only for append-only verification evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_registry_skills import validate_record


STATIC_ALLOWED = {"registry/v1/index.json"}
SOURCE_PREFIX = "verifications/v1/"
GENERATED_PREFIX = "registry/v1/verifications/"


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, stdout=subprocess.PIPE).stdout


def normalized_index(index: dict) -> dict:
    normalized = json.loads(json.dumps(index))
    normalized.get("inputDigests", {}).pop("verifications", None)
    for item in normalized.get("capabilities", []):
        item.pop("verification", None)
        item.pop("verificationFile", None)
    return normalized


def classify(root: Path, base: str) -> list[str]:
    errors: list[str] = []
    changed = git_output(root, "diff", "--name-status", base, "--").splitlines()
    changed.extend(f"A\t{path}" for path in git_output(root, "ls-files", "--others", "--exclude-standard").splitlines())
    source_files: list[str] = []
    generated_files: list[str] = []
    for line in changed:
        status, _, path = line.partition("\t")
        if path in STATIC_ALLOWED:
            if status != "M":
                errors.append(f"unexpected status for {path}: {status}")
        elif path.startswith(SOURCE_PREFIX) and path.endswith(".json"):
            if status != "A":
                errors.append(f"verification evidence is not append-only: {path}")
            source_files.append(path)
        elif path.startswith(GENERATED_PREFIX) and path.endswith(".json"):
            if status != "A":
                errors.append(f"generated verification is not append-only: {path}")
            generated_files.append(path)
        else:
            errors.append(f"unexpected file changed: {path}")
    if not source_files:
        errors.append("no verification evidence was added")
    if len(source_files) > 100:
        errors.append("verification batch exceeds 100 records")

    base_index = json.loads(git_output(root, "show", f"{base}:registry/v1/index.json"))
    candidate_index = json.loads((root / "registry/v1/index.json").read_text())
    if normalized_index(base_index) != normalized_index(candidate_index):
        errors.append("capability identity or non-verification registry data changed")
    capabilities = {item["releaseId"]: item for item in candidate_index.get("capabilities", [])}

    expected_generated: set[str] = set()
    for relative in source_files:
        record = json.loads((root / relative).read_text())
        for error in validate_record(record):
            errors.append(f"{relative}: {error}")
        release_id = record.get("releaseId", "")
        capability = capabilities.get(release_id)
        if capability is None:
            errors.append(f"{relative}: release is not in current registry")
            continue
        if capability.get("contentDigest") != record.get("contentDigest"):
            errors.append(f"{relative}: content digest does not match capability")
        if capability.get("verification") != record:
            errors.append(f"{relative}: embedded verification does not match evidence")
        generated = GENERATED_PREFIX + Path(relative).name
        expected_generated.add(generated)
        if capability.get("verificationFile") != "verifications/" + Path(relative).name:
            errors.append(f"{relative}: verificationFile is missing or incorrect")
        generated_path = root / generated
        if not generated_path.is_file() or json.loads(generated_path.read_text()) != record:
            errors.append(f"{relative}: generated verification copy does not match")
    if set(generated_files) != expected_generated:
        errors.append("generated verification files do not match source evidence additions")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors = classify(args.root.resolve(), args.base)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if errors:
        print("verification candidate requires human review:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("verification candidate is append-only and eligible for automatic merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
