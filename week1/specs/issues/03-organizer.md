# Issue #03 · Organizer Agent

> Week 1 · 第 3 节 · to-issues 展开产物（参考版 v1.0）
> 源自 [../agents-prd.md](../agents-prd.md)

## Depends on

- [Issue #02 · Analyzer](./02-analyzer.md) — 必须先产出 `knowledge/tagged/{date}.json` + `.analyzer.done`

## Description

读取 `knowledge/tagged/{date}.json`，按 tech 分组整理成 Markdown 日报，写入 `knowledge/articles/{date}.md`。

## Trigger

- 监听 `knowledge/tagged/{date}.analyzer.done` 文件出现
- 或手动运行 `python -m agents.organizer --date 2026-04-20`

## Acceptance Criteria

### 数据契约

- [ ] 输入：`knowledge/tagged/{date}.json`
- [ ] 输出：`knowledge/articles/{date}.md`
- [ ] 按 `labels.tech` 分组 · 每组内按 `stars` 降序
- [ ] Markdown 格式：H1 日期 · H2 分类 · H3 单条（title + link + innovation 摘要）

### 完成标记

- [ ] 写完文章后 `touch knowledge/articles/{date}.organizer.done`

### 失败处理

- [ ] 文件写入失败 retry 3 次
- [ ] 最终失败写兜底文案 `knowledge/articles/{date}.md` 内容为"今日采集失败 · 请查 knowledge/incidents/{date}.md"
- [ ] 写入 `knowledge/incidents/{date}.md`

### 幂等性

- [ ] 执行前检查 `.organizer.done` · 存在则跳过
- [ ] `--force` 先删除再执行

### 可观测性

- [ ] 启动 / 结束写 `knowledge/logs/{date}.log`
- [ ] 日志含 `start_ts` / `end_ts` / `article_count` / `categories`

### 日度汇总

- [ ] 每天 UTC 0:30 触发另一个轻量 job（不在本 issue 范围）生成 `knowledge/status/{date}.md`
- [ ] 汇总三个 Agent 的状态（done / failed / skipped）· 连续 3 天失败告警（Week 2 Hooks 实现）
