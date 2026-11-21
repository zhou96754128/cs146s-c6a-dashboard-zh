# Zhouruoying_C6A_demo走查（演示与验收路径）

> 一句话：这份文件是**验收入口**——照着做，10 分钟内能亲眼确认仪表盘的每个数字都来自真实数据源。
> 诚实边界先说：**本交付未提供视频录屏**，只有 6 张静态截图（`Zhouruoying_C6A_screenshots/`）。原因见第 4 节，不掩饰。

---

## 1. 三十秒打开

```bash
# 方式 A：直接开单文件（零依赖，推荐给评审）
open Zhouruoying_C6A_仪表盘.html

# 方式 B：起本地静态服务（验证多文件版 dashboard/ 与单文件版一致）
node _tools/serve.js        # 默认 http://127.0.0.1:8788
```

两种方式看到的内容应完全一致：单文件版是构建产物，把 `dashboard/` 的 `data.js`、`app.*.js`、`style.css` 内联进来，便于离线评审。

---

## 2. 六步走查（对应 6 张截图）

| 步 | 操作 | 应看到 | 证据切片 |
| --- | --- | --- | --- |
| 1 | 打开页面，停在总览 | 4 个 KPI：21 挑战 / 12 已提交 / 9 未提交 / 提交率 57.14%；分数分布直方图 5 个桶合计 12 | `01_总览.png`（523426 B） |
| 2 | 点「按学生」页签 | 单学生视图（周若莹），明示「仅单个真实账号数据」，无虚构同学 | `02_按学生.png`（624026 B） |
| 3 | 点「按挑战」页签 | 21 行挑战表，含必交物覆盖列（未校验显示「未校验」而非 0） | `03_按挑战.png`（548028 B） |
| 4 | 点「时间线」页签 | 月度提交节奏：2026-09 两条、10 月六条、11 月四条 | `04_时间线.png`（563536 B） |
| 5 | 点「缺失项」页签 | 缺失项为空 + 9 个未提交挑战清单（T0 标注「请忽略」） | `05_缺失项.png`（718738 B） |
| 6 | 点表格行右侧「详情」 | 右侧抽屉打开，展示该挑战的分数、评语来源、文件清单（C4D 标明 7016 文件 / 列 600 条 / 已截断） | `06_详情抽屉.png`（628383 B） |

页签与抽屉的切换不是靠肉眼判断，构建期用 `--dump-dom` 断言过：切换后对应节点的 `class="on"` 命中，6 张截图抓取均 `RC=0`。

---

## 3. 数字自证（关键一步）

不要相信截图上的数字，直接跟源数据对：

```bash
# 1) 看口径与快照值
python3 -c "import json;d=json.load(open('Zhouruoying_C6A_data/summary.json'));print(d['counts']);print(d['score']['mean'],d['score']['median'])"

# 2) 看明细（21 行 = 表头 1 + 挑战 21？不，21 行含表头，即 21 条记录在 submissions.json）
python3 -c "import json;d=json.load(open('Zhouruoying_C6A_data/submissions.json'));print(len(d))"

# 3) 看原始接口返回（平台真身）
ls -l raw/list-my-submissions.txt raw/evaluations.json

# 4) 全量自检：18 项断言，含产物字节一致性
python3 _tools/run_all.py ; echo "RUN_ALL_RC=$?"
```

若 `summary.json` 里的数字与页面显示不一致，以 `summary.json` 为准，并说明是构建未重跑。

---

## 4. 为什么没有录屏（不掩饰）

- 本机没有 `ffmpeg` / `ffprobe`，也没有系统级录屏工具链；C4D 那次是用 `swiftc` + AVFoundation 硬编出视频的，做一次成本很高。
- 这个仪表盘的核心是**静态数据可复核**，不是交互流程演示；因此把成本投在了「口径文档 + 18 项自检 + 截图批次一致性」上，而不是再编一段视频。
- 替代证据：6 张真实渲染截图（位图，非手绘）+ `--dump-dom` 交互断言 + `run_all.py` 18/18 全绿 + 数据字典逐项定义式。
- 如果评审方需要视频，我可以补；在补之前，这里明确写「未提供」，不假装有。

---

## 5. 截图批次一致性声明

首轮抓图后站点做了两次改动（按挑战表补覆盖列、详情抽屉补截断字段），因此**重新构建后整批重拍了 6 张**。当前截图与当前单文件 HTML 同源：

- 单文件 HTML：262608 字节，sha256 前缀 `2068b6ee0402a334`
- 截图字节：523426 / 624026 / 548028 / 563536 / 718738 / 628383
- 数据文件：`Zhouruoying_C6A_data/` 四份（`summary.json` 3366 B、`submissions.json` 52979 B、`submissions.csv` 3227 B、`file_index.json` 260942 B）

首轮截图的字节（226315 / 266591 / 231239 / 240454 / 317996 / 277054）在 AI 日志里作为历史记录保留，**当前交付以重拍批为准**。

---

## 6. 重跑全链路

```bash
python3 _tools/fetch_platform.py   # 拉平台最新数据 → raw/
python3 _tools/file_index.py       # 扫本地文件树 → data/file_index.json
python3 _tools/build_dataset.py    # 合并 → summary.json / submissions.*
python3 _tools/build_excel.py      # → report.xlsx
python3 _tools/build_site.py       # → 单文件 HTML + dashboard/
python3 _tools/run_all.py          # 18 项断言
```

顺序有依赖：`build_dataset` 依赖前两步产物，`build_site` 依赖 `summary.json`。`run_all.py` 会校验「文档声明值 == 磁盘实际值」。
