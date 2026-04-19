# Issue #02 · Analyzer Agent

> Week 1 · 第 3 节 · to-issues 展开产物（参考版 v1.0）
> 源自 [../agents-prd.md](../agents-prd.md)

## Depends on

- [Issue #01 · Collector](./01-collector.md) — 必须先产出 `knowledge/raw/{date}.json` + `.collector.done`

## Description

读取 `knowledge/raw/{date}.json`，对每条数据用 LLM 打 3 维度标签（tech / innovation / difficulty），写入 `knowledge/tagged/{date}.json`。

## Trigger

- 监听 `knowledge/raw/{date}.collector.done` 文件出现
- 或手动运行 `python -m agents.analyzer --date 2026-04-20`

## Acceptance Criteria

### 数据契约

- [ ] 输入：`knowledge/raw/{date}.json`（符合 collector-output schema）
- [ ] 输出：`knowledge/tagged/{date}.json`
- [ ] 每条数据新增 `labels: {tech, innovation, difficulty}` 字段
- [ ] 输出符合 [schemas/analyzer-output.json](../schemas/analyzer-output.json)

### 完成标记

- [ ] 写完 tagged 数据后 `touch knowledge/tagged/{date}.analyzer.done`

### 失败处理

- [ ] LLM 调用失败 retry 1 次
- [ ] 最终失败写 `knowledge/tagged/{date}.analyzer.failed`
- [ ] 今日 skip · 不阻塞后续日期
- [ ] 写入 `knowledge/incidents/{date}.md`

### 幂等性

- [ ] 执行前检查 `.analyzer.done` · 存在则跳过
- [ ] `--force` 先删除再执行

### 可观测性

- [ ] 启动 / 结束写 `knowledge/logs/{date}.log`
- [ ] 日志含 `start_ts` / `end_ts` / `tagged_count` / `llm_cost`
