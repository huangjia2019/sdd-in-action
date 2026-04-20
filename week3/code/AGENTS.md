# AGENTS.md · Week 3 基线 · V3 Multi-Agent 知识库

> 本文件是 OpenCode / Claude Code 启动时自动加载的"项目大脑"。`/opsx:*`、`@grill-me` 和 BMAD 角色（`bmad-pm` / `bmad-architect` / `bmad-dev` 等）都会读这份。

## 项目定义

**AI 知识库 V3（Multi-Agent 版）**。在 Week 1 单 Agent + Week 2 自动化流水线 + OpenSpec 基础上，引入 **7 个独立 Agent** 协作完成采集-分析-审核-入库闭环：

```
① Planner → ② Collector → ③ Analyzer → ④ Reviewer ┬─[pass]→ ⑥ Organizer → END
                                                    │
                                                    ├─[fail<max]→ ⑤ Reviser → ④ Reviewer（循环）
                                                    │
                                                    └─[>=max]→ ⑦ HumanFlag → END
```

## 7 个独立 Agent（一 Agent 一文件）

| 节点 | 文件 | 核心原则 |
|:----:|:-----|:-----|
| ① Planner | `workflows/planner.py` | 只规划不执行（Plan, don't execute）|
| ② Collector | `workflows/collector.py` | 只采集不分析（Collect, don't analyze）|
| ③ Analyzer | `workflows/analyzer.py` | 单条 LLM 分析 |
| ④ Reviewer | `workflows/reviewer.py` | **只评估不修改**（Evaluate, don't modify）· 5 维加权评分 |
| ⑤ Reviser | `workflows/reviser.py` | **只修改不评估**（Modify, don't evaluate）· 读反馈改 analyses |
| ⑥ Organizer | `workflows/organizer.py` | 整理入库（正常终点）|
| ⑦ HumanFlag | `workflows/human_flag.py` | 人工介入（异常终点）|

**职责隔离**：Reviewer 和 Reviser 不能是同一个 Agent（否则 Reviewer 会给自己修改的打高分，利益冲突）。

## 项目结构

```
week3/code/
├── AGENTS.md              # 本文件
├── requirements.txt
├── workflows/             # 7 个 Agent 节点（一 Agent 一文件）
│   ├── planner.py / collector.py / analyzer.py
│   ├── reviewer.py / reviser.py / organizer.py / human_flag.py
│   ├── graph.py · LangGraph 图 + 3 路条件边
│   ├── state.py · KBState (9 字段)
│   └── model_client.py
├── patterns/              # 通用 Agent 设计模式（和主流程解耦）
│   ├── router.py · Router 模式演示
│   └── supervisor.py · Supervisor 模式演示
├── tests/                 # 生产加固
│   ├── cost_guard.py · 预算守卫（含熔断）
│   ├── security.py · Prompt Injection 防御 + PII 检测
│   └── eval_test.py · LLM-as-Judge 评估
├── openspec/              # OpenSpec 工件（Week 2 引入）
└── .claude/ + .opencode/  # IDE 集成（opsx 命令 + skills）
```

## 关键数据契约

- `knowledge/raw/github-{YYYY-MM-DD}.json` · Collector 产出
- `knowledge/articles/{YYYY-MM-DD}-{NNN}.json` · Organizer 产出（正常终点）
- `knowledge/pending_review/pending-{timestamp}.json` · HumanFlag 产出（异常终点）
- KBState（`workflows/state.py`）· 所有 Agent 共享的 TypedDict · 9 个字段

## 技术栈

- Python 3.11+
- **LangGraph** · 有状态图工作流
- **OpenSpec** · Week 2 引入（change 生命周期管理）
- **BMAD-METHOD** · Week 3 引入（多角色 review + PRD/Architecture docs-as-code）
- LLM · OpenAI 兼容端点（DeepSeek / Qwen / OpenAI）

## 本周要做什么

**Week 3 不重建 V3**——V3 7 节点已经跑起来了。Week 3 是学 **多 Agent 场景下怎么用 OpenSpec + BMAD 协同开发新能力**。

具体要跑的 change：给 workflow 加一个 **`⑧ Metrics Collector`** 节点——在每个节点完成后记录指标（latency / cost / status / iterations），输出 observability dashboard 数据。

**为什么这个 change 适合 Week 3**：
- 必须 **BMAD Architect 角色** 先审（新 Agent 插哪里？边 observer 还是 in-graph node？影响 3 路条件边吗？）
- 必须 **BMAD PM 角色** 先定 PRD（给谁看的 dashboard？哪些指标必须？）
- **OpenSpec** 管 change 的 delta（MODIFIED Requirements on `state.py`，ADDED Requirements on new `metrics-collection` capability）

## 项目约定

- 每个 Agent 一个独立 `.py`·  **严禁**把两个职责合进一个文件
- Agent 间通过 `KBState` 字段通信 · **严禁**直接 import 对方
- 新增 Agent 必须：① 独立文件 ② 独立 requirement in spec ③ 不破坏已有 3 路 routing logic
- 所有成本记录单位 · 人民币元

## 术语表（防止 BMAD 和 LangGraph 术语混淆）

| 词 | 本项目里指 |
|:---|:---------|
| **node** | **LangGraph** 图里的一个节点（= 一个 Python Agent 函数，如 `collect_node`）|
| **agent**（小写） | LangGraph 的一个节点对应的 Python 函数 + 职责边界，**不带 LLM 会话** |
| **role** / **BMAD agent** | **BMAD** 的 AI 角色（`bmad-pm` / `bmad-architect` / `bmad-dev`）· 只在 IDE 对话里存在 · 不落代码 · 用于 review |
| **state** | KBState · 所有节点共享的数据总线 |
| **capability** | OpenSpec 里的能力单元（如 `metrics-collection`）|
| **change** | OpenSpec 里一次待合并的 PR（位于 `openspec/changes/<name>/`）|

**一句话区分**：
- LangGraph agent = 代码里真实存在的函数 · runtime 参与
- BMAD agent = 开发期的 AI 角色 · 只在 chat 里出现 · 帮你想清楚需求和架构
