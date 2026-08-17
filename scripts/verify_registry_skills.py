#!/usr/bin/env python3
"""Create auditable, non-executing isolated-install verification records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_registry_v1 import canonical_json, content_digest, package_files


API_VERSION = "effecta.dev/v1"
POLICY_VERSION = 1
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
STATUS_ORDER = {"direct": 0, "extracted": 1}


class VerificationError(ValueError):
    pass


def evidence_digest(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key not in {"evidenceDigest", "signature"}}
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


def verification_path(root: Path, release_id: str) -> Path:
    return root / "verifications" / "v1" / (release_id.removeprefix("sha256:") + ".json")


def existing_release_ids(root: Path) -> set[str]:
    result: set[str] = set()
    directory = root / "verifications" / "v1"
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.json")):
        record = json.loads(path.read_text())
        release_id = record.get("releaseId")
        if release_id in result:
            raise VerificationError(f"duplicate verification for {release_id}")
        result.add(release_id)
    return result


def select_candidates(index: dict, verified: set[str], limit: int) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for capability in index.get("capabilities", []):
        if capability.get("releaseId") in verified:
            continue
        if capability.get("status") not in STATUS_ORDER or capability.get("staticScanStatus") != "passed":
            continue
        groups[capability["category"]].append(capability)
    queues: dict[str, deque[dict]] = {}
    for category, items in groups.items():
        items.sort(
            key=lambda item: (
                STATUS_ORDER[item["status"]],
                -(item.get("sourceStars") or 0),
                item["name"].lower(),
                item["packageId"],
            )
        )
        queues[category] = deque(items)
    selected: list[dict] = []
    categories = sorted(queues)
    while len(selected) < limit and categories:
        remaining: list[str] = []
        for category in categories:
            queue = queues[category]
            if queue and len(selected) < limit:
                selected.append(queue.popleft())
            if queue:
                remaining.append(category)
        categories = remaining
    return selected


def frontmatter_valid(path: Path) -> bool:
    text = path.read_text(errors="replace")
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    if end < 0:
        return False
    metadata = text[4:end]
    return bool(re.search(r"(?m)^name:\s*\S", metadata) and re.search(r"(?m)^description:\s*\S", metadata))


def verifiable_files(package_root: Path) -> list[Path]:
    files = package_files(package_root)
    manifest_path = package_root / "effecta.manifest.json"
    if not manifest_path.is_file():
        return files
    manifest = json.loads(manifest_path.read_text())
    expected_count = int(manifest.get("fileCount") or 0)
    copied_license = package_root / "LICENSE"
    if expected_count > 0 and len(files) == expected_count + 1 and copied_license in files:
        files = [path for path in files if path != copied_license]
    return files


def check(name: str, passed: bool, success: str, failure: str) -> dict[str, str]:
    return {"name": name, "status": "passed" if passed else "failed", "summary": success if passed else failure}


def verify_capability(root: Path, capability: dict, *, run_id: str, recorded_at: str, signature: str) -> dict:
    package_root = (root / capability["localPath"]).resolve()
    root_resolved = root.resolve()
    within_root = package_root != root_resolved and root_resolved in package_root.parents
    source_url = (
        f"https://github.com/{capability['sourceRepository']}/tree/"
        f"{capability['sourceCommit']}/{capability['sourcePath']}"
    )
    immutable = (
        COMMIT_RE.fullmatch(str(capability.get("sourceCommit", ""))) is not None
        and capability.get("sourceUrl") == source_url
    )

    files = []
    package_error = ""
    try:
        if not within_root or not package_root.is_dir():
            raise VerificationError("package path is missing or outside repository")
        files = verifiable_files(package_root)
    except (OSError, ValueError) as error:
        package_error = str(error)

    actual_digest = content_digest(package_root, files) if files else ""
    digest_matches = bool(files) and actual_digest == capability.get("contentDigest")
    skill_file = next((path for path in files if path.name.lower() == "skill.md"), None)
    integrity = bool(skill_file and frontmatter_valid(skill_file))

    isolated = False
    isolated_error = ""
    if files and digest_matches and integrity:
        try:
            with tempfile.TemporaryDirectory(prefix="effecta-skill-verify-") as temporary:
                installed = Path(temporary) / "skills" / capability["name"]
                shutil.copytree(package_root, installed, symlinks=False)
                copied_files = verifiable_files(installed)
                isolated = content_digest(installed, copied_files) == capability["contentDigest"]
                isolated = isolated and frontmatter_valid(
                    next(path for path in copied_files if path.name.lower() == "skill.md")
                )
        except (OSError, ValueError, StopIteration) as error:
            isolated_error = str(error)

    static_passed = capability.get("staticScanStatus") == "passed"
    checks = [
        check("immutable-source", immutable, "来源固定到完整 Git Commit。", "来源 URL 或 Commit 不满足固定版本要求。"),
        check(
            "content-digest",
            digest_matches,
            "目录 SHA-256 与 Registry 记录一致。",
            f"目录摘要不一致：{actual_digest or '无法计算'}。",
        ),
        check(
            "package-integrity",
            integrity,
            f"SKILL.md、文件边界和 {len(files)} 个包文件通过。",
            package_error or "SKILL.md 缺少有效的 name/description frontmatter。",
        ),
        check("static-scan", static_passed, "基础静态规则无未解决发现。", "静态扫描未通过。"),
        check(
            "isolated-install",
            isolated,
            "隔离目录复制后摘要一致，SKILL.md 可重新加载。",
            isolated_error or "隔离复制后的包无法通过完整性复验。",
        ),
    ]
    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    record = {
        "apiVersion": API_VERSION,
        "checks": checks,
        "contentDigest": capability["contentDigest"],
        "environment": {
            "filesystem": "ephemeral-directory",
            "networkAccess": False,
            "policyVersion": POLICY_VERSION,
            "runner": "github-actions" if os.getenv("GITHUB_ACTIONS") == "true" else "local",
            "sourceCodeExecution": False,
        },
        "kind": "VerificationRecord",
        "level": "isolated-install",
        "metrics": {
            "commandsExecuted": 0,
            "fileCount": len(files),
            "networkRequests": 0,
            "totalBytes": sum(path.stat().st_size for path in files),
        },
        "releaseId": capability["releaseId"],
        "runId": run_id,
        "signedAt": recorded_at,
        "signature": signature,
        "status": status,
        "summary": (
            "固定 Commit、目录摘要、静态规则和隔离复制均通过；未执行来源脚本。"
            if status == "passed"
            else "至少一项固定来源、包完整性或隔离复制检查未通过；禁止安装。"
        ),
        "type": "sandbox-smoke",
    }
    record["evidenceDigest"] = evidence_digest(record)
    return record


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    if record.get("apiVersion") != API_VERSION or record.get("kind") != "VerificationRecord":
        errors.append("unsupported verification schema")
    if not DIGEST_RE.fullmatch(str(record.get("releaseId", ""))):
        errors.append("invalid releaseId")
    if not DIGEST_RE.fullmatch(str(record.get("contentDigest", ""))):
        errors.append("invalid contentDigest")
    if record.get("status") not in {"passed", "failed", "timed-out", "skipped"}:
        errors.append("invalid status")
    checks = record.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks are required")
    elif any(item.get("status") not in {"passed", "failed"} for item in checks):
        errors.append("invalid check status")
    if record.get("evidenceDigest") != evidence_digest(record):
        errors.append("evidence digest mismatch")
    if not record.get("runId") or not record.get("signature") or not record.get("signedAt"):
        errors.append("run identity is required")
    return errors


def default_run_identity() -> tuple[str, str, str]:
    recorded_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if os.getenv("GITHUB_ACTIONS") == "true":
        run_id = f"github-actions:{os.environ['GITHUB_RUN_ID']}:{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
        run_url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        signature = f"github-actions:{run_url}@{os.environ['GITHUB_SHA']}"
        return run_id, recorded_at, signature
    return "local:manual", recorded_at, "local:untrusted"


def run(root: Path, *, limit: int, run_id: str, recorded_at: str, signature: str, dry_run: bool = False) -> list[dict]:
    index = json.loads((root / "registry" / "v1" / "index.json").read_text())
    selected = select_candidates(index, existing_release_ids(root), limit)
    records = [
        verify_capability(root, capability, run_id=run_id, recorded_at=recorded_at, signature=signature)
        for capability in selected
    ]
    for record in records:
        errors = validate_record(record)
        if errors:
            raise VerificationError(f"{record['releaseId']}: {', '.join(errors)}")
        if not dry_run:
            path = verification_path(root, record["releaseId"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_json(record))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--run-id")
    parser.add_argument("--recorded-at")
    parser.add_argument("--signature")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        print("error: limit must be between 1 and 100")
        return 2
    default_run_id, default_recorded_at, default_signature = default_run_identity()
    try:
        records = run(
            args.root.resolve(),
            limit=args.limit,
            run_id=args.run_id or default_run_id,
            recorded_at=args.recorded_at or default_recorded_at,
            signature=args.signature or default_signature,
            dry_run=args.dry_run,
        )
    except (OSError, json.JSONDecodeError, VerificationError) as error:
        print(f"error: {error}")
        return 1
    passed = sum(record["status"] == "passed" for record in records)
    failed = sum(record["status"] == "failed" for record in records)
    print(f"verified {len(records)} Skill releases: {passed} passed, {failed} failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
