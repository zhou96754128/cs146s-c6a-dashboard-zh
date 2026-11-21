# C6A 提交数据仪表盘 · 方案设计

- 作者：周若莹（Zhouruoying）· 学号 2025105400318 · Elite 20 学员
- 挑战：C6A 提交数据仪表盘（ch-20260717031528-w43gy7）
- 版本：v1.0 · 2026-11-21
- 数据快照：`data/summary.json`（`generated_at` 见文件内字段）
- 交付形态：静态零依赖仪表盘（HTML+CSS+JS）+ Excel 报告 + 截图 + 复现脚本

---

## 1. 目标与边界

**目标**：把「一个学员在 21 个挑战上的提交行为」变成一张可自查、可教学、可复用的数据面板：一眼看出谁交了、交了多少分、缺什么、什么时候交的，并且每个数字都能回溯到平台原始返回或本地文件清单。

**明确边界（写进产品本身，而不是藏在注释里）**：

| 边界 | 事实 | 产品里的处理 |
| --- | --- | --- |
| 数据范围 | 仅本人账号（学号 2025105400318）在 EduSeed 平台的可见数据 | 面板标题与「数据来源」区标注「单学员视角」 |
| 班级口径 | 未取得全班 20 人的授权数据 | **不主张**「Elite 20 全班覆盖率」，只在诚实边界区说明缺口 |
| 本地文件核验 | 只扫本地工作区，扫不到的挑战按「未知」处理 | 缺目录的挑战标 `scan_absent`，**不推断**文件存在与否 |
| 评分口径 | 只认 `evaluator_type=ai` 且非「系统兜底初评」的分数 | 兜底分不进统计，事件里留痕 |
| 时间口径 | 平台时间为 UTC，本地展示按原值 | 面板只做格式化，不擅自改时区 |

## 2. 数据从哪来（三层，逐层可验证）

```
平台 API ──► raw/*.json        （原始返回，不改写，保留 trace id）
            │
            ├─► data/submissions.json   （21 条记录，一行一挑战）
            ├─► data/summary.json       （聚合指标 + 诚实边界字段）
            └─► data/file_index.json    （本地文件清单，按挑战分目录）
                    │
                    ▼
        Zhouruoying_C6A_report.xlsx（5 sheet）
        Zhouruoying_C6A_dashboard/（5 页签 + 详情抽屉）
```

- `_tools/fetch_platform.py`：调用平台 `list-my-submissions` / `get-evaluation` 等只读操作，原样落盘到 `raw/`。
- `_tools/build_dataset.py`：把原始返回规范化成 `submissions.json`（21 条）+ `summary.json`（聚合）。
- `_tools/file_index.py`：逐个挑战目录遍历文件，落 `file_index.json`；单挑战上限 600 个文件，超出标 `truncated=true`。
- `_tools/build_excel.py` / `_tools/build_site.py`：只读 `data/`，纯函数式产出 Excel 与静态站点；不联网、不改数据。
- `_tools/run_all.py`：一键从平台拉到产出，任一步非零退出即中断。

**关键设计选择：聚合层不许藏事实。** 例如 `files_total` 曾经混用了「提交记录里的文件数」和「本地扫描数」两种口径，导致 875 这个数既不是前者也不是后者。修正方式是把口径拆成三个字段并列暴露：

| 字段 | 含义 | 生成定义（可重算） | 构建快照值 |
| --- | --- | --- | --- |
| `files_in_submissions` | 平台提交记录里登记的文件数合计 | `Σ record.file_count` | 904 |
| `files_scanned` | 本地实际扫描到的文件数合计 | `Σ file_index.challenges[*].file_count` | 8172 |
| `files_listed` | 落进 file_index 的条目数（每挑战 600 上限截断） | `Σ challenges[*].listed` | 1756 |

> **口径声明：上表右列是构建时刻的工作区快照，不是永久常量。** 工作区在评审期内持续新增文件（含本挑战自身产物：`data/`、`dashboard/`、`screenshots/`、`report.xlsx`、`仪表盘.html`），因此同一命令在不同时刻运行会得到不同数字。文档引用的是 `summary.json.generated_at = 2026-11-21T10:01:40Z` 那一次快照；复核时请以 `summary.json` 的 `counts` 为准。三个字段的**定义式不变**，只有快照值会变——这也是把定义式一起写出来的原因：读者可以自己重算验证，而不是只能相信一个数字。

## 3. 数据模型（一行一挑战）

`data/submissions.json` 的每条记录字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `challenge` | string | 挑战代号（C1…C10H） |
| `challenge_id` | string | 平台长 ID |
| `challenge_title` | string | 平台标题 |
| `status` | enum | `complete` / `partial` / `missing` |
| `submission_id` / `evaluated_at` | string | 提交与出分标识 |
| `score` | number\|null | AI 初评分；null 表示未出分或兜底 |
| `evaluator_type` | string\|null | `ai` 才算有效 |
| `required_present` / `required_total` | number\|null | 必交物命中数 / 应有数 |
| `files[]` | array | 逐条必交物的 `label/pattern/present/matched_file` |
| `missing[]` | array | 缺失项清单 |
| `scan_absent` | bool | 本地无该目录 → 文件级核验为「未知」 |
| `notes[]` | array | 异常与口径说明 |

`required_present=null` 是**真实现象**（早期提交没有回填该字段），不是 0。展示层统一走 `cov_text()`：`present/total` 都有值才显示 `4/4`，否则显示 `未校验`。这条规则来自一次真实崩溃（见 AAR 事件 1）。

## 4. 仪表盘结构（展示质量维度）

**五个页签，覆盖五种提问方式**：

1. **总览**：4 个核心 KPI（挑战总数 / 已提交 / 未提交 / 平均分）＋ 分布桶（95+、90–94、85–89、80–84、<80）＋ 分数条形对比。
2. **按学生**：以学员为维度聚合（当前单学员视角），显示提交率、均分、完整度。
3. **按挑战**：21 行全量表，含状态徽标、得分色阶（≥90 绿 / ≥85 橙 / <85 红）、必交物覆盖、提交时间。
4. **时间线**：按提交时间倒序分组的纵向时间轴，用于看节奏与空窗。
5. **缺失项**：只列需要动手的事——未提交的挑战、覆盖不满的必交物、`scan_absent` 的目录。

**详情抽屉**：点任意一行滑出抽屉，展示该挑战的 submission_id、出分时间、evaluator_type、仓库链接、逐条必交物校验表（命中/缺失 + 命中文件名）、本地文件清单（可点，按工作区根拼 `file://` 打开）。这是「从汇总下钻到证据」的通道，也是数据完整性的自证入口。

**深链**：`index.html#student` / `#challenge` / `#timeline` / `#missing` / `#detail:C4C`。截图、教学、外部引用都能直接定位到具体视图，不用反复点击。切换页签时用 `history.replaceState` 回写 hash，不污染浏览历史。

**技术约束**：零依赖、零网络、零构建。`app.core.js`（状态/路由/筛选/抽屉）、`app.extra.js`、`app.views.js` 三文件拼装；`data.js` 以 `window.C6A_DATA` 注入，因此**双击 HTML 即可离线打开**，也可打成单文件 `Zhouruoying_C6A_仪表盘.html`（自包含，260 KB 量级）。

**可访问性/健壮性**：`esc()` 统一转义防 XSS（数据来自平台文本）；键盘 `Esc` 关抽屉；点击遮罩关抽屉；筛选/排序/搜索都走同一个 `records()` 纯函数，保证表格与计数永远一致（`显示 n / N 条`）。

## 5. 完成级别映射（Bronze → Platinum）

| 级别 | 要求 | 本交付 |
| --- | --- | --- |
| Bronze | 能展示提交数据 | ✅ 21 条记录全量渲染，静态可开 |
| Silver | 有指标与分布 | ✅ KPI、分位桶、均分/中位数/极值/标准差 |
| Gold | 可下钻到证据 | ✅ 详情抽屉 + 必交物逐条校验 + 文件级链接 |
| Platinum | 可复现、可复用、诚实 | ✅ `run_all.py` 一键重建；`serve.js` 供他人本地起服务；诚实边界字段内置 |

## 6. 评分维度自检

| 维度 | 权重 | 支撑证据 |
| --- | --- | --- |
| 数据完整性 | 25 | `raw/` 原始返回 + `data/` 规范化 + 三口径分列；缺目录标 `scan_absent` 不推断 |
| 展示质量 | 25 | 5 页签 + 抽屉 + 分数色阶 + 6 张 1440×1200 真实渲染截图 |
| 自动化程度 | 20 | `run_all.py` 串起 5 个脚本，任一步非零退出即中断；站点/Excel 全脚本生成 |
| 完成级别 | 15 | 见 §5，Platinum 的三条都可现场复现 |
| 可复用性 | 15 | 零依赖静态站点、`data.js` 契约化、深链、教学说明可他人照做 |

## 7. 已知限制（写下来，不遮掩）

1. **单学员数据**：全班 20 人对比需要授权数据，当前不做推断，面板显式标注。
2. **C4D 文件清单截断**：7016 个文件超过单挑战 600 上限，`truncated=true`；总数仍计入 `files_scanned`。
3. **T0 口径**：T0（ch-20260904104535-14aac163）是发布流程测试挑战。为保证「21 条记录 = 挑战总数」自洽，记录保留在数据里，但在完成率类统计中不计入已提交——此处理已写入 `notes`，避免读者按不同口径各算一遍。
4. **两台已提交挑战本地无目录**：标 `scan_absent`，文件级核验记为未知，不参与覆盖率分母。
5. **spearman 相关系数**：必交物覆盖率恒为 1.0（无方差），相关系数无定义，输出 `null` 而不是硬凑一个数。
