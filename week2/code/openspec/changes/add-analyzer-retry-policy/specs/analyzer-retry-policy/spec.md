## ADDED Requirements

### Requirement: Retry Policy for LLM API Calls

The `chat()` function in `pipeline/model_client.py` SHALL implement a retry decorator that retries transient failures with exponential backoff.

#### Scenario: Transient exception triggers retry
- **WHEN** `chat()` encounters a transient exception (`APITimeoutError`, `APIConnectionError`, `RateLimitError`, `httpx.TimeoutException`, `httpx.ConnectError`, or `APIStatusError` with status_code >= 500)
- **THEN** the system SHALL retry the call up to `max_attempts` times with exponential backoff starting at `base_delay` seconds

#### Scenario: Retry respects maximum delay cap
- **WHEN** a retry backoff delay exceeds `max_delay` seconds
- **THEN** the delay SHALL be capped at `max_delay` seconds

#### Scenario: Content exception does not trigger retry
- **WHEN** `chat()` encounters a content layer exception (`json.JSONDecodeError`, `KeyError`, or `ValueError`)
- **THEN** the exception SHALL be raised immediately without retry

#### Scenario: All retries exhausted triggers degraded status
- **WHEN** all retry attempts are exhausted and a transient exception persists
- **THEN** the item SHALL be marked with `status: "degraded"` and processing SHALL continue for remaining items

### Requirement: Per-Call Independent Retry State

Each invocation of `chat()` SHALL have independent retry state with no shared attempt count or delay timer across calls.

#### Scenario: Multiple items processed independently
- **WHEN** `step_analyze` processes multiple items in sequence
- **THEN** each item's retry budget SHALL be independent and reset for each item

### Requirement: Cost Tracking for All Attempts

The system SHALL track costs for every `chat()` call attempt, including failed retries.

#### Scenario: Successful call records actual cost
- **WHEN** `chat()` succeeds on attempt N
- **THEN** the cost SHALL be calculated from `response.usage.prompt_tokens` and `response.usage.completion_tokens`

#### Scenario: Failed retry attempt records zero cost
- **WHEN** `chat()` fails on a retry attempt
- **THEN** the cost SHALL be recorded as 0.0

#### Scenario: Degraded item excluded from articles
- **WHEN** `step_organize` processes items
- **THEN** items with `status: "degraded"` SHALL be excluded from the output articles

### Requirement: Retry Configuration Parameters

The `with_retry` decorator SHALL accept the following configuration:
- `max_attempts`: Maximum number of retry attempts (default: 3)
- `base_delay`: Initial backoff delay in seconds (default: 1.0)
- `max_delay`: Maximum backoff delay cap in seconds (default: 20.0)
- `jitter`: Random jitter range multiplier (default: 0.5)

#### Scenario: Jitter applied to each delay
- **WHEN** a retry delay is calculated
- **THEN** a random jitter of `uniform(-jitter, jitter)` SHALL be added to the base delay