# Week 1 · 物料

## 文章

- [SDD 的 95/5 原则](./advance/01-SDD的95-5原则.md)
- [SDD 工具四层金字塔](./advance/02-四层金字塔.md)
- [老项目逆向策略](./advance/03-老项目逆向策略.md)
- [Spec 的粒度怎么把握](./advance/04-Spec的粒度怎么把握.md)
- [AI 给的 spec 我该信多少](./advance/05-AI给的spec我该信多少.md)
- [SDD 遇到紧急 bug 怎么办](./advance/06-SDD遇到紧急bug怎么办.md)
- [团队里只有我想用 SDD 怎么办](./advance/07-团队里只有我想用SDD怎么办.md)

## 工具

Week 1 只装 3 个开源 skill（来自 [mattpocock/skills](https://github.com/mattpocock/skills)）：

```bash
# Claude Code
npx skills@latest add mattpocock/skills/grill-me        -a claude-code
npx skills@latest add mattpocock/skills/prd-to-plan     -a claude-code
npx skills@latest add mattpocock/skills/write-a-skill   -a claude-code

# OpenCode
npx skills@latest add mattpocock/skills/grill-me        -a opencode
npx skills@latest add mattpocock/skills/prd-to-plan     -a opencode
npx skills@latest add mattpocock/skills/write-a-skill   -a opencode
```

skill 靠 description 字段自动触发 · 无需 `/skill` 前缀。

---

## 📦 这个目录里的文件怎么用

每周有三类东西：**文章（advance/）· spec 参考（specs/）· 代码参考（code/）**。

### specs/ 和 code/ 是"B 路参考答案"不是"应 CV 的模板"

跟着实操讲义跑完 B 路，你会产出自己的 `specs/project-vision.md` / `specs/coding-standards.md` 等文件。**那是你的版本**——带你自己项目的业务特点。

本目录下的 `specs/` 存的是我（咖哥）带着 ai-knowledge-base v1-skeleton 跑出来的同名文件——**老师的版本**。

**两者的关系是"对照"，不是"上下游"**：

```
   你自己跑一遍  →  产出你的 specs/xxx.md
                           ↓
                      打开本目录对照
                           ↓
             发现差异 → 你自己解释"为什么差"
                           ↓
              这个差异就是本节你学到的东西
```

如果你发现自己的版本和老师版本几乎一样——那是你没把自己项目的特殊性想进去。
如果差异很大——那是健康的，你在真正做 SDD 而不是抄作业。

### 什么时候才 CV

两种情况可以直接 CV：

1. **跑完 B 路自己产出后**，发现某一段（比如 failure mode 的标准写法）老师版比你自己写的更严谨——CV 过来**补进你自己的版本**
2. **code/ 下的可运行示例**（比如 `04/skills/github-trending/SKILL.md`）——这是基础设施代码，不是设计产物，CV 进你的项目即可

### 本周物料清单

**specs/ · 4 份 B 路参考**

- `_template.md` · 4-H2 spec 空模板
- `project-vision.md` · N1 产出 · 项目愿景
- `coding-standards.md` · N2 产出 · 编码规范（grill-me 8 轮拷问后）
- `agents-collaboration.md` · N3 产出 · 三 Agent 协作契约 16 条
- `github-trending-skill.md` · N4 产出 · skill 需求规格
- `schemas/collector-output.json` · N3 产出 · JSON Schema
- `schemas/analyzer-output.json` · N3 产出

**code/ · 可运行示例**

- `02/AGENTS-coding-standards-section.md` · N2 · 合并进 AGENTS.md 的片段
- `03/agents/collector.md` · N3 · Sub-Agent 配置
- `03/agents/analyzer.md`
- `03/agents/organizer.md`
- `04/skills/github-trending/SKILL.md` · N4 · 可立即用的 SKILL
