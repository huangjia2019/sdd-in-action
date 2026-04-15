## Why

The `knowledge/raw/*.json` files produced by the collector agent are the contract between collector → analyzer. When a bad JSON slips through (missing fields, wrong types), the downstream analyzer fails silently or produces garbage, and the failure only surfaces hours later during analyze or organize. We need the schema violation caught at the moment the file enters the repo.

## What Changes

- Add a `pre-commit` git hook that validates any staged `knowledge/raw/*.json` files against `specs/schemas/collector-output.json` before the commit lands.
- Reject the commit with a precise error pointer (file + field path) when validation fails.
- When the schema itself (`specs/schemas/*.json`) is modified in the same commit, downgrade the reject to a warning to avoid the "can't ever commit a schema change" trap.
- Document the `jsonschema` CLI dependency in `week2/code/hook/README.md`.

## Capabilities

### New Capabilities

- `pre-commit-schema-validation`: Enforce JSON Schema contracts on `knowledge/raw/*.json` at git commit boundary, with targeted scope (only raw/), precise error reporting, and a deliberate schema-change exception.

### Modified Capabilities

<!-- None: this is a greenfield hook for the week-2 demo project -->

## Impact

- **Code added**: `week2/code/hook/pre-commit` (bash) + `week2/code/hook/validate.py` (schema runner)
- **Dependency added**: `jsonschema` Python package (declared in `week2/code/hook/requirements.txt`)
- **Schema referenced**: `week1/specs/schemas/collector-output.json` (unchanged, but becomes load-bearing)
- **Developer workflow**: `git commit` now runs schema validation on staged raw files (300-500ms overhead); `git commit --no-verify` bypasses as standard
- **Breaking change**: None (no prior hook to break)
