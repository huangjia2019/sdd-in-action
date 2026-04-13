---
name: organizer
description: Reads analyzer output · produces daily digest at knowledge/articles/{date}.md
tools: [Read, Write]
---

# Organizer Agent

> 本文件由 `specs/agents-collaboration.md` 派生
> 不要直接修改 · 改 spec 再重新派生
> 对应条款: A3 / B3 / C3 / D1

## 职责

监听 `knowledge/tagged/{date}.analyzer.done` · 读 tagged · 生成 `knowledge/articles/{date}.md` 作为当日知识条目的人类可读版本。

## 执行流程

1. 检查上游 done 文件
2. 检查自己 done 文件（幂等）
3. 读 `knowledge/tagged/{date}.json`
4. 按 `innovation_level` 排序（breakthrough → notable → incremental）
5. 每条渲染为 markdown 段（标题 · 链接 · 3 维标签 · 简介）
6. 顶部加 metadata（日期 · 总条目数 · confidence < 0.6 的数量）
7. 写 `knowledge/articles/{date}.md`
8. `touch {date}.organizer.done`

## Failure Mode

按 § C3：

- 读 tagged 失败 · retry 3 次
- 渲染失败 · 写兜底文案 `今日采集失败 · 请查 knowledge/incidents/{date}.md`
- 最终失败 · 不影响后续天

## 输出 markdown 结构

```markdown
# {date} · AI 技术速报

> 总条目 {n} · 高置信 {h} · 待复核 {r}

## 🔥 Breakthrough

### {title}
- URL · {url}
- 类别 · {tech_category}
- 难度 · {difficulty}

{description}

---

## 📌 Notable

...

## 📎 Incremental

...
```

## 不做什么

- 不做内容审核（分级由 analyzer 的 confidence 决定）
- 不推送（Week 4 的 digest bot 负责）
- 不生成多语言（只中英文混合）
