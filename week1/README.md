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

## 物料

- [specs/_template.md](./specs/_template.md) · 4 H2 spec 模板
- [specs/project-vision.md](./specs/project-vision.md) · 项目愿景示例
- [specs/github-trending-skill.md](./specs/github-trending-skill.md) · skill 需求规格
- [code/04/skills/github-trending/SKILL.md](./code/04/skills/github-trending/SKILL.md) · 可直接运行的 SKILL
