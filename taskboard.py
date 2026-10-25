#!/usr/bin/env python3
"""taskboard —— 用一个纯文本文件当看板，按状态整理任务。

看板文件就是一个每行一条任务的文本文件，可以用 # 写注释。
每行格式:
    [状态] 任务描述 @负责人 #标签

状态用中文或英文都认: todo / doing / done / 待办 / 进行中 / 完成

用法:
    python taskboard.py board.txt
    python taskboard.py board.txt --add "写文档 @me #doc"
    python taskboard.py board.txt --move 3 doing
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

STATUS_ALIASES = {
    "todo": "todo", "待办": "todo", "未开始": "todo",
    "doing": "doing", "进行中": "doing", "在做": "doing",
    "done": "done", "完成": "done", "已完成": "done",
    "blocked": "blocked", "阻塞": "blocked",
}

STATUS_ORDER = ["todo", "doing", "blocked", "done"]
LINE_RE = re.compile(r"^\s*(?:\[([^\]]*)\])?\s*(.+?)\s*$")
MENTION_RE = re.compile(r"(?:^|\s)@([\w\-.]+)")
TAG_RE = re.compile(r"(?:^|\s)#([\w\-.]+)")


@dataclass
class Task:
    line_no: int
    status: str
    text: str
    owner: str
    tags: list[str]

    def render(self) -> str:
        meta = []
        if self.owner:
            meta.append(f"@{self.owner}")
        if self.tags:
            meta.append(" ".join(f"#{t}" for t in self.tags))
        suffix = "  " + " ".join(meta) if meta else ""
        return f"[{self.status}] {self.text}{suffix}"


def parse_line(line_no: int, raw: str) -> Task | None:
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = LINE_RE.match(stripped)
    if not match:
        return None
    raw_status = (match.group(1) or "").strip().lower()
    body = match.group(2).strip()
    status = STATUS_ALIASES.get(raw_status, "todo")
    owner_match = MENTION_RE.search(body)
    owner = owner_match.group(1) if owner_match else ""
    tags = TAG_RE.findall(body)
    body = MENTION_RE.sub("", body)
    body = TAG_RE.sub("", body).strip()
    return Task(line_no=line_no, status=status, text=body, owner=owner, tags=tags)


def load(path: Path) -> list[Task]:
    tasks: list[Task] = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        task = parse_line(index, raw)
        if task:
            tasks.append(task)
    return tasks


def render(tasks: list[Task]) -> str:
    groups: dict[str, list[Task]] = {status: [] for status in STATUS_ORDER}
    for task in tasks:
        groups.setdefault(task.status, []).append(task)
    lines: list[str] = []
    for status in STATUS_ORDER:
        bucket = groups.get(status) or []
        if not bucket:
            continue
        lines.append(f"{status.upper()}  ({len(bucket)})")
        for task in bucket:
            meta = []
            if task.owner:
                meta.append(f"@{task.owner}")
            if task.tags:
                meta.append(" ".join(f"#{t}" for t in task.tags))
            suffix = ("  " + " ".join(meta)) if meta else ""
            lines.append(f"  #{task.line_no:<4} {task.text}{suffix}")
        lines.append("")
    lines.append(f"共 {len(tasks)} 个任务。")
    return "\n".join(lines)


def cmd_show(args) -> int:
    path = Path(args.board)
    if not path.exists():
        print(f"taskboard: 找不到看板文件 {path}", file=sys.stderr)
        return 2
    tasks = load(path)
    if args.json:
        import json
        print(json.dumps([{
            "line": t.line_no, "status": t.status, "text": t.text,
            "owner": t.owner, "tags": t.tags,
        } for t in tasks], ensure_ascii=False, indent=2))
    else:
        print(render(tasks))
    return 0


def cmd_add(args) -> int:
    path = Path(args.board)
    if not path.exists():
        print(f"taskboard: 找不到看板文件 {path}", file=sys.stderr)
        return 2
    status = STATUS_ALIASES.get(args.status.lower(), "todo")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{status}] {args.text}\n")
    print(f"已追加到 {path}（状态 {status}）。")
    return 0


def cmd_move(args) -> int:
    path = Path(args.board)
    if not path.exists():
        print(f"taskboard: 找不到看板文件 {path}", file=sys.stderr)
        return 2
    status = STATUS_ALIASES.get(args.status.lower())
    if status is None:
        print(f"taskboard: 未知状态 {args.status}", file=sys.stderr)
        return 2
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        index = int(args.task) - 1
    except ValueError:
        print("taskboard: 任务编号必须是数字", file=sys.stderr)
        return 2
    if not (0 <= index < len(lines)):
        print(f"taskboard: 行号 {args.task} 超出范围（文件共 {len(lines)} 行）", file=sys.stderr)
        return 2
    original = lines[index]
    match = LINE_RE.match(original.strip())
    if not match:
        print("taskboard: 该行不是任务", file=sys.stderr)
        return 2
    body = match.group(2).strip()
    lines[index] = f"[{status}] {body}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"第 {args.task} 行已改为 [{status}]。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="taskboard",
        description="用一个纯文本文件当看板，按状态整理任务",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show", help="按状态展示看板")
    s.add_argument("board")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    a = sub.add_parser("add", help="追加一条任务")
    a.add_argument("board")
    a.add_argument("text")
    a.add_argument("--status", default="todo")
    a.set_defaults(fn=cmd_add)

    m = sub.add_parser("move", help="修改某条任务的状态")
    m.add_argument("board")
    m.add_argument("task", help="任务在文件中的行号")
    m.add_argument("status")
    m.set_defaults(fn=cmd_move)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
