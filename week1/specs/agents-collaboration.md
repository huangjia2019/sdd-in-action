# AI 知识库 · 三 Agent 协作规格 · 参考版 v1.0

> Week 1 · 第 3 节 · B 路产出示例
> 跑完 `prd-to-plan` + `grill-me` 后的终态 · 共 16 条款分 4 组

## 总流程

每天 UTC 0:00 触发 · `collector → analyzer → organizer` 串行执行。

## Agent 职责

- **collector**: 抓 GitHub Trending Top 50 · 过滤 AI 相关 · 存 `knowledge/raw/{date}.json`
- **analyzer**: 读 raw · 给每条打 3 维度标签（tech / innovation / difficulty）· 存 `knowledge/tagged/{date}.json`
- **organizer**: 读 tagged · 整理成 `knowledge/articles/{date}.md`

---

## Group A · 数据契约（回答"数据怎么传？"）

- **A1** · collector 输出 schema: `{source, url, title, stars, topics, scraped_at}`，详见 [schemas/collector-output.json](./schemas/collector-output.json)
- **A2** · analyzer 输入读 `knowledge/raw/{date}.json` · 输出 `knowledge/tagged/{date}.json` · 加 `labels[3]`
- **A3** · organizer 读 `knowledge/tagged/{date}.json` · 输出 `knowledge/articles/{date}.md`
- **A4** · 所有 schema 用 JSON Schema 描述 · 放 [schemas/](./schemas/)

## Group B · 触发契约（"谁触发谁"）

- **B1** · collector 由 cron 每天 UTC 0:00 触发 · 写完 raw 后 `touch {date}.collector.done`
- **B2** · analyzer 监听 `{date}.collector.done` · 完成后 `touch {date}.analyzer.done`
- **B3** · organizer 监听 `{date}.analyzer.done` · 完成后 `touch {date}.organizer.done`
- **B4** · 失败不触发下游 · 由 failure SOP 处理

## Group C · 失败契约（"上游失败下游怎么办？"）

- **C1** · collector 失败 · retry 3 次（指数退避 1s/4s/16s）· 最终失败写 `{date}.collector.failed`
- **C2** · analyzer 失败 · retry 1 次 · 失败不阻塞其他天（今日 skip）
- **C3** · organizer 失败 · retry 3 次 · 最终写兜底文案 `今日采集失败 · 请查 knowledge/incidents/{date}.md`
- **C4** · 任一 Agent 失败 · 写入 `knowledge/incidents/{date}.md` 供人工复核

## Group D · 可观测性（"进度追踪？"）

- **D1** · 每个 Agent start/end 写 `knowledge/logs/{date}.log` · 含 `start_ts` / `end_ts` / `item_count`
- **D2** · 每天 0:30 生成 `knowledge/status/{date}.md` · 汇总三个 Agent 的状态
- **D3** · 连续 3 天失败告警（Week 2 Hooks 节引入具体实现）

---

## 幂等性（grill-me 最后一轮补的）

- 每个 Agent 执行前先检查 `.done` 文件 · 存在则跳过
- `--force` 参数可强制重跑 · 会先删除所有 `.done`/`.failed` 标记

## 选型说明

- **done 文件用 `touch` 不用 SQLite**：v1 文件就是真相源 · 不引入数据库依赖
- **串行不并行**：三个 agent 的输出量不大 · 串行足够 · 降低复杂度
