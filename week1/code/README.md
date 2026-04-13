# Week 1 · code/ · B 路产出物

每节 B 路跑完 · SDD 产出的代码/配置文件放在这里 · **可以直接 CV 进你的 ai-knowledge-base/v1-skeleton**。

## 目录

| 节 | 产出 | 路径 |
|----|------|-----|
| 01 | 项目愿景 → AGENTS.md 初稿 | `01/AGENTS.md`（示例） |
| 02 | coding-standards 段 | `02/AGENTS-coding-standards.md`（片段） |
| 03 | 3 Agent 配置 | `03/agents/{collector,analyzer,organizer}.md` |
| 04 | SKILL.md | `04/skills/github-trending/SKILL.md` ★ |

> Week 1 只提供 04 的完整可运行 SKILL.md · 01-03 的"产出"本质是文档片段 ·
> 建议跟着讲义的 mock screen 自己跑一次 · 不要直接 CV（跑一次才有肌肉记忆）。

## 用法

1. Fork [ai-knowledge-base](https://github.com/huangjia2019/ai-knowledge-base)
2. 拷贝 `04/skills/github-trending/` 到你 fork 的 `v1-skeleton/.opencode/skills/`
3. 在 v1-skeleton 目录下跑 `opencode` · 问 "今天 github 有啥 AI 新项目"
4. 应自动触发 skill · 返回 JSON

如果没触发 · 检查 `SKILL.md` 的 `description` · 确认有"trending" / "github" / "AI" 等关键词。
