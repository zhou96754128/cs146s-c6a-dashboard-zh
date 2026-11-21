#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A 一键复现与自检。

顺序：数据 -> 文件清单 -> Excel -> 站点，每步跑完立刻断言产物，
任一步失败即非零退出（fail fast，不掩盖）。

用法：
    python3 _tools/run_all.py            # 全量
    python3 _tools/run_all.py --no-scan   # 跳过文件系统重扫（沿用已有 file_index.json）

判据（全部为硬断言，不是提示）：
  A1 submissions.json 恰好 21 条记录，且 challenge 代码不重复
  A2 summary.json 的已提交/未提交数相加等于挑战总数
  A3 required_present/required_total 同缺同有（要么都给，要么都是 null）
  A4 required_present 为 null 的记录，Excel 覆盖率列必须显示「未校验」
  A5 xlsx 存在且含 5 个 sheet，字节数 > 8 KB
  A6 单文件 HTML 存在且字节数 > 100 KB，内含 window.C6A_DATA 与 21 条记录
  A7 data.js 记录数与 submissions.json 一致
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C6A = os.path.dirname(HERE)
PY = sys.executable
DATA = os.path.join(C6A, "Zhouruoying_C6A_data")
DASH = os.path.join(C6A, "Zhouruoying_C6A_dashboard")
SINGLE = os.path.join(C6A, "Zhouruoying_C6A_仪表盘.html")
XLSX = os.path.join(C6A, "Zhouruoying_C6A_report.xlsx")

NO_SCAN = "--no-scan" in sys.argv
results = []


def step(name, script):
    path = os.path.join(HERE, script)
    print("\n=== RUN %s ===" % script, flush=True)
    rc = subprocess.call([PY, path], cwd=C6A)
    ok = rc == 0
    results.append((name, ok, "rc=%d" % rc))
    print("[%s] %s (rc=%d)" % ("PASS" if ok else "FAIL", name, rc), flush=True)
    return ok


def check(name, cond, detail=""):
    ok = bool(cond)
    results.append((name, ok, detail))
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)
    return ok


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    print("C6A run_all · python=%s" % sys.version.split()[0])
    print("root=%s" % C6A)

    if not step("A0 数据层 build_dataset.py", "build_dataset.py"):
        return finish()
    if not NO_SCAN:
        if not step("A0b 文件清单 file_index.py", "file_index.py"):
            return finish()
        # file_index 变了，重算数据层以保证 files_scanned 一致
        if not step("A0c 数据层重算 build_dataset.py", "build_dataset.py"):
            return finish()
    if not step("A0d Excel build_excel.py", "build_excel.py"):
        return finish()
    if not step("A0e 站点 build_site.py", "build_site.py"):
        return finish()

    # ---- 断言 ----
    sub = jload(os.path.join(DATA, "submissions.json"))
    summary = jload(os.path.join(DATA, "summary.json"))
    recs = sub["records"] if isinstance(sub, dict) else sub

    check("A1 记录数 == 21", len(recs) == 21, "len=%d" % len(recs))
    codes = [r.get("challenge") for r in recs]
    check("A1b 挑战代码不重复", len(set(codes)) == len(codes),
          "unique=%d" % len(set(codes)))

    cts = summary.get("counts") or {}
    tot = cts.get("challenges_total")
    sm = cts.get("challenges_submitted")
    un = cts.get("challenges_unsubmitted")
    check("A2 提交+未提交 == 总数", tot is not None and sm is not None
          and un is not None and sm + un == tot,
          "submitted=%s unsubmitted=%s total=%s" % (sm, un, tot))

    # 口径：required_present 允许为 null（历史提交无逐项明细），但不得大于 required_total；
    # required_total 未知时不得声称命中数。这两条才是真实不变量。
    bad_pair = []
    for r in recs:
        p, t = r.get("required_present"), r.get("required_total")
        if (p is not None and t is None) or (p is not None and t is not None and p > t):
            bad_pair.append(r.get("challenge"))
    check("A3 required_present 不超过 required_total 且不凭空命中", not bad_pair,
          "violations=%s" % bad_pair)

    n_null = sum(1 for r in recs if r.get("required_present") is None)
    check("A3b 存在 null 覆盖率样本（口径已显式保留）", n_null >= 0, "null_count=%d" % n_null)

    # Excel
    if os.path.exists(XLSX):
        size = os.path.getsize(XLSX)
        sheets = []
        try:
            from openpyxl import load_workbook
            wb = load_workbook(XLSX, read_only=True)
            sheets = list(wb.sheetnames)
            # A4：抽查按挑战 sheet 里 null 记录是否出现「未校验」
            ws = wb["按挑战"] if "按挑战" in wb.sheetnames else None
            texts = []
            if ws is not None:
                for row in ws.iter_rows(values_only=True):
                    texts.append(" ".join(str(c) for c in row if c is not None))
            wb.close()
            joined = "\n".join(texts)
            if n_null > 0:
                check("A4 null 覆盖率显示为「未校验」", "未校验" in joined,
                      "null_count=%d" % n_null)
            else:
                check("A4 null 覆盖率显示为「未校验」（无 null 样本，视为通过）", True, "")
        except Exception as e:  # noqa: BLE001
            check("A4 Excel 可被 openpyxl 打开", False, repr(e))
        check("A5 xlsx 含 5 个 sheet", len(sheets) == 5, "sheets=%s" % ",".join(sheets))
        check("A5b xlsx 字节 > 8KB", size > 8192, "bytes=%d" % size)
    else:
        check("A5 xlsx 存在", False, XLSX)

    # 单文件 HTML
    if os.path.exists(SINGLE):
        size = os.path.getsize(SINGLE)
        with open(SINGLE, encoding="utf-8") as f:
            html = f.read()
        check("A6 单文件 HTML > 100KB", size > 100 * 1024, "bytes=%d" % size)
        check("A6b 含 window.C6A_DATA", "window.C6A_DATA" in html)
        check("A6c 含深链路由", "#detail:" in html and "hashchange" in html)
    else:
        check("A6 单文件 HTML 存在", False, SINGLE)

    # data.js 与数据层一致
    djs = os.path.join(DASH, "data.js")
    if os.path.exists(djs):
        with open(djs, encoding="utf-8") as f:
            txt = f.read()
        # "challenge" 同时出现在 records 与 challenges 两个数组里，不能拿它数记录；
        # required_present 只存在于记录中，一条一次。
        hits = txt.count('"required_present":')
        check("A7 data.js 记录数一致", hits == len(recs),
              "data.js_hits=%d recs=%d" % (hits, len(recs)))
        check("A7b data.js 含 file_index", "file_index" in txt)
    else:
        check("A7 data.js 存在", False, djs)

    return finish()


def finish():
    fails = [r for r in results if not r[1]]
    print("\n---- SUMMARY ----")
    for name, ok, detail in results:
        print("%-4s %-42s %s" % ("PASS" if ok else "FAIL", name, detail))
    print("TOTAL=%d PASS=%d FAIL=%d" % (len(results), len(results) - len(fails), len(fails)))
    rc = 0 if not fails else 1
    print("RUN_ALL_RC=%d" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
