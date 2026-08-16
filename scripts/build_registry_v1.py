#!/usr/bin/env python3
"""Build the deterministic Effecta capability registry from reviewed inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path, PurePosixPath


API_VERSION = "effecta.dev/v1"
GENERATOR_VERSION = 1
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
IGNORED_NAMES = {".DS_Store", "effecta.manifest.json", "NOTICE.effecta"}
REDISTRIBUTABLE_LICENSES = {
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC-BY-4.0",
    "ISC",
    "MIT",
    "MPL-2.0",
    "Unlicense",
}


class RegistryError(ValueError):
    pass


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode())


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def safe_local_path(root: Path, value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise RegistryError(f"invalid localPath {value!r}")
    path = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise RegistryError(f"localPath escapes repository: {value!r}")
    if not path.is_dir():
        raise RegistryError(f"missing package directory: {value}")
    return path


def package_files(package_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(package_root.rglob("*")):
        if path.is_symlink():
            raise RegistryError(f"symlink is not allowed: {path}")
        if not path.is_file() or path.name in IGNORED_NAMES:
            continue
        files.append(path)
    if not any(path.name.lower() == "skill.md" for path in files):
        raise RegistryError(f"missing SKILL.md in {package_root}")
    return files


def content_digest(package_root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(package_root).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def repository_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RegistryError("cannot resolve repository commit") from error
    commit = result.stdout.strip().lower()
    if not COMMIT_RE.fullmatch(commit):
        raise RegistryError(f"invalid repository commit {commit!r}")
    return commit


def normalize_repository(value: str) -> str:
    repository = value.strip()
    parts = repository.split("/")
    if len(parts) != 2 or not all(parts):
        raise RegistryError(f"invalid source repository {value!r}")
    return repository


def normalize_source_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RegistryError(f"invalid source path {value!r}")
    return path.as_posix()


def package_id(repository: str, source_path: str) -> str:
    return f"github:{repository.lower()}:{source_path}"


def release_id(package_identifier: str, source_commit: str, digest: str) -> str:
    return sha256_text(f"{package_identifier}\0{source_commit}\0{digest}")


def object_filename(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest() + ".json"


def source_url(repository: str, commit: str, source_path: str) -> str:
    return f"https://github.com/{repository}/tree/{commit}/{source_path}"


def redistribution_status(license_name: str) -> str:
    if license_name in REDISTRIBUTABLE_LICENSES:
        return "allowed"
    if license_name in {"AGPL-3.0", "GPL-2.0", "GPL-3.0", "LGPL-3.0"}:
        return "review-required"
    return "unknown"


def build_source_observations(catalog: dict) -> dict:
    snapshot_date = catalog.get("snapshotDate")
    if not isinstance(snapshot_date, str) or not snapshot_date:
        raise RegistryError("catalog snapshotDate is required")
    observations = []
    seen: set[str] = set()
    for item in catalog.get("repositories", []):
        repository = normalize_repository(item.get("repository", ""))
        key = repository.lower()
        if key in seen:
            continue
        seen.add(key)
        observations.append(
            {
                "archived": bool(item.get("archived", False)),
                "defaultBranch": item.get("defaultBranch") or "",
                "description": item.get("description") or "",
                "kind": item.get("kind") or "unknown",
                "license": item.get("license") or "NOASSERTION",
                "observedAt": snapshot_date + "T00:00:00Z",
                "qualification": item.get("qualification") or "unknown",
                "rank": item.get("rank"),
                "repository": repository,
                "skillFileCount": int(item.get("skillFileCount") or 0),
                "stars": int(item.get("stars") or 0),
                "status": item.get("status") or "index-only",
                "url": item.get("url") or f"https://github.com/{repository}",
            }
        )
    observations.sort(key=lambda item: (item["rank"] or 10**9, item["repository"].lower()))
    return {
        "apiVersion": API_VERSION,
        "kind": "SourceObservationList",
        "minimumStarsExclusive": int(catalog.get("minimumStarsExclusive") or 0),
        "observations": observations,
        "snapshotDate": snapshot_date,
    }


def build_objects(root: Path, catalog: dict, community_index: dict, direct_commit: str) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    source_lookup: dict[str, dict] = {}
    for source in catalog.get("repositories", []):
        if source.get("repository"):
            source_lookup.setdefault(source["repository"].lower(), source)
    index_entries: list[dict] = []
    packages: dict[str, dict] = {}
    releases: dict[str, dict] = {}
    release_ids: set[str] = set()

    for item in community_index.get("skills", []):
        name = str(item.get("name") or "").strip()
        category = str(item.get("category") or "").strip()
        status = str(item.get("status") or "").strip()
        if not name or not category or status not in {"direct", "extracted", "needs-review"}:
            raise RegistryError(f"invalid concrete Skill record {name!r}")

        repository = normalize_repository(str(item.get("sourceRepository") or ""))
        source_path_value = normalize_source_path(str(item.get("sourcePath") or ""))
        local_path = str(item.get("localPath") or "")
        package_root = safe_local_path(root, local_path)
        files = package_files(package_root)

        if status == "direct":
            commit = direct_commit
            digest = content_digest(package_root, files)
            file_count = len(files)
            total_bytes = sum(path.stat().st_size for path in files)
        else:
            commit = str(item.get("sourceCommit") or "").lower()
            digest = str(item.get("contentDigest") or "")
            file_count = int(item.get("fileCount") or 0)
            total_bytes = int(item.get("totalBytes") or 0)

        if not COMMIT_RE.fullmatch(commit):
            raise RegistryError(f"{name}: source commit must be a full SHA")
        if not DIGEST_RE.fullmatch(digest):
            raise RegistryError(f"{name}: invalid content digest")
        if file_count <= 0 or total_bytes <= 0:
            raise RegistryError(f"{name}: invalid package size metadata")

        identifier = package_id(repository, source_path_value)
        if identifier in packages:
            raise RegistryError(f"duplicate package id {identifier}")
        rid = release_id(identifier, commit, digest)
        if rid in release_ids:
            raise RegistryError(f"duplicate release id {rid}")
        release_ids.add(rid)

        source_observation = source_lookup.get(repository.lower(), {})
        license_name = str(item.get("license") or "NOASSERTION")
        static_scan = item.get("staticScan") or {"status": "unknown", "findings": []}
        package_record = {
            "apiVersion": API_VERSION,
            "category": category,
            "description": str(item.get("description") or ""),
            "id": identifier,
            "kind": "CapabilityPackage",
            "name": name,
            "slug": PurePosixPath(local_path).name,
            "source": {"path": source_path_value, "repository": repository},
            "type": "skill",
        }
        release_record = {
            "apiVersion": API_VERSION,
            "artifact": {
                "digest": digest,
                "mediaType": "application/vnd.effecta.skill.directory.v1",
                "path": local_path,
            },
            "compatibility": {"declared": False, "runtimes": ["agent-skill"]},
            "content": {"digest": digest, "fileCount": file_count, "totalBytes": total_bytes},
            "dependencies": {"items": [], "status": "not-declared"},
            "kind": "CapabilityRelease",
            "license": {"redistribution": redistribution_status(license_name), "spdx": license_name},
            "packageId": identifier,
            "permissions": {
                "commands": [],
                "filesystem": [],
                "network": [],
                "status": "not-declared",
            },
            "releaseId": rid,
            "security": {
                "staticScan": {
                    "findings": static_scan.get("findings") or [],
                    "status": static_scan.get("status") or "unknown",
                }
            },
            "smokeTests": [],
            "source": {
                "commit": commit,
                "path": source_path_value,
                "repository": repository,
                "url": source_url(repository, commit, source_path_value),
            },
            "status": status,
        }
        packages[identifier] = package_record
        releases[rid] = release_record
        index_entries.append(
            {
                "category": category,
                "contentDigest": digest,
                "description": package_record["description"],
                "license": license_name,
                "localPath": local_path,
                "name": name,
                "packageFile": "packages/" + object_filename(identifier),
                "packageId": identifier,
                "releaseFile": "releases/" + rid.removeprefix("sha256:") + ".json",
                "releaseId": rid,
                "sourcePath": source_path_value,
                "sourceRank": item.get("sourceRank", source_observation.get("rank")),
                "sourceRepository": repository,
                "sourceStars": item.get("sourceStars", source_observation.get("stars")),
                "staticScanStatus": release_record["security"]["staticScan"]["status"],
                "status": status,
                "type": "skill",
            }
        )

    index_entries.sort(key=lambda item: (item["category"], item["name"].lower(), item["packageId"]))
    return index_entries, packages, releases


def build_categories(entries: list[dict]) -> dict:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"direct": 0, "extracted": 0, "needs-review": 0, "total": 0})
    for item in entries:
        bucket = counts[item["category"]]
        bucket["total"] += 1
        bucket[item["status"]] += 1
    return {
        "apiVersion": API_VERSION,
        "categories": [{"name": name, **counts[name]} for name in sorted(counts)],
        "kind": "CategoryIndex",
    }


def validate_generated(index: dict, packages: dict[str, dict], releases: dict[str, dict]) -> None:
    entries = index["capabilities"]
    if index["counts"]["total"] != len(entries):
        raise RegistryError("registry total count mismatch")
    if len(packages) != len(entries) or len(releases) != len(entries):
        raise RegistryError("registry object count mismatch")
    for item in entries:
        package = packages.get(item["packageId"])
        release = releases.get(item["releaseId"])
        if package is None or release is None:
            raise RegistryError(f"missing object for {item['packageId']}")
        if release["packageId"] != package["id"]:
            raise RegistryError(f"package/release mismatch for {package['id']}")
        if item["contentDigest"] != release["content"]["digest"]:
            raise RegistryError(f"digest mismatch for {package['id']}")


def write_registry(root: Path, output: Path, direct_commit: str | None = None) -> dict:
    root = root.resolve()
    output = output.resolve()
    if output == root or root not in output.parents:
        raise RegistryError("output must be a child of the repository root")

    catalog_path = root / "catalog.json"
    community_path = root / "community-skills" / "index.json"
    catalog = json.loads(catalog_path.read_text())
    community_index = json.loads(community_path.read_text())
    commit = direct_commit or repository_commit(root)
    if not COMMIT_RE.fullmatch(commit):
        raise RegistryError("direct source commit must be a full SHA")

    observations = build_source_observations(catalog)
    entries, packages, releases = build_objects(root, catalog, community_index, commit)
    status_counts = {status: sum(item["status"] == status for item in entries) for status in ("direct", "extracted", "needs-review")}
    index = {
        "apiVersion": API_VERSION,
        "capabilities": entries,
        "counts": {**status_counts, "total": len(entries)},
        "generatorVersion": GENERATOR_VERSION,
        "inputDigests": {
            "catalog": file_digest(catalog_path),
            "communitySkills": file_digest(community_path),
        },
        "kind": "CapabilityIndex",
        "snapshotDate": catalog["snapshotDate"],
        "sourceCommit": commit,
    }
    validate_generated(index, packages, releases)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="effecta-registry-v1-", dir=output.parent) as temporary:
        staging = Path(temporary) / "v1"
        write_json(staging / "index.json", index)
        write_json(staging / "categories.json", build_categories(entries))
        write_json(
            staging / "changes.json",
            {
                "apiVersion": API_VERSION,
                "counts": index["counts"],
                "kind": "RegistryBackfill",
                "mode": "initial-v1-backfill",
                "snapshotDate": index["snapshotDate"],
            },
        )
        write_json(staging / "observations" / "github.json", observations)
        for identifier, package in sorted(packages.items()):
            write_json(staging / "packages" / object_filename(identifier), package)
        for rid, release in sorted(releases.items()):
            write_json(staging / "releases" / (rid.removeprefix("sha256:") + ".json"), release)

        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)
    return index


def directory_snapshot(path: Path) -> dict[str, str]:
    if not path.is_dir():
        return {}
    return {
        item.relative_to(path).as_posix(): sha256_bytes(item.read_bytes())
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def check_registry(root: Path, output: Path) -> list[str]:
    existing = directory_snapshot(output)
    if not existing:
        return [f"missing generated registry: {output}"]
    with tempfile.TemporaryDirectory(prefix="effecta-registry-check-", dir=root) as temporary:
        generated = Path(temporary) / "registry" / "v1"
        write_registry(root, generated)
        expected = directory_snapshot(generated)
    errors = []
    for name in sorted(set(existing) | set(expected)):
        if existing.get(name) != expected.get(name):
            errors.append(name)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "registry" / "v1").resolve()
    try:
        if args.check:
            changed = check_registry(root, output)
            if changed:
                print("registry/v1 is stale:")
                for path in changed[:50]:
                    print(f"  {path}")
                if len(changed) > 50:
                    print(f"  ... and {len(changed) - 50} more")
                return 1
            print("registry/v1 is deterministic and current")
            return 0
        index = write_registry(root, output)
    except (OSError, json.JSONDecodeError, RegistryError) as error:
        print(f"error: {error}")
        return 1
    print(f"generated {index['counts']['total']} capability releases in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
