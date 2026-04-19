# AI 知识库 · 三 Agent PRD · 参考版 v1.0

> Week 1 · 第 3 节 · B 路产出示例
> 跑 `grill-me` 问清"协作意图"后，先写这份高阶 PRD，再用 `to-issues` 展开成 3 份任务票（见 [issues/](./issues/)）。

## 总流程

每天 UTC 0:00 触发 · `collector → analyzer → organizer` 串行执行。

## Agent 职责

- **collector**: 抓 GitHub Trending Top 50 · 过滤 AI 相关 · 存 `knowledge/raw/{date}.json`
- **analyzer**: 读 raw · 给每条打 3 维度标签（tech / innovation / difficulty）· 存 `knowledge/tagged/{date}.json`
- **organizer**: 读 tagged · 整理成 `knowledge/articles/{date}.md`

## 开放问题（用 to-issues 展开为带 depends_on + acceptance 的任务票）

- 上游失败下游怎么办？
- 数据怎么传？文件标记 or 消息队列？
- 重跑策略？
- 进度追踪？

## 非功能约束

- **幂等性**：每个 Agent 执行前先检查 `.done` 文件 · 存在则跳过
- **强制重跑**：`--force` 参数可强制重跑 · 会先删除所有 `.done`/`.failed` 标记
- **数据源**：JSON Schema 放 [schemas/](./schemas/) · 作为 Agent 间契约的可执行真相源

## 选型说明

- **done 文件用 `touch` 不用 SQLite**：v1 文件就是真相源 · 不引入数据库依赖
- **串行不并行**：三个 agent 的输出量不大 · 串行足够 · 降低复杂度

---

**下一步**：运行 `to-issues` 展开为 [issues/01-collector.md](./issues/01-collector.md) / [issues/02-analyzer.md](./issues/02-analyzer.md) / [issues/03-organizer.md](./issues/03-organizer.md) 三份任务票。每份 issue 自带 `depends_on` / `acceptance` / 对应 schema，组合起来就是完整的协作契约。
