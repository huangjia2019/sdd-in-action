# spec · pipeline runner · 参考版 v1.0

> Week 2 · 第 6 节 · B 路产出
> grill-me 4 轮拷问后的终态 · 重点是错误分类和幂等

## 要做什么

- 按顺序跑三个 agent：collector → analyzer → organizer
- 每个 agent 独立的 retry 策略（见"失败分类"）
- 统一日志输出到 `knowledge/logs/{date}.log`
- 状态写到 `knowledge/status/{date}.md`
- 支持 `--force` 强制重跑（忽略 .done 文件）
- 支持 `--skip-to <agent>` 从指定 agent 开始（debug 用）

## 不做什么

- 不并行跑三 agent（本期串行 · Week 3 多 agent 模式再考虑）
- 不自动清理历史日志（Week 2 N7 CI 里加 retention）
- 不发告警（Week 2 N7 的 Slack 处理）

## 失败分类（grill-me 第 1 轮）

| 错误类型 | 判断 | 策略 |
|---------|------|-----|
| 网络抖动 | HTTPError 5xx | retry 3 · 指数退避 1s/4s/16s |
| rate limit | HTTPError 429 | retry 5 · 等 `Retry-After` header |
| 认证 | 401/403 | 不 retry · 立即失败 · 告警 |
| LLM 格式 | JSONDecodeError / schema 不符 | retry 1 · 再错标 `confidence=0` 继续 |

## 边界 & 验收

- 单 agent 最长执行 5 min · 超时视为失败
- 整条 pipeline 最长 30 min · 超时强制终止
- 幂等：同日重跑检查 `.done` 文件 · 跳过已完成
- failure 日志必须包含 stack trace 和 request/response 摘要

## 怎么验证

- mock 网络 500 · 应 retry 3 次 · 最后失败
- mock auth 401 · 应立即失败不 retry
- 手动删 `.done` 文件 · 再跑应跳过
- `--force` 下 · `.done` 存在也重跑
- 单元测试覆盖率 ≥ 85%
