## Context

This is the first change in Week 2 that **builds on** Week 1 artifacts rather than introducing a new concept from scratch. The pipeline is a thin orchestrator — all the real work lives in the three agents that Week 1 already defined. The challenge is respecting the inter-agent contract (`week1/specs/agents-collaboration.md`) without re-implementing it or silently drifting from it.

Concretely, Week 1 agents communicate via:
- **Data contract**: JSON files at fixed paths (`knowledge/raw/{date}.json`, `knowledge/tagged/{date}.json`, `knowledge/articles/{date}.md`)
- **Trigger contract**: `.done` marker files that each stage touches on success

The pipeline's job is to drive this handshake mechanically.

## Goals / Non-Goals

**Goals:**

- Single command runs the three stages in order
- Re-running for the same date is idempotent: a clean run regenerates outputs, a resumed run skips completed stages based on `.done` markers
- One failure stops the pipeline (fail-fast), not "run everything and report all errors"
- Every run produces a timestamped `pipeline.log` for post-mortem

**Non-Goals:**

- No parallelization across stages (they're strictly sequential by contract)
- No retry logic in v1 (one failure = one incident; manual re-run with intent)
- No daemon mode / scheduling (Week 2 Session N7's CI handles that)
- No web UI or status dashboard

## Decisions

**Decision 1: Python CLI via `python -m pipeline`, not bash.**
Agents are Python; keeping the runner Python avoids cross-language failure modes (argument escaping, env propagation, exit code translation). `python -m pipeline` is invokable from anywhere the venv is active.

**Decision 2: Stage invocation is subprocess, not in-process import.**
Each agent is a Claude Code / OpenCode skill. Running them as subprocesses preserves their execution isolation (own cwd, own env, own memory), matches how Week 2 CI will run them, and keeps the pipeline runner agnostic to agent internals. Cost: subprocess startup per stage (~200ms × 3).

**Decision 3: Resume on `.done` markers, not a state file.**
Reuse the existing trigger contract rather than introducing a `pipeline_state.json`. Rationale: one source of truth, and the existing markers already mean "this stage finished successfully." The pipeline just reads what agents write.

**Decision 4: Fail-fast, record incident, do not retry.**
When a stage exits non-zero, write `knowledge/incidents/{date}.md` (per Week 1 `project-vision` contract), log the exit code, and return non-zero from the pipeline. This matches Week 1's failure behavior; CI in N7 will layer alerting on top.

**Decision 5: No date-range mode in v1.**
The CLI accepts exactly one `--date`. Backfills are handled by looping externally (`for d in dates; do python -m pipeline run --date $d; done`). Avoids designing a multi-date concurrency story prematurely.

## Risks / Trade-offs

**Risk: pipeline drifts from the inter-agent contract over time.**
If someone adds a new field to `knowledge/raw/` schema without updating the contract doc, the pipeline wouldn't catch it. Mitigation: the pre-commit hook from `add-pre-commit-schema-validation` enforces the schema at commit time. The two changes are complementary — the hook catches field-level drift, the pipeline respects file-level handoffs.

**Trade-off: subprocess overhead (~600ms total startup cost).**
Acceptable for a daily batch job. Unacceptable if this ever becomes per-request; revisit only if that becomes a real requirement.

**Risk: Week 1 agents may have been tweaked since the contract was written.**
On first pipeline run, this will surface. Mitigation: the pipeline logs exit codes and stdout verbatim; mismatches show up immediately. This is a feature not a bug — running the pipeline becomes a drift-detection test for the Week 1 layer.
