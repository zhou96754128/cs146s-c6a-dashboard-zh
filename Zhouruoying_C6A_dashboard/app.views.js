/* C6A 仪表盘 — 视图：总览 / 按学生 / 按挑战 */
(function () {
  "use strict";
  var V = window.C6A_VIEWS || {};

  function kpi(k, v, h, tone) {
    return '<div class="kpi"><div class="k">' + k + '</div><div class="v"' +
      (tone ? ' style="color:' + tone + '"' : "") + ">" + v + "</div>" +
      (h ? '<div class="h">' + h + "</div>" : "") + "</div>";
  }

  /* ---------------- 总览 ---------------- */
  V.overview = function (c) {
    var S = c.D.summary || {};
    var cnt = S.counts || {}, sc = S.score || {};
    var rs = c.all;
    var real = rs.filter(function (r) { return r.challenge !== "T0"; });
    var submitted = real.filter(function (r) { return r.status !== "missing"; });
    var complete = real.filter(function (r) { return r.status === "complete"; });

    var html = '<div class="kpis">' +
      kpi("挑战总数", cnt.challenges_total != null ? cnt.challenges_total : real.length, "含发布流程测试 T0（已排除出统计）") +
      kpi("已提交", cnt.challenges_submitted, "占 " + c.num(100 * cnt.submission_rate, 1) + "%", "#4f46e5") +
      kpi("必交物全齐", complete.length + " / " + submitted.length, "已提交挑战的完整率", "#059669") +
      kpi("已出分", cnt.evaluations_read, "平均 " + c.num(sc.mean, 2) + " 分", "#059669") +
      kpi("最高 / 最低", c.num(sc.max) + " / " + c.num(sc.min), "中位数 " + c.num(sc.median, 1) + "，标准差 " + c.num(sc.stdev, 2)) +
      kpi("本地文件", cnt.files_scanned, "扫描 " + cnt.local_dirs_scanned + " 个目录 · 提交侧 " + cnt.files_in_submissions) +
      "</div>";

    /* 完成进度 + 分数分布 */
    html += '<div class="grid2">';
    html += '<div class="card"><h2>提交进度</h2><p class="hint">按 20 个正式挑战计（T0 只用于验证发布链路，不计入）</p>' +
      '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">' +
      "<span>已提交 <b>" + submitted.length + "</b> / " + real.length + "</span>" +
      '<span style="color:#6b7280">' + c.num(100 * submitted.length / real.length, 1) + "%</span></div>" +
      '<div class="bar"><i style="width:' + c.pct(submitted.length, real.length) + '%"></i></div>' +
      '<div class="legend"><span><i style="background:#10b981"></i>完整 ' + complete.length + "</span>" +
      '<span><i style="background:#f59e0b"></i>部分 ' + real.filter(function (r) { return r.status === "partial"; }).length + "</span>" +
      '<span><i style="background:#ef4444"></i>未提交 ' + real.filter(function (r) { return r.status === "missing"; }).length + "</span></div>" +
      '<h2 style="margin-top:18px">分数区间分布</h2><p class="hint">共 ' + cnt.evaluations_read + " 份 AI 初评（evaluator_type=ai）</p>" +
      (window.C6A_CHARTS ? window.C6A_CHARTS.buckets(sc.buckets || {}) : "") +
      "</div>";

    /* 挑战状态热力图 */
    html += '<div class="card"><h2>挑战状态一览</h2><p class="hint">绿=必交物全齐，黄=部分缺失，红=未提交；点格子看详情</p>' +
      (window.C6A_CHARTS ? window.C6A_CHARTS.heat(real, c) : "") +
      "</div></div>";

    /* 分数排行 */
    var scored = rs.filter(function (r) { return r.score != null; })
      .sort(function (a, b) { return b.score - a.score; });
    html += '<div class="grid2"><div class="card"><h2>得分排行</h2><p class="hint">横向看：同一评分维度下的相对位置</p><table><thead><tr><th>#</th><th>挑战</th><th>标题</th><th class="num">得分</th><th>状态</th></tr></thead><tbody>' +
      scored.map(function (r, i) {
        return "<tr onclick=\"C6A.state.tab='challenge';C6A.render();C6A_open('" + c.esc(r.challenge) + "')\" style=\"cursor:pointer\">" +
          '<td class="num">' + (i + 1) + "</td><td><b>" + c.esc(r.challenge) + "</b></td><td>" + c.esc(r.challenge_title) +
          '</td><td class="num">' + c.scoreCell(r) + "</td><td>" + c.badge(r.status) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    /* 口径说明 */
    html += '<div class="card"><h2>数据口径与已知边界</h2><p class="hint">这一节是给评审看的：哪些是实测，哪些是「未知」</p>' +
      '<ul style="margin:0;padding-left:18px;font-size:12.5px;color:#374151;line-height:1.9">' +
      ((S.caveats || []).map(function (x) { return "<li>" + c.esc(x) + "</li>"; }).join("")) +
      "</ul></div></div>";
    return html;
  };

  /* ---------------- 按学生 ---------------- */
  V.student = function (c) {
    var S = c.D.summary || {}, st = S.student || {};
    var rs = c.records;
    var html = '<div class="card"><h2>' + c.esc(st.name || "—") + "</h2>" +
      '<p class="hint">学号 ' + c.esc(st.id || "—") + "　GitHub " + c.esc(st.github || "—") +
      "　身份 " + c.esc(st.track || "Elite 20 学员") + "</p>" +
      '<div style="display:flex;gap:26px;flex-wrap:wrap;margin-top:6px;font-size:13px">' +
      "<div>已提交 <b>" + rs.filter(function (r) { return r.status !== "missing"; }).length + "</b></div>" +
      "<div>必交物全齐 <b>" + rs.filter(function (r) { return r.status === "complete"; }).length + "</b></div>" +
      "<div>已出分 <b>" + rs.filter(function (r) { return r.score != null; }).length + "</b></div>" +
      "<div>平均分 <b>" + c.num((S.score || {}).mean, 2) + "</b></div>" +
      '<div style="color:#6b7280">本地扫描文件 <b>' + (S.counts || {}).files_scanned + "</b>（明细 " + (S.counts || {}).files_listed + " 条，单挑战上限 600 截断）</div></div>" +
      '<p class="hint" style="margin-top:14px;margin-bottom:0">口径：本页只反映该学员本人的平台提交与本地工作区，<b>不含同班其他学员数据</b>——没有授权数据时不做任何推断填充。点行看逐项明细。</p></div>';

    html += '<div class="card"><h2>逐挑战明细（' + rs.length + " 条）</h2>" +
      '<table><thead><tr><th>挑战</th><th>标题</th><th>提交时间</th><th>状态</th><th>必交物</th><th class="num">得分</th><th class="num">本地文件</th><th>缺失项</th></tr></thead><tbody>' +
      rs.map(function (r) {
        return '<tr onclick="C6A_open(\'' + c.esc(r.challenge) + '\')" style="cursor:pointer">' +
          "<td><b>" + c.esc(r.challenge) + "</b></td><td>" + c.esc(r.challenge_title) + "</td>" +
          '<td class="mono">' + c.esc((r.submitted_at || "—").replace("T", " ").slice(0, 19)) + "</td>" +
          "<td>" + c.badge(r.status) + "</td>" +
          '<td class="num">' + (r.required_total ? (r.required_present || 0) + "/" + r.required_total : "—") + "</td>" +
          '<td class="num">' + c.scoreCell(r) + "</td>" +
          '<td class="num">' + (r.local_file_count || 0) + "</td>" +
          '<td style="color:#b91c1c;font-size:11.5px">' + c.esc((r.missing || []).join("、") || "—") + "</td></tr>";
      }).join("") + "</tbody></table></div>";
    return html;
  };

  /* ---------------- 按挑战 ---------------- */
  V.challenge = function (c) {
    var rs = c.records;
    var html = '<div class="card"><h2>挑战卡片</h2><p class="hint">点任意卡片查看必交物逐项校验与本地文件清单</p><div class="cards">' +
      rs.map(function (r) {
        return '<div class="ccard" onclick="C6A_open(\'' + c.esc(r.challenge) + '\')">' +
          '<div class="code">' + c.esc(r.challenge) + (r.score != null ? '<span class="score" style="float:right">' + r.score + "</span>" : "") + "</div>" +
          '<div class="t">' + c.esc(r.challenge_title) + "</div>" +
          '<div class="foot"><span>' + c.badge(r.status) + "</span><span>" +
          (r.required_total ? (r.required_present || 0) + "/" + r.required_total + " 必交物" : (r.local_file_count || 0) + " 文件") +
          "</span></div></div>";
      }).join("") + "</div></div>";

    html += '<div class="card"><h2>必交物覆盖矩阵</h2><p class="hint">未命中即红色——这些就是「缺什么」的硬证据</p>' +
      '<table><thead><tr><th>挑战</th><th>必交项</th><th>要求</th><th>结果</th><th>命中文件</th><th class="num">得分</th></tr></thead><tbody>';
    rs.forEach(function (r) {
      var files = r.files || [];
      if (!files.length) {
        html += '<tr><td><b>' + c.esc(r.challenge) + "</b></td><td colspan=\"4\" style=\"color:#9ca3af\">" +
          (r.status === "missing" ? "未提交，无必交物校验" : "该挑战无必交物定义") + "</td>" +
          '<td class="num">' + c.scoreCell(r) + "</td></tr>";
        return;
      }
      files.forEach(function (f, i) {
        html += "<tr" + (i === 0 ? ' style="border-top:2px solid #e5e7eb"' : "") + ">" +
          (i === 0 ? "<td rowspan=\"" + files.length + "\"><b>" + c.esc(r.challenge) + "</b></td>" : "") +
          "<td>" + c.esc(f.label || "") + '</td><td class="mono">' + c.esc(f.pattern || "") + "</td>" +
          "<td>" + (f.present ? '<span class="badge ok">命中</span>' : '<span class="badge bad">缺失</span>') + "</td>" +
          "<td>" + (f.matched_file ? c.fileLink(f.matched_file) : '<span style="color:#9ca3af">—</span>') + "</td>" +
          (i === 0 ? '<td class="num" rowspan="' + files.length + '">' + c.scoreCell(r) + "</td>" : "") + "</tr>";
      });
    });
    html += "</tbody></table></div>";
    return html;
  };

  window.C6A_VIEWS = V;
})();
