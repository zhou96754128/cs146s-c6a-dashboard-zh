#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A 数据采集：从 EduSeed 平台拉取真实提交记录 / 挑战清单 / 评审评分。
只读。原始响应全部落盘到 C6A/raw/，供后续 diff 与复跑。
"""
import json
import os
import subprocess
import sys

BASE = "/Users/xiaowo/.cogseed-dev/userWorkSpace/检查挑战清单完成情况"
RAW = os.path.join(BASE, "C6A", "raw")
NODE = os.environ["COGSEED_NODE"]
PC = os.environ["COGSEED_PC_DIR"]


def call(op, payload):
    """调用 eduseed-student-submit 运行时，返回解析后的 JSON。"""
    r = subprocess.run(
        [NODE, os.path.join(PC, "bin", "run-skill.cjs"),
         "eduseed-student-submit", "runtime", "--", op, json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True, timeout=300,
    )
    out = r.stdout or ""
    i = out.find('{"ok"')
    if i < 0:
        raise RuntimeError("no json for %s: %s | %s" % (op, out[:400], (r.stderr or "")[:400]))
    return json.loads(out[i:])


def main():
    os.makedirs(RAW, exist_ok=True)

    # 1) 我的提交记录
    subs = call("list-my-submissions", {})
    with open(os.path.join(RAW, "submissions.json"), "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)
    rows = subs.get("submissions", [])
    print("submissions=%d" % len(rows))

    # 2) 挑战清单
    chs = call("list-challenges", {})
    with open(os.path.join(RAW, "challenges.json"), "w", encoding="utf-8") as f:
        json.dump(chs, f, ensure_ascii=False, indent=2)
    print("challenges=%d" % len(chs.get("challenges", [])))

    # 3) 每条提交的评审详情（分数 + evaluator_type + 评语长度）
    evals = []
    for s in rows:
        sid = s["submission_id"]
        try:
            e = call("get-evaluation", {"submissionId": sid})
        except Exception as exc:  # 网络/接口异常要如实记录，不伪造
            evals.append({"submission_id": sid, "error": str(exc)[:300]})
            print("EVAL-FAIL %s" % sid)
            continue
        e["_submission_id"] = sid
        evals.append(e)
        body = e.get("evaluation") or e.get("result") or {}
        print("EVAL %s score=%s type=%s" % (
            sid, body.get("score_total") or body.get("scoreTotal") or body.get("score"),
            body.get("evaluator_type")))
    with open(os.path.join(RAW, "evaluations.json"), "w", encoding="utf-8") as f:
        json.dump(evals, f, ensure_ascii=False, indent=2)

    # 4) 平台进度仪表盘
    try:
        dash = call("get-dashboard", {})
        with open(os.path.join(RAW, "dashboard.json"), "w", encoding="utf-8") as f:
            json.dump(dash, f, ensure_ascii=False, indent=2)
        print("dashboard ok")
    except Exception as exc:
        print("DASHBOARD-FAIL %s" % str(exc)[:200])

    return 0


if __name__ == "__main__":
    sys.exit(main())
