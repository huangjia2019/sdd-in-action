# spec · GitHub Actions daily-run workflow · 参考版 v1.0

> Week 2 · 第 7 节 · B 路产出
> 用 `/opsx:verify` 检查后的终态

## 要做什么

- 每天 UTC 0:00 触发（`schedule: cron: '0 0 * * *'`）
- 在 Ubuntu Latest 上跑 `python -m pipeline --date $(date -u +%Y-%m-%d)`
- 超时 30 min
- 失败时发 Slack 到 `#devops` 频道
- 成功时不通知（避免 spam）
- 允许手动触发（`workflow_dispatch`）用于调试
- 只在 main 分支触发

## 不做什么

- 不对非 main 分支触发
- schedule 成功不发 Slack
- 不保存超过 7 天的 artifact

## 边界 & 验收

- 密钥必须走 GitHub Secrets（`ANTHROPIC_API_KEY` · `SLACK_WEBHOOK`）
- Secrets 不能在日志里出现
- `concurrency` 控制 · 防止同一天被手动触发多次
- workflow 文件第 1 行必须有注释指向本 spec

## 怎么验证

- 手动 `workflow_dispatch` · 应能触发
- `schedule` 到点应自动触发
- 故意抛错 · Slack 应收到消息
- 成功跑一次 · Slack 不应收到消息
- `concurrency` 测试 · 并行触发应被取消一次
