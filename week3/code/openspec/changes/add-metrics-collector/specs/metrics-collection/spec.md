## ADDED Requirements

### Requirement: KBState SHALL include a metrics field
KBState MUST define `metrics` as `list[dict]`, initialized to `[]`, storing per-node execution records accumulated across the workflow run.

#### Scenario: Initial state has empty metrics
- **WHEN** a new workflow run starts with initial state
- **THEN** `state["metrics"]` SHALL be an empty list

#### Scenario: Metrics accumulate across nodes
- **WHEN** the plan node completes, then the collect node completes
- **THEN** `state["metrics"]` SHALL contain exactly 2 records in node execution order

### Requirement: track_metrics decorator SHALL record per-node execution metrics
A `track_metrics(node_name: str)` decorator MUST wrap LangGraph node functions transparently. For each wrapped node invocation, it SHALL append one metrics record to `state["metrics"]` containing: `node`, `start_time`, `end_time`, `latency_ms`, `status`, `cost_snapshot`, `iteration`.

#### Scenario: Successful node execution
- **WHEN** a wrapped node completes without exception
- **THEN** a record SHALL be appended with `status: "success"` and `latency_ms` equal to the wall-clock execution time of the node

#### Scenario: Node raises exception
- **WHEN** a wrapped node raises an exception during execution
- **THEN** a record SHALL be appended with `status: "error"` and `latency_ms` equal to the time until the exception
- **AND** the exception SHALL propagate to LangGraph for normal error handling

#### Scenario: Decorator does not modify node return value
- **WHEN** a wrapped node returns `{"plan": {...}, "cost_tracker": {...}}`
- **THEN** the wrapper SHALL return the same dict with `"metrics"` merged in (appended record)
- **AND** all original fields from the node SHALL be preserved unchanged

### Requirement: flush_metrics_node SHALL write metrics to disk on both exit paths
A `flush_metrics_node` MUST be registered in the graph after `organize` and after `human_flag`, so that metrics are written before every `END`. The output file SHALL be `knowledge/metrics/metrics-{timestamp}.json`.

#### Scenario: Normal workflow completion
- **WHEN** the workflow reaches `organize` and then `flush_metrics_node`
- **THEN** a JSON file SHALL be written to `knowledge/metrics/metrics-{timestamp}.json` containing all accumulated metrics records and a summary

#### Scenario: Human flag workflow completion
- **WHEN** the workflow reaches `human_flag` and then `flush_metrics_node`
- **THEN** a JSON file SHALL be written to `knowledge/metrics/` containing all metrics records accumulated up to that point

### Requirement: Metrics output SHALL follow a structured JSON schema
The output file MUST contain: `workflow_start` (ISO 8601 UTC), `strategy` (from plan), `records` (list of per-node metric dicts), and `summary` (aggregated totals including `total_latency_ms`, `total_cost_yuan`, `node_count`, `review_iterations`, `errors`).

#### Scenario: Output contains correct summary
- **WHEN** a workflow completes with 8 node records, 2 review iterations, and 0 errors
- **THEN** `summary.node_count` SHALL be 8
- **AND** `summary.review_iterations` SHALL be 2
- **AND** `summary.errors` SHALL be 0
- **AND** `summary.total_latency_ms` SHALL equal the sum of all `latency_ms` values in records

### Requirement: Metrics write failure SHALL NOT block workflow completion
If `flush_metrics_node` fails to write the metrics file (e.g., disk full, permission denied), it MUST log a warning to stderr and return successfully without raising an exception, so the workflow reaches END normally.

#### Scenario: Write fails due to permissions
- **WHEN** `flush_metrics_node` cannot write to `knowledge/metrics/` due to a permission error
- **THEN** the node SHALL print a warning message to stderr
- **AND** the node SHALL return an empty state delta (not raise)
- **AND** the workflow SHALL proceed to END
