## 1. KBState & Data Model

- [x] 1.1 Add `metrics: list[dict]` field to KBState in `workflows/state.py`
- [x] 1.2 Update `initial_state` in `workflows/graph.py` `__main__` block to include `"metrics": []`
- [x] 1.3 Create `knowledge/metrics/` output directory (add `.gitkeep` so it's tracked)

## 2. Core Implementation

- [x] 2.1 Create `workflows/metrics_collector.py` with `track_metrics(node_name)` decorator that wraps node functions, records start/end/latency/status/cost_snapshot/iteration, and merges the record into the returned state delta
- [x] 2.2 Implement `flush_metrics_node(state)` that writes `state["metrics"]` to `knowledge/metrics/metrics-{timestamp}.json` with the structured schema (workflow_start, strategy, records, summary)
- [x] 2.3 Ensure flush failure prints warning to stderr and does not raise (return empty state delta)

## 3. Graph Integration

- [x] 3.1 Import `track_metrics` from `workflows.metrics_collector` in `workflows/graph.py`
- [x] 3.2 Wrap all 7 existing nodes with `track_metrics(...)` in `build_graph()` (plan, collect, analyze, review, revise, organize, human_flag)
- [x] 3.3 Register `flush_metrics` as a LangGraph node
- [x] 3.4 Replace `organize → END` with `organize → flush_metrics → END`
- [x] 3.5 Replace `human_flag → END` with `human_flag → flush_metrics → END`

## 4. Verification

- [x] 4.1 Run `python workflows/graph.py` and verify `knowledge/metrics/metrics-*.json` is created
- [x] 4.2 Verify output JSON contains `workflow_start`, `strategy`, `records[]` (one per node), and `summary` with correct aggregates
- [x] 4.3 Verify records have correct fields: `node`, `start_time`, `end_time`, `latency_ms`, `status`, `cost_snapshot`, `iteration`

## 5. Backward Compatibility

- [x] 5.1 Add `track_metrics` to `workflows/nodes.py` re-exports (consistent with existing convention)
- [x] 5.2 Verify `from workflows.nodes import planner_node` still works (no import breakage)
