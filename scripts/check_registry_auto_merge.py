#!/usr/bin/env python3
"""Allow unattended merges only for observation-only registry refreshes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ALLOWED_PATHS = {
    "README.md",
    "RANKING.md",
    "catalog.json",
    "registry/v1/index.json",
    "registry/v1/observations/github.json",
}
REMOVAL_REASONS = {"archived", "below-star-threshold"}
TRUST_FIELDS = ("status", "reason", "skillFileCount", "kind", "qualification")
VOLATILE_CAPABILITY_FIELDS = {"sourceRank", "sourceStars"}


def repository_map(catalog: dict) -> dict[str, dict]:
    return {item["repository"].lower(): item for item in catalog["repositories"]}


def normalized_capabilities(index: dict) -> dict[str, dict]:
    normalized: dict[str, dict] = {}
    for capability in index["capabilities"]:
        item = {key: value for key, value in capability.items() if key not in VOLATILE_CAPABILITY_FIELDS}
        normalized[capability["packageId"]] = item
    return normalized


def classify_candidate(
    base_catalog: dict,
    candidate_catalog: dict,
    base_registry: dict,
    candidate_registry: dict,
    changed_files: set[str],
) -> list[str]:
    errors: list[str] = []
    unexpected_files = sorted(changed_files - ALLOWED_PATHS)
    if unexpected_files:
        errors.append("unexpected files changed: " + ", ".join(unexpected_files))

    if candidate_catalog.get("minimumStarsExclusive") != base_catalog.get("minimumStarsExclusive"):
        errors.append("minimum Star threshold changed")
    if candidate_catalog.get("sort") != base_catalog.get("sort"):
        errors.append("ranking sort changed")
    if candidate_catalog.get("directSkillCount") != base_catalog.get("directSkillCount"):
        errors.append("direct Skill count changed")

    candidate_items = candidate_catalog.get("repositories", [])
    candidate_names = [item["repository"].lower() for item in candidate_items]
    if len(candidate_names) != len(set(candidate_names)):
        errors.append("candidate catalog contains duplicate repositories")
    if candidate_catalog.get("repositoryCount") != len(candidate_items):
        errors.append("repositoryCount does not match catalog contents")
    if candidate_catalog.get("repositoriesWithSkillFiles") != sum(
        int(item.get("skillFileCount", 0)) > 0 for item in candidate_items
    ):
        errors.append("repositoriesWithSkillFiles does not match catalog contents")
    threshold = int(candidate_catalog.get("minimumStarsExclusive", 300))
    for item in candidate_items:
        if int(item.get("stars", 0)) <= threshold:
            errors.append(f"repository no longer meets the Star threshold: {item['repository']}")

    base = repository_map(base_catalog)
    candidate = repository_map(candidate_catalog)
    added = set(candidate) - set(base)
    removed = set(base) - set(candidate)
    newly_discovered = int(candidate_catalog.get("newlyDiscoveredCount", 0))
    if newly_discovered < 0 or newly_discovered > len(added):
        errors.append("newlyDiscoveredCount exceeds added repositories")

    for name in sorted(added):
        item = candidate[name]
        if item.get("status") != "index-only":
            errors.append(f"new repository is not index-only: {item['repository']}")
        if item.get("reason") not in {"awaiting-manual-review", "license-not-detected"}:
            errors.append(f"new repository has an unsafe review state: {item['repository']}")

    for name in sorted(set(base) & set(candidate)):
        before = base[name]
        after = candidate[name]
        for field in TRUST_FIELDS:
            if before.get(field) != after.get(field):
                errors.append(f"trusted field changed for {after['repository']}: {field}")

    removal_records = candidate_catalog.get("removedRepositories", [])
    removal_names = [item.get("repository", "").lower() for item in removal_records]
    if len(removal_names) != len(set(removal_names)):
        errors.append("removal audit contains duplicate repositories")
    if set(removal_names) != removed:
        errors.append("removal audit does not match removed repositories")
    for record in removal_records:
        if record.get("reason") not in REMOVAL_REASONS:
            errors.append(f"unattended removal is not allowed: {record.get('repository', '')}")
        if record.get("reason") == "below-star-threshold" and int(record.get("observedStars", 0)) > int(
            threshold
        ):
            errors.append(f"threshold removal has an invalid Star count: {record.get('repository', '')}")

    for key in ("apiVersion", "kind", "generatorVersion", "counts"):
        if base_registry.get(key) != candidate_registry.get(key):
            errors.append(f"registry {key} changed")
    if base_registry.get("inputDigests", {}).get("communitySkills") != candidate_registry.get("inputDigests", {}).get(
        "communitySkills"
    ):
        errors.append("concrete Skill digest changed")
    if normalized_capabilities(base_registry) != normalized_capabilities(candidate_registry):
        errors.append("installable capability identity or content changed")

    return errors


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout


def load_base_json(root: Path, base: str, path: str) -> dict:
    return json.loads(git_output(root, "show", f"{base}:{path}"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD", help="Git ref for the trusted base tree")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    changed_files = set(git_output(root, "diff", "--name-only", args.base, "--").splitlines())
    changed_files.update(git_output(root, "ls-files", "--others", "--exclude-standard").splitlines())
    errors = classify_candidate(
        load_base_json(root, args.base, "catalog.json"),
        json.loads((root / "catalog.json").read_text()),
        load_base_json(root, args.base, "registry/v1/index.json"),
        json.loads((root / "registry/v1/index.json").read_text()),
        changed_files,
    )
    if errors:
        print("candidate requires human review:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("candidate is observation-only and eligible for automatic merge")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
