# AI 知识库 · 项目愿景 v1.0

> Week 1-01 的 B 路产出示例 · 你照着这个写自己的版本

## 要做什么

- 每天 UTC 0:00 触发 · 抓 GitHub Trending Top 50
- 过滤 topics 含 `ai` / `llm` / `agent` / `ml` 的 repo
- 三个 Agent 串行协作：collector → analyzer → organizer
- 输出结构化 JSON 知识条目 · 放 `knowledge/articles/YYYY-MM-DD.md`
- 单日处理目标：20-30 条知识点

## 不做什么

- 不做通用爬虫（只服务 AI 技术情报场景）
- 不做内容审核（信任上游源 · 不判断真假）
- 不做商业化推荐（无广告 · 无 SEO 优化）
- 不做跨语言翻译（只处理中英文混合）
- 不存商业数据库（只文件系统）

## 边界 & 验收

- 单日执行总耗时 < 10 min
- Token 成本 < $0.50 / 天
- 失败时产出 `knowledge/incidents/YYYY-MM-DD.md` · 不静默
- 连续 3 天失败告警
- 任意时刻可从 `knowledge/articles/` 找到最近 30 天的数据

## 怎么验证

- `make run` 一键跑完整流水线
- `make verify` 对照本 spec 自动检查（字段 / 性能 / 成本）
- CI 每次 PR 跑 smoke test（抓 3 条样本数据走完全程）
- 每周人工复核 1 次 · 看输出质量
