# spec · Daily Digest Bot · 参考版 v1.0

> Week 4 · 第 16 节 · B 路产出
> Superpowers /brainstorm + BMAD PM × UX review + grill-me 的终态

## 要做什么

- 每天 UTC 0:30 读 `knowledge/articles/{date}.md`
- 选出 Top 5（按 `innovation_level` · 同级按 `stars` 排）
- 渲染成纯文本邮件 · 发给订阅者
- 邮件主题格式：`今日 5 条 AI 热点 · {Top1 标题}`（前 8 字辨识 · 后续勾起好奇）
- 取消订阅链接放邮件最底 · 字号正常 · 不隐藏

## 不做什么

- 不做 HTML 邮件（纯文本最稳定）
- 不做个性化推荐（mvp 一视同仁）
- 不做订阅管理界面（手动改 `subscribers.yaml`）
- 不做 Telegram / Webhook 渠道（mvp 只邮件）
- 不翻译

## 边界 & 验收

- 取关率指标 ≤ 5%（超过说明价值不够 · 应停推）
- 邮件发送 p99 延迟 < 10s（单个订阅者）
- 总发送时长 < 5 min（假设 <500 订阅者）
- SMTP 连接失败 · retry 3 次 · 指数退避
- 邮件大小 < 100KB

## 邮件结构

```
今日 5 条 AI 热点 · {top1_title}

{date} · 共 5 条精选

1. {title}
   {url}
   标签: {tech_category} · {difficulty}
   {description · 50 字内}

2. ...

───────────────────────────
完整内容 · {web_url}
取消订阅 · {unsubscribe_url}
```

## 怎么验证

- dry-run 模式 · 不真发邮件 · 看输出格式
- mock SMTP · 验证 retry 逻辑
- 邮件大小压测（10 条全量 description 应 < 100KB）
- subscribers.yaml 格式错 · 应优雅失败（不全员停发）
