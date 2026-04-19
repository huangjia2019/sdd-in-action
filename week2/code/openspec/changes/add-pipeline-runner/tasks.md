## 1. Package skeleton

- [ ] 1.1 Create `week2/code/pipeline/` with `__init__.py`, `__main__.py`, `runner.py`
- [ ] 1.2 Add `week2/code/pipeline/README.md` explaining CLI usage with an example command
- [ ] 1.3 Ensure `python -m pipeline run --date 2026-04-15` is importable from a clean venv

## 2. CLI surface

- [ ] 2.1 Implement `__main__.py` with `argparse`: subcommand `run` with required `--date YYYY-MM-DD`
- [ ] 2.2 Validate date format up front; exit non-zero with a friendly message on malformed date
- [ ] 2.3 Reject unknown flags explicitly (no silent ignores); include `--date-range` in the rejection test

## 3. Stage orchestration

- [ ] 3.1 Implement `runner.run(date)` that sequentially invokes collector → analyzer → organizer
- [ ] 3.2 Each stage launches via `subprocess.run` with cwd at project root and a minimal copied env
- [ ] 3.3 After each stage, check the expected `.done` marker path from `week1/specs/agents-prd.md`
- [ ] 3.4 If marker missing, treat as failure even when subprocess exited 0 (defensive)
- [ ] 3.5 If marker already exists at stage start, log skip and move on

## 4. Failure handling

- [ ] 4.1 On non-zero subprocess exit, stop immediately (do not run downstream)
- [ ] 4.2 Write `knowledge/incidents/{date}.md` with timestamp, stage name, exit code, last 20 stdout lines
- [ ] 4.3 Return the failing stage's exit code from the CLI

## 5. Logging

- [ ] 5.1 Generate a `run_id` (uuid4) at pipeline start
- [ ] 5.2 Stream each stage's stdout to `knowledge/logs/pipeline-{date}-{run_id}.log`
- [ ] 5.3 Append per-stage header: start ISO timestamp, end ISO timestamp, exit code
- [ ] 5.4 Truncate captured stdout at 100 lines per stage in the log (full output is still in subprocess capture)

## 6. Acceptance

- [ ] 6.1 Happy path: clean workspace, run command, all three output files + three markers + log file present, exit 0
- [ ] 6.2 Resume: pre-seed collector.done marker, run command, verify collector is skipped and downstream runs
- [ ] 6.3 Fully-complete no-op: pre-seed all three markers, run command, verify no stages invoked, exit 0
- [ ] 6.4 Fail-fast: stub analyzer to exit 1, run command, verify organizer is NOT invoked, incident file exists, pipeline exits 1
- [ ] 6.5 Isolation: make collector raise an uncaught exception, verify pipeline process survives and records the exit code
- [ ] 6.6 Measure end-to-end latency on a typical day's data; confirm under 10 minutes per the Week 1 project-vision budget

## 7. Documentation

- [ ] 7.1 Add a "Run the pipeline" section to `week2/README.md` linking this change
- [ ] 7.2 Record in `week2/code/pipeline/README.md` that this pipeline depends on the Week 1 `agents-prd` contract and will break if that contract is modified without a coordinated change
