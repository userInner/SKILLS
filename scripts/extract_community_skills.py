#!/usr/bin/env python3
"""Extract concrete Skill packages from reviewed GitHub source repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC0-1.0"}
IGNORED_PARTS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "fixtures",
    "tests",
    "testdata",
}
CANONICAL_SKILL_PARENTS = {"skills", ".agents", ".claude", ".cursor", ".codex"}
MAX_FILES_PER_PACKAGE = 250
MAX_FILE_BYTES = 1_500_000
MAX_PACKAGE_BYTES = 5_000_000
EXTRACTOR_VERSION = 1

CATEGORY_KEYWORDS = {
    "design": ("design", "frontend", "ui", "ux", "css", "visual", "image", "video", "slide", "presentation"),
    "engineering": (
        "api",
        "backend",
        "code",
        "database",
        "debug",
        "deploy",
        "devops",
        "engineering",
        "git",
        "interface",
        "mcp",
        "performance",
        "programming",
        "security",
        "test",
    ),
    "growth": ("content", "growth", "launch", "marketing", "sales", "seo", "social"),
    "product": ("competitor", "discovery", "market", "prd", "priorit", "product", "roadmap", "strategy"),
    "research": ("academic", "analysis", "citation", "experiment", "paper", "research", "science", "scientific", "statistics"),
    "writing": ("article", "copy", "document", "humaniz", "writing", "writer"),
    "workflow": ("agent", "automation", "brainstorm", "context", "memory", "plan", "skill", "task", "workflow"),
}
GENERIC_CATEGORY_KEYWORDS = {"analysis", "content", "design", "skill", "strategy", "workflow"}

RISK_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "embedded-token": re.compile(r"\b(?:gh[opsu]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    "pipe-to-shell": re.compile(r"\b(?:curl|wget)\b[^\n|]{0,300}\|\s*(?:ba|z|k)?sh\b", re.IGNORECASE),
    "recursive-delete": re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r\b"),
    "privilege-escalation": re.compile(r"\bsudo\b"),
    "shell-eval": re.compile(r"\b(?:eval|exec)\s*\("),
    "unsafe-subprocess": re.compile(r"subprocess\.[A-Za-z_]+\([^\n]{0,400}shell\s*=\s*True"),
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"name", "description"}:
            metadata[key.strip()] = value.strip().strip("'\"")
    return metadata


def safe_slug(value: str) -> str:
    value = value.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")[:80]


def is_canonical_skill(path: Path, checkout: Path) -> bool:
    relative = path.relative_to(checkout)
    parts = relative.parts
    lowered = {part.lower() for part in parts}
    if lowered & IGNORED_PARTS or path.name.lower() != "skill.md":
        return False
    if len(parts) == 1:
        return True
    if len(parts) >= 3 and parts[-3].lower() == "skills":
        prefix = parts[:-3]
        if not prefix:
            return True
        if len(prefix) == 1 and prefix[0].lower() in CANONICAL_SKILL_PARENTS:
            return True
        if len(prefix) <= 2 and not any(part.lower() in {"docs", "examples", "translations", "locales"} for part in prefix):
            return True
    return False


def package_files(package_root: Path) -> tuple[list[Path], str | None]:
    files: list[Path] = []
    total_bytes = 0
    for path in sorted(package_root.rglob("*")):
        if path.is_symlink():
            return [], f"symlink:{path.relative_to(package_root)}"
        if not path.is_file():
            continue
        relative = path.relative_to(package_root)
        if set(relative.parts) & IGNORED_PARTS or path.name == ".DS_Store":
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            return [], f"file-too-large:{relative}"
        total_bytes += size
        if total_bytes > MAX_PACKAGE_BYTES:
            return [], "package-too-large"
        files.append(path)
        if len(files) > MAX_FILES_PER_PACKAGE:
            return [], "too-many-files"
    if not any(path.name.lower() == "skill.md" for path in files):
        return [], "missing-skill-md"
    return files, None


def content_digest(package_root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(package_root).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def scan_risks(files: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in files:
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".woff", ".woff2"}:
            continue
        text = path.read_text(errors="replace")
        for rule, pattern in RISK_PATTERNS.items():
            if pattern.search(text):
                findings.append({"rule": rule, "file": path.name})
    return findings


def classify(name: str, description: str, source_path: str) -> str:
    identity = f"{name} {source_path}".lower()
    detail = description.lower()

    def matches(keyword: str, text: str) -> bool:
        if len(keyword) <= 3:
            return bool(re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text))
        return keyword in text

    scores = {
        category: sum(
            ((1 if keyword in GENERIC_CATEGORY_KEYWORDS else 2) if matches(keyword, identity) else 0)
            + (1 if matches(keyword, detail) else 0)
            for keyword in keywords
        )
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "workflow"


def clone_source(source: dict, destination: Path) -> str:
    command = [
        "git",
        "clone",
        "--quiet",
        "--depth=1",
        "--filter=blob:none",
        "--no-tags",
        "--branch",
        source.get("defaultBranch", "main"),
        source["url"],
        str(destination),
    ]
    subprocess.run(command, check=True)
    return subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()


def find_license(checkout: Path) -> Path | None:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md"):
        candidate = checkout / name
        if candidate.is_file():
            return candidate
    return None


def existing_direct_names(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for skill_file in (root / "skills").glob("*/*/SKILL.md"):
        metadata = parse_frontmatter(skill_file)
        name = safe_slug(metadata.get("name") or skill_file.parent.name)
        result[name] = skill_file.parent.relative_to(root).as_posix()
    return result


def write_notice(destination: Path, source: dict, commit: str, source_path: str, license_id: str) -> None:
    notice = (
        f"Source: {source['url']}/tree/{commit}/{source_path}\n"
        f"Imported from commit: {commit}\n"
        f"License: {license_id}\n\n"
        "Extracted by userInner/SKILLS without modifying upstream package files. "
        "Candidate status does not imply security or quality approval.\n"
    )
    (destination / "NOTICE.effecta").write_text(notice)


def copy_package(package_root: Path, files: list[Path], destination: Path) -> None:
    destination.mkdir(parents=True)
    for path in files:
        relative = path.relative_to(package_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def render_community_readme(index: dict) -> str:
    category_counts: dict[str, int] = {}
    for item in index["skills"]:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
    category_rows = "\n".join(
        f"| `{category}` | {count} |" for category, count in sorted(category_counts.items())
    )
    return f"""# Community Skills

从许可证明确且已进入精选来源名单的 GitHub 仓库中，按真实 Skill 包根目录提取的候选能力包。

当前记录 **{index['concreteSkillCount']} 个具体 Skill**：

- **{index['directSkillCount']} 个 `direct`**：已在 `skills/` 中完成人工整理，可直装。
- **{index['extractedSkillCount']} 个 `extracted`**：包文件完整，基础静态扫描未命中；尚未完成人工验收与沙箱运行。
- **{index['needsReviewCount']} 个 `needs-review`**：命中高风险命令模式，必须人工审查。
- **{index['rejectedCount']} 个 rejected**：重复、超限或结构不完整，不进入包目录。

机器读取入口：[index.json](index.json)。每个候选包包含原始 `SKILL.md`、包内依赖文件、许可证、`NOTICE.effecta` 和 `effecta.manifest.json`。

## 分类

| 分类 | Skill 数 |
|---|---:|
{category_rows}

## 状态边界

`extracted` 只表示文件结构、体积、许可证和基础静态规则通过，不表示安全认证或运行验证。Agent 可以搜索、读取和提出安装方案；人类批准后，仍应在隔离目录校验摘要并执行该包声明的最小冒烟测试。

`needs-review` 不应自动安装。包被保留是为了让审查过程可复现，而不是推荐使用。

## 重新生成

```bash
python3 scripts/extract_community_skills.py
```

排行榜更新成功后，GitHub Actions 会自动运行提取器和校验器。只有具体 Skill 发生变化时才会更新 `automation/community-skills` 候选分支并创建或刷新审核 PR；不会自动合并到主分支。

提取器只处理 `catalog.json` 中状态为 `selected-import` 且许可证在允许列表中的来源；翻译文档、测试夹具、vendor、缓存、重复内容、超大文件和超大包会被排除。
"""


def update_root_readme(root: Path, index: dict) -> None:
    path = root / "README.md"
    text = path.read_text()
    start_marker = "<!-- community-stats:start -->"
    end_marker = "<!-- community-stats:end -->"
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    summary = (
        f"{start_marker}\n"
        f"包级索引现有 **{index['concreteSkillCount']} 个具体 Skill**："
        f"**{index['directSkillCount']} 个可直装**、"
        f"**{index['extractedSkillCount']} 个已提取待验收**、"
        f"**{index['needsReviewCount']} 个待安全审查**。"
        "来源仓库数不等于 Skill 数，候选包也不等于安全认证。"
        "查看 [具体 Skill 目录](community-skills/README.md) 与 [机器索引](community-skills/index.json)。\n"
        f"{end_marker}"
    )
    path.write_text(text[:start] + summary + text[end + len(end_marker) :])


def stable_generated_at(previous: dict, current: dict) -> str:
    previous_semantic = {key: value for key, value in previous.items() if key != "generatedAt"}
    current_semantic = {key: value for key, value in current.items() if key != "generatedAt"}
    if previous.get("generatedAt") and previous_semantic == current_semantic:
        return previous["generatedAt"]
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def extract(root: Path, *, max_sources: int | None = None, max_packages: int | None = None) -> dict:
    catalog = json.loads((root / "catalog.json").read_text())
    previous_index_path = root / "community-skills" / "index.json"
    previous_index = json.loads(previous_index_path.read_text()) if previous_index_path.is_file() else {}
    previous_candidates = {
        (item.get("sourceRepository"), item.get("sourcePath"), item.get("contentDigest")): item
        for item in previous_index.get("skills", [])
        if item.get("status") != "direct" and item.get("contentDigest")
    }
    can_reuse_previous = previous_index.get("extractorVersion") == EXTRACTOR_VERSION
    sources = [
        source
        for source in catalog["repositories"]
        if source.get("status") == "selected-import" and source.get("license") in ALLOWED_LICENSES
    ]
    if max_sources is not None:
        sources = sources[:max_sources]

    direct = existing_direct_names(root)
    entries: list[dict] = []
    for name, local_path in sorted(direct.items()):
        skill_file = root / local_path / "SKILL.md"
        metadata = parse_frontmatter(skill_file)
        entries.append(
            {
                "name": name,
                "category": PurePosixPath(local_path).parts[1],
                "description": metadata.get("description", ""),
                "sourceRepository": "userInner/SKILLS",
                "sourcePath": local_path,
                "sourceCommit": "local-reviewed",
                "sourceRank": None,
                "sourceStars": None,
                "license": "see-package",
                "status": "direct",
                "staticScan": {"status": "passed", "findings": []},
                "localPath": local_path,
            }
        )
    rejected: list[dict] = []
    seen_digests: dict[str, str] = {}
    copied_count = 0

    with tempfile.TemporaryDirectory(prefix="effecta-skill-extract-") as temporary:
        temporary_root = Path(temporary)
        output = temporary_root / "community-skills"
        for source_index, source in enumerate(sources, 1):
            checkout = temporary_root / f"source-{source_index}"
            commit = clone_source(source, checkout)
            source_license = find_license(checkout)
            skill_files = [path for path in checkout.rglob("SKILL.md") if is_canonical_skill(path, checkout)]
            for skill_file in sorted(skill_files):
                package_root = skill_file.parent
                metadata = parse_frontmatter(skill_file)
                name = safe_slug(metadata.get("name") or package_root.name)
                source_path = package_root.relative_to(checkout).as_posix()
                if not name:
                    rejected.append({"source": source["repository"], "path": source_path, "reason": "invalid-name"})
                    continue
                if name in direct:
                    continue
                files, package_error = package_files(package_root)
                if package_error:
                    rejected.append({"source": source["repository"], "path": source_path, "reason": package_error})
                    continue
                digest = content_digest(package_root, files)
                if digest in seen_digests:
                    rejected.append(
                        {
                            "source": source["repository"],
                            "path": source_path,
                            "reason": "duplicate-content",
                            "duplicateOf": seen_digests[digest],
                        }
                    )
                    continue
                if max_packages is not None and copied_count >= max_packages:
                    break
                previous = previous_candidates.get((source["repository"], source_path, digest)) if can_reuse_previous else None
                if previous:
                    previous_local_path = PurePosixPath(previous["localPath"])
                    if not previous_local_path.parts or previous_local_path.parts[0] != "community-skills":
                        raise RuntimeError(f"invalid previous localPath: {previous['localPath']}")
                    previous_package = root / previous["localPath"]
                    if not previous_package.is_dir():
                        raise RuntimeError(f"missing previous package: {previous['localPath']}")
                    destination = output.joinpath(*previous_local_path.parts[1:])
                    shutil.copytree(previous_package, destination)
                    entries.append(previous)
                    seen_digests[digest] = previous["localPath"]
                    copied_count += 1
                    continue
                risks = scan_risks(files)
                category = classify(name, metadata.get("description", ""), source_path)
                source_key = safe_slug(source["repository"].replace("/", "--"))
                destination = output / category / f"{name}--{source_key}"
                if destination.exists():
                    destination = output / category / f"{name}--{source_key}--{digest.removeprefix('sha256:')[:10]}"
                copy_package(package_root, files, destination)
                if source_license and not (destination / "LICENSE").exists():
                    shutil.copy2(source_license, destination / "LICENSE")
                write_notice(destination, source, commit, source_path, source["license"])
                status = "needs-review" if risks else "extracted"
                manifest = {
                    "schemaVersion": 1,
                    "name": name,
                    "category": category,
                    "description": metadata.get("description", ""),
                    "source": {
                        "repository": source["repository"],
                        "url": source["url"],
                        "path": source_path,
                        "commit": commit,
                        "rank": source.get("rank"),
                        "stars": source.get("stars"),
                    },
                    "license": source["license"],
                    "contentDigest": digest,
                    "fileCount": len(files),
                    "totalBytes": sum(path.stat().st_size for path in files),
                    "staticScan": {"status": "review" if risks else "passed", "findings": risks},
                    "status": status,
                }
                (destination / "effecta.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                local_path = destination.relative_to(output.parent).as_posix()
                entries.append(
                    {
                        **manifest,
                        "sourceRepository": source["repository"],
                        "sourcePath": source_path,
                        "sourceCommit": commit,
                        "sourceRank": source.get("rank"),
                        "sourceStars": source.get("stars"),
                        "localPath": local_path,
                    }
                )
                seen_digests[digest] = local_path
                copied_count += 1
            if max_packages is not None and copied_count >= max_packages:
                break

        entries.sort(key=lambda item: (item["category"], item["name"], item["sourceRepository"]))
        index = {
            "schemaVersion": 1,
            "extractorVersion": EXTRACTOR_VERSION,
            "sourceCount": len(sources),
            "concreteSkillCount": len(entries),
            "directSkillCount": sum(item["status"] == "direct" for item in entries),
            "extractedSkillCount": sum(item["status"] == "extracted" for item in entries),
            "needsReviewCount": sum(item["status"] == "needs-review" for item in entries),
            "rejectedCount": len(rejected),
            "skills": entries,
            "rejected": rejected,
        }
        index["generatedAt"] = stable_generated_at(previous_index, index)
        (output / "index.json").parent.mkdir(parents=True, exist_ok=True)
        (output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
        (output / "README.md").write_text(render_community_readme(index))
        final_output = root / "community-skills"
        backup = root / ".community-skills.previous"
        if backup.exists():
            shutil.rmtree(backup)
        if final_output.exists():
            final_output.rename(backup)
        shutil.copytree(output, final_output)
        if backup.exists():
            shutil.rmtree(backup)
    update_root_readme(root, index)
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-sources", type=int)
    parser.add_argument("--max-packages", type=int)
    args = parser.parse_args()
    index = extract(args.root.resolve(), max_sources=args.max_sources, max_packages=args.max_packages)
    print(
        f"concrete={index['concreteSkillCount']} extracted={index['extractedSkillCount']} "
        f"review={index['needsReviewCount']} rejected={index['rejectedCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
