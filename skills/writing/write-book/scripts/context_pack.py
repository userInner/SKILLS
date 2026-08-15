#!/usr/bin/env python3
"""Build a bounded chapter context packet without loading the whole manuscript."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CORE_FILES = (
    "brief.md",
    "style.md",
    "canon.md",
    "outline.md",
    "continuity.md",
    "research.md",
    "decisions.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--chapter", required=True, help="Chapter number or chapter-NNN key")
    parser.add_argument("--budget-tokens", type=int, default=48_000)
    parser.add_argument("--previous", type=int, default=2, help="Previous summaries to include")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help="Additional project-relative context file; repeat as needed",
    )
    parser.add_argument("--include-draft", action="store_true")
    parser.add_argument("--output", type=Path, help="Write packet instead of stdout")
    return parser.parse_args()


def chapter_key(raw: str) -> tuple[str, int | None]:
    value = raw.strip().removesuffix(".md")
    if value.isdigit():
        number = int(value)
        if number < 1:
            raise ValueError("chapter number must be positive")
        return f"chapter-{number:03d}", number
    match = re.fullmatch(r"chapter-(\d+)", value)
    if match:
        number = int(match.group(1))
        if number < 1:
            raise ValueError("chapter number must be positive")
        return f"chapter-{number:03d}", number
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("chapter key may contain only letters, digits, underscores, and hyphens")
    return value, None


def estimate_tokens(text: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))
    other = len(text) - cjk
    return cjk + (other + 3) // 4


def truncate_text(text: str, token_budget: int) -> str:
    if token_budget <= 20:
        return "[内容因预算不足而省略]"
    if estimate_tokens(text) <= token_budget:
        return text

    low, high = 1, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if estimate_tokens(text[:middle]) <= token_budget:
            low = middle
        else:
            high = middle - 1
    char_budget = low
    head = max(1, int(char_budget * 0.7))
    tail = max(1, char_budget - head)
    return (
        text[:head].rstrip()
        + "\n\n[...中段因上下文预算被截断；写作前应拆分或压缩源文件...]\n\n"
        + text[-tail:].lstrip()
    )


def safe_project_file(project: Path, relative: str) -> Path:
    candidate = (project / relative).resolve()
    if candidate != project and project not in candidate.parents:
        raise ValueError(f"included path escapes project: {relative}")
    if not candidate.is_file():
        raise FileNotFoundError(f"included file does not exist: {relative}")
    return candidate


def add_unique(items: list[tuple[str, Path, bool]], label: str, path: Path, required: bool) -> None:
    if any(existing == path for _, existing, _ in items):
        return
    items.append((label, path, required))


def main() -> int:
    args = parse_args()
    if args.budget_tokens < 4_000:
        raise SystemExit("--budget-tokens must be at least 4000")
    if args.previous < 0:
        raise SystemExit("--previous must not be negative")

    project = args.project.expanduser().resolve()
    if not project.is_dir():
        raise SystemExit(f"Not a book project directory: {project}")
    try:
        key, number = chapter_key(args.chapter)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    items: list[tuple[str, Path, bool]] = []
    plan = project / "plans" / f"{key}.md"
    if plan.is_file():
        add_unique(items, "目标章节计划", plan, True)
    else:
        print(f"WARNING: missing target plan: {plan}", file=sys.stderr)

    for relative in ("brief.md", "style.md", "canon.md", "outline.md"):
        path = project / relative
        if path.is_file():
            add_unique(items, relative, path, True)
        else:
            print(f"WARNING: missing core file: {path}", file=sys.stderr)

    for relative in args.include:
        try:
            path = safe_project_file(project, relative)
        except (ValueError, FileNotFoundError) as exc:
            raise SystemExit(str(exc)) from exc
        add_unique(items, f"显式资料：{relative}", path, True)

    for relative in ("continuity.md", "research.md", "decisions.md"):
        path = project / relative
        if path.is_file():
            add_unique(items, relative, path, False)

    if number is not None:
        first = max(1, number - args.previous)
        for previous_number in range(first, number):
            path = project / "summaries" / f"chapter-{previous_number:03d}.md"
            if path.is_file():
                add_unique(items, f"前章摘要 {previous_number:03d}", path, False)

    if args.include_draft:
        draft = project / "chapters" / f"{key}.md"
        if not draft.is_file():
            raise SystemExit(f"Target draft does not exist: {draft}")
        add_unique(items, "目标章节现有草稿", draft, True)

    preamble = f"""# {key} 上下文包

- 项目：{project}
- 预算：约 {args.budget_tokens:,} tokens
- 原则：源文件是事实源；本包只是工作快照。遇到截断或冲突时返回源文件核验。

"""
    sections: list[str] = [preamble]
    used = estimate_tokens(preamble)
    notes: list[str] = []

    for label, path, required in items:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(project)
        header = f"\n## {label}\n\n来源：`{relative}`\n\n"
        header_tokens = estimate_tokens(header)
        remaining = args.budget_tokens - used - header_tokens
        if remaining <= 20:
            notes.append(f"省略 `{relative}`：上下文预算已耗尽")
            continue

        original_tokens = estimate_tokens(text)
        rendered = truncate_text(text, remaining)
        if estimate_tokens(rendered) < original_tokens:
            qualifier = "权威文件" if required else "辅助文件"
            notes.append(
                f"截断 `{relative}`（{qualifier}）：估算 {original_tokens:,} tokens，剩余 {remaining:,}"
            )
        section = header + rendered.rstrip() + "\n"
        sections.append(section)
        used += estimate_tokens(section)

    report = "\n## 上下文完整性报告\n\n"
    if notes:
        report += "\n".join(f"- {note}" for note in notes) + "\n"
    else:
        report += "- 未发生截断或预算性省略。\n"
    report += f"- 上下文包估算：{used:,} tokens（启发式，不是 API 精确计数）。\n"
    packet = "".join(sections) + report

    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(packet, encoding="utf-8")
        print(f"Wrote context packet to {output}")
    else:
        sys.stdout.write(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
