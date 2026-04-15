## 1. Scaffolding

- [ ] 1.1 Create `week2/code/hook/` directory (if not present) with README.md documenting the `jsonschema` dependency and install instruction
- [ ] 1.2 Create `week2/code/hook/requirements.txt` with `jsonschema>=4.0.0`
- [ ] 1.3 Verify `week1/specs/schemas/collector-output.json` is reachable from the hook's working directory

## 2. Validator implementation

- [ ] 2.1 Implement `week2/code/hook/validate.py` that takes a file path, loads the JSON, loads the schema, validates, and prints `{file}:{pointer} - {msg}` per violation
- [ ] 2.2 Add parallel file handling via `concurrent.futures` or equivalent for the multi-file case
- [ ] 2.3 Unit-test `validate.py` against the three scenarios: valid file, missing field, wrong type

## 3. Hook wrapper

- [ ] 3.1 Create `week2/code/hook/pre-commit` bash script: detect staged files via `git diff --cached --name-only --diff-filter=ACM`
- [ ] 3.2 Filter to `knowledge/raw/*.json` only; exit 0 if none match
- [ ] 3.3 Detect schema-change condition: scan staged list for `specs/schemas/*.json` → set `WARN_ONLY=1` flag
- [ ] 3.4 Invoke `validate.py` per matched file; aggregate exit codes
- [ ] 3.5 In WARN_ONLY mode, print `WARN:` prefix and exit 0; else exit with validator's code
- [ ] 3.6 Handle missing `jsonschema`: print install instruction, exit 0

## 4. Install path

- [ ] 4.1 Document `ln -s` or `git config core.hooksPath` install procedure in `week2/code/hook/README.md`
- [ ] 4.2 Add a `week2/code/hook/install.sh` convenience script
- [ ] 4.3 Verify installation works on a clean clone of the repo

## 5. Acceptance testing

- [ ] 5.1 Craft a valid `knowledge/raw/2026-04-15.json` fixture, stage and commit → SHOULD pass
- [ ] 5.2 Craft an invalid fixture (missing `scraped_at`), stage and commit → SHOULD be rejected with the exact error format
- [ ] 5.3 Stage both schema update and raw file with a new-schema violation → SHOULD warn and pass
- [ ] 5.4 Run with 10 raw files concurrently and measure latency → SHOULD stay under 3 seconds
- [ ] 5.5 Run on an env without `jsonschema` installed → SHOULD print install message and pass

## 6. Documentation

- [ ] 6.1 Update `week2/code/hook/README.md` with the schema-change exception rule and `--no-verify` semantics
- [ ] 6.2 Add a short section in `week2/README.md` linking to this change as a reference for Session N5
