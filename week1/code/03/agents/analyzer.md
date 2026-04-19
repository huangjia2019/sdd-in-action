---
name: analyzer
description: Reads collector output · tags each item with 3-dimension labels · writes knowledge/tagged/{date}.json
tools: [Read, Write]
---

# Analyzer Agent

> 本文件由 `specs/issues/02-analyzer.md` 派生
> 不要直接修改 · 改 issue 再重新派生
> 对应 issue 的 Acceptance Criteria · 依赖 Issue #01 Collector

## 职责

监听 `knowledge/raw/{date}.collector.done` · 读 raw · 对每一条打 3 维度标签（tech_category / innovation_level / difficulty）和 confidence · 输出 `knowledge/tagged/{date}.json`（schema: [specs/schemas/analyzer-output.json](../../specs/schemas/analyzer-output.json)）。

## 执行流程

1. 检查 `knowledge/raw/{date}.collector.done` · 不存在则退出（上游失败或未触发）
2. 检查 `knowledge/tagged/{date}.analyzer.done` · 存在则跳过（幂等）
3. 读 `knowledge/raw/{date}.json`
4. 逐条调 LLM 打标签 · 得到 3 维度 + confidence
5. confidence < 0.6 的条目标记为需人工复核（Week 3 N11 实现队列）
6. JSON Schema 校验
7. 写 `knowledge/tagged/{date}.json`
8. `touch {date}.analyzer.done`

## Failure Mode

按 § C2：

- LLM 返回格式错（不符 schema）· retry 1 次 · 再错则该条目标记 `confidence=0` · 继续处理其他条目
- API key 错 · 立即失败 · 不 retry
- rate limit · 指数退避 · 最多 3 次
- 整体失败 · 不阻塞其他天（今日 skip · 不影响明日）

## 不做什么

- 不调网络（只读本地 raw · 不二次抓取）
- 不写 markdown（organizer 的职责）
- 不处理 confidence < 0.6 的人工复核（标记即可）
