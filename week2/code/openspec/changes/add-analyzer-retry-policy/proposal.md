# Proposal: add-analyzer-retry-policy

## Why

sdd-in-action/week2/code 的 analyzer（`pipeline/pipeline.py::step_analyze`）在 LLM API
调用层没有重试逻辑。历史事故：采集 50 条跑到第 23 条 timeout，脚本退出，前 22 条的
token 成本 ¥0.04 沉没，当天知识库空。LLM API 的瞬时故障（timeout / rate limit /
connection reset / 5xx）是常态，pipeline 必须自己扛住这一层抖动。

## What

在 `pipeline/model_client.py` 新增 `with_retry` 装饰器，套在 `chat()` 上实现指数
退避重试：

- **可重试异常**：`APITimeoutError`、`APIConnectionError`、`RateLimitError`、
  `httpx.TimeoutException`、`httpx.ConnectError`、`APIStatusError where status_code >= 500`
- **不可重试异常**：`json.JSONDecodeError`、`KeyError`、`ValueError`
  （内容层错误 · 重试无效）
- **重试策略**：max_attempts=3，base_delay=1s，指数退避 1s → 2s → 4s，
  max_delay=20s 封顶，jitter 1.0-1.5× 只加不减（防雪崩）
- **成本追踪**：每次 API 调用（包括失败的重试）都记一次 cost_tracker，
  失败的 tokens=0，成功的按 response.usage 记
- **终极失败**：max_attempts 用完仍失败 → 沿用现有 fallback（降级 summary），
  该 item 的 `status` 字段标记 `"degraded"`，pipeline 继续跑完其他 items

## Out of scope

- 不做 provider 级 fallback（OpenAI 挂了切 DeepSeek）—— 未来迭代
- 不做 circuit breaker（连续失败 N 次后停止调用）—— ROI 不够
- 不做 async / 并发重试 —— 保持同步简单
- 不吃 `Retry-After` header —— 统一走 exp backoff 简化实现
- 不改 step_collect / step_organize / step_save —— 作用域就这一个函数