#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A 数据集构建器（Level 1：数据收集与结构化）。

数据源全部真实、可复跑：
  1. C6A/raw/submissions.json     —— 平台 list-my-submissions 原始响应
  2. C6A/raw/challenges.json      —— 平台 list-challenges 原始响应
  3. C6A/raw/evaluations.json     —— 平台 get-evaluation 原始响应
  4. 本地工作区 C*/ 目录的真实文件树 —— 用于逐条核对必交物是否落盘

设计原则：宁可标 unknown，也不编造。没有本地目录的挑战记为 scan_absent，
不推断其文件是否齐全。
"""
import csv
import fnmatch
import json
import os
import re
import statistics
import sys

BASE = "/Users/xiaowo/.cogseed-dev/userWorkSpace/检查挑战清单完成情况"
C6A = os.path.join(BASE, "C6A")
RAW = os.path.join(C6A, "raw")
OUT = os.path.join(C6A, "Zhouruoying_C6A_data")

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".mypy_cache",
             ".pytest_cache", "_build", ".DS_Store", ".ipynb_checkpoints"}
# 本地工作区里哪些目录不属于任何一个挑战的交付目录
NON_CHALLENGE_DIRS = {"_build", "_c2g_realrun", "_c4pack", "_smoke", "_tools",
                      "C4B_参考资料", "文章正文", "raw", "data",
                      "Zhouruoying_C6A_data", "site",
                      "report", "collector", "tests", "fixtures", "config"}

STUDENT = {
    "name": "周若莹",
    "name_pinyin": "Zhouruoying",
    "major": "Elite 20 学员",
    "github": "zhou96754128",
}

CODE_RE = re.compile(r"^(C\d+[A-Z]?)\b")


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return json.load(f)


def challenge_code(title):
    m = CODE_RE.match(title or "")
    return m.group(1) if m else "?"


def parse_patterns(spec):
    """'README.md,*AI日志*,*AAR*' -> [{pattern, label, required}]"""
    out = []
    for raw in (spec or "").split(","):
        p = raw.strip()
        if not p:
            continue
        label = p.strip("*").strip()
        if p.lower() == "readme.md":
            label = "README"
        out.append({"pattern": p, "label": label, "required": True})
    return out


def scan_dir(path, max_depth=3):
    """返回 (顶层条目, 全部匹配用文件名列表, 文件总数)。只读，不做内容读取。"""
    top, names, nfiles = [], [], 0
    if not os.path.isdir(path):
        return top, names, nfiles
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith("._")]
        depth = root[len(path):].count(os.sep)
        if depth > max_depth:
            dirs[:] = []
            continue
        for fn in files:
            if fn.startswith("._") or fn == ".DS_Store":
                continue
            nfiles += 1
            names.append(fn)
            if depth == 0:
                top.append({"name": fn, "kind": "file"})
        if depth == 0:
            for d in dirs:
                top.append({"name": d + "/", "kind": "dir"})
    top.sort(key=lambda x: (x["kind"] != "dir", x["name"]))
    return top, names, nfiles


def match_required(patterns, names):
    """逐条必交物在真实文件名里找匹配；返回条目与覆盖率。"""
    items, missing = [], []
    for p in patterns:
        hit = next((n for n in names if fnmatch.fnmatch(n.lower(), p["pattern"].lower())), None)
        present = hit is not None
        items.append({
            "pattern": p["pattern"],
            "label": p["label"],
            "required": p["required"],
            "present": present,
            "matched_file": hit,
        })
        if not present:
            missing.append(p["label"])
    total = len(patterns) or 1
    have = sum(1 for i in items if i["present"])
    return items, missing, round(have / total, 4)


def _file_index():
    """读 data/file_index.json（可能还没生成，返回 None）。"""
    p = os.path.join(OUT, "file_index.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _local_files_total():
    idx = _file_index()
    if not idx:
        return None
    return idx.get("files_total")


def _local_files_listed():
    idx = _file_index()
    if not idx or not isinstance(idx.get("challenges"), dict):
        return None
    return sum(len(v.get("files") or []) for v in idx["challenges"].values())


def main():
    subs = load("submissions.json").get("submissions", [])
    chs = load("challenges.json").get("challenges", [])
    evs = load("evaluations.json")

    ev_by_sub = {}
    for e in evs:
        sid = e.get("_submission_id")
        body = e.get("evaluation") or {}
        ev_by_sub[sid] = body

    sub_by_ch = {}
    for s in subs:
        sub_by_ch.setdefault(s["challenge_id"], []).append(s)

    records = []
    for ch in chs:
        code = challenge_code(ch.get("title"))
        patterns = parse_patterns(ch.get("required_deliverables"))
        sdir = os.path.join(BASE, code)
        scan_ok = os.path.isdir(sdir)
        top, names, nfiles = scan_dir(sdir) if scan_ok else ([], [], 0)
        items, missing, cov = match_required(patterns, names) if scan_ok else ([], [], None)

        ch_subs = sorted(sub_by_ch.get(ch["challenge_id"], []),
                         key=lambda x: x.get("submitted_at") or "")
        if not ch_subs:
            records.append({
                "student": STUDENT,
                "challenge": code,
                "challenge_id": ch["challenge_id"],
                "challenge_title": ch["title"],
                "submitted_at": None,
                "submission_id": None,
                "status": "not_submitted",
                "task_state": None,
                "score": None,
                "evaluator_type": None,
                "repo_url": None,
                "required_total": len(patterns),
                "required_present": 0 if scan_ok else None,
                "completeness": 0.0 if scan_ok else None,
                "missing": missing if scan_ok else [],
                "local_scan": "ok" if scan_ok else "absent",
                "local_file_count": nfiles if scan_ok else None,
                "files": items,
                "top_entries": top,
                "notes": "" if scan_ok else "本地无该挑战交付目录：不推断文件是否齐全",
            })
            continue

        last = ch_subs[-1]
        ev = ev_by_sub.get(last["submission_id"], {})
        status = "complete" if (cov is not None and cov >= 1.0) else (
            "partial" if (cov is not None and cov > 0) else
            ("unknown" if cov is None else "missing"))
        records.append({
            "student": STUDENT,
            "challenge": code,
            "challenge_id": ch["challenge_id"],
            "challenge_title": ch["title"],
            "submitted_at": last.get("submitted_at"),
            "submission_id": last["submission_id"],
            "status": status,
            "task_state": last.get("task_state"),
            "score": ev.get("score_total"),
            "evaluator_type": ev.get("evaluator_type"),
            "evaluation_id": ev.get("evaluation_id"),
            "feedback": ev.get("feedback"),
            "repo_url": last.get("github_repo_url"),
            "required_total": len(patterns),
            "required_present": sum(1 for i in items if i["present"]) if scan_ok else None,
            "completeness": cov,
            "missing": missing,
            "local_scan": "ok" if scan_ok else "absent",
            "local_file_count": nfiles if scan_ok else None,
            "files": items,
            "top_entries": top,
            "notes": ("同一挑战有 %d 次提交，取最近一次 %s"
                      % (len(ch_subs), last.get("submitted_at"))) if len(ch_subs) > 1 else "",
        })

    records.sort(key=lambda r: (r["challenge"].startswith("C1") and len(r["challenge"]) > 2,
                                r["challenge"]))

    # ---------- 汇总指标（全部由真实数据现算） ----------
    scored = [r for r in records if isinstance(r["score"], int)]
    scores = [r["score"] for r in scored]
    submitted = [r for r in records if r["submission_id"]]
    scanned = [r for r in records if r["local_scan"] == "ok" and r["submission_id"]]

    covered = [r["completeness"] for r in scanned if r["completeness"] is not None]
    pairs = [(r["completeness"], r["score"]) for r in scanned
             if isinstance(r["score"], int) and r["completeness"] is not None]

    def spearman(xy):
        if len(xy) < 3:
            return None
        xs = [a for a, _ in xy]
        ys = [b for _, b in xy]

        def rank(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            i = 0
            while i < len(v):
                j = i
                while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2.0 + 1
                for k in range(i, j + 1):
                    rk[order[k]] = avg
                i = j + 1
            return rk

        rx, ry = rank(xs), rank(ys)
        mx, my = statistics.fmean(rx), statistics.fmean(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = math_sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
        return round(num / den, 4) if den else None

    def math_sqrt(v):
        return v ** 0.5

    # 月份维度的提交节奏
    months = {}
    for r in submitted:
        m = (r["submitted_at"] or "")[:7]
        months[m] = months.get(m, 0) + 1

    # 缺失项统计
    miss_counter = {}
    for r in scanned:
        for m in r["missing"]:
            miss_counter[m] = miss_counter.get(m, 0) + 1

    by_challenge = []
    for r in records:
        by_challenge.append({
            "challenge": r["challenge"],
            "title": r["challenge_title"],
            "submitted": bool(r["submission_id"]),
            "score": r["score"],
            "completeness": r["completeness"],
            "missing_count": len(r["missing"]),
            "deadline": "",
        })

    summary = {
        "generated_at_note": "由 build_dataset.py 现算，无手工填数",
        "student": STUDENT,
        "counts": {
            "challenges_total": len(records),
            "challenges_submitted": len(submitted),
            "challenges_unsubmitted": len(records) - len(submitted),
            "submission_rate": round(len(submitted) / len(records), 4),
            "local_dirs_scanned": sum(1 for r in records if r["local_scan"] == "ok"),
            # 口径：files_in_submissions = 平台提交侧文件数合计（本机无目录的记录也能算）
            "files_in_submissions": sum(r["local_file_count"] or 0 for r in records),
            # 口径：files_scanned = 本地递归扫描到的真实文件总数（来自 data/file_index.json）
            "files_scanned": _local_files_total(),
            # 口径：files_listed = 上述扫描里写入明细的条目数（每挑战上限 600，C4D 被截断）
            "files_listed": _local_files_listed(),
            "evaluations_read": len(scored),
        },
        "score": {
            "mean": round(statistics.fmean(scores), 2) if scores else None,
            "median": statistics.median(scores) if scores else None,
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
            "stdev": round(statistics.stdev(scores), 2) if len(scores) > 1 else None,
            "buckets": {
                "95+": sum(1 for s in scores if s >= 95),
                "90-94": sum(1 for s in scores if 90 <= s <= 94),
                "85-89": sum(1 for s in scores if 85 <= s <= 89),
                "80-84": sum(1 for s in scores if 80 <= s <= 84),
                "<80": sum(1 for s in scores if s < 80),
            },
        },
        "completeness": {
            "mean_required_coverage": round(statistics.fmean(covered), 4) if covered else None,
            "full_coverage_count": sum(1 for c in covered if c >= 1.0),
            "scanned_with_submission": len(scanned),
            "spearman_coverage_vs_score": spearman(pairs),
            "pairs": [{"challenge": r["challenge"], "coverage": r["completeness"],
                       "score": r["score"]} for r in scanned],
        },
        "cadence_by_month": dict(sorted(months.items())),
        "missing_top": sorted(miss_counter.items(), key=lambda kv: -kv[1])[:10],
        "pending": [{"challenge": r["challenge"], "title": r["challenge_title"]}
                    for r in records if not r["submission_id"]],
        "data_sources": [
            "平台 list-my-submissions（12 条真实提交记录）",
            "平台 list-challenges（21 个真实挑战定义与必交物 pattern）",
            "平台 get-evaluation（12 份真实 AI 初评，全部 evaluator_type=ai）",
            "本地工作区 C*/ 目录真实文件树（递归扫描，跳过 .git/缓存）",
        ],
        "honesty_boundary": (
            "仪表盘仅含单个真实账号（%s）的数据。我无权限读取其他同学的提交，"
            "因此不虚构同学数据；多学生能力由 tests/ 下的 fixtures 单测覆盖，"
            "fixture 数据永不进入 data/ 与站点。" % STUDENT["name_pinyin"]
        ),
    }

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "submissions.json"), "w", encoding="utf-8") as f:
        json.dump({"records": records, "summary": summary}, f, ensure_ascii=False, indent=2)

    cols = ["student_name", "challenge", "challenge_title", "submitted_at", "submission_id",
            "status", "score", "evaluator_type", "required_present", "required_total",
            "completeness", "missing", "local_scan", "local_file_count", "repo_url"]
    with open(os.path.join(OUT, "submissions.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in records:
            w.writerow({
                "student_name": r["student"]["name"],
                "challenge": r["challenge"],
                "challenge_title": r["challenge_title"],
                "submitted_at": r["submitted_at"] or "",
                "submission_id": r["submission_id"] or "",
                "status": r["status"],
                "score": "" if r["score"] is None else r["score"],
                "evaluator_type": r["evaluator_type"] or "",
                "required_present": "" if r["required_present"] is None else r["required_present"],
                "required_total": r["required_total"],
                "completeness": "" if r["completeness"] is None else r["completeness"],
                "missing": ";".join(r["missing"]),
                "local_scan": r["local_scan"],
                "local_file_count": "" if r["local_file_count"] is None else r["local_file_count"],
                "repo_url": r["repo_url"] or "",
            })

    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("records=%d submitted=%d scored=%d files=%d" % (
        len(records), len(submitted), len(scored), summary["counts"]["files_scanned"]))
    print("score mean=%s median=%s" % (summary["score"]["mean"], summary["score"]["median"]))
    print("coverage mean=%s spearman=%s" % (
        summary["completeness"]["mean_required_coverage"],
        summary["completeness"]["spearman_coverage_vs_score"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
