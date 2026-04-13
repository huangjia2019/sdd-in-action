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

# 备用 marketplace
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# 验证
/brainstorm --help
```

OpenCode 暂无官方 Superpowers 入口 · 可以把 skill 文件手工拷到 `~/.opencode/skills/`。

## 工具梯子完工

四周下来你装的工具：

| 周 | 工具 | 层级 | 装法 |
|----|------|-----|------|
| W1 | grill-me / prd-to-plan / write-a-skill | L1 | `npx skills add ... -a opencode` |
| W2 | OpenSpec | L3 | `npm i -g @fission-ai/openspec@latest` |
| W3 | BMAD | L4 | `npx bmad-method install` |
| W4 | Superpowers | L4 | `/plugin install superpowers@...` |

下个项目按需取用 · 不必全装。
