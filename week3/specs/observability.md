# spec · 多 Agent 可观测性 · 参考版 v1.0

> Week 3 · 第 12 节 · B 路产出
> BMAD QA 角色 review 后的终态 · 从"可能出问题"倒推 trace span

## 设计原则

- span 从"最可能出问题的地方"倒推 · 不从代码结构正推
- 每个 span 带统一 attribute · 支持按任意维度 group by

## 必须暴露的 span

### collector（3 个）

- `fetch.github_trending`
  - attr: `top_n` · `filter_count`
  - 为什么：网络抖动导致 fetch 拿不全
- `filter.by_topics`
  - attr: `matched_count` · `filtered_count`
  - 为什么：topic 规则变了导致 matched_count 断崖
- `dedup`
  - attr: `before_count` · `after_count`
  - 为什么：去重逻辑错导致重复

### analyzer（3 个）

- `load_raw`
  - attr: `file_path` · `item_count`
- `classify`
  - attr: `confidence_score` · `label_3d`
  - 为什么：confidence 分布异常是问题早期信号
- `low_confidence_branch`
  - attr: `threshold` · `triggered_count`
  - 为什么：质量阈值功能的观测入口（对齐 `planning-review.md`）

### organizer（2 个）

- `assemble`
  - attr: `section_count`
- `format_markdown`
  - attr: `output_bytes`

## 统一 attribute（每个 span 必带）

- `agent_name` · 当前 agent 名字
- `day_partition` · 处理的日期 · `YYYY-MM-DD`
- `pipeline_run_id` · 本次 pipeline 的全局 UUID

## 不做什么

- 不在 span 里记录用户数据（隐私）
- 不记录整个 request/response body（太大 · 只记关键 attr）
- 不做 tracing sampling（全量 · 本项目量不大）

## 导出目标

- OTLP endpoint（默认 `http://localhost:4318`）
- 本地开发可用 Jaeger · 生产对接公司的 trace collector

## 边界 & 验收

- 所有 8 个 span 都能在 Jaeger 里看到
- span attribute 命名严格对齐本 spec（写单元测试断言）
- span 创建失败不阻塞主流程（try/except 包装）

## 怎么验证

- 跑一次完整 pipeline · 去 Jaeger 看应有 8 个 span
- 统一 attribute 查询：按 `pipeline_run_id` 能聚合一次完整运行
- 单元测试覆盖所有 span 的存在性
