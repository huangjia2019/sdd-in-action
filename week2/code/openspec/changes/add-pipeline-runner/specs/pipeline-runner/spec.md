## ADDED Requirements

### Requirement: Single-Command Run

The pipeline SHALL expose a CLI entry point `python -m pipeline run --date <YYYY-MM-DD>` that executes `collector → analyzer → organizer` in order for the given date.

#### Scenario: Happy path end-to-end run

- **WHEN** a developer runs `python -m pipeline run --date 2026-04-15` in a clean workspace
- **THEN** `knowledge/raw/2026-04-15.json`, `knowledge/tagged/2026-04-15.json`, and `knowledge/articles/2026-04-15.md` all exist and the command exits 0

### Requirement: Contract-Respecting Handoff

The pipeline SHALL invoke each downstream stage only after the upstream stage's `.done` marker exists at the path declared by `week1/specs/agents-collaboration.md`.

#### Scenario: Analyzer waits for collector marker

- **WHEN** the collector subprocess returns before writing `{date}.collector.done`
- **THEN** the pipeline exits non-zero with an error referencing the missing marker, and analyzer is NOT invoked

### Requirement: Idempotent Resume

When a `.done` marker already exists for a stage, the pipeline SHALL skip that stage and proceed to the next.

#### Scenario: Partial prior run resumes from analyzer

- **WHEN** `2026-04-15.collector.done` exists but `2026-04-15.analyzer.done` does not, and the developer runs the pipeline
- **THEN** collector is skipped, analyzer runs, organizer runs, command exits 0

#### Scenario: Fully completed run is a no-op

- **WHEN** all three `.done` markers for the date already exist and the pipeline runs
- **THEN** no stage is invoked and the command exits 0 with a log line stating "already complete"

### Requirement: Fail-Fast with Incident Record

When any stage exits non-zero, the pipeline SHALL stop, write `knowledge/incidents/{date}.md` with stage name and exit code, and return non-zero.

#### Scenario: Analyzer fails mid-pipeline

- **WHEN** analyzer exits non-zero during a run for 2026-04-15
- **THEN** organizer is NOT invoked, `knowledge/incidents/2026-04-15.md` contains the stage name and exit code, and the pipeline exits with the analyzer's exit code

### Requirement: Run Log

Each pipeline invocation SHALL produce a `knowledge/logs/pipeline-{date}-{run_id}.log` containing, for each stage: start timestamp, end timestamp, exit code, and the first 100 lines of stdout.

#### Scenario: Log written on success

- **WHEN** a happy path run completes for 2026-04-15
- **THEN** `knowledge/logs/pipeline-2026-04-15-{uuid}.log` exists with three stage entries, each with exit code 0

#### Scenario: Log written on failure

- **WHEN** collector fails for 2026-04-15
- **THEN** the log file exists and contains the collector entry with non-zero exit code and the failing stdout excerpt

### Requirement: Isolated Subprocess Execution

Each stage SHALL be executed as a separate subprocess with its own working directory and environment, not imported in-process.

#### Scenario: Subprocess isolation

- **WHEN** collector raises an uncaught exception
- **THEN** the pipeline process itself does NOT crash; it records the non-zero exit code and proceeds to the fail-fast handling

### Requirement: No Implicit Scheduling

The CLI SHALL NOT include daemon mode, scheduling, or multi-date iteration in v1.

#### Scenario: Invalid flag rejected

- **WHEN** the developer runs `python -m pipeline run --date-range 2026-04-01:2026-04-15`
- **THEN** the command exits non-zero with an error explaining that only `--date` is supported
