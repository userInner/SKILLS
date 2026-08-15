#!/usr/bin/env python3
"""Initialize a non-destructive, context-efficient book project."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Book project directory")
    parser.add_argument("--title", required=True, help="Working title")
    parser.add_argument(
        "--type",
        choices=("fiction", "nonfiction", "hybrid"),
        default="fiction",
        help="Book type",
    )
    parser.add_argument("--language", default="zh-CN", help="Primary language")
    return parser.parse_args()


def templates(title: str, book_type: str, language: str) -> dict[str, str]:
    return {
        "brief.md": f"""# 书籍简报

- 暂定书名：{title}
- 类型：{book_type}
- 主要语种：{language}
- 目标读者：
- 一句话承诺：
- 目标长度：

## 读者起点


## 读者终点


## 范围与边界


## 预期体验


## 完成标准

""",
        "outline.md": """# 全书大纲

## 全书主线


## 分部结构

### 第一部

- 作用：
- 开始状态：
- 结束状态：

## 章节表

| 章 | 暂定标题 | 主要任务 | 开始状态 | 结束状态 | 状态 |
|---|---|---|---|---|---|
| 001 |  |  |  |  | planned |
""",
        "style.md": """# 文风指南

## 叙述声音


## 视角、时态与称谓


## 节奏与句法


## 术语与格式


## 鼓励使用


## 禁止使用


## 样本文段或参照

""",
        "canon.md": """# 设定与固定事实

只记录已确定、需要跨章节保持一致的事实。未确定内容放入“待决问题”。

## 人物、主体或关键概念


## 世界、背景或适用范围


## 时间线


## 固定术语与定义


## 已锁定事实


## 待决问题

""",
        "continuity.md": """# 连续性账本

## 当前状态


## 时间线


## 开放伏笔、问题或读者承诺


## 已兑现项目


## 已知冲突

""",
        "research.md": """# 研究与证据账本

## 主张登记

| ID | 主张 | 证据 | 来源 ID | 状态 | 使用章节 |
|---|---|---|---|---|---|

状态使用：`unverified`、`verified`、`disputed`、`remove`。

## 来源登记

| 来源 ID | 标题/作者 | 日期 | URL 或文件 | 类型 | 可靠性说明 |
|---|---|---|---|---|---|

## 待核验

""",
        "decisions.md": """# 决策记录

| 日期 | 决策 | 原因 | 影响章节 | 是否可逆 |
|---|---|---|---|---|
""",
        "chapter-index.md": """# 章节索引

| 章 | 标题 | 状态 | 计划 | 草稿 | 摘要 | 字数/字量 |
|---|---|---|---|---|---|---|
| 001 |  | planned | plans/chapter-001.md |  |  | 0 |
""",
        "plans/chapter-001.md": """# 第 001 章计划

## 唯一主要目的


## 开始状态与结束状态


## 必须出现


## 禁止提前出现


## 场景、论证、例子或证据


## 承接前章


## 推进后章


## 需要加载的资料


## 目标长度与完成判据

""",
        "chapters/.gitkeep": "",
        "summaries/.gitkeep": "",
        "sources/.gitkeep": "",
        "exports/.gitkeep": "",
    }


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    if project.exists() and any(project.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty directory: {project}")

    files = templates(args.title.strip(), args.type, args.language.strip())
    if not args.title.strip():
        raise SystemExit("--title must not be empty")

    for relative, content in files.items():
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    print(f"Initialized {args.type} book project at {project}")
    print(f"Created {len(files)} files; no existing content was overwritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
