#!/usr/bin/env python3
"""Validate the generated concrete Skill package index and local package tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    index_path = root / "community-skills" / "index.json"
    index = json.loads(index_path.read_text())
    skills = index.get("skills", [])
    local_paths: set[str] = set()
    status_counts = {"direct": 0, "extracted": 0, "needs-review": 0}

    for item in skills:
        name = item.get("name", "<missing-name>")
        status = item.get("status")
        local_path = item.get("localPath", "")
        if status not in status_counts:
            errors.append(f"{name}: invalid status {status!r}")
            continue
        status_counts[status] += 1
        if local_path in local_paths:
            errors.append(f"{name}: duplicate localPath {local_path}")
        local_paths.add(local_path)
        package = root / local_path
        if not package.is_dir():
            errors.append(f"{name}: missing package directory {local_path}")
            continue
        if not (package / "SKILL.md").is_file():
            errors.append(f"{name}: missing SKILL.md")
        if status == "direct":
            if not local_path.startswith("skills/"):
                errors.append(f"{name}: direct package is outside skills/")
            continue
        if not local_path.startswith("community-skills/"):
            errors.append(f"{name}: candidate package is outside community-skills/")
        for required in ("effecta.manifest.json", "NOTICE.effecta", "LICENSE"):
            if not (package / required).is_file():
                errors.append(f"{name}: missing {required}")
        manifest_path = package / "effecta.manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            for field in ("name", "category", "status", "contentDigest"):
                if manifest.get(field) != item.get(field):
                    errors.append(f"{name}: manifest/index mismatch for {field}")
            findings = manifest.get("staticScan", {}).get("findings", [])
            if status == "extracted" and findings:
                errors.append(f"{name}: extracted package contains unresolved findings")
            if status == "needs-review" and not findings:
                errors.append(f"{name}: needs-review package has no finding")
        for path in package.rglob("*"):
            if path.is_symlink():
                errors.append(f"{name}: symlink present at {path.relative_to(package)}")

    expected = {
        "concreteSkillCount": len(skills),
        "directSkillCount": status_counts["direct"],
        "extractedSkillCount": status_counts["extracted"],
        "needsReviewCount": status_counts["needs-review"],
    }
    for field, value in expected.items():
        if index.get(field) != value:
            errors.append(f"index: {field}={index.get(field)!r}, expected {value}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    index = json.loads((args.root / "community-skills" / "index.json").read_text())
    print(f"validated {index['concreteSkillCount']} concrete Skill records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
