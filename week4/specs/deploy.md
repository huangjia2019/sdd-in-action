# spec · Daily Digest 部署 · 参考版 v1.0

> Week 4 · 第 16 节 · B 路产出
> Superpowers /dockerize 后的终态

## 要做什么

- 用 docker compose 单机部署
- 容器内 cron 触发 · 每天 UTC 0:30
- 所有配置通过环境变量注入
- 日志走 stdout · `docker compose logs -f` 能看
- 订阅者列表 mount 进容器（只读）

## 不做什么

- 不上 Kubernetes（mvp 单机足够）
- 不用 host crontab（容器自包含更好迁移）
- 不 mount config 文件（用 env vars）
- 不做 SSL 证书管理（SMTP 用 STARTTLS · 交给邮件服务商）

## 环境变量

```
ANTHROPIC_API_KEY     # 用于生成邮件主题
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASS
FROM_EMAIL
WEB_BASE_URL          # 用于生成 {web_url} 和 {unsubscribe_url}
```

## 边界 & 验收

- `docker compose up -d` 一键起
- 首次启动应能识别"当日已发送"标记 · 不重发
- 容器 restart 后 cron 重新注册 · 不需要手动干预
- 镜像大小 < 200MB

## 怎么验证

- `docker compose build` 成功
- `docker compose up` · `docker compose exec daily-digest python -m daily_digest --dry-run` 应输出 digest
- 容器重启 · cron 仍生效
- 镜像 size 检查 · `docker images | grep daily-digest`
