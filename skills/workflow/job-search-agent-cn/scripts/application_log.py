#!/usr/bin/env python3
"""Maintain a deduplicated CSV application log."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "timestamp",
    "platform",
    "company",
    "role",
    "location",
    "salary",
    "url",
    "recruiter",
    "status",
    "last_contact",
    "notes",
]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def identity(row: dict[str, str]) -> tuple[str, str]:
    url = row.get("url", "").strip()
    if url:
        return ("url", url)
    return (
        row.get("company", "").strip().casefold(),
        row.get("role", "").strip().casefold(),
    )


def command_init(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        write_rows(path, [])
    print(path)


def command_add(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser().resolve()
    rows = read_rows(path)
    row = {field: getattr(args, field, "") or "" for field in FIELDS}
    row["timestamp"] = now()
    row["last_contact"] = row["last_contact"] or row["timestamp"]
    key = identity(row)
    if any(identity(existing) == key for existing in rows):
        raise SystemExit("duplicate application: URL or company/role already exists")
    rows.append(row)
    write_rows(path, rows)
    print(f"added: {row['company']} | {row['role']} | {row['status']}")


def command_update(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser().resolve()
    rows = read_rows(path)
    matched = 0
    for row in rows:
        if args.url and row.get("url") != args.url:
            continue
        if not args.url and not (
            row.get("company", "").casefold() == args.company.casefold()
            and row.get("role", "").casefold() == args.role.casefold()
        ):
            continue
        if args.status:
            row["status"] = args.status
        if args.notes:
            row["notes"] = args.notes
        row["last_contact"] = args.last_contact or now()
        matched += 1
    if matched != 1:
        raise SystemExit(f"expected one matching application, found {matched}")
    write_rows(path, rows)
    print("updated")


def command_list(args: argparse.Namespace) -> None:
    rows = read_rows(Path(args.path).expanduser().resolve())
    for row in rows:
        if args.status and row.get("status") != args.status:
            continue
        print(
            "\t".join(
                [
                    row.get("last_contact", ""),
                    row.get("company", ""),
                    row.get("role", ""),
                    row.get("status", ""),
                    row.get("url", ""),
                ]
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--path", required=True)
    init_parser.set_defaults(func=command_init)

    add_parser = sub.add_parser("add")
    add_parser.add_argument("--path", required=True)
    names = [
        "platform",
        "company",
        "role",
        "location",
        "salary",
        "url",
        "recruiter",
        "status",
        "last_contact",
        "notes",
    ]
    for name in names:
        add_parser.add_argument(
            f"--{name.replace('_', '-')}", dest=name, default=""
        )
    add_parser.set_defaults(func=command_add)

    update_parser = sub.add_parser("update")
    update_parser.add_argument("--path", required=True)
    update_parser.add_argument("--url", default="")
    update_parser.add_argument("--company", default="")
    update_parser.add_argument("--role", default="")
    update_parser.add_argument("--status", default="")
    update_parser.add_argument("--last-contact", default="")
    update_parser.add_argument("--notes", default="")
    update_parser.set_defaults(func=command_update)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--path", required=True)
    list_parser.add_argument("--status", default="")
    list_parser.set_defaults(func=command_list)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
