#!/usr/bin/env python3
"""Report book-project completeness, chapter size, and stale summaries."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED = (
    "brief.md",
    "outline.md",
    "style.md",
    "canon.md",
    "continuity.md",
    "research.md",
    "decisions.md",
    "chapter-index.md",
)


def count_text_units(text: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))
    latin_words = len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text))
    return cjk + latin_words


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero on warnings")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        raise SystemExit(f"Not a directory: {project}")

    warnings: list[str] = []
    missing = [relative for relative in REQUIRED if not (project / relative).is_file()]
    warnings.extend(f"missing core file: {relative}" for relative in missing)

    chapter_dir = project / "chapters"
    plan_dir = project / "plans"
    summary_dir = project / "summaries"
    chapters = sorted(chapter_dir.glob("chapter-*.md")) if chapter_dir.is_dir() else []
    plans = sorted(plan_dir.glob("chapter-*.md")) if plan_dir.is_dir() else []

    total = 0
    print(f"Book project: {project}")
    print("\nChapters:")
    if not chapters:
        print("  (no chapter drafts yet)")

    chapter_keys = {path.stem for path in chapters}
    for chapter in chapters:
        key = chapter.stem
        units = count_text_units(chapter.read_text(encoding="utf-8"))
        total += units
        plan = plan_dir / f"{key}.md"
        summary = summary_dir / f"{key}.md"
        flags: list[str] = []
        if not plan.is_file():
            flags.append("missing-plan")
            warnings.append(f"{key}: missing plan")
        if not summary.is_file():
            flags.append("missing-summary")
            warnings.append(f"{key}: missing summary")
        elif summary.stat().st_mtime < chapter.stat().st_mtime:
            flags.append("stale-summary")
            warnings.append(f"{key}: summary is older than draft")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        print(f"  {key}: {units:,} words/CJK chars{suffix}")

    planned_only = [path.stem for path in plans if path.stem not in chapter_keys]
    print(f"\nDraft total: {total:,} words/CJK chars")
    if planned_only:
        print("Planned without draft: " + ", ".join(planned_only))

    print("\nWarnings:")
    if warnings:
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("  (none)")

    return 1 if args.strict and warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
