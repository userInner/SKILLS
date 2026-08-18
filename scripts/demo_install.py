#!/usr/bin/env python3
"""Install one curated Skill into an isolated target and verify the copy."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"missing YAML frontmatter: {path}")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"unclosed YAML frontmatter: {path}")
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"name", "description"}:
            metadata[key.strip()] = value.strip().strip("'\"")
    if not metadata.get("name") or not metadata.get("description"):
        raise ValueError(f"frontmatter must include name and description: {path}")
    return metadata


def discover_skills(root: Path) -> dict[str, Path]:
    discovered: dict[str, Path] = {}
    for skill_file in sorted((root / "skills").glob("*/*/SKILL.md")):
        name = parse_frontmatter(skill_file)["name"]
        if name in discovered:
            raise ValueError(f"duplicate Skill name: {name}")
        discovered[name] = skill_file.parent
    if not discovered:
        raise ValueError(f"no curated Skills found under {root / 'skills'}")
    return discovered


def directory_digest(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in the demo: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
        file_count += 1
    return digest.hexdigest(), file_count


def install_skill(source: Path, target_root: Path) -> tuple[Path, str, int]:
    name = parse_frontmatter(source / "SKILL.md")["name"]
    destination = target_root / name
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {destination}")
    target_root.mkdir(parents=True, exist_ok=True)
    source_digest, source_files = directory_digest(source)
    shutil.copytree(source, destination)
    copied_digest, copied_files = directory_digest(destination)
    if (copied_digest, copied_files) != (source_digest, source_files):
        raise RuntimeError("copied Skill does not match the source")
    return destination, copied_digest, copied_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy one curated Skill, verify its digest, and print a ready-to-run prompt."
    )
    parser.add_argument("skill", nargs="?", default="systematic-debugging")
    parser.add_argument(
        "--target",
        type=Path,
        help="Skill root to install into. Defaults to a new temporary demo directory.",
    )
    parser.add_argument("--list", action="store_true", help="List curated Skill names and exit.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    skills = discover_skills(root)
    if args.list:
        for name in sorted(skills):
            print(name)
        return 0
    if args.skill not in skills:
        choices = ", ".join(sorted(skills))
        parser.error(f"unknown Skill {args.skill!r}; choose one of: {choices}")

    target = args.target or Path(tempfile.mkdtemp(prefix="agent-skills-demo-"))
    destination, digest, file_count = install_skill(skills[args.skill], target.expanduser().resolve())
    metadata = parse_frontmatter(destination / "SKILL.md")
    print(f"✓ Found curated Skill: {metadata['name']}")
    print(f"✓ Copied and verified {file_count} files")
    print(f"✓ SHA-256: {digest}")
    print(f"✓ Demo path: {destination}")
    print()
    print(f"Codex prompt: Use ${metadata['name']} to investigate a reproducible bug in this project.")
    print(f"Claude Code: /{metadata['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
