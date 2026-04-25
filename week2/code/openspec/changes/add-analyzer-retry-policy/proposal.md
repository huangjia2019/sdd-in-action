# Proposal: add-analyzer-retry-policy

## Summary

给 `pipeline/model_client.py::chat()` 加上 per-call retry 装饰器，专治 LLM 调用时的瞬时故障（timeout / 429 / 5xx / connection reset）。重试耗尽后走 degraded continue 模式，不 abort pipeline，不让前面花的 tokens 沉没。

## Motivation

当前 `chat()` 裸调 API，任意一个瞬时故障（APITimeoutError / RateLimitError / APIStatusError / APIConnectionError）就直接向上抛。`step_analyze()` 的 for 循环会在第 N 条 item crash，整个 pipeline 中断：

- 第 1~N-1 条的 token 成本已花，但 pipeline 没跑完，当日知识库为空
- 重启后从头跑，又要重新花第 1~N-1 条的 token

50 条跑到第 30 条挂 = 前 29 条 token 白扔。

## Scope

### 改
- `pipeline/model_client.py` · `chat()` 函数内部加 retry 装饰器
- `pipeline/pipeline.py` · `step_analyze()` 末尾加 degraded item 过滤逻辑（只改末尾，不动循环主体）
- `tests/test_retry.py` · 新建，覆盖正常/瞬时失败/内容失败三种路径

### 不改
- `step_collect`
- `step_organize`（已在内部按 `status` 过滤）
- `step_save`
- 其他任何文件

## Design

### 1. 异常分类

```
可重试（transient）                    不可重试（content）
──────────────────────────────────────  ──────────────────────────────────
APITimeoutError                         JSONDecodeError
RateLimitError (429)                    KeyError / ValueError（LLM 返回缺字段）
APIStatusError (status_code >= 500)     其他所有内容解析类异常
APIConnectionError
httpx.TimeoutException
httpx.ConnectError
```

重试装饰器只 catch 左侧。右侧异常直接 `raise`，不做任何重试。

### 2. retry 装饰器设计

```python
# 伪签名
@with_retry(max_retries: int = 3,
            base_delay: float = 1.0,
            max_delay: float = 30.0,
            retry_on: tuple[type[Exception], ...] = (transient_exceptions,))

def chat(prompt, system, temperature, max_tokens) -> ChatResponse:
    ...
```

- **per-call 独立**：每个 `chat()` 调用维护自己的 attempt count 和 backoff timer，互不干扰
- **指数退避**：`delay = min(base_delay * 2^attempt, max_delay)` + jitter
- **对上层透明**：`step_analyze()` 的 for 循环不感知 retry 存在，拿到的是最终结果（成功 or 抛异常）
- **每次调用必留日志**：`attempt=1/3`, `delay=2.5s`, `exception=RateLimitError` 等

### 3. 重试耗尽后的降级路径

当某条 item 的 `chat()` 在 `max_retries` 次尝试后仍失败（且是 transient 异常）：

```
step_analyze() 内部:
  item['status'] = 'degraded'
  item['summary'] = item['description'][:200]   # 兜底摘要
  item['tags']   = ['unknown']
  item['regraded_reason'] = '<异常类型>: <最后一条异常消息>'
  analyzed.append(item)   # 继续循环，不 abort
  continue  # 处理下一条
```

关键约束：**绝对不 abort `step_analyze()`**，循环必须跑完整条 items 列表。

### 4. 成本追踪

| 场景 | token 记录 | 成本记录 |
|------|-----------|---------|
| `chat()` 成功 | `response.usage.prompt_tokens` + `response.usage.completion_tokens` | 计入 `total_cost` |
| `chat()` retry 中某次失败 | 该次 attempt token = 0 | 计入调用次数，不计入 token 成本 |
| `chat()` 重试耗尽（transient） | token = 0 | 调用次数 + 失败状态 + 异常类型全量记录 |

所有 attempt（成功/失败）的日志必须包含：`attempt_number`、`exception_type`、`delay_used`，支持事后追溯。

### 5. step_analyze 返回值

`step_analyze` 返回的 `analyzed` 列表中，item 可能处于两种状态：

| status | 含义 | 是否进 step_organize |
|--------|------|---------------------|
| `ok` | LLM 分析成功 | ✅ 是 |
| `parse_failed` | LLM 返回了但 JSON 解析失败 | ✅ 是（走降级默认值） |
| `degraded` | 重试耗尽，transient 故障无法恢复 | ❌ 被 step_organize 过滤 |

`step_organize` 不需要任何代码改动——它本来就会检查 `item.get("regraded_reason")` 或在实践中检查 `status == "degraded"` 的过滤逻辑（需要确认 `step_organize` 有这个过滤，如果没有则需要微调一行）。

> 注：`step_organize` 目前按 `relevance_score < min_score` 过滤，还没有 `status` 过滤。需要确认是否加一行过滤 `status == "degraded"` 的 item。

### 6. 数据流

```
knowledge/raw/github-{date}.json
         │
         ▼
step_collect() → step_analyze(items)
                        │
                        ▼  for item in items:
                        chat() ──── retry 1~3 ──── 成功 ──→ JSON parse ──→ status="ok"
                        │                                  │
                        │                     JSONDecodeError ──→ status="parse_failed"
                        │
                        └── retry × 3 全部失败 ──→ status="degraded" + description[:200]
                        │
                        ▼
               analyzed: list[dict]  (可能含 ok / parse_failed / degraded)
                        │
                        ▼
step_organize(items)  ── 过滤掉 status="degraded" ──→
                        │
                        ▼
step_save(articles) → knowledge/articles/{date}-{nnn}.json
```

## Non-goals

- provider 级 fallback（OpenAI 挂了切 DeepSeek）—— 未来课题
- circuit breaker
- async / 并发重试
- 改动 `step_collect` / `step_organize` / `step_save`

## OpenSpec Artifacts

| Artifact | Location |
|---------|----------|
| Proposal | `openspec/changes/add-analyzer-retry-policy/proposal.md` |
| Design | `openspec/changes/add-analyzer-retry-policy/design.md` |
| Spec | `openspec/specs/analyzer-retry-policy/spec.md` |
| Tasks | `openspec/changes/add-analyzer-retry-policy/tasks.md` |

## Capability

`analyzer-retry-policy` · LLM 调用层 per-call retry + degraded continue
