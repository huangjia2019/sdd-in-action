# OpenSpec 项目上下文 · Week 3

> 本文件是 `/opsx:*` 每次执行时必读的项目上下文。**写得越具体，AI 跑偏概率越低**。
>
> 注 · 如果你用的 OpenSpec 较新（`openspec init` 不再创建 project.md），把本文件内容迁到 `openspec/config.yaml` 的 `context:` 字段里即可。

## 项目

**AI 知识库 V3 · Multi-Agent 版** · LangGraph 7 节点工作流 + OpenSpec + BMAD。

## 技术栈

- Python 3.11+
- **LangGraph** · 有状态图工作流 · `StateGraph(KBState)`
- **OpenSpec** · Week 2 沿用
- **BMAD-METHOD** · Week 3 引入 · 多角色 review（PM / Architect / Dev / QA）
- LLM · OpenAI 兼容端点（DeepSeek / Qwen / OpenAI 通过 `.env` 配置）
- 依赖 · `langgraph`, `openai`, `python-dotenv`, `httpx`, `pytest`

## 7 节点拓扑

```
plan → collect → analyze → review ─[pass]→ organize → END
                             │
                             ├─[fail<max]→ revise → review（循环）
                             │
                             └─[>=max]→ human_flag → END
```

核心决策点 · `workflows/graph.py::route_after_review` 3 路条件边。

## 关键数据契约

- `KBState`（`workflows/state.py`）· TypedDict · 9 字段 · 所有节点共享
- `knowledge/raw/*.json` · Collector 产出
- `knowledge/articles/{date}-{idx}.json` · Organizer 产出（正常终点）
- `knowledge/pending_review/pending-{ts}.json` · HumanFlag 产出（异常终点）

## 项目约定

- 每个 Agent 一个独立 `.py` 文件 · 文件名 = Agent 名
- Agent 间通过 KBState 字段通信 · 严禁直接 import 对方
- 新增 Agent 必须：独立文件 + 独立 capability + 不破坏已有 routing logic
- 所有成本追踪单位 · 人民币元

## 已知 gap（本周要用 OpenSpec + BMAD 修的）

- 没有指标记录 · 不知道每个 Agent 平均耗时 / 成本 / 失败率
- 没有 dashboard · 业务方看不到 pipeline 健康度
- review 循环的迭代次数分布没有统计

## 术语表（防跑偏）

| 词 | 本项目里指 |
|:---|:---------|
| node | LangGraph 的节点函数（runtime）|
| role / BMAD agent | BMAD 的开发期角色（`bmad-pm` 等）· 只在 chat 里，不落代码 |
| capability | OpenSpec 的能力单元 |
| agent | 两种含义 · 见 AGENTS.md 术语表分清楚 |
| schema | 业务 JSON schema · **不是** OpenSpec 工件 schema |
