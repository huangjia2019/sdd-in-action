# Tasks: add-analyzer-retry-policy

## 变更概述

给 `pipeline/model_client.py::chat()` 加上 per-call retry 装饰器，transient 故障重试耗尽后走 degraded continue，不 abort pipeline。

---

## Task 1 · model_client.py 加 retry 装饰器

**文件**: `pipeline/model_client.py`

**步骤**:
1. 从 `openai` 导入 `APITimeoutError, RateLimitError, APIStatusError, APIConnectionError`
2. 从 `httpx` 导入 `TimeoutException as httpx_TimeoutException, ConnectError as httpx_ConnectError`
3. 定义 `TRANSIENT_EXCEPTIONS = (...)` 元组
4. 定义 `CONTENT_EXCEPTIONS = (json.JSONDecodeError, KeyError, ValueError)`
5. 实现 `with_retry(max_retries, base_delay, max_delay, jitter, retry_on)` 装饰器，指数退避算法，对 chat() 透明
6. 给 `chat()` 函数加上 `@with_retry()` 装饰器
7. 每次 attempt 日志: `attempt=N/M delay=Xs exception=XXX`
8. 成功后日志含 prompt_tokens / completion_tokens / cost

**验收**:
- [ ] `openai` 库抛 APITimeoutError 时，chat() 自动重试直到耗尽
- [ ] 抛 json.JSONDecodeError 时不重试，直接 raise
- [ ] 每个 chat() 调用独立 retry 状态，互不影响
- [ ] 日志完整覆盖每次 attempt

---

## Task 2 · pipeline.py step_analyze 降级路径

**文件**: `pipeline/pipeline.py`

**步骤**:
1. `step_analyze()` 内新增 `except TRANSIENT_EXCEPTIONS as e:` 分支 → 降级 item，status="degraded"，summary=description[:200]，degraded_reason=异常信息，continue
2. `except json.JSONDecodeError as e:` 分支改名为 `except CONTENT_EXCEPTIONS as e:`（保持语义准确）
3. `step_organize()` 的 `for item in items:` 循环开头加 `if item.get("status") == "degraded": continue`

**验收**:
- [ ] 第 N 条 transient 失败后，step_analyze 继续处理第 N+1 条
- [ ] degraded item 的 status == "degraded"，summary == description[:200]
- [ ] degraded item 不出现在 step_organize 输出里

---

## Task 3 · tests/test_retry.py

**文件**: `tests/test_retry.py`（新建）

**步骤**:
1. 用 `pytest.mark.parametrize` 或独立函数覆盖 4 条路径:
   - `test_chat_success()` — 单次成功，无 retry
   - `test_chat_transient_then_success()` — 第 1 次 429，第 2 次 200
   - `test_chat_all_transient_failures_go_degraded()` — 3 次都是 transient → raise，验证 decorated function 抛异常给上层
   - `test_chat_content_error_not_retried()` — JSONDecodeError 不 retry，直接 raise
2. 用 `requests_mock` / `unittest.mock.patch` 模拟异常和响应
3. 验证 cost_logger 记录了每次 attempt

**验收**:
- [ ] 4 条测试路径全部通过
- [ ] pytest 运行无 warning

---

## Task 4 · 端到端验证

**步骤**:
1. 运行 `python3 -m pipeline.pipeline --limit 5`
2. 确认 pipeline 跑完不 crash
3. 确认 `knowledge/articles/` 有 5 条 article（假设无 degraded）
4. 如果中途有 429/5xx，看日志确认 retry 行为正确（attempt 递增）
5. 确认 `knowledge/raw/` 仍保留原始采集数据

**验收**:
- [ ] pipeline 完整跑完，输出含 token cost
- [ ] 无 Python 异常中断
