## Why

V3 的 7-node LangGraph 工作流目前没有可观测性（observability）。无法知道每个节点的耗时、成本分布、通过/失败状态，以及 Reviewer→Revise 循环的迭代次数。调试靠 print，优化靠猜。加一个 Metrics Collector 节点来系统性地记录这些指标，为 dashboard 和成本优化提供数据基础。

## What Changes

- **新增 ⑧ Metrics Collector 节点**：在每个节点执行完成后记录 latency / cost / status / iteration 快照
- **扩展 KBState**：新增 `metrics` 字段（`list[dict]`），存储所有节点的指标记录
- **输出 dashboard-ready 数据**：工作流结束时将 `metrics` 写入 `knowledge/metrics/` 目录供外部消费
- **不破坏现有 routing**：Metrics Collector 采用 observer 模式（in-graph node，放在终点前），不改变现有的 3 路条件边

## Capabilities

### New Capabilities
- `metrics-collection`: 在每个 LangGraph 节点完成后记录指标快照（node_name, start_time, end_time, latency_ms, status, cost_tracker, iteration），并在工作流正常终点前（organize 之后）输出为 JSON 文件

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- `workflows/state.py` — KBState 新增 `metrics: list[dict]` 字段
- `workflows/graph.py` — 注册 `metrics_collector` 节点，在 `organize` 之后插入收集点，再路由到 END
- 新增 `workflows/metrics_collector.py` — ⑧ 节点实现，负责追加指标记录 + 序列化输出
- 新增 `knowledge/metrics/` — 输出目录，存储 `metrics-{timestamp}.json`
