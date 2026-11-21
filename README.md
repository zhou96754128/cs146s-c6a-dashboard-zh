# C6A 提交数据仪表盘 · 周若莹（2025105400318）

把「本人 21 个挑战的提交情况」做成本地可跑的静态仪表盘 + Excel 报表，全部数字由脚本现算，不手工填表。

- 学员：周若莹 / `2025105400318` / Elite 20 / GitHub `@zhou96754128`
- 挑战：`ch-20260717031528-w43gy7`（C6A 提交数据仪表盘），截止 2026-12-31
- 交付时间：2026-11-21

---

## 1. 30 秒看懂这份交付

| 想知道什么 | 打开哪里 |
| --- | --- |
| 一共提交了几个、多少分、还差什么 | `Zhouruoying_C6A_仪表盘.html`（单文件，双击即开） |
| 每个挑战的文件、必交物、评分 | 同上 → 按挑战 / 详情抽屉（`#detail:C5`） |
| 表格版汇报 | `Zhouruoying_C6A_report.xlsx`（5 sheet） |
| 数据从哪来、怎么算 | `Zhouruoying_C6A_data/summary.json` + 本文第 4 节 |
| 一键复跑并自检 | `python3 _tools/run_all.py` |

**单文件版**不需要服务器、不需要联网、不需要装任何东西——直接双击 `Zhouruoying_C6A_仪表盘.html`。

## 2. 目录结构

```
C6A/
├── Zhouruoying_C6A_仪表盘.html          # ★ 单文件仪表盘（自包含，双击可开）
├── Zhouruoying_C6A_report.xlsx          # Excel：总览/按学生/按挑战/时间线/缺失项
├── Zhouruoying_C6A_data/                # 结构化数据（全部由脚本生成）
│   ├── submissions.json                 # 21 条挑战记录，一行一挑战
│   ├── summary.json                     # 聚合指标 + 口径说明 + 诚实边界
│   ├── file_index.json                  # 本地工作区文件扫描清单
│   └── submissions.csv                  # 便于 Excel/BI 直接导入
├── Zhouruoying_C6A_dashboard/           # 站点源码（分文件版，供改动与二次开发）
│   ├── index.html
│   ├── style.css
│   ├── data.js                          # build_site.py 生成，勿手改
│   ├── app.core.js                      # 状态/路由/渲染主逻辑
│   ├── app.views.js                     # 五个页签的视图
│   └── app.extra.js                     # 详情抽屉/时间线等附加视图
├── Zhouruoying_C6A_screenshots/         # 6 张真实渲染截图
├── _tools/                              # 构建脚本（复现入口）
│   ├── fetch_platform.py                # 平台只读取数
│   ├── build_dataset.py                 # 规范化 → submissions/summary/csv
│   ├── file_index.py                    # 本地文件扫描 → file_index.json
│   ├── build_excel.py                   # → report.xlsx
│   ├── build_site.py                    # → data.js + 单文件 HTML
│   ├── serve.js                         # 本地静态服务（截图用）
│   └── run_all.py                       # 一键复现 + 硬断言自检
├── raw/                                 # 平台原始返回（原样落盘，便于追溯）
├── challenge/                           # 挑战正文 / challenge.yaml / rubric.json（只读参考）
├── Zhouruoying_C6A_数据说明.md           # 数据字典与口径声明（三口径文件数、各指标定义式）
├── Zhouruoying_C6A_demo走查.md           # 演示与验收路径（六步走查 + 数字自证 + 无录屏声明）
├── Zhouruoying_C6A_方案设计.md
├── Zhouruoying_C6A_教学说明.md
├── Zhouruoying_C6A_AAR.md
├── Zhouruoying_C6A_AI日志.md
└── Zhouruoying_C6A_拿来说明.md
```

## 3. 怎么跑

### 3.1 只看结果（无需安装）

双击 `Zhouruoying_C6A_仪表盘.html`。若浏览器限制本地文件脚本，用任一本机静态服务器指向 `Zhouruoying_C6A_dashboard/`。

### 3.2 从零复现

```bash
# 依赖：Python 3.11+；只有 Excel 一步需要 openpyxl
python3 -m pip install openpyxl==3.1.5

cd C6A
python3 _tools/run_all.py
echo "RC=$?"          # 期望 0，末尾打印 RUN_ALL_RC=0
```

`run_all.py` 会依次跑：数据层 → 文件清单 → 数据层重算 → Excel → 站点，并断言 7 组条件（记录数 21、提交+未提交=总数、`required_*` 两字段同缺同有、null 覆盖率显示「未校验」、xlsx 五 sheet、单文件 HTML 含数据与深链、data.js 与数据层一致）。任一条不满足即非零退出。

### 3.3 只更新数据

```bash
python3 _tools/fetch_platform.py     # 重新拉平台记录（只读）
python3 _tools/run_all.py            # 重算 + 重出 Excel 与站点
```

## 4. 口径（读数字前请先看这一节）

1. **视角是单学员**：只含本人提交与本人本地工作区，不含同班其他数据。
2. **三个文件数不是一个东西**，面板与 Excel 里分列显示：
   - `files_in_submissions`：平台提交记录登记的文件数（**加总**）
   - `files_scanned`：本地工作区递归扫描到的真实文件数
   - `files_listed`：进入 `file_index.json` 的条目数（单挑战上限 600，超出标 `truncated`）
3. **`null` 不等于 `0`**：早期提交未回填必交物命中数时，`required_present` 保持 `null`，展示层显示「未校验」，不臆造为 0。
4. **本地无目录的已提交挑战**标 `scan_absent`：只说明「本地没扫到」，不推断其文件内容。
5. **分数只认 `evaluator_type=ai` 的评审**；系统兜底分不计入统计。
6. **T0（`ch-20260904104535-14aac163`）** 是发布流程测试挑战：保留记录以维持「平台可见 21 条」，但不计入已提交统计，原因写在该条 `notes`。
7. **不给无意义的统计量**：必交物覆盖率恒为 1.0，无方差 → `spearman_coverage_vs_score = null`，不凑近似值。

## 5. 页面能力

- 五个页签：总览 / 按学生 / 按挑战 / 时间线 / 缺失项
- 详情抽屉：点任一挑战看逐条必交物、分数、评语摘要
- **深链**（可截图、可引用、可教学指名）：
  `#overview` `#student` `#challenge` `#timeline` `#missing` `#detail:C5`
- 切页签用 `history.replaceState` 回写地址，不污染浏览历史
- 零依赖：手写 SVG/CSS 图表，无 CDN、无网络字体

## 6. 证据留痕

| 证据 | 位置 |
| --- | --- |
| 平台原始返回 | `raw/` |
| 数据生成结果 | `Zhouruoying_C6A_data/*.json`（含 `generated_at`） |
| 站点构建输出 | `Zhouruoying_C6A_dashboard/data.js` + 单文件 HTML |
| 渲染证据 | `Zhouruoying_C6A_screenshots/` 6 张（1440×1200） |
| 自检输出 | `python3 _tools/run_all.py` 的 PASS/FAIL 明细 |
| 协作与返工 | `Zhouruoying_C6A_AI日志.md`、`Zhouruoying_C6A_AAR.md` |

## 7. 已知限制

- 单学员视角，不主张班级覆盖率。
- C4D 目录 7016 个文件，清单按 600 上限截断（已显式标注，总数不受影响）。
- 两个已提交但本地无目录的挑战无法做文件级核验（标 `scan_absent`）。
- 评语只取平台返回文本，未做二次解读或改写。
