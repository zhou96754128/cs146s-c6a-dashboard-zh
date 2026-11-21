#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C6A 仪表盘打包器。

把 data/*.json + raw/challenges.json 汇成 data.js，再把
index.html + style.css + app.*.js 内联成一份可离线打开的单文件仪表盘。

用法：python3 _tools/build_site.py
输出：Zhouruoying_C6A_dashboard/data.js
      Zhouruoying_C6A_仪表盘.html        （单文件版，交这个）
"""
import hashlib
import json
import os
import sys

WS = "/Users/xiaowo/.cogseed-dev/userWorkSpace/检查挑战清单完成情况"
C6A = os.path.join(WS, "C6A")
SITE = os.path.join(C6A, "Zhouruoying_C6A_dashboard")
SINGLE = os.path.join(C6A, "Zhouruoying_C6A_仪表盘.html")

JS_ORDER = ["data.js", "app.core.js", "app.views.js", "app.extra.js"]


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def norm_file_index(raw):
    """把 file_index.json 归一成 {code: {count, bytes, files:[{path,size,ext}]}}。
    兼容两种形状：顶层直接是 code->obj，或包在 challenges 键里。"""
    src = raw.get("challenges") if isinstance(raw, dict) and "challenges" in raw else raw
    out = {}
    if isinstance(src, dict):
        items = src.items()
    else:  # list 形状
        items = [(x.get("challenge") or x.get("code"), x) for x in (src or [])]
    for code, obj in items:
        if not code:
            continue
        files = obj.get("files") or []
        norm = []
        for f in files:
            if isinstance(f, str):
                norm.append({"path": f, "size": None, "ext": os.path.splitext(f)[1].lower()})
            else:
                rel = f.get("path") or f.get("rel") or f.get("name") or ""
                norm.append({
                    "path": rel,
                    "size": f.get("size") if f.get("size") is not None else f.get("bytes"),
                    "ext": f.get("ext") or os.path.splitext(rel)[1].lower(),
                })
        out[code] = {
            "count": obj.get("count", len(norm)),
            "bytes": obj.get("bytes") or obj.get("bytes_total"),
            "files": norm,
        }
    return out


def build_data():
    sub = jload(os.path.join(C6A, "Zhouruoying_C6A_data", "submissions.json"))
    summary = jload(os.path.join(C6A, "Zhouruoying_C6A_data", "summary.json"))
    fidx = norm_file_index(jload(os.path.join(C6A, "Zhouruoying_C6A_data", "file_index.json")))
    raw_ch = jload(os.path.join(C6A, "raw", "challenges.json"))
    catalog = {x["challenge_id"]: x for x in raw_ch.get("challenges", [])}

    challenges = []
    for rec in sub["records"]:
        meta = catalog.get(rec.get("challenge_id")) or {}
        challenges.append({
            "code": rec["challenge"],
            "challenge_id": rec.get("challenge_id"),
            "title": rec.get("challenge_title") or meta.get("title"),
            "deadline": meta.get("deadline") or "2026-12-31T23:59",
            "required": meta.get("required_deliverables") or "",
            "status": rec.get("status"),
            "score": rec.get("score"),
        })

    data = {
        "generated_at": summary.get("generated_at") or fidx_generated(),
        "workspace_root": os.path.join(WS, "").rstrip("/"),
        "student": summary.get("student") or {},
        "summary": summary,
        "records": sub["records"],
        "challenges": challenges,
        "file_index": fidx,
    }
    return data


def fidx_generated():
    try:
        return jload(os.path.join(C6A, "Zhouruoying_C6A_data", "file_index.json")).get("generated_at")
    except Exception:
        return None


def main():
    data = build_data()
    js = "/* 由 _tools/build_site.py 自动生成，勿手改 */\nwindow.C6A_DATA = " + \
         json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
        f.write(js)

    with open(os.path.join(SITE, "index.html"), encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(SITE, "style.css"), encoding="utf-8") as f:
        css = f.read()

    html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + css + "\n</style>")
    for name in JS_ORDER:
        with open(os.path.join(SITE, name), encoding="utf-8") as f:
            body = f.read()
        html = html.replace('<script src="%s"></script>' % name, "<script>\n" + body + "\n</script>")
    html = html.replace("<title>", "<!-- 单文件版：数据、样式、脚本全部内联，双击即可离线打开 -->\n<title>")

    with open(SINGLE, "w", encoding="utf-8") as f:
        f.write(html)

    b = open(SINGLE, "rb").read()
    print("data.js  bytes=%d" % os.path.getsize(os.path.join(SITE, "data.js")))
    print("single   bytes=%d sha256=%s" % (len(b), hashlib.sha256(b).hexdigest()[:16]))
    print("records=%d challenges=%d file_index=%d" % (len(data["records"]), len(data["challenges"]),
                                                      len(data["file_index"])))
    assert len(data["records"]) == 21, "记录数应为 21"
    assert "window.C6A_DATA" in html and "<style>" in html
    assert 'src="app.core.js"' not in html, "内联失败：仍有外链脚本"
    return 0


if __name__ == "__main__":
    sys.exit(main())
