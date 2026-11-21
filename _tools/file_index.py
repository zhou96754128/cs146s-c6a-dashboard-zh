#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A 文件索引器：把本地挑战目录扫成可点击的文件清单。

仅做只读扫描，不做任何推断：
  - 只认工作区根目录下形如 C<数字><可选大写字母> 的挑战目录
  - 跳过 .git / __pycache__ / node_modules / .DS_Store
  - 每个挑战记录相对路径、字节数、类型，供仪表盘做「点击文件名打开」的链接

用法：python3 _tools/file_index.py
输出：data/file_index.json
"""
import json
import os
import re
import sys
import time

WS = "/Users/xiaowo/.cogseed-dev/userWorkSpace/检查挑战清单完成情况"
OUT = os.path.join(WS, "C6A", "Zhouruoying_C6A_data", "file_index.json")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".ipynb_checkpoints", ".venv"}
SKIP_FILES = {".DS_Store"}
DIR_RE = re.compile(r"^C\d+[A-Z]?$")
MAX_FILES = 600


def walk(root):
    """返回 (文件计数, 文件列表)。文件列表最多 MAX_FILES 条，超出记 truncated。"""
    n = 0
    items = []
    for cur, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name in SKIP_FILES:
                continue
            full = os.path.join(cur, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            n += 1
            if len(items) < MAX_FILES:
                items.append({
                    "rel": os.path.relpath(full, WS),
                    "name": name,
                    "bytes": size,
                })
    return n, items


def main():
    challenges = {}
    total = 0
    if not os.path.isdir(WS):
        print("WORKSPACE_MISSING", WS, file=sys.stderr)
        return 2
    for name in sorted(os.listdir(WS)):
        full = os.path.join(WS, name)
        if not os.path.isdir(full) or not DIR_RE.match(name):
            continue
        n, items = walk(full)
        total += n
        challenges[name] = {
            "dir": name,
            "exists": True,
            "file_count": n,
            "listed": len(items),
            "truncated": n > len(items),
            "files": items,
        }
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "workspace_root": WS,
        "challenges_scanned": len(challenges),
        "files_total": total,
        "max_files_per_challenge": MAX_FILES,
        "challenges": challenges,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("scanned_dirs=%d files_total=%d bytes=%d" % (
        len(challenges), total, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
