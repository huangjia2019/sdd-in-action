# Week 4 · 物料

## 文章

- [Superpowers 的强制 TDD 是不是过度设计](./advance/01-Superpowers的强制TDD是不是过度设计.md)
- [从 grill-me 到 Superpowers · 四周的工具演化路径](./advance/02-从grill-me到Superpowers的演化路径.md)
- [Plugin 市场会让 SDD 变成另一种"党派斗争"吗](./advance/03-Plugin市场会让SDD变成另一种党派斗争吗.md)
- [grill-me + OpenSpec + BMAD + Superpowers 一起装会打架吗](./advance/04-四个工具一起装会打架吗.md)
- [SDD 四周下来 · 你真正带走的是什么](./advance/05-四周下来你真正带走的是什么.md)

## 工具

Week 4 装 Superpowers（Anthropic 官方市场 · 149K ★）：

```
# 在 Claude Code 会话里 · 不是 shell
/plugin install superpowers@claude-plugins-official

# 验证
/brainstorm --help
```

OpenCode 暂无官方 Superpowers 入口 · 可手工拷 skill 文件到 `~/.opencode/skills/`。

## 📦 物料 · B 路参考答案

> 怎么用？见 [Week 1 README](../week1/README.md#-这个目录里的文件怎么用)。**先自己跑，再对照，不 CV**。

**specs/ · 2 份**

- `digest.md` · N16 · Daily Digest Bot 功能规格
- `deploy.md` · N16 · docker compose 部署规格

**code/ · 可部署的毕业项目**

- `daily_digest.py` · 主 Python 脚本（SMTP + cron 触发）
- `Dockerfile` · 容器镜像定义
- `docker-compose.yml` · 单机部署

## 工具梯子完工

| 周 | 工具 | 层级 |
|----|------|-----|
| W1 | grill-me / prd-to-plan / write-a-skill | L1 |
| W2 | OpenSpec | L3 |
| W3 | BMAD | L4 |
| W4 | Superpowers | L4 |

下个项目按需取用 · 不必全装。
