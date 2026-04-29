## Context

V3 工作流当前有 7 个节点（Plan → Collect → Analyze → Review → {Organize, Revise, HumanFlag}），每个节点是独立的 Python 函数，通过 LangGraph 编排。没有任何机制记录每个节点的执行耗时、成本快照、成功/失败状态或迭代轮次。调试依赖 `print()` 输出，瓶颈定位和成本归因只能手工推算。

约束：
- 必须遵循项目约定：一个 Agent 一个文件，Agent 间仅通过 KBState 通信
- 不能破坏现有的 3 路条件路由 (`route_after_review`)
- 所有成本记录单位：人民币元

## Goals / Non-Goals

**Goals:**
- 每次工作流运行后输出一份结构化 metrics JSON，包含每个节点的 latency / cost / status / iteration
- 对现有 7 个节点零侵入（不修改它们的内部实现）
- 工作流正常终点和异常终点都能输出 metrics
- Metrics 写入 `knowledge/metrics/` 目录，按时间戳命名

**Non-Goals:**
- 不实现实时 dashboard UI（只产出 JSON 数据文件）
- 不引入外部监控库（Prometheus / OpenTelemetry）——保持零外部依赖
- 不对 Analyzer 或 Collector 内部进行细粒度插桩
- 不提供 metrics 历史聚合或趋势分析

## Decisions

### Decision 1: Decorator 包装器（而非 in-graph routing）

**选择**：用 Python decorator `track_metrics(node_name)` 透明包装每个 LangGraph 节点函数，在 `build_graph()` 里统一注册。

**理由**：
- 现有 7 个节点的代码不需要任何修改（零侵入）
- 不需要在图中新增 7 条 → metrics → return 的边，保持图结构简单
- decorator 天然捕获 `try/finally` 语义：即使节点抛异常也能记录这次失败
- 符合项目"一 Agent 一文件"约定——metrics 逻辑完全隔离在 `metrics_collector.py`

**替代方案**：
- *每个节点后插一个 metrics 节点*：会增加 7 个节点和 7 条条件边，图拓扑变复杂，且影响 `route_after_review` 的清晰性 → 拒绝
- *在 `app.stream()` 外层 Hook*：LangGraph 的 stream API 给的是 state delta，拿不到节点级别的 wall-clock 时间 → 无法实现

### Decision 2: 单文件 `metrics_collector.py` 包含 decorator + flush 节点

**选择**：`workflows/metrics_collector.py` 包含两个导出：`track_metrics` decorator（每个节点调用时用）和 `flush_metrics_node`（作为 LangGraph 节点注册）。

**理由**：
- Flush 操作必须在图内完成（需要访问最终 state），不能在图外做
- Decorator 和 flush 逻辑高度内聚，放在一个文件里方便维护

### Decision 3: Metrics 写入时机——正常和异常两条路径都写

**选择**：`flush_metrics_node` 放在 `organize → END` 之前。同时在 `human_flag → END` 之前也插入 flush 节点（或一个共享节点）。正常路径和异常路径都输出 metrics。

**图拓扑变化**：
```
原来:  organize → END    human_flag → END
现在:  organize → flush_metrics → END
       human_flag → flush_metrics → END
```

### Decision 4: KBState `metrics` 字段结构

```python
metrics: list[dict]

# 每条记录:
{
    "node": "collect",                              # 节点名
    "start_time": "2026-04-30T10:00:00.000Z",       # ISO 8601 UTC
    "end_time": "2026-04-30T10:00:02.150Z",
    "latency_ms": 2150.0,                           # 毫秒，保留 2 位小数
    "status": "success",                             # "success" | "error"
    "cost_snapshot": {"total_cost_yuan": 0.05},      # 该节点结束后累计 cost
    "iteration": 0,                                  # 当前 iteration（仅 Reviewer/Reviser 循环有意义）
}
```

### Decision 5: 输出格式

输出到 `knowledge/metrics/metrics-{YYYY-MM-DD-HHmmss}.json`：

```json
{
  "workflow_start": "2026-04-30T10:00:00.000Z",
  "strategy": "standard",
  "records": [ ... ],
  "summary": {
    "total_latency_ms": 12345.0,
    "total_cost_yuan": 0.12,
    "node_count": 8,
    "review_iterations": 2,
    "errors": 0
  }
}
```

## Risks / Trade-offs

- **[风险] Decorator 在异常时依赖 `finally` 块写入 metrics → 如果 Python 进程被 SIGKILL，本次运行的 metrics 丢失**
  → 缓解：这是 Python 层面的固有限制，不做额外处理。依赖 LangGraph 的错误处理让节点最终走到 human_flag。

- **[风险] `flush_metrics_node` 写入磁盘失败（磁盘满/权限问题）**
  → 缓解：写文件失败时打印 warning 到 stderr，不阻塞工作流正常结束。不会因 observability 故障导致业务中断。

- **[权衡] metrics 累积在 state 里随图传递，但 LangGraph 的 state 不是为大数据设计的**
  → 每次运行 ~7-15 条记录（含 review 循环），每条 ~200 bytes，总量 < 5KB，不影响性能。
