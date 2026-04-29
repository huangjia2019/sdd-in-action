## 1. Retry decorator

- [x] 1.1 Create `with_retry` decorator in `pipeline/model_client.py`
- [x] 1.2 Define retriable exceptions: `APITimeoutError`, `APIConnectionError`, `RateLimitError`, `httpx.TimeoutException`, `httpx.ConnectError`, `APIStatusError` with status_code >= 500
- [x] 1.3 Define non‑retriable exceptions: `json.JSONDecodeError`, `KeyError`, `ValueError`
- [x] 1.4 Implement retry loop with `max_attempts=4` (initial + three retries)

## 2. Exponential backoff with jitter

- [x] 2.1 Calculate delay as `base_delay * (2 ** (attempt-1))` where `base_delay=1.0`
- [x] 2.2 Apply positive jitter: multiply delay by random factor between 1.0 and 1.5
- [x] 2.3 Cap maximum delay at 20 seconds (`min(delay, 20.0)`)
- [x] 2.4 Sleep between retries using `time.sleep()`

## 3. Cost tracking integration

- [x] 3.1 Increment cost‑tracker counter for every API call (including failed retries)
- [x] 3.2 Record token count as zero for failed attempts
- [x] 3.3 Record token count from `response.usage` for successful attempts

## 4. Fallback behavior

- [x] 4.1 After exhausting retries, mark item status as `"degraded"`
- [x] 4.2 Generate placeholder summary (empty strings for `summary`, `tags`, `relevance_score`, `category`, `key_insight`)
- [x] 4.3 Ensure pipeline continues processing next items (no abort)

## 5. Pipeline integration

- [x] 5.1 Apply `@with_retry` decorator to `chat()` function in `model_client.py`
- [x] 5.2 Modify `step_analyze` in `pipeline/pipeline.py` to handle `status == "degraded"` items
- [x] 5.3 Update logging to distinguish degraded items from successful ones

## 6. Testing

- [x] 6.1 Create `tests/test_retry.py` with test cases for retry logic
- [x] 6.2 Mock transient failures and verify retry attempts
- [x] 6.3 Verify non‑retriable exceptions abort immediately
- [x] 6.4 Verify degraded items are marked correctly
- [x] 6.5 Verify cost‑tracker counts calls accurately
- [x] 6.6 Run existing test suite to ensure no regressions