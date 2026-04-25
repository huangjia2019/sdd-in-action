# Design: add-analyzer-retry-policy

> 本文档是 `add-analyzer-retry-policy` change 的技术实现蓝图。
> 严格对应 `proposal.md` 的 scope，不改动 `step_collect / step_organize / step_save`。

---

## 1. 异常分类体系

### 1.1 Transient Exceptions（可重试）

从 `openai` 和 `httpx` 两个库导入，retry 装饰器只 catch 以下异常：

```python
# model_client.py
from openai import APITimeoutError, RateLimitError, APIStatusError, APIConnectionError
from httpx import TimeoutException as httpx_TimeoutException
from httpx import ConnectError as httpx_ConnectError

TRANSIENT_EXCEPTIONS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,           # 仅当 status_code >= 500 时重试（见 1.2）
    httpx_TimeoutException,
    httpx_ConnectError,
)
```

### 1.2 Content Exceptions（不重试）

```python
CONTENT_EXCEPTIONS = (
    json.JSONDecodeError,
    KeyError,
    ValueError,
)
```

> 判定逻辑：`isinstance(exc, CONTENT_EXCEPTIONS)` → 直接 raise，不 retry
> `APIStatusError` 需要额外判断 `exc.status_code >= 500`，否则 raise

---

## 2. `with_retry` 装饰器设计

### 2.1 签名与参数

```python
@with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,     # 秒，初始退避基础值
    max_delay: float = 30.0,      # 秒，延迟上限
    jitter: float = 0.5,         # 秒，随机抖动幅度
    retry_on: tuple[type[Exception], ...] = TRANSIENT_EXCEPTIONS,
)
def chat(prompt: str, system: str = "你是一个专业的技术分析师。",
         temperature: float = 0.3, max_tokens: int = 2000) -> ChatResponse:
```

### 2.2 退避算法

```
attempt = 0
delay   = base_delay

while attempt <= max_retries:
    try:
        result = _call_llm_once(...)
        return result
    except TRANSIENT_EXCEPTIONS as e:
        attempt += 1
        if attempt > max_retries:
            raise  # 装饰器层不 catch，交给 step_analyze 处理
        sleep(delay + random.uniform(-jitter, jitter))
        delay = min(delay * 2, max_delay)  # 指数增长，上限 cap
```

### 2.3 per-call 独立状态

```python
def with_retry(fn):
    def wrapper(*args, **kwargs):
        # 每个调用独立的状态，不共享
        attempt = 0
        delay = base_delay
        # ...
    return wrapper
```

- **不使用** class-level 或 module-level 的 shared state
- **不共享** attempt count / delay timer / retry budget
- 每次 `chat()` 调用进来都是全新的状态机

### 2.4 日志规范

每次 attempt 记录一条完整日志（logger.info）：

```python
logger.info(
    "[retry] attempt=%d/%d delay=%.2fs exception=%s prompt_len=%d",
    attempt, max_retries, delay, exc.__class__.__name__, len(prompt)
)
```

成功时：

```python
logger.info(
    "[retry] success attempt=%d prompt_tokens=%d completion_tokens=%d cost=¥%.6f",
    attempt, resp.prompt_tokens, resp.completion_tokens, cost
)
```

---

## 3. 降级路径（Degraded Continue）

### 3.1 降级条件

`chat()` 在 `max_retries + 1` 次尝试后仍失败，且异常是 transient 类型 → 进入降级路径。

装饰器本身**不 catch 耗尽异常**，直接 `raise`。降级逻辑由 `step_analyze` 处理（见 3.2）。

### 3.2 step_analyze 中的降级处理

```python
# pipeline/pipeline.py · step_analyze()

for i, item in enumerate(items, 1):
    prompt = build_prompt(item)
    try:
        response = chat(prompt)          # retry 发生在 chat() 内部，对这里透明
        analysis = parse_json_response(response.content)
        analyzed.append({**item, **analysis, "status": "ok", ...})

    except TRANSIENT_EXCEPTIONS as e:
        # 所有 retry 耗尽，transient 故障无法恢复 → 降级
        logger.warning("[degraded] %s failed after retries: %s", item['title'], e)
        degraded_item = {
            **item,
            "status": "degraded",
            "summary": item.get("description", "")[:200],
            "tags": ["unknown"],
            "relevance_score": 0.5,
            "category": "unknown",
            "key_insight": "",
            "degraded_reason": f"{e.__class__.__name__}: {str(e)}",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        analyzed.append(degraded_item)
        continue

    except CONTENT_EXCEPTIONS as e:
        # 内容层错误 → 走原有的 parse_failed 路径（不做 retry）
        logger.warning("[parse_failed] %s: %s", item['title'], e)
        analyzed.append({**item, ..., "status": "parse_failed", ...})
        continue
```

### 3.3 degraded_reason 字段说明

- **保留在 raw 层**（`analyzed` 列表内），用于 debug 追溯
- **不进入 article JSON**（`knowledge/articles/`），article schema 保持干净
- `step_organize` 输出 article 时显式排除 `degraded_reason`

### 3.4 step_organize 过滤 degraded item

在 `step_organize()` 函数中，`for item in items:` 循环的最前方加一行：

```python
if item.get("status") == "degraded":
    continue
```

> 这是 degraded continue 策略的必要组成部分：不在 proposal 原始 scope 内，但属于策略完整性所需的最少改动。

---

## 4. 成本追踪（cost_tracker）

### 4.1 追踪单位

- **Token 计数**：从 `response.usage.prompt_tokens` 和 `response.usage.completion_tokens` 读取
- **成本单位**：人民币元（默认 DeepSeek 定价）
- **失败 attempt**：token = 0，不计入 token 总量，但计入调用次数

### 4.2 日志字段

每次 `chat()` 返回后（无论成功失败）均记录：

```
[cost] prompt_tokens=N completion_tokens=N total_cost=¥X.XXXXXX status=ok|failed|degraded attempt=N
```

`total_cost` 字段：
- 成功：`estimate_cost(response.prompt_tokens, response.completion_tokens)`
- 失败（transient）：`0.0`

### 4.3 step_analyze 累加

```python
total_cost = 0.0
for item in items:
    try:
        response = chat(prompt)
        total_cost += estimate_cost(response.prompt_tokens, response.completion_tokens)
    except TRANSIENT_EXCEPTIONS:
        total_cost += 0.0   # 失败 attempt 不计入 token 成本，但仍触发 cost 日志
```

---

## 5. 最终 article schema（不变）

`knowledge/articles/{date}-{nnn}.json` 输出的字段**不受本次 change 影响**：

```json
{
  "id": "{date}-{nnn}",
  "title": "...",
  "url": "...",
  "source": "github",
  "summary": "...",
  "tags": ["..."],
  "relevance_score": 0.85,
  "category": "llm",
  "key_insight": "...",
  "collected_at": "...",
  "analyzed_at": "..."
}
```

`degraded_reason` **不出现**在 article JSON 中。

---

## 6. 模块职责划分

| 模块 | 职责 |
|------|------|
| `pipeline/model_client.py` | `with_retry` 装饰器、`TRANSIENT_EXCEPTIONS` 元组、`chat()` 函数 |
| `pipeline/pipeline.py` | `step_analyze()` 内的 try/except 降级路径 + `step_organize()` 的一行 degraded 过滤 |
| `tests/test_retry.py` | 覆盖正常调用、transient 重试成功、transient 耗尽降级、内容错误不重试 4 条路径 |

---

## 7. 文件改动清单

```
pipeline/model_client.py
  + TRANSIENT_EXCEPTIONS / CONTENT_EXCEPTIONS 常量
  + with_retry() 装饰器（内部含退避算法）
  + cost_logger helper
  ~ chat() 函数加 @with_retry 装饰器

pipeline/pipeline.py
  ~ step_analyze()：新增 except TRANSIENT_EXCEPTIONS 分支（降级路径）
  ~ step_analyze()：已有的 except json.JSONDecodeError 分支改名为 CONTENT_EXCEPTIONS
  ~ step_organize()：for 循环加一行 if item.get("status") == "degraded": continue

tests/test_retry.py
  + test_chat_success()
  + test_chat_transient_then_success()
  + test_chat_all_transient_failures_go_degraded()
  + test_chat_content_error_not_retried()
```

---

## 8. 验证要点（供 tasks.md 引用）

- [ ] transient 异常触发 retry，且达到 max_retries 后进入降级
- [ ] 内容层异常（JSONDecodeError / KeyError）不 retry，直接 raise 给 step_analyze
- [ ] per-call 独立：连续 3 个 item 都 429，每个 item 独立 retry 3 次
- [ ] 降级 item 的 `status == "degraded"`，summary 为 description[:200]
- [ ] 降级 item 不出现在 `knowledge/articles/` 最终输出中
- [ ] 成本日志包含每次 attempt 的记录（成功/失败均有）
- [ ] `step_analyze` 跑完 50 条，即使中间有 degraded 也不 abort
