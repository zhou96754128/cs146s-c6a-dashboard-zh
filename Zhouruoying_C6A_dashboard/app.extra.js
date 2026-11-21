/* C6A 仪表盘 — 图表 + 时间线 / 缺失项 + 全局桥接 */
(function () {
  "use strict";
  var V = window.C6A_VIEWS || {};

  window.C6A_open = function (code) {
    var found = (window.C6A_DATA.records || []).filter(function (r) { return r.challenge === code; })[0];
    if (found) window.C6A.openDrawer(window.C6A.recordDetail(found));
  };

  /* ---------- 图表 ---------- */
  var CH = {};

  CH.buckets = function (b) {
    var keys = ["95+", "90-94", "85-89", "80-84", "<80"];
    var max = 1;
    keys.forEach(function (k) { max = Math.max(max, b[k] || 0); });
    var total = keys.reduce(function (s, k) { return s + (b[k] || 0); }, 0) || 1;
    var colors = ["#059669", "#10b981", "#6366f1", "#f59e0b", "#ef4444"];
    return '<div style="display:flex;flex-direction:column;gap:7px">' + keys.map(function (k, i) {
      var v = b[k] || 0;
      return '<div style="display:flex;align-items:center;gap:9px;font-size:12px">' +
        '<span style="width:52px;color:#6b7280;font-variant-numeric:tabular-nums">' + k + "</span>" +
        '<span style="flex:1;background:#eef0f6;border-radius:999px;height:14px;overflow:hidden">' +
        '<i style="display:block;height:100%;width:' + (100 * v / max) + "%;background:" + colors[i] + ';border-radius:999px"></i></span>' +
        '<b style="width:34px;text-align:right;font-variant-numeric:tabular-nums">' + v + "</b>" +
        '<span style="width:44px;text-align:right;color:#9ca3af;font-size:11px">' + (100 * v / total).toFixed(1) + "%</span></div>";
    }).join("") + "</div>";
  };

  CH.heat = function (rs, c) {
    return '<div class="heat" style="grid-template-columns:repeat(5,minmax(0,1fr))">' + rs.map(function (r) {
      var cls = r.status === "complete" ? "ok" : (r.status === "partial" ? "warn" : "bad");
      var tip = r.challenge + " · " + r.challenge_title + " · " +
        (r.status === "complete" ? "完整" : (r.status === "partial" ? "部分" : "未提交")) +
        (r.score != null ? " · " + r.score + " 分" : "");
      return '<div class="cell ' + cls + '" title="' + c.esc(tip) + '" onclick="C6A_open(\'' + c.esc(r.challenge) + '\')" style="cursor:pointer">' +
        c.esc(r.challenge) + "</div>";
    }).join("") + "</div>" +
      '<div class="legend"><span><i style="background:#10b981"></i>必交物全齐</span>' +
      '<span><i style="background:#f59e0b"></i>部分缺失</span>' +
      '<span><i style="background:#ef4444"></i>未提交</span></div>';
  };

  window.C6A_CHARTS = CH;

  /* ---------- 时间线 ---------- */
  V.timeline = function (c) {
    var subs = c.records.filter(function (r) { return r.submitted_at; })
      .sort(function (a, b) { return String(a.submitted_at).localeCompare(String(b.submitted_at)); });
    if (!subs.length) return '<div class="card"><div class="empty">当前筛选下没有提交记录</div></div>';
    var html = '<div class="card"><h2>提交时间线</h2><p class="hint">按 UTC 时间正序；间隔为相邻两次提交的天数差（真实时间戳相减，非估算）</p><div class="tl">';
    var prev = null;
    subs.forEach(function (r) {
      var t = new Date(r.submitted_at.replace(" ", "T") + "Z");
      var gap = prev ? ((t - prev) / 86400000) : null;
      prev = t;
      html += '<div class="item"><div class="when">' + c.esc(r.submitted_at.replace("T", " ").slice(0, 19)) + " UTC" +
        (gap != null ? ' <span class="gap">· 距上次 ' + gap.toFixed(2) + " 天</span>" : "") + "</div>" +
        '<div class="what"><b>' + c.esc(r.challenge) + "</b> " + c.esc(r.challenge_title) +
        " " + (r.score != null ? c.scoreCell(r) + " 分 " : "") + c.badge(r.status) + "</div>" +
        '<div class="mono" style="color:#9ca3af">' + c.esc(r.submission_id || "—") + "</div></div>";
    });
    html += "</div></div>";

    /* 提交节奏表 */
    var byMonth = {};
    subs.forEach(function (r) { var m = String(r.submitted_at).slice(0, 7); byMonth[m] = (byMonth[m] || 0) + 1; });
    html += '<div class="card"><h2>按月提交量</h2><p class="hint">用于看节奏是否集中在截止前（避坑：不要把一个月的量堆到最后一周）</p>' +
      '<table><thead><tr><th>月份</th><th class="num">提交数</th><th>分布</th></tr></thead><tbody>' +
      Object.keys(byMonth).sort().map(function (m) {
        var n = byMonth[m];
        return "<tr><td class=\"mono\">" + m + '</td><td class="num">' + n + "</td><td>" +
          '<span style="display:inline-block;height:10px;border-radius:3px;background:#6366f1;width:' + (n * 34) + 'px"></span></td></tr>';
      }).join("") + "</tbody></table></div>";
    return html;
  };

  /* ---------- 缺失项 ---------- */
  V.missing = function (c) {
    var rows = [];
    c.records.forEach(function (r) {
      if (r.status === "missing") rows.push({ r: r, kind: "平台未提交", desc: "截至抽数时间无提交记录", sev: "高", act: "开工并提交" });
      (r.files || []).forEach(function (f) {
        if (!f.present) rows.push({ r: r, kind: "必交物缺失", desc: "未命中 " + f.pattern + "（" + f.label + "）", sev: "高", act: "补齐 " + f.label });
      });
      if (r.local_scan === "absent") rows.push({ r: r, kind: "本地无目录", desc: "工作区无 " + r.challenge + "/ 目录，无法做文件级核验", sev: "中", act: "补建目录或从平台拉回交付物" });
    });
    var html = '<div class="card"><h2>缺口清单（' + rows.length + " 条）</h2>" +
      '<p class="hint">三类缺口：平台未提交 / 必交物未命中 / 本地无目录。全部由数据现算，没有人工挑拣。</p>';
    if (!rows.length) return html + '<div class="empty">✅ 当前筛选下没有缺口</div></div>';
    html += '<table><thead><tr><th>挑战</th><th>标题</th><th>类型</th><th>说明</th><th>严重度</th><th>当前状态</th><th>建议动作</th></tr></thead><tbody>' +
      rows.map(function (x) {
        var cls = x.sev === "高" ? "bad" : (x.sev === "中" ? "warn" : "");
        return "<tr><td><b>" + c.esc(x.r.challenge) + "</b></td><td>" + c.esc(x.r.challenge_title) + "</td>" +
          "<td>" + c.esc(x.kind) + "</td><td>" + c.esc(x.desc) + "</td>" +
          '<td><span class="badge ' + cls + '">' + x.sev + "</span></td>" +
          "<td>" + c.badge(x.r.status) + "</td><td>" + c.esc(x.act) + "</td></tr>";
      }).join("") + "</tbody></table>";
    html += '<p class="hint" style="margin-top:12px;margin-bottom:0">严重度口径：高=直接影响该挑战得分或必交物校验；中=不影响评分，但降低可核验性（如缺本地目录）。</p></div>';
    return html;
  };

  window.C6A_VIEWS = V;
})();
