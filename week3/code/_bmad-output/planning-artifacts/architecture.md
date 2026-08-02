---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd-metrics-collection.md
  - AGENTS.md
workflowType: 'architecture'
project_name: 'KM系统 · V3 Multi-Agent 知识库'
user_name: 'HuangJia'
date: '2026-04-29'
lastStep: 8
status: 'complete'
completedAt: '2026-04-29'
authoritative_version: 'v0.2'
related_change: 'add-metrics-collector'
---

# Architecture Decision Document

> ⚠️ **以 v0.2 为准 · v0.1 保留供学员对照过度设计的反例。** 跳到文末 [v0.2 Course Correction](#v02--course-correction-2026-04-29) 看正确方案。

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

**v0.1 内容（step-1 ~ step-7 各章节）保留作为教学反例 ——** 展示如何在不严守约束时陷入"全套交付"思维。**实施请以文末 v0.2 章节为准。**

## Project Context Analysis

### Requirements Overview

**Functional Requirements (from PRD v0.1):**
- FR1 — 节点状态采集：7 个 LangGraph node 的 success / failure / stuck，每条粒度
- FR2 — Review 迭代数采集：Reviewer ↔ Reviser 循环次数（每条）
- FR3 — Agent token 消耗采集：按 Agent 拆分，daily 总量 + 单条均值（人民币元）
- FR4 — Daily throughput 计数：实际入库数 vs 目标 20
- FR5 — End-to-end latency 采集：单条从触发到入库的 p50 / p95
- FR6 — 双视图呈现：工程视图（Tech Lead，节点级粒度）+ 业务视图（运营，业务聚合）

**Non-Functional Requirements:**
- NFR1 — 采集开销 < 5% pipeline latency（硬指标，强约束同步/异步决策）
- NFR2 — 排障时长 ≤ 5 分钟（驱动 dashboard 易用性，节点级 drill-down 必须）
- NFR3 — 运营自助率 = 100%（驱动部署形态，必须无需工程介入即可访问）
- NFR4 — MVP 2 周交付（强约束 boring tech 选择，禁奢侈方案）
- NFR5 — 成本单位人民币元（业务方语言，需要 token → CNY 换算层）

### Scale & Complexity

- 数据规模：7 节点 × ~20 条/日 × 5 指标 ≈ 每日 700 数据点（极小）
- 用户：2 类（Tech Lead / 内容运营）、内部网络、单组织、无多租户
- 实时性：daily / hourly 批量足够，**已显式排除**实时流
- 集成范围：仅 V3 workflow 内部，**不跨系统**

- Primary domain: observability backend + lightweight read-only dashboard
- Complexity level: low-to-medium
- Estimated architectural components: 3~5（采集器、存储、查询/聚合、dashboard、可选 OpenSpec capability 层）

### Technical Constraints & Dependencies

**From AGENTS.md (hard constraints):**
- C1 — 必须独立文件：`workflows/metrics_collector.py`，禁止合入现有节点
- C2 — 仅通过 KBState 通信：禁止跨节点 import
- C3 — 不能破坏 Reviewer 3 路条件边（pass / fail<max / >=max）
- C4 — 职责隔离：metrics_collector 只采集，不评分、不修改、不路由
- C5 — 必须以 OpenSpec change 形式落地：`openspec/changes/metrics-collection/`
- C6 — 数据契约决策：metrics 字段是否进 KBState 仍开放（影响 spec delta 形态）

**From PRD (open):**
- O1 — 存储/展示栈未锁定（候选：SQLite+Streamlit / Prometheus+Grafana / JSONL+Notion）
- O2 — 工程视图 vs 运营视图优先级冲突时的仲裁规则
- O3 — Daily throughput 20 条是硬 SLA 还是观察值

### Cross-Cutting Concerns Identified

- **数据契约管理**：KBState 是否扩字段，决定 OpenSpec change 的 spec delta 形态与回滚成本
- **失败隔离**：metrics 采集出错绝不能拖垮主 pipeline（必须 try/except + 兜底降级）
- **成本归因**：按 Agent 维度聚合 token，需要在每个 LLM 调用点统一打点入口
- **双视图聚合**：同一份采集底层 → 衍生工程视图（节点级）+ 业务视图（每日聚合）的查询/视图层
- **时间口径**：单条流水可能跨 retry 循环，"开始/结束"时间戳定义需要明确

## Starter Template Evaluation

### Project Type: Brownfield Feature, Not Greenfield

This is a **feature being added to a running codebase**, not a new project initialization.
There is no starter template to evaluate. The existing V3 codebase serves as the foundation.

### Existing Foundation (Inherited Scaffolding)

**Language & Runtime:**
- Python 3.11+
- 已有依赖（`requirements.txt`）：`langgraph >=0.2.0`、`langchain-core >=0.3.0`、`openai >=1.0.0`、`pytest >=8.0.0`、`pytest-asyncio >=0.23.0`、`python-dotenv >=1.0.0`

**Workflow Engine:**
- LangGraph 有状态图（7 个 node + 3 路条件边 + KBState 数据总线）

**Code Organization Conventions (from AGENTS.md, hard-locked):**
- 一 Agent 一文件：`workflows/{role}.py`，禁止合并职责
- Agent 间仅通过 `KBState`（TypedDict, 9 字段）通信，禁止跨节点 import
- 通用 Agent 模式（Router / Supervisor）放 `patterns/`，与主流程解耦
- 生产加固代码（cost guard / security / eval）放 `tests/`

**Spec / Change Management:**
- OpenSpec change 流程：所有新能力以 `openspec/changes/<name>/` 形式落地，含 spec delta（ADDED / MODIFIED Requirements）
- 本 feature 对应 change 名：`metrics-collection`

**Testing Convention:**
- pytest + pytest-asyncio
- LLM-as-Judge 评估（`tests/eval_test.py`）

**LLM Client:**
- OpenAI 兼容端点（DeepSeek / Qwen / OpenAI）via `workflows/model_client.py`

### Anticipated Additions (Deferred to Step-04 Decisions)

下列依赖**可能**会进 `requirements.txt`，但**具体选哪个、什么版本，留到 step-04 架构决策时再敲**：

| 用途 | 候选（仅列出，不预选） | 决策时机 |
|------|---------------------|---------|
| **指标存储** | `sqlite3`(stdlib) / JSONL+Pandas / `prometheus_client` | step-04 决策 1 |
| **Dashboard** | Streamlit / Plotly Dash / FastAPI+静态前端 / Notion 嵌入 | step-04 决策 2 |
| **Token→CNY 换算** | 自写小函数 vs `tiktoken` 计 token 后换算 | step-04 决策 3 |
| **数据契约扩展** | KBState 新增 `metrics: dict` 字段（侵入） vs 旁路写盘（不扩） | step-04 决策 4 |

### Initialization Command

```bash
# 项目已初始化，本 feature 不需要重新 init
# 后续依赖追加将通过 PR 修改 requirements.txt：
pip install -r requirements.txt
```

### Architectural Decisions Provided by Existing Codebase (Not Subject to Re-evaluation)

| Aspect | Decided By Existing Codebase |
|--------|----------------------------|
| Language | Python 3.11+ |
| Workflow runtime | LangGraph |
| State sharing | KBState (TypedDict, 9 fields) |
| File-per-Agent | Yes, hard-enforced |
| Spec management | OpenSpec change lifecycle |
| Testing | pytest + LLM-as-Judge |
| LLM client | OpenAI-compatible endpoint |
| Routing logic | LangGraph conditional edges (3-route Reviewer fan-out) |

**Note:** 本 feature 的实施第一步**不是** project init（已存在），而是创建 `openspec/changes/metrics-collection/` change scaffold。

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- D1 — Collection mechanism (decorator + LLM client wrapper)
- D2 — State contract (side-channel, KBState untouched)
- D3 — Storage backend (SQLite + WAL)
- D4 — Write timing (synchronous direct-write with failure isolation)

**Important Decisions (Shape Architecture):**
- D5 — Dashboard tool (Streamlit 1.57.0 + systemd)
- D6 — Token→CNY conversion (double-write: raw tokens + USD + CNY)
- D7 — Time convention (E2E + per-node cumulative + visit_count)

**Deferred Decisions (Post-MVP):**
- Backfill tool for re-deriving costs when rates change (YAGNI; build when first needed)
- ContextVar/thread-local migration of MetricsBuffer (only if parallel pipeline runs are introduced)
- Per-visit drill-down event log (only if PRD nice-to-have promoted to must-have)

### Default Step-04 Categories: Applicability

| Default Category | Status for This Feature |
|------------------|------------------------|
| Data Architecture | ✅ Decided (D3 + D7 schema) |
| Authentication & Security | ❌ N/A — internal network, single-organization, no auth needed for MVP |
| API & Communication | ❌ N/A — no public API; metrics flow via in-process buffer + SQLite read |
| Frontend Architecture | ✅ Decided (D5 — Streamlit handles state internally) |
| Infrastructure & Deployment | ✅ Decided (D5 — systemd unit on internal server) |

The categories in this section are remapped to D1–D7 because the feature is observability tooling, not a web app.

### D1 — Collection Mechanism: Decorator + LLM Client Wrapper

- **Decision:** `@track_metrics(node_name)` decorator applied to each node function. `model_client.py` wrapper captures token/cost at LLM call boundary.
- **Rationale:** Pure Python pattern, framework-agnostic, file-per-Agent friendly, testable. LangGraph callbacks rejected to avoid binding to internal API.
- **Affects:**
  - new: `workflows/metrics_collector.py`
  - modified: `workflows/model_client.py` (wrap LLM calls)
  - modified: each of the 7 node files (one-line decorator)
  - modified: `workflows/graph.py` (build-time guard assertion that all nodes are decorated)
- **Provided by Starter:** No (new)
- **Revisit Trigger:** If decorator stack interferes with LangGraph async debugging — switch to LangGraph events/callbacks API after verifying it can read KBState fields.

### D2 — State Contract: Side-Channel (KBState Untouched)

- **Decision:** Metrics flow via in-process `MetricsBuffer` singleton, NOT through KBState.
- **Rationale:** YAGNI — no current FR requires metrics-aware routing. Keeps KBState 9-field contract intact. OpenSpec change becomes pure ADDED capability, not MODIFIED Requirements.
- **Assumption (must be documented in code):** V3 runs as single-process daily batch. If parallel/concurrent runs are introduced, `MetricsBuffer` must migrate to `contextvars.ContextVar` or thread-local.
- **Affects:**
  - NOT modified: `workflows/state.py`
  - new: `workflows/metrics_collector.py` (owns buffer)
- **Provided by Starter:** No
- **Revisit Trigger:** When a metrics-aware routing or circuit-breaker FR is added (e.g., "skip Reviser if token budget exceeded").

### D3 — Storage Backend: SQLite + WAL Mode

- **Decision:** SQLite (Python stdlib) with `PRAGMA journal_mode=WAL`. Database file at `data/metrics.db` (gitignored).
- **Rationale:** Zero infrastructure cost, full SQL queryability, ACID, single-file backup, WAL allows concurrent reader (dashboard) + writer (pipeline) without lock contention. Data scale (~500 rows/day) is far below SQLite's design limits.
- **Schema:**

```sql
CREATE TABLE IF NOT EXISTS piece_runs (
    piece_id      TEXT PRIMARY KEY,
    e2e_start     TEXT NOT NULL,        -- ISO 8601
    e2e_end       TEXT,
    e2e_ms        INTEGER,
    final_status  TEXT                  -- pass | human_flagged | failed
);

CREATE TABLE IF NOT EXISTS piece_node_stats (
    piece_id      TEXT NOT NULL,
    node_name     TEXT NOT NULL,
    total_ms      INTEGER NOT NULL,
    visit_count   INTEGER NOT NULL,
    last_status   TEXT,
    last_exit_at  TEXT,
    PRIMARY KEY (piece_id, node_name)
);

CREATE TABLE IF NOT EXISTS token_usage (
    piece_id          TEXT NOT NULL,
    agent_name        TEXT NOT NULL,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    cost_usd          REAL,             -- D6 double-write
    cost_cny          REAL,             -- D6 double-write
    recorded_at       TEXT NOT NULL,
    PRIMARY KEY (piece_id, agent_name, recorded_at)
);

CREATE INDEX IF NOT EXISTS idx_piece_runs_date ON piece_runs(e2e_start);
CREATE INDEX IF NOT EXISTS idx_token_recorded ON token_usage(recorded_at);
```

- **Affects:** `workflows/metrics_collector.py` (DDL + writer), `.gitignore` (add `data/metrics.db`)
- **Provided by Starter:** No
- **Revisit Trigger:** When data volume exceeds ~100M rows or when concurrent multi-process writers are needed → migrate to PostgreSQL or DuckDB.

### D4 — Write Timing: Synchronous Direct-Write with Failure Isolation

- **Decision:** Synchronous append-only writes to SQLite at each metric point. WAL mode + reasonable indexing. **Hard rule:** all metric write calls wrapped in `try/except` that logs and swallows errors (never propagates).
- **Rationale:** Math says ~400 writes/day × ~1ms each = <0.5s/day total → <0.05% pipeline overhead. NFR1 (<5%) is satisfied with margin of 100×. No need for async complexity. Sync writes give crash-safety for free.
- **Failure isolation rule (mandatory):**

```python
# pseudocode
def _safe_record(**kwargs):
    """Metrics write failures must NEVER propagate to pipeline."""
    try:
        _write_to_sqlite(**kwargs)
    except Exception as e:
        logger.warning("metrics write failed; dropping record: %s", e)
        # silently swallow — pipeline must continue
```

- **Two-layer error contract:**
  - Business exceptions in node code → propagate normally (LangGraph routes to HumanFlag)
  - Metrics infrastructure exceptions → swallow + log (cross-cutting concern from step-2)

- **Affects:** All metric recording code paths in `workflows/metrics_collector.py` and `workflows/model_client.py`
- **Provided by Starter:** No
- **Revisit Trigger:** If pipeline overhead measurement (post-MVP) shows >2% — likely indicates lock contention or schema issue, not the sync/async axis.

### D5 — Dashboard Tool: Streamlit 1.57.0 + systemd Deployment

- **Decision:** Streamlit `>=1.57.0,<2.0.0` (latest stable as of 2026-04-28). Deployed as a systemd service on internal-network server.
- **Rationale:** Python-native, single-file dashboards, fastest path from SQLite to chart. `st.menu_button` and updated dataframe selection (1.55+) provide good drill-down UX for engineering view. Internal access via URL bookmark satisfies NFR3 (100% self-serve).
- **Layout:** Two views via `st.navigation`:
  - **Engineering view:** 7-node status grid, e2e latency p50/p95, single-piece trace table, failure list
  - **Operations view:** today's throughput vs target 20, review iteration distribution, 7-day cost trend, top-N expensive agents
- **File structure:**

```
dashboards/
├── app.py                       # entry: st.navigation
├── views/
│   ├── engineering.py
│   └── operations.py
├── queries.py                   # all SQL centralized
└── systemd/
    └── km-dashboard.service     # one-time deployment unit
```

- **New dependency:** `streamlit>=1.57.0,<2.0.0` (transitively pulls pandas, altair)
- **Provided by Starter:** No
- **Revisit Trigger:** If operations team requests features Streamlit cannot deliver (e.g., custom interactive widgets, complex auth, embedding in another product).

### D6 — Token→CNY Conversion: Double-Write at Collection Time + Rates as Code

- **Decision:** Store raw `prompt_tokens` and `completion_tokens` (immutable truth). At collection time, also compute and store `cost_usd` (model rates) and `cost_cny` (USD × FX rate). Rates live in `workflows/llm_rates.py` as Python constants.
- **Rationale:** Real-world driver — DeepSeek V4 Pro pricing changes 2026-05-05 ($0.435 → $1.74). Storing raw tokens keeps historical re-derivation possible; storing snapshot CNY makes dashboard queries fast. Double-storage cost negligible (2 extra REAL columns × ~400 rows/day).
- **Rates module:**

```python
# workflows/llm_rates.py

USD_TO_CNY = 7.20  # team-agreed snapshot, manual update on FX swing

MODEL_RATES = {
    # USD per 1M tokens, separate input / output
    "deepseek-chat-v4-flash": {"in": 0.14,  "out": 0.28},
    "deepseek-chat-v4-pro":   {"in": 0.435, "out": 0.87},   # NOTE: rises to 1.74/3.48 on 2026-05-05
    "qwen-max":               {"in": 0.42,  "out": 1.68},
}

def calc_cost(model: str, in_tok: int, out_tok: int) -> tuple[float, float]:
    """Return (usd, cny). Unknown model returns (0,0); caller logs warning."""
    if model not in MODEL_RATES:
        return (0.0, 0.0)
    r = MODEL_RATES[model]
    usd = (in_tok / 1_000_000) * r["in"] + (out_tok / 1_000_000) * r["out"]
    return (usd, usd * USD_TO_CNY)
```

- **Why Python module not YAML:** No new dependency (`pyyaml` avoided). Rate changes go through git, providing audit trail.
- **Backfill tool for rate changes:** **Deferred** (YAGNI). When first needed, write `tools/backfill_costs.py` to re-derive `cost_usd / cost_cny` from raw token counts under new rates.
- **Affects:** new `workflows/llm_rates.py`, `workflows/model_client.py` (calls `calc_cost`)
- **Provided by Starter:** No
- **Revisit Trigger:** When non-engineering personnel need to edit rates without a code review, OR when rate changes become frequent enough that PR-based updates feel heavy.

### D7 — Time Convention: E2E + Per-Node Cumulative + Visit Count

- **Decision:** Two-layer timing schema (already in D3 schema):
  - `piece_runs`: one row per piece with end-to-end timing
  - `piece_node_stats`: one row per (piece, node) with accumulated `total_ms` and `visit_count` across all entries (handles Reviewer↔Reviser loop)
- **Key time-stamping definitions:**
  - `e2e_start`: timestamp at Planner node entry
  - `e2e_end`: timestamp at Organizer entry (normal terminal) OR HumanFlag entry (abnormal terminal)
  - `visit_count`: incremented on each node entry — Reviewer in a `review→revise→review` loop has `visit_count = 2`
  - `last_status`: status at the most recent exit from this node
- **Direct PRD metric mappings:**
  - M1 (节点状态分布) ← `SELECT node_name, last_status, COUNT(*) FROM piece_node_stats GROUP BY ...`
  - M2 (Review 通过迭代数) ← `SELECT AVG(visit_count) FROM piece_node_stats WHERE node_name='reviewer'`
  - M3 (Agent token 消耗) ← `SELECT agent_name, SUM(cost_cny) FROM token_usage GROUP BY agent_name, DATE(recorded_at)`
  - M4 (Daily Throughput) ← `SELECT DATE(e2e_end), COUNT(*) FROM piece_runs WHERE final_status='pass' GROUP BY DATE(e2e_end)`
  - M5 (E2E latency p50/p95) ← `SELECT * FROM piece_runs ORDER BY e2e_ms` then percentile in dashboard
- **Time format throughout:** ISO 8601 strings stored as `TEXT` in SQLite (consistent with stdlib `datetime.isoformat()`).
- **Affects:** schema (D3), all `_safe_record` writes, dashboard queries
- **Provided by Starter:** No
- **Revisit Trigger:** When per-visit-level drill-down is promoted from nice-to-have to must-have → add `node_visit_events` table without migrating old rows.

### Decision Impact Analysis

**Implementation Sequence (build order):**

1. Create `openspec/changes/metrics-collection/` change scaffold with proposal.md, tasks.md, specs/.
2. Add `workflows/llm_rates.py` (D6) + tests — foundational, no V3 changes yet.
3. Add `workflows/metrics_collector.py` (D1, D3, D4) with decorator, MetricsBuffer, SQLite writer + DDL + tests.
4. Modify `workflows/model_client.py` (D1+D6) to capture token usage and call `calc_cost`.
5. Add `@track_metrics(...)` to each of the 7 node files in `workflows/`.
6. Add build-time guard in `workflows/graph.py` asserting all nodes are decorated.
7. Add `dashboards/` (D5) with `app.py`, two views, `queries.py`, `systemd/km-dashboard.service`.
8. Update `requirements.txt` (+ streamlit), `.gitignore` (+ data/metrics.db).
9. End-to-end test: run pipeline → verify metrics rows → verify dashboard renders.

**Cross-Component Dependencies:**

- `metrics_collector.py` depends on `llm_rates.py` (calls `calc_cost` indirectly via model_client wrapper).
- All 7 node files depend on `metrics_collector.@track_metrics`.
- `graph.py` build assertion depends on `metrics_collector.is_tracked()` introspection helper.
- Dashboard depends on SQLite schema being initialized (handled by `metrics_collector` on first import).
- `model_client.py` depends on `llm_rates.calc_cost` and `metrics_collector.record_token_usage`.

**OpenSpec Change Spec Delta (final):**

```
ADDED capability: metrics-collection
  Req-1: Decorator-based node instrumentation captures latency, status,
         and visit count for all 7 LangGraph nodes. Build-time assertion
         enforces full coverage.
  Req-2: LLM client wrapper captures prompt_tokens, completion_tokens,
         and computes USD/CNY cost using rates from workflows/llm_rates.py.
  Req-3: SQLite persistence with WAL mode at data/metrics.db. Schema:
         piece_runs, piece_node_stats, token_usage. ISO 8601 time format.
  Req-4: Failure isolation — all metrics infrastructure errors logged
         at WARNING level and silently swallowed. Pipeline must continue.
  Req-5: Streamlit 1.57+ dashboard at dashboards/ with engineering and
         operations views. Deployed as systemd service.
  Req-6: Token rate configuration in workflows/llm_rates.py, updated
         via PR. Backfill tool deferred (YAGNI).

NOT MODIFIED: workflows/state.py (KBState 9-field contract preserved)
```

## Implementation Patterns & Consistency Rules

### Scope of This Section

This feature has narrow conflict surface area:
- No public API → no REST/GraphQL naming patterns needed
- No SPA frontend → no component/state pattern needed (Streamlit handles its own state)
- No DB ORM → schema is hand-written DDL with explicit conventions
- Most file/test/Python naming conventions inherited from AGENTS.md and PEP 8

The patterns below cover only the genuinely undecided choices specific to metrics-collection.

### Inherited Conventions (Not Re-Decided)

| Convention | Source | Rule |
|-----------|--------|------|
| File naming | AGENTS.md + PEP 8 | snake_case `.py`, one Agent per file |
| Function/variable naming | PEP 8 | snake_case |
| Class naming | PEP 8 | PascalCase |
| Test file naming | pytest | `test_*.py` in `tests/` |
| LangGraph node fn signature | LangGraph + AGENTS.md | `def <name>_node(state: KBState) -> KBState` |

### P1 — Node Name Constants

One source of truth in `workflows/metrics_collector.py`:

```python
NODE_PLANNER = "planner"
NODE_COLLECTOR = "collector"
NODE_ANALYZER = "analyzer"
NODE_REVIEWER = "reviewer"
NODE_REVISER = "reviser"
NODE_ORGANIZER = "organizer"
NODE_HUMAN_FLAG = "human_flag"
```

**Usage:** `@track_metrics(node=NODE_PLANNER)` — never raw strings. Prevents typo drift across 7 node files; rename is a single-file change.

### P2 — Decorator Keyword Args

- ✅ `@track_metrics(node=NODE_PLANNER)`
- ❌ `@track_metrics(NODE_PLANNER)`

**Rationale:** keyword args document intent at call site and support future expansion (e.g., `metric_subset=...`) without breaking existing call sites.

### P3 — Buffer Access via Factory

- ✅ `from workflows.metrics_collector import get_buffer; buf = get_buffer()`
- ❌ `from workflows.metrics_collector import _buffer` (private leak)

**Rationale:** tests can monkey-patch `get_buffer`; future swap to `contextvars.ContextVar` is internal change only.

### P4 — Time Representation

- **In-memory:** `datetime.now(timezone.utc)` (timezone-aware, never naive)
- **DB:** ISO 8601 string via `.isoformat()`
- **Single conversion point:** the SQLite write layer

| Form | Verdict |
|------|---------|
| `datetime.now(timezone.utc).isoformat()` | ✅ |
| `datetime.utcnow()` | ❌ deprecated, naive |
| Unix timestamp integer in DB | ❌ |

### P5 — Failure Isolation Template (Mandatory)

```python
try:
    # any metrics infrastructure operation
    # (DB write, calc_cost on unknown model, etc.)
    ...
except Exception as e:
    logger.warning("metrics op failed; dropping: %s", e)
    # MUST NOT raise — pipeline must continue
```

- **Business exceptions** in node code: NOT wrapped — propagate normally so LangGraph routes to HumanFlag.
- ❌ Anti-pattern: `try / except / pass` (silent swallow without log)
- ❌ Anti-pattern: `try / except / raise CustomException` (still propagates)

### P6 — Logging

- **Logger init:** `logger = logging.getLogger(__name__)` per module
- **Resulting names:** `workflows.metrics_collector`, `workflows.llm_rates`, `dashboards.app`, etc.
- **Levels:**
  - WARNING — metrics write failures (and only this)
  - INFO — buffer flush, schema initialization, FX rate snapshot loaded
  - DEBUG — per-record writes (off by default; opt-in for debugging)
- **Lazy formatting:** `logger.warning("write failed: %s", e)` — never f-string

### P7 — SQL Centralization

- All SQL strings live in `dashboards/queries.py` as named constants
- View files call queries by name; never inline SQL
- **Rationale:** schema changes touch one file; tests can run query strings without spinning up Streamlit

### SQLite Schema Naming

- **Tables:** snake_case (`piece_runs`, `piece_node_stats`, `token_usage`)
- **Columns:** snake_case (`prompt_tokens`, `e2e_start`)
- **Primary keys:** explicit (composite or single), never auto-increment surrogate
- **Indexes:** `idx_<table>_<column>` (e.g., `idx_piece_runs_date`)

### Numeric Formats

- Latency `*_ms`: integer milliseconds
- Cost `cost_usd` / `cost_cny`: REAL, displayed at 4 decimals
- Token counts: integer

### MetricsBuffer Record Shape

- Records are plain `dict` — not dataclass, not Pydantic
- Required keys are snake_case, matching SQL column names
- **Rationale:** dict is sufficient for in-process buffering; dict→SQL serialization is direct; no new dependency

### Visit Count Semantics (Locked)

- `visit_count++` happens at node entry, BEFORE the try block. A node that raises still counts as a visit.
- `last_status` reflects exit reason: `success` (normal return), `failure` (exception), `stuck` (reserved for future deadman-timer feature)

### Enforcement Guidelines

**All AI Agents implementing this feature MUST:**

1. Use `NODE_*` constants from `workflows/metrics_collector.py` — never hardcoded node name strings.
2. Wrap all metrics infrastructure code in the failure isolation template (P5).
3. Initialize loggers as `logger = logging.getLogger(__name__)` at module top.
4. Use `datetime.now(timezone.utc)` — never `datetime.utcnow()` or naive `datetime.now()`.
5. Run all SQL through `dashboards/queries.py` — no inline SQL in view files.
6. **NEVER** add metrics fields to KBState (D2 contract — pure side-channel).
7. **NEVER** introduce pyyaml, asyncio.Queue, Celery, or any pub/sub system for metrics.

**Pattern Enforcement Mechanisms (CI-checkable):**

| Rule | Mechanism |
|------|-----------|
| All 7 nodes wrapped with `@track_metrics` | `workflows/graph.py` build-time assertion |
| `NODE_*` constants ↔ `graph.py` registered nodes match | `tests/test_metrics_collector.py` unit test |
| `KBState` stays at exactly 9 fields | `tests/test_state_contract.py`: `assert len(KBState.__annotations__) == 9` |
| No `datetime.utcnow()` | optional ruff/pylint rule |

### Pattern Examples

**Good — adding metrics to a new node:**

```python
# workflows/new_node.py
from workflows.metrics_collector import track_metrics, NODE_NEW

@track_metrics(node=NODE_NEW)
def new_node(state: KBState) -> KBState:
    ...
```

**Anti-patterns rejected in code review:**

```python
# ❌ raw string instead of NODE_* constant
@track_metrics(node="new_node")
def new_node(state):
    ...

# ❌ silent swallow without log
def _safe_record(**kwargs):
    try:
        _write_to_sqlite(**kwargs)
    except Exception:
        pass

# ❌ violates D2 — KBState must stay 9 fields
def planner_node(state: KBState) -> KBState:
    state["metrics"] = {...}
    return state

# ❌ inline SQL in view
def render_engineering_view():
    df = pd.read_sql("SELECT ...", con)
```

## Project Structure & Boundaries

### Brownfield Note

This section documents the **resulting tree after this feature is implemented**.
Legend: **✚ NEW** (added) · **⚙ MODIFIED** (existing file changed) · **◯ UNCHANGED** (existing file untouched, listed for boundary context).

### Complete Project Directory Structure (Post-Feature)

```
week3/code/
├── AGENTS.md                              ◯
├── README.md                              ◯
├── requirements.txt                       ⚙ + streamlit>=1.57.0,<2.0.0
├── .gitignore                             ⚙ + data/metrics.db
│
├── workflows/                             # 7 LangGraph node Agents (existing) + new metrics infra
│   ├── __init__.py                        ◯
│   ├── state.py                           ◯ KBState UNCHANGED — 9 fields preserved (D2)
│   ├── graph.py                           ⚙ + build-time guard (all nodes @track_metrics)
│   ├── model_client.py                    ⚙ wraps LLM call → records token usage + computes cost
│   ├── nodes.py                           ◯
│   ├── planner.py                         ⚙ + @track_metrics(node=NODE_PLANNER)
│   ├── collector.py                       ⚙ + @track_metrics(node=NODE_COLLECTOR)
│   ├── analyzer.py                        ⚙ + @track_metrics(node=NODE_ANALYZER)
│   ├── reviewer.py                        ⚙ + @track_metrics(node=NODE_REVIEWER)
│   ├── reviser.py                         ⚙ + @track_metrics(node=NODE_REVISER)
│   ├── organizer.py                       ⚙ + @track_metrics(node=NODE_ORGANIZER)
│   ├── human_flag.py                      ⚙ + @track_metrics(node=NODE_HUMAN_FLAG)
│   ├── metrics_collector.py               ✚ NEW — decorator, MetricsBuffer, SQLite writer, DDL
│   └── llm_rates.py                       ✚ NEW — model rates, FX rate, calc_cost()
│
├── patterns/                              ◯ Router/Supervisor demos unchanged
│   ├── router.py
│   └── supervisor.py
│
├── dashboards/                            ✚ NEW DIRECTORY
│   ├── __init__.py                        ✚
│   ├── app.py                             ✚ Streamlit entry (st.navigation)
│   ├── queries.py                         ✚ all SQL strings as named constants
│   ├── views/
│   │   ├── __init__.py                    ✚
│   │   ├── engineering.py                 ✚ engineering view (Tech Lead)
│   │   └── operations.py                  ✚ operations view (内容运营)
│   └── systemd/
│       └── km-dashboard.service           ✚ deployment unit (one-time install)
│
├── data/                                  ✚ NEW DIRECTORY (gitignored)
│   └── metrics.db                         ✚ SQLite, runtime-created
│
├── tests/                                 # production hardening (existing) + new tests
│   ├── cost_guard.py                      ◯
│   ├── security.py                        ◯
│   ├── eval_test.py                       ◯
│   ├── test_metrics_collector.py          ✚ NEW unit tests + decorator coverage + overhead test
│   ├── test_llm_rates.py                  ✚ NEW unit tests for cost calculation
│   ├── test_state_contract.py             ✚ NEW assert KBState has exactly 9 fields (guards D2)
│   └── test_dashboard_queries.py          ✚ NEW SQL query smoke tests
│
└── openspec/
    ├── config.yaml                        ◯
    ├── project.md                         ◯
    ├── specs/                             ◯ existing capabilities
    └── changes/
        └── metrics-collection/            ✚ NEW change directory
            ├── proposal.md                ✚ why + scope + risk
            ├── tasks.md                   ✚ implementation steps (matches D1-D7 build order)
            └── specs/
                └── metrics-collection/
                    └── spec.md            ✚ ADDED Requirements (Req-1..Req-6)
```

### Architectural Boundaries

| # | Boundary | Direction | Owner | Red Line |
|---|----------|-----------|-------|----------|
| **B1** | Pipeline → MetricsBuffer | write-only | `workflows/metrics_collector.py` | Pipeline must NOT read buffer or react to its contents |
| **B2** | MetricsBuffer → SQLite | append-only sync write + WAL | `metrics_collector._write_to_sqlite()` | Write errors MUST NOT propagate (P5 template) |
| **B3** | Dashboard → SQLite | **read-only** | `dashboards/queries.py` | Dashboard MUST NOT INSERT / UPDATE / DDL |
| **B4** | model_client → llm_rates | pure function call | `workflows/llm_rates.calc_cost()` | Rate changes only via git commit; no runtime mutation |
| **B5** | KBState contract | UNCHANGED (frozen) | `workflows/state.py` + `tests/test_state_contract.py` | Any PR adding/removing/renaming KBState field is a blocking failure |

### Requirements to Structure Mapping

| Req | Implementation Location |
|-----|------------------------|
| FR1 — node status (success/failure/stuck) | `metrics_collector.py` decorator → `piece_node_stats` table |
| FR2 — review iteration count | `piece_node_stats.visit_count` (Reviewer row) |
| FR3 — token cost by agent | `model_client.py` wrapper → `token_usage` table; aggregation in `queries.py` |
| FR4 — daily throughput vs target 20 | `queries.py: DAILY_THROUGHPUT_SQL` against `piece_runs` |
| FR5 — e2e latency p50/p95 | `queries.py: E2E_LATENCY_SQL` against `piece_runs.e2e_ms` |
| FR6 — dual views (engineering + operations) | `dashboards/views/engineering.py` + `dashboards/views/operations.py` |
| NFR1 — < 5% pipeline overhead | sync direct-write (D4); validated by `tests/test_metrics_collector.py::test_overhead_under_threshold` |
| NFR2 — diagnose ≤ 5 min | engineering view single-piece trace table (query in `queries.py`) |
| NFR3 — operations 100% self-serve | systemd long-running service (`dashboards/systemd/km-dashboard.service`) |
| NFR4 — 2-week MVP | reflected in `openspec/changes/metrics-collection/tasks.md` build sequence |
| NFR5 — CNY units | `workflows/llm_rates.py: USD_TO_CNY`; `token_usage.cost_cny` column |

### Cross-Cutting Concerns to Locations

| Concern | Location |
|---------|----------|
| Failure isolation pattern (P5) | central helper `_safe_record()` in `workflows/metrics_collector.py`; pattern enforced everywhere |
| Time format consistency | central helper `_now_iso()` in `workflows/metrics_collector.py` |
| Cost computation | single owner: `workflows/llm_rates.calc_cost()` |
| Schema bootstrap | `workflows/metrics_collector.py` on first `get_buffer()` call (idempotent CREATE TABLE IF NOT EXISTS) |
| Rate change audit trail | git history of `workflows/llm_rates.py` |

### Integration Points

**Internal Communication (single piece flow):**

```
[Pipeline node entry]
   │
   ▼
[@track_metrics decorator]   captures start_ts, increments visit_count
   │
   ▼
[node body executes]
   │
   ├──→ [model_client wrapper]   records prompt/completion tokens
   │       │
   │       └──→ [llm_rates.calc_cost()]   pure function: returns (usd, cny)
   │
   ▼
[node body returns / raises]
   │
   ▼
[decorator finally block]   captures end_ts, last_status
   │
   ▼
[_safe_record() → SQLite WAL append]   ← errors swallowed, pipeline continues

[Dashboard process — separate from pipeline]
   │
   │ on user request
   ▼
[Streamlit view (engineering.py | operations.py)]
   │ calls
   ▼
[queries.py: NAMED_SQL]   pandas.read_sql
   │
   ▼
[SQLite metrics.db (read-only via WAL)]
```

**External Integrations:** None for MVP. Future option: FX rate API for `USD_TO_CNY` auto-update (deferred).

### Development Workflow Integration

**Local development:**
- Run pipeline as today: existing entry point (no change to invocation)
- Metrics persist to `data/metrics.db` automatically on first run (schema auto-created)
- Run dashboard locally: `streamlit run dashboards/app.py` — opens browser at `localhost:8501`

**Production deployment:**
- Pipeline: unchanged (existing cron/scheduler)
- Dashboard: `systemctl enable --now km-dashboard.service` (one-time install of unit file)
- Internal users access via bookmarked URL on internal network

**Test execution:**
- All new tests under `tests/` follow existing pytest convention
- `pytest tests/` runs full suite including new `test_metrics_collector.py`, `test_llm_rates.py`, `test_state_contract.py`, `test_dashboard_queries.py`
- **CI gates** (must pass to merge):
  - `test_state_contract.py` — KBState 9-field invariant (B5)
  - `test_metrics_collector.py::test_all_nodes_decorated` — graph build assertion (P1, B2)
  - `test_metrics_collector.py::test_overhead_under_threshold` — NFR1 sanity check

**OpenSpec change lifecycle:**
1. Create `openspec/changes/metrics-collection/` with `proposal.md`, `tasks.md`, `specs/metrics-collection/spec.md`
2. Implement per `tasks.md` sequence (matches D1-D7 build order from step-04 Decision Impact Analysis)
3. After merge, archive change per OpenSpec convention; spec delta becomes part of `openspec/specs/metrics-collection/`

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
D1 (decorator) → D2 (in-process MetricsBuffer) → D3 (SQLite) → D4 (sync write + WAL) → D5 (Streamlit reader) form a single coherent write/read chain. Token cost (D6) flows from `model_client` wrapper through `llm_rates.calc_cost()` into the `token_usage` table whose schema (D3) is shaped by D7 time conventions. No conflicting decisions detected.

**Pattern Consistency:**
P1 NODE_* constants are consumed by the D1 decorator. P5 failure isolation template is the precondition that makes D4 sync-write safe (errors never propagate to pipeline). P3 buffer factory keeps D2's singleton swappable for future ContextVar migration. P7 SQL centralization aligns with B3 read-only dashboard boundary.

**Structure Alignment:**
The step-6 directory tree maps every ✚/⚙ entry to a specific decision (D1-D7) or pattern (P1-P7). KBState (B5) preservation is structurally enforced — `workflows/state.py` is annotated ◯ UNCHANGED and guarded by `tests/test_state_contract.py`.

**Version Compatibility:**
- Streamlit 1.57.0 (web-verified, 2026-04-28 release) compatible with Python 3.11+ and pandas/altair transitive deps
- LangGraph >=0.2 (existing) — decorator approach (D1) is framework-agnostic, no version coupling
- SQLite (Python stdlib) — no version concern

### Requirements Coverage Validation ✅

| Requirement | Implementation Path | Status |
|-------------|---------------------|--------|
| FR1 — node status | D1 decorator → D7 schema → D3 `piece_node_stats` | ✅ |
| FR2 — review iteration count | D7 `visit_count` column on Reviewer rows | ✅ |
| FR3 — agent token cost | D6 `calc_cost` + D3 `token_usage` table | ✅ |
| FR4 — daily throughput vs target 20 | D5 view + D3 `piece_runs` aggregation | ✅ |
| FR5 — e2e p50/p95 latency | D7 `e2e_ms` column + D5 view percentile calc | ✅ |
| FR6 — dual views | D5 `engineering.py` + `operations.py` | ✅ |
| NFR1 — < 5% pipeline overhead | D4 math (calc shows ~0.05%) + `test_overhead_under_threshold` | ✅ |
| NFR2 — diagnose ≤ 5 min | D5 engineering view single-piece trace drill-down | ✅ |
| NFR3 — operations 100% self-serve | D5 systemd long-running service | ✅ |
| NFR4 — 2-week MVP delivery | All decisions favor boring tech (SQLite stdlib, Streamlit, sync) | ✅ |
| NFR5 — CNY units | D6 `USD_TO_CNY` + `cost_cny` column in `token_usage` | ✅ |

**5/5 must-have FRs covered; 5/5 NFRs addressed architecturally.**

### Implementation Readiness Validation ✅

**Decision Completeness:** All 7 decisions (D1-D7) carry rationale, affected components, "Provided by Starter" status, and explicit "Revisit Trigger" conditions. Versions verified for external dependencies.

**Structure Completeness:** Full project tree provided post-feature with ✚/⚙/◯ legend. 5 boundaries (B1-B5) defined with owner, direction, and red lines. Requirements-to-structure mapping table connects every FR/NFR to specific files.

**Pattern Completeness:** 7 conflict points addressed (P1-P7). Inherited conventions table makes clear what is NOT being re-decided. Enforcement mechanisms (build-time assertion, contract tests, optional ruff rule) translate rules into CI-checkable gates.

### Gap Analysis Results

**Critical Gaps (block implementation):** 🟢 None

**Important Gaps (acknowledged, not blocking):**

1. **PRD not formally validated** — `bmad-validate-prd` was skipped at step-01. PRD remains v0.1 draft. Recommend running validation post-architecture for closed-loop verification.
2. **Stories not produced** — `bmad-create-epics-and-stories` was not run. Architecture is implementable but no sprint-level breakdown exists.
3. **MetricsBuffer single-process assumption lacks automated guard** — D2 documents the revisit trigger ("introduce concurrent runs → migrate to ContextVar"), but no test will fail if `multiprocessing` is silently introduced.
4. **D6 rate-update review mechanism is informal** — `workflows/llm_rates.py` changes are tracked only by git history. No CODEOWNERS or PR template currently enforces additional eyes on rate edits.
5. **Backfill tool deferred (YAGNI)** — When DeepSeek V4 Pro pricing changes 2026-05-05, recomputing historical CNY values requires writing `tools/backfill_costs.py` first.

**Nice-to-Have Gaps (acceptable for MVP):**

1. No alerting on pipeline failures (PRD explicitly out-of-scope)
2. No data retention policy on `metrics.db` (~150K rows/year — not urgent)
3. No visual mockups for Streamlit views (Streamlit's iteration cost makes prose-only spec acceptable)

### Validation Issues Addressed

All issues identified are documented as "Important Gaps" or "Nice-to-Have Gaps" with explicit follow-up paths. None block step-08 completion or initial implementation. Important Gaps 1 and 2 are best resolved by returning to John (`bmad-agent-pm`) after architecture is locked.

### Architecture Completeness Checklist

**Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

**Score: 16/16 ✅**

### Architecture Readiness Assessment

**Overall Status:** READY WITH MINOR GAPS

Rationale for not "READY FOR IMPLEMENTATION": although all 16 checklist items are checked and zero Critical Gaps remain, 5 Important Gaps are open (PRD validation, stories, singleton automated guard, rate-edit governance, backfill tool). None block initial implementation, but they should be tracked.

**Confidence Level:** medium-to-high

Honest reasoning:
- HIGH on coherence and structure — all decisions self-consistent and traceable
- HIGH on Streamlit / SQLite version stability — verified
- MEDIUM on performance assumptions — NFR1 < 5% is computed (~0.05%) but not yet measured against real pipeline
- MEDIUM on singleton MetricsBuffer — works for current single-process batch but no guard against accidental concurrent runs

**Key Strengths:**

- Boring technology throughout (SQLite stdlib, Streamlit, synchronous direct-write)
- KBState 9-field contract structurally enforced (B5 + `test_state_contract.py` CI gate)
- P5 failure isolation pattern uniformly applied via mandatory template
- All 5 PRD must-haves map directly to specific schema columns — no semantic translation needed
- OpenSpec change cleanly scoped as pure ADDED capability (no MODIFIED Requirements)
- All design decisions carry explicit "Revisit Trigger" conditions for future re-evaluation

**Areas for Future Enhancement:**

- Run `bmad-validate-prd` to formally close PRD coverage loop (resolves Important Gap #1)
- Run `bmad-create-epics-and-stories` for sprint-level decomposition (resolves Important Gap #2)
- Add a contract test asserting no `multiprocessing` import in `workflows/` (resolves Important Gap #3)
- Add CODEOWNERS or PR template requiring second review on `workflows/llm_rates.py` (resolves Important Gap #4)
- Build `tools/backfill_costs.py` when first rate change is imminent (resolves Important Gap #5)
- Post-MVP: failure alerting, data retention policy, visual mockups

### Implementation Handoff

**AI Agent Guidelines:**

- Follow all D1-D7 decisions exactly as documented; deviations require new architecture cycle.
- Use P1-P7 implementation patterns consistently — `NODE_*` constants over raw strings, P5 failure isolation in every metrics infra block, P4 timezone-aware datetimes only.
- Respect B1-B5 architectural boundaries — especially B5 (KBState 9-field contract) and B3 (dashboard read-only).
- All SQL through `dashboards/queries.py` — no inline queries in views.
- Refer to this document for any architectural ambiguity; if a decision is missing, surface it before coding.

**First Implementation Priority:**

```bash
# Step 1 — create OpenSpec change scaffold
mkdir -p openspec/changes/metrics-collection/specs/metrics-collection
touch openspec/changes/metrics-collection/{proposal.md,tasks.md}
touch openspec/changes/metrics-collection/specs/metrics-collection/spec.md
```

**Subsequent build order (matches step-04 Decision Impact Analysis):**

1. `workflows/llm_rates.py` (foundation, no V3 changes) + `tests/test_llm_rates.py`
2. `workflows/metrics_collector.py` (decorator, MetricsBuffer, SQLite writer, DDL) + `tests/test_metrics_collector.py`
3. `workflows/model_client.py` modification (token capture + `calc_cost` integration)
4. Add `@track_metrics(node=NODE_*)` to each of the 7 node files
5. `workflows/graph.py` build-time assertion (all nodes decorated)
6. `dashboards/` full tree (`app.py`, `queries.py`, `views/`, `systemd/`)
7. `requirements.txt` + `.gitignore` updates
8. End-to-end smoke test → verify metrics rows → verify dashboard renders

---

## v0.2 — Course Correction (2026-04-29)

> v0.1（step-1 ~ step-7）违反了 V2 讲义 4 条核心约束：**不破图 / 不污染 / 不加 LLM / 最小侵入**。
>
> v0.2 是修正版。v0.1 内容保留供学员对照"过度设计"的反例。**实施请以本节为准。**

### 4 项违规对照

| 违规面 | v0.1（错） | v0.2（对） |
|--------|-----------|-----------|
| **D1 采集机制** | 装饰器 `@track_metrics` 改 7 个 Agent 文件（"option B"） | LangChain `BaseCallbackHandler` 子类 + invoke-time config（"option C"）—— 7 个 Agent 文件 0 字节变动 |
| **D5 Dashboard** | Streamlit 1.57.0 + systemd + `dashboards/` 全套 | **删除**——PRD 显式 OOS（Prometheus 导出·下季度） |
| **D6 Rates 模块** | `workflows/llm_rates.py`（USD/CNY 双写 + rates as code） | **删除**——MVP 只存 raw tokens（`prompt_tokens` + `completion_tokens`）；换算下季度 dashboard 工作时再做；不复用 `tests/cost_guard.py`（那是 budget enforcement，与 reporting 职责不同） |
| **命名** | `metrics_collector.py` / change `metrics-collection` | `workflows/metrics.py` / `openspec/changes/add-metrics-collector/`（动词开头） |

### Corrected D1 — Collection Mechanism: BaseCallbackHandler at Invoke-Time

`workflows/metrics.py` 实现一个 `BaseCallbackHandler` 子类。LangChain 回调系统在每次 chain（= LangGraph node）和 LLM 调用前后自动触发钩子——**无需修改任何 Agent 文件，也无需包装 `model_client.py`**。

```python
# workflows/metrics.py
from langchain_core.callbacks import BaseCallbackHandler

class MetricsCollector(BaseCallbackHandler):
    """Captures node + LLM metrics via LangChain callback hooks.

    Attached at invoke-time:
        app.invoke(state, config={"callbacks": [MetricsCollector()]})

    Touches no Agent file. Owns its own in-process state.
    """
    def __init__(self):
        self._node_starts: dict[str, float] = {}
        self._records: list[dict] = []

    def on_chain_start(self, serialized, inputs, *, run_id, **kw): ...
    def on_chain_end(self, outputs, *, run_id, **kw): ...
    def on_chain_error(self, error, *, run_id, **kw): ...
    def on_llm_start(self, serialized, prompts, *, run_id, **kw): ...
    def on_llm_end(self, response, *, run_id, **kw): ...

    def flush(self) -> None:
        """Append _records to data/metrics-{YYYY-MM-DD}.jsonl. Errors swallowed."""
        ...
```

```python
# workflows/graph.py  (+~5 lines, only at invoke site — no other changes)
from workflows.metrics import MetricsCollector

def run_pipeline(state):
    collector = MetricsCollector()
    result = app.invoke(state, config={"callbacks": [collector]})
    collector.flush()
    return result
```

### Corrected D3 — Storage: JSONL Append-Only

| Aspect | v0.2 |
|--------|------|
| Backend | JSONL append-only |
| Path | `data/metrics-{YYYY-MM-DD}.jsonl` |
| Write timing | Run 结束 `collector.flush()` 一次性追加（不写中途） |
| Concurrency | Run 内单进程，不需要锁 |
| Query | 下季度 dashboard 工作时按需 pandas / DuckDB 读取 |
| Failure mode | flush 失败 swallow + WARNING log，主 pipeline 不阻塞 |

**Why JSONL not SQLite (v0.1 错):** Dashboard OOS、查询能力 MVP 不需要 → SQLite 多余。JSONL 满足"事件流持久化"的真实需求，零依赖、与 V3 现有 `knowledge/raw/*.json` 风格一致。

`.gitignore`：追加 `data/`。

### Corrected D6 — Token Cost: Raw Only, No Conversion

MVP 仅存 `prompt_tokens` + `completion_tokens`（两个整数字段）。

- ❌ 不引入 `llm_rates.py` / `cost.py` / 任何换算模块
- ❌ 不复用 `tests/cost_guard.py`（职责是 **budget enforcement** 实时熔断；metrics 是 **reporting** 离线读取——两件事）
- ✅ 下季度做 dashboard / 报表时再决定换算策略（rates 来源、CNY 双写、回填等）

### D2 — Side-Channel · 沿用

KBState 9 字段不动。Metrics 数据由 `MetricsCollector` 实例自身持有（`self._records`），不进 KBState。spec delta 形态：纯 ADDED capability。

### D7 — Schema 沿用（事件记录形式）

每条 JSONL 记录的字段（直接对应 PRD 5 项 must-have）：

```jsonc
// kind 1 — piece-level，每条 piece 一行
{
  "kind": "piece_run",
  "piece_id": "...",
  "e2e_start":   "2026-04-29T03:14:00.123+00:00",  // ISO 8601
  "e2e_end":     "2026-04-29T03:18:42.456+00:00",
  "e2e_ms":      282333,
  "final_status": "pass"        // pass | human_flagged | failed
}

// kind 2 — per (piece, node)，一条 piece 可有多行（每节点一行）
{
  "kind": "node_stat",
  "piece_id": "...",
  "node_name":   "reviewer",
  "total_ms":    18421,
  "visit_count": 2,             // M2: review iteration count
  "last_status": "success"      // success | failure | stuck
}

// kind 3 — per LLM call，单条 piece 内多次 LLM 调用各一行
{
  "kind": "token_usage",
  "piece_id":          "...",
  "agent_name":        "analyzer",
  "prompt_tokens":     1450,
  "completion_tokens": 312,
  "model":             "deepseek-chat-v4-flash",
  "recorded_at":       "2026-04-29T03:15:11.987+00:00"
}
```

**PRD must-have 映射（不变）：**
- M1（节点状态）← `node_stat.last_status` group by `node_name`
- M2（review 迭代）← `node_stat.visit_count` where `node_name = "reviewer"`
- M3（token 消耗）← `token_usage` sum by `agent_name`（仅 raw tokens；CNY 换算下季度）
- M4（daily throughput）← `piece_run` count by date where `final_status = "pass"`
- M5（e2e p50/p95）← `piece_run.e2e_ms` 分布

### Corrected Build Order

```
[Step 1] OpenSpec scaffold（动词开头命名）
  + openspec/changes/add-metrics-collector/proposal.md
  + openspec/changes/add-metrics-collector/tasks.md
  + openspec/changes/add-metrics-collector/specs/metrics/spec.md   # ADDED capability "metrics"

[Step 2] Implement collector
  + workflows/metrics.py        # MetricsCollector(BaseCallbackHandler) + flush()
  + tests/test_metrics.py       # callback hook 单测 + JSONL flush 测试

[Step 3] Wire at invoke site
  ⚙ workflows/graph.py          # +~5 行，仅 invoke 处

[Step 4] Storage path setup
  ⚙ .gitignore                  # + data/

[Step 5] End-to-end smoke
  · 跑现有 pipeline → 验证 data/metrics-{date}.jsonl 三种 record kind 都出现
```

### Corrected File Delta

```
✚ NEW（5 个文件）:
  workflows/metrics.py
  tests/test_metrics.py
  openspec/changes/add-metrics-collector/proposal.md
  openspec/changes/add-metrics-collector/tasks.md
  openspec/changes/add-metrics-collector/specs/metrics/spec.md

⚙ MODIFIED（2 个文件）:
  workflows/graph.py       # +~5 行，仅 invoke 处
  .gitignore               # + data/

◯ UNCHANGED — 0 字节变动:
  workflows/state.py                 ← KBState 9 字段契约
  workflows/model_client.py          ← LangChain callback 自动覆盖 LLM 调用
  workflows/planner.py
  workflows/collector.py
  workflows/analyzer.py              ┐
  workflows/reviewer.py              ├ 7 Agent 文件全部 0 字节变动
  workflows/reviser.py               │
  workflows/organizer.py             │
  workflows/human_flag.py            ┘
  workflows/nodes.py
  patterns/* · tests/{cost_guard,security,eval_test}.py · 其他既有文件

❌ NOT CREATED（v0.1 误列）:
  workflows/metrics_collector.py     ← 命名错
  workflows/llm_rates.py             ← OOS
  dashboards/* (整个目录)             ← OOS
  data/metrics.db                    ← SQLite 已被 JSONL 替代
```

### Corrected Boundaries

| # | Boundary | Direction | Owner | Red Line |
|---|----------|-----------|-------|----------|
| **B1** | Pipeline → MetricsCollector | LangChain callback 单向触发 | `workflows/metrics.py` | Pipeline 不读 collector 状态、不依赖 collector 行为 |
| **B2** | MetricsCollector → JSONL file | run 结束一次 flush | `MetricsCollector.flush()` | flush 失败 swallow + log；绝不抛回 pipeline |
| **B5** | KBState 契约 | UNCHANGED（9 字段） | `workflows/state.py` + `tests/test_state_contract.py` | 任何 PR 加/删 KBState 字段 = 阻塞合并 |

> 删除：v0.1 的 B3（dashboard 读 SQLite）、B4（model_client → llm_rates）—— 都不存在了。

### Corrected OpenSpec Change Shape

```
openspec/changes/add-metrics-collector/   # 动词开头
├── proposal.md        # why + scope（含明确 OOS：dashboards、cost calc）
├── tasks.md           # 5 步实施序列（如上 Build Order）
└── specs/
    └── metrics/
        └── spec.md    # ADDED capability "metrics"
                       #   Req-1: BaseCallbackHandler 子类 attached at invoke
                       #   Req-2: JSONL append at data/metrics-{date}.jsonl
                       #   Req-3: 3 record kinds (piece_run / node_stat / token_usage)
                       #   Req-4: flush 失败 swallow + log；pipeline 不阻塞
                       #   Explicitly NOT MODIFIED: state.py · 7 Agent files · model_client.py
```

### v0.2 Validation Snapshot

| 项 | v0.2 状态 |
|----|----------|
| **不破图**（约束 1） | ✅ `graph.py` 仅 +5 行 invoke 处，topology / 3 路条件边不变 |
| **不污染**（约束 2） | ✅ 7 个 Agent 文件 0 字节变动 |
| **不加 LLM**（约束 3） | ✅ MetricsCollector 不调任何 LLM |
| **最小侵入**（约束 4） | ✅ 5 新增文件 + 2 修改（其中 1 仅 +1 行） |
| PRD 5 项 must-have 覆盖 | ✅ 全覆盖（schema 沿用 D7） |
| OOS 严格排除 | ✅ 无 dashboard、无 cost 换算模块 |
| 命名规范 | ✅ `metrics.py` + `add-metrics-collector` |
| 16 项 readiness checklist | ✅ 全过 |

**Overall Status:** READY FOR IMPLEMENTATION
**Confidence:** **high**（v0.1 是 medium-to-high；v0.2 收紧 scope 后假设面更小、更接近"代码即文档"——无 dashboard 部署不确定性、无 rates 跨季度延展性问题）

### Implementation Handoff (v0.2)

第一步立即执行：

```bash
mkdir -p openspec/changes/add-metrics-collector/specs/metrics
touch openspec/changes/add-metrics-collector/{proposal.md,tasks.md}
touch openspec/changes/add-metrics-collector/specs/metrics/spec.md
```

后续 4 步按上面 Build Order 执行即可。

### Lessons Encoded in Memory（已落盘到 user memory）

- `feedback_v3_metrics_callback_pattern.md` — 用 BaseCallbackHandler，不用装饰器
- `feedback_v3_metrics_mvp_scope.md` — Dashboard / rates module 都是 OOS
- `feedback_v3_naming_conventions.md` — `metrics.py` + `add-metrics-collector`
- `project_v3_metrics_collection_constraints.md` — 4 条核心约束（不破图 / 不污染 / 不加 LLM / 最小侵入）

下次任何 BMad 角色重新进入这个项目，会自动加载这 4 条记忆——不会再翻同一个跟头。

---

**Workflow Status: COMPLETE** · stepsCompleted: [1..8] · authoritative_version: v0.2
