# analyzer-retry-policy

## Purpose

Retry transient LLM API failures with exponential backoff, while avoiding retries for content-layer errors and marking items as degraded after exhaustion.

## Requirements

### Requirement: Retry transient LLM API failures
The system SHALL retry LLM API calls that fail due to transient errors, using exponential backoff with jitter.

#### Scenario: Timeout triggers retry
- **WHEN** the `chat()` function raises an `openai.APITimeoutError` or `httpx.TimeoutException`
- **THEN** the call is retried up to 3 additional times (4 attempts total) with delays of 1s, 2s, 4s (plus positive jitter)

#### Scenario: Server error triggers retry
- **WHEN** the API returns a 5xx status code (`openai.APIStatusError` with `status_code >= 500`)
- **THEN** the call is retried with exponential backoff as above

#### Scenario: Rate limit triggers retry
- **WHEN** the API returns a rate‑limit error (`openai.RateLimitError`)
- **THEN** the call is retried with exponential backoff (not respecting `Retry‑After` header)

#### Scenario: Connection error triggers retry
- **WHEN** the HTTP transport raises `httpx.ConnectError` or `openai.APIConnectionError`
- **THEN** the call is retried with exponential backoff

### Requirement: Do not retry content‑layer errors
The system SHALL NOT retry API calls that fail due to content‑layer errors, as retrying would not resolve the issue.

#### Scenario: JSON decode error aborts immediately
- **WHEN** the API response body cannot be parsed as JSON (`json.JSONDecodeError`)
- **THEN** no retry is attempted; the item is marked as degraded immediately

#### Scenario: Missing required field aborts immediately
- **WHEN** the parsed response lacks a required field (`KeyError`) or contains invalid values (`ValueError`)
- **THEN** no retry is attempted; the item is marked as degraded immediately

### Requirement: Mark items as degraded after retry exhaustion
After exhausting all retry attempts, the system SHALL mark the item as degraded and continue pipeline execution.

#### Scenario: Fourth attempt fails
- **WHEN** the fourth API attempt (initial + three retries) still raises a retriable exception
- **THEN** the item's `status` field is set to `"degraded"` and a placeholder summary is generated (`summary="", tags="", relevance_score=0, category="", key_insight="")`

#### Scenario: Pipeline continues after degraded item
- **WHEN** an item is marked as degraded
- **THEN** the pipeline proceeds to process the next item without aborting the entire `step_analyze`

### Requirement: Track API call costs across retries
The system SHALL increment the cost‑tracker counter for every API call (including failed retries) and record token counts only for successful responses.

#### Scenario: Failed attempt counts as zero tokens
- **WHEN** an API call fails (retriable or non‑retriable)
- **THEN** the cost‑tracker records one API call with `tokens=0`

#### Scenario: Successful attempt records actual tokens
- **WHEN** an API call succeeds (any attempt)
- **THEN** the cost‑tracker records one API call with `tokens` taken from `response.usage`

### Requirement: Apply exponential backoff with capped maximum delay
Retry delays SHALL follow exponential backoff with a base of 1 second, multiplier of 2, and a maximum delay of 20 seconds.

#### Scenario: Delay calculation
- **WHEN** the first retry occurs
- **THEN** the delay is 1 second multiplied by a random factor between 1.0 and 1.5 (positive jitter)
- **WHEN** the second retry occurs
- **THEN** the delay is 2 seconds multiplied by a random factor between 1.0 and 1.5
- **WHEN** the third retry occurs
- **THEN** the delay is 4 seconds multiplied by a random factor between 1.0 and 1.5
- **WHEN** a calculated delay exceeds 20 seconds
- **THEN** the delay is capped at 20 seconds