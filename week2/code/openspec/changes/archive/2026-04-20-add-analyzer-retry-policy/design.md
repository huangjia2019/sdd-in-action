## Context

The AI knowledge base pipeline includes four steps: collect → analyze → organize → save. The analyzer step (`pipeline/pipeline.py::step_analyze`) uses an LLM API call via `pipeline/model_client.py::chat()` to process raw collected items. Currently, any transient API failure (timeout, rate limit, 5xx, connection reset) causes the entire step to abort, wasting tokens already spent on previous items and leaving the knowledge base empty for that day.

The pipeline runs daily and must be resilient to temporary API outages while maintaining cost tracking accuracy. The existing code has no retry logic at the LLM call layer.

## Goals / Non-Goals

**Goals:**
- Add retry‑with‑backoff logic to the `chat()` function to handle transient API failures
- Ensure pipeline continues processing subsequent items even when an individual item fails after retries
- Maintain accurate cost tracking across retry attempts (count each API call, record tokens only for successful attempts)
- Keep the change focused and minimal, affecting only the analyzer step

**Non-Goals:**
- Provider‑level fallback (e.g., switching from OpenAI to DeepSeek) – future iteration
- Circuit‑breaker pattern (stop calling after N consecutive failures) – insufficient ROI for current scope
- Asynchronous or concurrent retries – keep synchronous simplicity
- Respecting `Retry‑After` headers – uniform exponential backoff simplifies implementation
- Modifying `step_collect`, `step_organize`, or `step_save` – scope limited to analyzer

## Decisions

1. **Decorator pattern** – Wrap `chat()` with a `@with_retry` decorator that intercepts the call and applies retry logic. This keeps the core `chat()` function clean and separates concerns.

2. **Retriable exceptions** – Retry on:
   - `APITimeoutError`, `APIConnectionError`, `RateLimitError` (custom exceptions from the client)
   - `httpx.TimeoutException`, `httpx.ConnectError` (transport‑layer errors)
   - `APIStatusError` where `status_code >= 500` (server‑side errors)
   
   Non‑retriable exceptions (content‑layer errors that would not benefit from retry):
   - `json.JSONDecodeError`, `KeyError`, `ValueError`

3. **Retry policy** – Exponential backoff with capped maximum delay:
   - `max_attempts = 3` (initial attempt + up to two retries)
   - `base_delay = 1.0` second, multiplier = 2.0
   - `max_delay = 20.0` seconds (cap to avoid excessive waiting)
   - Jitter: multiply each delay by a random factor between 1.0 and 1.5 (only positive jitter to avoid thundering herd)

4. **Fallback behavior** – After exhausting retries, the item is marked as `degraded` (status field set to `"degraded"`). The pipeline continues processing remaining items. The degraded item receives a placeholder summary (e.g., empty strings) so the overall daily knowledge base is still produced, albeit with one incomplete entry.

5. **Cost tracking** – Every API call (including failed retries) increments a cost‑tracker counter. Token counts are recorded only for successful responses (via `response.usage`). Failed attempts count as zero tokens.

## Risks / Trade-offs

- **Increased latency** – Retries add delay (up to 1+2+4 = 7 seconds plus jitter). This extends total pipeline runtime but ensures completion.
- **Cost‑tracking complexity** – Counting each attempt separately may slightly over‑count API calls in metrics, but preserves accurate token accounting.
- **Degraded items** – Items that fail after retries produce placeholder content. This trades off completeness for resilience; the pipeline still outputs a daily knowledge base rather than none.
- **Jitter direction** – Using only positive jitter (multiply delay) avoids reducing delays below the calculated backoff, which could worsen overload situations. This is a conservative choice that may increase total wait time slightly.
- **Testing challenges** – Simulating transient failures requires mocking or injecting faults. The test suite must verify both retry behavior and fallback logic.