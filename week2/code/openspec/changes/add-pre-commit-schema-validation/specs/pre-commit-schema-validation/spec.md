## ADDED Requirements

### Requirement: Validate Staged Raw JSON

The pre-commit hook SHALL validate every staged file matching `knowledge/raw/*.json` against the schema at `week1/specs/schemas/collector-output.json` before allowing the commit to proceed.

#### Scenario: Valid raw JSON commits successfully

- **WHEN** the developer stages a `knowledge/raw/2026-04-15.json` file that conforms to the schema and runs `git commit`
- **THEN** the hook exits with code 0 and the commit proceeds

#### Scenario: Invalid raw JSON blocks the commit

- **WHEN** the developer stages a `knowledge/raw/2026-04-15.json` with a missing required field or wrong type and runs `git commit`
- **THEN** the hook exits non-zero, prints `{file}:{json_pointer} - {message}` for each violation, and the commit is aborted

### Requirement: Narrow Scope

The hook SHALL validate ONLY staged files whose path matches the glob `knowledge/raw/*.json`. It MUST NOT touch any other JSON files, YAML files, or other assets.

#### Scenario: Unrelated JSON is ignored

- **WHEN** the developer stages `package.json` and `knowledge/config/routes.json` without modifying `knowledge/raw/`
- **THEN** the hook performs no validation and exits with code 0

### Requirement: Schema-Change Exception

When the same commit stages at least one file matching `specs/schemas/*.json`, the hook SHALL downgrade any validation failure from reject to warning so that coordinated schema-and-data updates can land together.

#### Scenario: Schema edit plus raw data edit warns but allows commit

- **WHEN** the developer stages both `week1/specs/schemas/collector-output.json` and `knowledge/raw/2026-04-15.json`, and the raw file violates the new schema
- **THEN** the hook prints the violation(s) prefixed with `WARN:` and exits with code 0

#### Scenario: Pure data edit still rejects

- **WHEN** the developer stages only `knowledge/raw/2026-04-15.json` (no schema file staged) with a violation
- **THEN** the hook rejects with non-zero exit

### Requirement: Precise Error Format

On validation failure, the hook SHALL emit one line per violation in the format `{file_path}:{json_pointer} - {human_readable_message}`.

#### Scenario: Missing required field produces pointed error

- **WHEN** `knowledge/raw/2026-04-15.json` is missing the `scraped_at` field at item index 3
- **THEN** the hook prints `knowledge/raw/2026-04-15.json:/items/3/scraped_at - required field missing`

### Requirement: Performance Budget

The hook SHALL complete validation within 3 seconds for any commit staging up to 10 raw files, validating files in parallel.

#### Scenario: Typical commit stays under budget

- **WHEN** the developer stages 5 raw JSON files of typical size (≤200 items each)
- **THEN** total hook runtime is under 3 seconds on a standard developer laptop

### Requirement: Graceful Missing Dependency

If the `jsonschema` CLI is not installed, the hook SHALL print a single-line install instruction and exit with code 0 (do not block the commit).

#### Scenario: Fresh environment without jsonschema

- **WHEN** a developer with a freshly cloned repo runs `git commit` for the first time and has not installed `jsonschema`
- **THEN** the hook prints `jsonschema not installed. Install: pip install jsonschema. Skipping validation.` and exits with code 0

### Requirement: Bypass Remains Standard

The hook SHALL NOT interfere with git's standard `--no-verify` bypass.

#### Scenario: Developer uses --no-verify intentionally

- **WHEN** the developer runs `git commit --no-verify` with an invalid raw file staged
- **THEN** the hook is not executed and the commit proceeds
