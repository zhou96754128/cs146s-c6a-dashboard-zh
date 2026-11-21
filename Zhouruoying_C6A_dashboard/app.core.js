/* C6A 仪表盘 — 核心：状态、路由、筛选、抽屉、（零依赖） */
(function () {
  "use strict";
  var D = window.C6A_DATA || {};
  var LS_WS = "c6a_workspace_root";

  var TABS = ["overview", "student", "challenge", "timeline", "missing"];

  /* 深链：index.html#student / #challenge / #timeline / #missing / #detail:C4C
     用于演示、截图、教学与外部引用（可直接跳到某一页签或某条挑战详情）。 */
  function hashState() {
    var h = String(location.hash || "").replace(/^#/, "");
    if (!h) return { tab: "overview", detail: null };
    var m = h.match(/^detail:([A-Za-z0-9]+)$/);
    if (m) return { tab: "challenge", detail: m[1] };
    return { tab: TABS.indexOf(h) >= 0 ? h : "overview", detail: null };
  }
  var H0 = hashState();
  function setHash(tab) {
    try { if (location.hash.replace(/^#/, "") !== tab) history.replaceState(null, "", "#" + tab); } catch (e) {}
  }

  var state = {
    tab: H0.tab,
    q: "",
    status: "all",
    sort: "challenge",
    ws: (function () {
      try { return localStorage.getItem(LS_WS) || D.workspace_root || ""; } catch (e) { return D.workspace_root || ""; }
    })()
  };

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function num(v, d) { return (v == null || isNaN(v)) ? "—" : Number(v).toFixed(d == null ? 0 : d); }
  function bytes(n) {
    if (n == null) return "—";
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(2) + " MB";
  }
  function badge(st) {
    var m = { complete: ["ok", "✅ 完整"], partial: ["warn", "⚠️ 部分"], missing: ["bad", "❌ 未提交"] };
    var x = m[st] || ["bad", st || "—"];
    return '<span class="badge ' + x[0] + '">' + x[1] + "</span>";
  }
  function statusOf(rec) { return rec.status || "missing"; }
  function scoreCell(rec) {
    if (rec.score == null) return '<span style="color:#9ca3af">—</span>';
    var v = Number(rec.score);
    var color = v >= 90 ? "#059669" : (v >= 85 ? "#b45309" : "#b91c1c");
    return '<b style="color:' + color + ';font-variant-numeric:tabular-nums">' + v + "</b>";
  }
  function fileHref(rel) {
    if (!state.ws) return null;
    var root = state.ws.replace(/\/+$/, "");
    return "file://" + root + "/" + rel.split("/").map(encodeURIComponent).join("/");
  }
  function fileLink(rel) {
    var href = fileHref(rel);
    if (!href) return '<span class="mono">' + esc(rel) + "</span>";
    return '<a class="mono" href="' + esc(href) + '" target="_blank" rel="noopener">' + esc(rel) + "</a>";
  }
  function el(id) { return document.getElementById(id); }
  function pct(a, b) { return b ? (100 * a / b) : 0; }

  /* ---------- 数据视图 ---------- */
  function records() {
    var rs = (D.records || []).slice();
    if (state.status !== "all") rs = rs.filter(function (r) { return statusOf(r) === state.status; });
    if (state.q) {
      var q = state.q.toLowerCase();
      rs = rs.filter(function (r) {
        return [r.challenge, r.challenge_title, r.submission_id, r.repo_url, (r.missing || []).join(" ")]
          .join(" ").toLowerCase().indexOf(q) >= 0;
      });
    }
    if (state.sort === "score_desc") rs.sort(function (a, b) { return (b.score || -1) - (a.score || -1); });
    else if (state.sort === "score_asc") rs.sort(function (a, b) { return (a.score == null ? 999 : a.score) - (b.score == null ? 999 : b.score); });
    else if (state.sort === "date") rs.sort(function (a, b) { return String(b.submitted_at || "").localeCompare(String(a.submitted_at || "")); });
    else rs.sort(function (a, b) { return String(a.challenge).localeCompare(String(b.challenge)); });
    return rs;
  }
  function filesOf(code) {
    var fi = (D.file_index || {})[code];
    return (fi && fi.files) || [];
  }
  function challengeMeta(code) {
    var cs = D.challenges || [];
    for (var i = 0; i < cs.length; i++) if (cs[i].code === code) return cs[i];
    return null;
  }

  /* ---------- 抽屉 ---------- */
  function openDrawer(html) {
    el("drawerBody").innerHTML = html;
    el("drawer").classList.add("on");
  }
  function closeDrawer() { el("drawer").classList.remove("on"); }

  function recordDetail(rec) {
    var code = rec.challenge;
    var files = filesOf(code);
    var reqRows = (rec.files || []).map(function (f) {
      return "<tr><td>" + esc(f.label || "") + '</td><td class="mono">' + esc(f.pattern || "") + "</td><td>" +
        (f.present ? '<span class="badge ok">命中</span>' : '<span class="badge bad">缺失</span>') + "</td><td>" +
        (f.matched_file ? fileLink(f.matched_file) : '<span style="color:#9ca3af">—</span>') + "</td></tr>";
    }).join("");
    var fileRows = files.length ? files.map(function (f) {
      return "<li><span class=\"ico\">📄</span>" + fileLink(f.path) + '<span class="sz">' + bytes(f.size) + "</span></li>";
    }).join("") : '<li class="nofiles">本地无该挑战目录，无法做文件级核验（全部按「未知」处理，不做推断）</li>';

    return '<button class="x" onclick="C6A.closeDrawer()">✕</button>' +
      "<h3>" + esc(code) + " · " + esc(rec.challenge_title) + "</h3>" +
      '<div class="meta">' + badge(statusOf(rec)) +
      "　submission <span class=\"mono\">" + esc(rec.submission_id || "—") + "</span>" +
      "　提交 " + esc((rec.submitted_at || "—").replace("T", " ").slice(0, 19)) +
      "　得分 " + (rec.score == null ? "—" : rec.score) +
      (rec.evaluator_type ? "（" + esc(rec.evaluator_type) + "）" : "") + "</div>" +
      (rec.repo_url ? '<div style="font-size:12px">仓库：<a href="' + esc(rec.repo_url) + '" target="_blank" rel="noopener">' + esc(rec.repo_url) + "</a></div>" : "") +
      "<h4>必交物校验（" + (rec.required_present || 0) + "/" + (rec.required_total || 0) + "）</h4>" +
      (reqRows ? "<table><thead><tr><th>必交项</th><th>要求</th><th>结果</th><th>命中文件</th></tr></thead><tbody>" + reqRows + "</tbody></table>"
        : '<div class="nofiles">该挑战无必交物要求或尚未提交</div>') +
      "<h4>本地文件（" + files.length + " 个 / 目录 " + esc(code) + "/）</h4>" +
      '<ul class="files">' + fileRows + "</ul>" +
      "<h4>备注</h4><div style=\"font-size:12px;color:#4b5563\">" + esc((rec.notes || []).join("；") || "—") + "</div>";
  }

  /* ---------- 渲染壳 ---------- */
  function renderNav() {
    var tabs = [["overview", "总览"], ["student", "按学生"], ["challenge", "按挑战"], ["timeline", "时间线"], ["missing", "缺失项"]];
    el("tabs").innerHTML = tabs.map(function (t) {
      return '<button data-tab="' + t[0] + '" class="' + (state.tab === t[0] ? "on" : "") + '">' + t[1] + "</button>";
    }).join("");
    Array.prototype.forEach.call(el("tabs").querySelectorAll("button"), function (b) {
      b.onclick = function () { state.tab = b.dataset.tab; setHash(b.dataset.tab); render(); window.scrollTo(0, 0); };
    });
  }

  function renderToolbar() {
    var rs = D.records || [];
    var n = records().length;
    el("toolbar").innerHTML =
      '<input type="search" id="q" placeholder="搜索挑战 / 标题 / submission_id / 缺失项" value="' + esc(state.q) + '">' +
      '<select id="fStatus">' + [["all", "全部状态"], ["complete", "✅ 完整"], ["partial", "⚠️ 部分"], ["missing", "❌ 未提交"]]
        .map(function (o) { return '<option value="' + o[0] + '"' + (state.status === o[0] ? " selected" : "") + ">" + o[1] + "</option>"; }).join("") + "</select>" +
      '<select id="fSort">' + [["challenge", "按挑战编号"], ["score_desc", "分数从高到低"], ["score_asc", "分数从低到高"], ["date", "提交时间最新"]]
        .map(function (o) { return '<option value="' + o[0] + '"' + (state.sort === o[0] ? " selected" : "") + ">" + o[1] + "</option>"; }).join("") + "</select>" +
      '<span class="count">显示 ' + n + " / " + rs.length + " 条</span>";
    el("q").oninput = function (e) { state.q = e.target.value; renderView(); };
    el("fStatus").onchange = function (e) { state.status = e.target.value; render(); };
    el("fSort").onchange = function (e) { state.sort = e.target.value; renderView(); };
  }

  function renderView() {
    var fn = window.C6A_VIEWS[state.tab] || window.C6A_VIEWS.overview;
    el("view").innerHTML = fn(ctx());
    renderToolbar();
    if (window.C6A_AFTER) window.C6A_AFTER[state.tab] && window.C6A_AFTER[state.tab](ctx());
  }

  function ctx() {
    return {
      D: D, state: state, records: records(), all: D.records || [],
      filesOf: filesOf, challengeMeta: challengeMeta, esc: esc, bytes: bytes,
      badge: badge, scoreCell: scoreCell, fileLink: fileLink, num: num, pct: pct,
      openRecord: function (code) {
        var rec = (D.records || []).filter(function (r) { return r.challenge === code; })[0];
        if (rec) openDrawer(recordDetail(rec));
      }
    };
  }

  function render() { renderNav(); renderView(); }

  function boot() {
    el("wsRoot").value = state.ws || "";
    el("genAt").textContent = D.generated_at || "";
    el("wsRoot").oninput = function (e) {
      state.ws = e.target.value.trim();
      try { localStorage.setItem(LS_WS, state.ws); } catch (err) {}
      renderView();
    };
    el("drawer").onclick = function (e) { if (e.target === el("drawer")) closeDrawer(); };
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });
    window.addEventListener("hashchange", function () {
      var h = hashState();
      state.tab = h.tab;
      render();
      if (h.detail) openRecord(h.detail);
    });
    render();
    if (H0.detail) openRecord(H0.detail);
  }

  function openRecord(code) {
    var rec = (D.records || []).filter(function (r) { return r.challenge === code; })[0];
    if (rec) openDrawer(recordDetail(rec));
  }

  window.C6A = { state: state, render: render, openDrawer: openDrawer, closeDrawer: closeDrawer, recordDetail: recordDetail, esc: esc };
  window.C6A_VIEWS = window.C6A_VIEWS || {};
  window.C6A_AFTER = window.C6A_AFTER || {};
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
