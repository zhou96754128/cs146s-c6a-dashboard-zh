#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A Excel 报表生成器（Level 2）。

由 data/submissions.json + data/summary.json 现算，不手工填表。
五个 Sheet：总览 / 按学生 / 按挑战 / 时间线 / 缺失项。

用法：python3 _tools/build_excel.py
输出：Zhouruoying_C6A_report.xlsx
"""
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

WS = "/Users/xiaowo/.cogseed-dev/userWorkSpace/检查挑战清单完成情况"
C6A = os.path.join(WS, "C6A")
OUT = os.path.join(C6A, "Zhouruoying_C6A_report.xlsx")

FONT = "PingFang SC"
H_FILL = PatternFill("solid", fgColor="1F2937")
H_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=11)
OK_FILL = PatternFill("solid", fgColor="D1FAE5")
WARN_FILL = PatternFill("solid", fgColor="FEF3C7")
BAD_FILL = PatternFill("solid", fgColor="FECACA")
GREY_FILL = PatternFill("solid", fgColor="F3F4F6")
THIN = Side(style="thin", color="D1D5DB")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
MARK = {"complete": "✅ 完整", "partial": "⚠️ 部分", "missing": "❌ 缺失"}


def load():
    with open(os.path.join(C6A, "Zhouruoying_C6A_data", "submissions.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(C6A, "Zhouruoying_C6A_data", "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    return data["records"], summary


def title_row(ws, text, ncol, sub=None):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(ncol, 6))
    c = ws.cell(row=1, column=1, value=text)
    c.font = Font(name=FONT, bold=True, size=14, color="111827")
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 26
    if sub:
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max(ncol, 6))
        c2 = ws.cell(row=2, column=1, value=sub)
        c2.font = Font(name=FONT, size=9, color="6B7280")
        return 4
    return 3


def header(ws, row, cols):
    for i, name in enumerate(cols, start=1):
        c = ws.cell(row=row, column=i, value=name)
        c.fill = H_FILL
        c.font = H_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    ws.row_dimensions[row].height = 30


def put(ws, row, values, fills=None, bold=False):
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(name=FONT, size=10, bold=bold)
        c.border = BOX
        c.alignment = Alignment(vertical="center", wrap_text=(i > 2 and isinstance(v, str) and len(str(v)) > 40))
        if fills and fills.get(i):
            c.fill = fills[i]


def widths(ws, spec):
    for i, w in enumerate(spec, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def status_fill(status):
    return OK_FILL if status == "complete" else (WARN_FILL if status == "partial" else BAD_FILL)


def cov_text(rec):
    """必交物覆盖率单元格。没拿到逐项校验结果的（未提交/历史提交无明细）如实写「—」。"""
    present = rec.get("required_present")
    total = rec.get("required_total")
    if present is None or total is None:
        return "未校验"
    return "%d/%d" % (present, total)


def sheet_overview(wb, records, summary):
    ws = wb.active
    ws.title = "总览"
    codes = [r["challenge"] for r in records]
    r0 = title_row(ws, "Elite 20 提交数据总览", len(codes) + 5,
                   "生成时间 %s ｜ 数据源：平台 list-my-submissions + list-challenges + get-evaluation + 本地文件扫描（全部现算）"
                   % summary.get("generated_at", ""))
    kpis = [
        ("学员", summary["student"]["name"] + "（" + summary["student"]["github"] + "）"),
        ("挑战总数 / 已提交", "%d / %d" % (summary["counts"]["challenges_total"], summary["counts"]["challenges_submitted"])),
        ("提交率", "%.2f%%" % (summary["counts"]["submission_rate"] * 100)),
        ("已出分", "%d 份，均分 %.2f，中位数 %.1f，最高 %d，最低 %d"
         % (summary["counts"]["evaluations_read"], summary["score"]["mean"],
            summary["score"]["median"], summary["score"]["max"], summary["score"]["min"])),
        ("本地扫描", "%d 个挑战目录 / %d 个文件"
         % (summary["counts"]["local_dirs_scanned"], summary["counts"]["files_scanned"])),
        ("数据口径", summary.get("scope_note", "单学员视角")),
    ]
    row = r0
    for k, v in kpis:
        a = ws.cell(row=row, column=1, value=k)
        a.font = Font(name=FONT, bold=True, size=10, color="374151")
        a.fill = GREY_FILL
        a.border = BOX
        b = ws.cell(row=row, column=2, value=v)
        b.font = Font(name=FONT, size=10)
        b.border = BOX
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=max(len(codes) + 2, 8))
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="学生 × 挑战 完成矩阵").font = Font(name=FONT, bold=True, size=12)
    row += 1
    header(ws, row, ["学生"] + codes + ["已提交", "完成率"])
    row += 1
    st = {r["challenge"]: r["status"] for r in records}
    marks = [MARK.get(st.get(c, "missing"), "❌ 缺失") for c in codes]
    done = sum(1 for m in marks if m.startswith("✅"))
    put(ws, row, [summary["student"]["name"]] + marks + [done, "%.1f%%" % (100.0 * done / len(codes))])
    for i, m in enumerate(marks, start=2):
        fill = OK_FILL if m.startswith("✅") else (WARN_FILL if m.startswith("⚠️") else BAD_FILL)
        ws.cell(row=row, column=i).fill = fill
        ws.cell(row=row, column=i).alignment = Alignment(horizontal="center")
    row += 2

    ws.cell(row=row, column=1, value="分数分布").font = Font(name=FONT, bold=True, size=12)
    row += 1
    header(ws, row, ["区间", "数量", "占比"])
    row += 1
    total = summary["counts"]["evaluations_read"] or 1
    for k, v in summary["score"]["buckets"].items():
        put(ws, row, [k, v, "%.1f%%" % (100.0 * v / total)])
        row += 1
    row += 1
    ws.cell(row=row, column=1, value="口径说明").font = Font(name=FONT, bold=True, size=12)
    row += 1
    for line in summary.get("caveats", []):
        c = ws.cell(row=row, column=1, value="· " + line)
        c.font = Font(name=FONT, size=9, color="4B5563")
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max(len(codes) + 2, 8))
        row += 1
    widths(ws, [22] + [11] * len(codes) + [10, 10])
    ws.freeze_panes = ws.cell(row=r0 + 9, column=2)
    return ws


def sheet_by_student(wb, records):
    ws = wb.create_sheet("按学生")
    r = title_row(ws, "按学生 · 全部提交明细", 10,
                  "状态口径：complete=必交物全齐；partial=缺部分必交物；missing=未提交")
    header(ws, r, ["学生", "挑战", "挑战标题", "提交时间", "submission_id", "状态",
                   "必交物", "得分", "本地文件数", "缺失项"])
    r += 1
    for rec in records:
        fills = {6: status_fill(rec["status"])}
        put(ws, r, [rec["student"]["name"], rec["challenge"], rec["challenge_title"],
                    (rec.get("submitted_at") or "").replace("T", " ")[:19],
                    rec.get("submission_id") or "—", MARK.get(rec["status"], rec["status"]),
                    cov_text(rec),
                    rec.get("score") if rec.get("score") is not None else "—",
                    rec.get("local_file_count", 0),
                    "、".join(rec.get("missing") or []) or "—"], fills)
        r += 1
    widths(ws, [10, 9, 34, 20, 26, 11, 8, 7, 11, 24])
    ws.freeze_panes = ws.cell(row=5, column=1)
    return ws


def sheet_by_challenge(wb, records):
    ws = wb.create_sheet("按挑战")
    r = title_row(ws, "按挑战 · 必交物逐项校验", 10,
                  "每行一个「挑战 × 必交物」，present=false 即为缺失项；没拿到逐项明细的挑战覆盖率写「未校验」")
    header(ws, r, ["挑战", "挑战标题", "截止", "必交物要求", "必交项", "是否命中", "命中文件",
                   "必交物覆盖率", "提交状态", "得分"])
    r += 1
    for rec in records:
        files = rec.get("files") or []
        if not files:
            put(ws, r, [rec["challenge"], rec["challenge_title"], "2026-12-31T23:59",
                        "—", "（该挑战必交物未知）", "—", "—", cov_text(rec),
                        MARK.get(rec["status"], rec["status"]), rec.get("score") if rec.get("score") is not None else "—"],
                {9: status_fill(rec["status"])})
            r += 1
            continue
        for f in files:
            ok = bool(f.get("present"))
            put(ws, r, [rec["challenge"], rec["challenge_title"], "2026-12-31T23:59",
                        f.get("pattern"), f.get("label"), "是" if ok else "否",
                        f.get("matched_file") or "—", cov_text(rec),
                        MARK.get(rec["status"], rec["status"]),
                        rec.get("score") if rec.get("score") is not None else "—"],
                {6: OK_FILL if ok else BAD_FILL, 9: status_fill(rec["status"])})
            r += 1
    widths(ws, [9, 30, 18, 22, 14, 9, 40, 13, 11, 7])
    ws.freeze_panes = ws.cell(row=5, column=1)
    return ws


def sheet_timeline(wb, records):
    ws = wb.create_sheet("时间线")
    r = title_row(ws, "时间线 · 按提交时间排序", 8, "仅含真实提交记录；未提交挑战不进入时间线")
    header(ws, r, ["序号", "提交时间(UTC)", "挑战", "标题", "间隔(天)", "得分", "状态", "submission_id"])
    r += 1
    subs = [x for x in records if x.get("submitted_at")]
    subs.sort(key=lambda x: x["submitted_at"])
    prev = None
    from datetime import datetime
    for i, rec in enumerate(subs, start=1):
        t = datetime.strptime(rec["submitted_at"][:19], "%Y-%m-%dT%H:%M:%S")
        gap = "—" if prev is None else "%.2f" % ((t - prev).total_seconds() / 86400.0)
        prev = t
        put(ws, r, [i, rec["submitted_at"].replace("T", " ")[:19], rec["challenge"],
                    rec["challenge_title"], gap, rec.get("score", "—"),
                    MARK.get(rec["status"], rec["status"]), rec.get("submission_id", "—")],
            {7: status_fill(rec["status"])})
        r += 1
    widths(ws, [6, 20, 9, 34, 10, 7, 11, 26])
    ws.freeze_panes = ws.cell(row=5, column=1)
    return ws


def sheet_missing(wb, records):
    ws = wb.create_sheet("缺失项")
    r = title_row(ws, "缺失项 · 需要补的条目（标红）", 7,
                  "规则：必交物未命中 / 平台未提交 / 本地无目录，三类都算缺口")
    header(ws, r, ["挑战", "标题", "缺口类型", "缺口说明", "严重度", "当前状态", "建议动作"])
    r += 1
    sev_fill = {"高": BAD_FILL, "中": WARN_FILL, "低": GREY_FILL}
    for rec in records:
        gaps = []
        if rec["status"] == "missing":
            gaps.append(("平台未提交", "该挑战截至抽数时间无提交记录", "高", "开工并提交"))
        for f in (rec.get("files") or []):
            if not f.get("present"):
                gaps.append(("必交物缺失", "未命中 %s（%s）" % (f.get("pattern"), f.get("label")), "高",
                             "补齐 " + str(f.get("label"))))
        if rec.get("local_scan") == "absent":
            gaps.append(("本地无目录", "工作区没有 %s/ 目录，无法做文件级核验" % rec["challenge"], "中",
                         "补建目录或从平台重新拉取交付物"))
        for kind, desc, sev, act in gaps:
            put(ws, r, [rec["challenge"], rec["challenge_title"], kind, desc, sev,
                        MARK.get(rec["status"], rec["status"]), act],
                {5: sev_fill[sev]})
            r += 1
    if r == 5:
        put(ws, r, ["—", "—", "无", "全部必交物命中", "低", "✅", "—"])
    widths(ws, [9, 30, 14, 46, 8, 11, 30])
    ws.freeze_panes = ws.cell(row=5, column=1)
    return ws


def main():
    records, summary = load()
    wb = Workbook()
    sheet_overview(wb, records, summary)
    sheet_by_student(wb, records)
    sheet_by_challenge(wb, records)
    sheet_timeline(wb, records)
    sheet_missing(wb, records)
    wb.properties.creator = "Zhouruoying C6A pipeline"
    wb.properties.title = "Elite 20 提交数据报表"
    wb.save(OUT)
    print("xlsx=%s bytes=%d sheets=%s" % (os.path.basename(OUT), os.path.getsize(OUT),
                                          ",".join(wb.sheetnames)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
