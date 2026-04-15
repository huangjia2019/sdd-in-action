## Why

Week 1 delivered three agents (collector, analyzer, organizer) that are triggered manually one at a time. Week 2 Session N6 needs to chain them into a runnable pipeline so a single command produces the day's `knowledge/articles/{date}.md`. Without this, the agents remain a demo; with it, they become a reproducible daily job that Week 2 Session N7 (CI) and Week 4 (deploy) can build on.

## What Changes

- Add a `pipeline` CLI entry point: `python -m pipeline run --date YYYY-MM-DD`
- Wire `collector → analyzer → organizer` via file-based handoffs using the Week 1 `agents-collaboration` contract
- Respect the trigger contract: each stage writes a `{date}.{stage}.done` marker; downstream stage starts only when its upstream marker exists
- Emit a single `pipeline.log` per run with per-stage duration and exit code
- Surface failures early: if any stage fails, stop the pipeline and write `knowledge/incidents/{date}.md` per the Week 1 `project-vision` contract

## Capabilities

### New Capabilities

- `pipeline-runner`: Orchestrate the three agents end-to-end via a single command, honoring the pre-existing inter-agent contracts, with deterministic failure behavior.

## Impact

- **Code added**: `week2/code/pipeline/` (CLI entry + runner module)
- **Depends on (unchanged)**: `week1/specs/agents-collaboration.md` (data contract + trigger contract)
- **Reuses (unchanged)**: Week 1 agent implementations at `week1/code/04/skills/`
- **New dependency**: none beyond Python stdlib (`argparse`, `subprocess`, `pathlib`)
- **Developer workflow**: `python -m pipeline run --date 2026-04-15` replaces three manual Claude Code sessions
