## Context

Week 2 is the first week where we enforce inter-agent contracts mechanically. In Week 1 we documented the schema for `knowledge/raw/*.json` (see `week1/specs/schemas/collector-output.json`) but relied on "the collector promises to follow it" — a social contract, not an enforced one. This change upgrades that social contract into a machine-checked one at the commit boundary.

We deliberately pick `pre-commit` (not `pre-push`, not CI-only) because the failure mode we most want to prevent is "a bad raw JSON enters the repo history." Once it's in history, downstream analyzers read it, fail silently, and debugging walks backwards through commits. Rejecting at commit time keeps history clean.

## Goals / Non-Goals

**Goals:**

- Validate every staged `knowledge/raw/*.json` against the declared JSON Schema before the commit lands.
- Produce developer-legible error messages: file path + JSON pointer + expected-vs-actual.
- Complete in under 3 seconds for typical commits (1–5 raw files); support parallel validation.
- Preserve the `git commit --no-verify` escape hatch as standard behavior.
- Allow schema evolution: when the schema itself is edited in the same commit, warn instead of reject.

**Non-Goals:**

- Do not validate any JSON outside `knowledge/raw/`. We will NOT schema-check `package.json`, lockfiles, workflow YAML, etc.
- Do not run network requests, linters, or formatters. This hook stays focused on one contract.
- Do not validate `git stash` or `git add -p` partial state. The hook runs on what is staged at commit time; standard git semantics.
- Do not install dependencies automatically. We document the `jsonschema` dep; installation is explicit.

## Decisions

**Decision 1: bash entry script + Python validator, not pure bash.**
JSON Schema validation in bash is unreliable. We use a 20-line `pre-commit` bash script that collects staged files via `git diff --cached --name-only --diff-filter=ACM` and invokes a small Python validator (`validate.py`) that uses the `jsonschema` library. Bash handles git, Python handles semantics.

**Decision 2: Schema location is `week1/specs/schemas/collector-output.json`.**
Reuse the Week 1 artifact. Do not copy or fork. This makes the Week 1 → Week 2 dependency explicit and is our first concrete example of "regular spec from a previous week becomes load-bearing in this week."

**Decision 3: Schema-change exception via staged-file inspection.**
If `git diff --cached --name-only` contains any `specs/schemas/*.json`, the hook downgrades `reject` to `warn`. Rationale: without this, a developer updating the schema and the raw files in the same commit cannot commit without --no-verify, which breaks the "trust the hook" contract. The warning still surfaces mismatches but does not block.

**Decision 4: Error message format is `{file}:{json_pointer} - {message}`.**
Matches standard compiler-like error output. Makes errors grep-able and IDE-clickable. Example: `knowledge/raw/2026-04-15.json:/items/3/scraped_at - expected string, got null`.

**Decision 5: No caching in v1.**
The validator runs from scratch every commit. For <10 staged files this is under 500ms total. Caching adds state-management complexity without enough payoff at this stage.

## Risks / Trade-offs

**Risk: `jsonschema` not installed → hook crashes on every commit.**
Mitigation: hook first checks `command -v jsonschema` and prints an install instruction if missing, exiting 0 (do not block commits on a missing dev dependency — dev should install when they see the message). We accept that a developer without the dep effectively skips validation; this is a deliberate trade-off against "blocking everyone until every env has the dep."

**Risk: Schema-change exception hides real violations.**
When both the schema and raw files change together, and the raw files violate the new schema, we only warn. This is a real gap. Mitigation: CI (Week 2 Session 7) runs a strict validation on every push, with no schema-change exception. Local = lenient for developer flow; CI = strict for truth.

**Trade-off: commit latency grows with staged raw file count.**
Parallel validation helps but is not instant. For commits staging >50 raw files, latency may exceed 3s. Acceptable because such bulk commits are rare and the validation is load-bearing.

**Trade-off: coupling to Python.**
We could write a pure-Node validator instead. Chosen Python because (a) Week 3 analyzer is Python, (b) `jsonschema` is the canonical Python validator, (c) course stack is already Python. Re-evaluate if Node becomes the dominant runtime later.
