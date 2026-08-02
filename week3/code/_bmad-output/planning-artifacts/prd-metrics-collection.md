---
title: V3 Workflow Metrics Collection · PRD
version: 0.1
status: draft
owner: HuangJia (Tech Lead)
date: 2026-04-29
author: John (BMad PM)
project: KM系统 · V3 Multi-Agent 知识库
related_change: openspec/changes/metrics-collection
---

# PRD · V3 Workflow Metrics Collection (MVP)

> **Status:** v0.1 草稿 · 由 `bmad-agent-pm`（John）在 2026-04-29 引导产出 · 未经过 `bmad-validate-prd` 校验
> **目的:** 给 V3 7 节点工作流加 metrics 采集，回答"昨晚卡哪了 / review 几次能过 / 谁最烧钱"三大盲点

## 1. Problem Statement

V3 知识库 workflow（7 节点、每日 20 条）已在生产稳定运行，但**对自身运行状态完全失明**：

- 排障靠翻日志：无法快速回答"昨晚 pipeline 卡在哪一步"
- 质量靠感觉：不知道一条内容平均要 review 几轮才能通过
- 成本不可见：无法定位最烧 token 的 Agent，预算讨论缺乏依据

业务方（内容运营）也需要一份"知识库健康度" dashboard 来跟踪产能与质量，目前只能找工程同学手工拉数。

## 2. Users

| 角色 | 核心场景 | 决策频率 |
|------|---------|---------|
| **Tech Lead / On-call**（HuangJia） | 凌晨/早上排障、判断是否需要重跑、看成本异常 | 每日 |
| **内容运营**（业务方） | 看知识库每日产出、审核效率、内容质量趋势 | 每日 / 每周 |

> ⚠️ 两类用户**指标重叠但视图不同**：工程要节点级粒度，运营要业务级聚合。MVP 共用一套采集，分两个视图呈现。

## 3. Must-have Metrics (MVP · 5 项)

| # | 指标 | 回答的问题 | 粒度 |
|---|------|-----------|------|
| M1 | **节点状态分布**（success / failure / stuck，按 7 节点拆） | 昨晚卡在哪一步？ | 每条 × 每节点 |
| M2 | **Review 通过迭代数**（avg / p50 / p95） | 平均几次能通过？ | 每条 |
| M3 | **Agent Token 消耗**（按 Agent 拆，daily 总量 + 单条均值） | 谁最烧钱？ | 每条 × 每 Agent |
| M4 | **Daily Throughput**（实际入库条数 vs 目标 20） | 今天产能够不够？ | 每日 |
| M5 | **End-to-end Latency**（p50 / p95，单条从触发到入库） | pipeline 健康吗？ | 每条 |

## 4. Nice-to-have（明确**不做**进 MVP）

- 单条内容的全链路追踪（drill-down 到某一篇文章的完整轨迹）
- 失败率告警（Slack / 邮件，阈值触发）
- 成本周/月趋势对比与预算告警
- Review 通过率按内容类型/来源拆分
- 历史回填（MVP 仅采集上线后的新数据）

## 5. Success Criteria

- ✅ **排障时长**：Tech Lead 看 dashboard 能在 **5 分钟内**定位故障节点（baseline：今天靠翻日志约 30 分钟）
- ✅ **运营自助率**：内容运营**每周 0 次**找工程拉数（baseline：当前每周 2~3 次）
- ✅ **采集开销**：metrics 采集对 pipeline 单条 latency 增加 **< 5%**
- ✅ **MVP 上线 2 周内**：5 个 must-have 指标全部可见、口径文档化

## 6. Out of Scope

- 实时流式 dashboard（每日 / 每小时批量足够）
- ML 异常检测、自动 root cause 分析
- 重跑 / retry 的 UI 操作入口（只读优先）
- 跨系统调用链追踪（仅采集 V3 workflow 内部）
- 历史数据回填与对比（仅采集上线后的新流水）

## 7. Open Questions（PM 留给架构师 Winston 的输入）

1. **Metrics 用户优先级**：当工程视图与运营视图发生冲突，以哪边为准？（默认假设：MVP 工程优先，运营靠工程视图聚合派生）
2. **存储/展示栈**：未在 PRD 锁定，留给架构决策（候选：SQLite+Streamlit / Prometheus+Grafana / JSONL+Notion）
3. **吞吐 SLA 强度**：每天 20 条是硬 SLA 还是观察值？低于 20 算事故吗？
