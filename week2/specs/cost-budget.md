# spec · cost governance · 参考版 v1.0

> Week 2 · 第 8 节 · B 路产出
> 横切关注点 · 管所有 LLM 调用 · 不只是新代码

## 预算（分三层）

- **单次调用** · `< $0.02` 异常值立即记录 warn
- **每日** · `< $5` 硬上限
- **每月** · `< $100` 季度复盘调整

## 告警（按比例 · 不硬编码绝对数）

- 日消耗 50% · info log · 不打扰
- 日消耗 80% · Slack warn → `#devops`
- 日消耗 100% · Slack critical + 邮件 team lead
- 日消耗 120% · PagerDuty + 停 pipeline

## 降级策略（自动执行 · 不依赖人工判断）

- 80%-100% · 自动切便宜模型（Haiku 替 Sonnet）
- 100%-120% · 跳过非关键 agent（organizer 可跳）
- 120%+ · 停 pipeline · 写 `incidents/{date}.md`

## 覆盖范围

- v2-automation 的所有 LLM 调用（带 `@track_llm_call` 装饰）
- v1-skeleton 通过 `/opsx:onboard` 补挂钩 · 一并监控
- 每次调用记录：`timestamp · agent · model · input_tokens · output_tokens · cost_usd`

## 数据存储

- 实时累计：`cost/{date}.jsonl` · 每次调用追加一行
- 每日汇总：`cost/{date}.summary.json` · 0:30 UTC 生成
- 月度汇总：`cost/{month}.summary.json` · 每月 1 日生成

## 怎么验证

- 单元测试：mock LLM 调用 · 验证成本累计正确
- mock 成本超 80% · 应看到 warn 日志 + Slack 消息
- mock 成本超 100% · 应自动切模型
- mock 成本超 120% · pipeline 应退出且有 incident 记录
