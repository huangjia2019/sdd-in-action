# OpenSpec 项目上下文 · Week 2

> 本文件是 `/opsx:*` 每次执行时必读的项目上下文。**写得越具体，AI 跑偏概率越低**。

## 项目

**AI 知识库 · Week 2 基线版本**。四步流水线：`collect → analyze → organize → save`。

## 技术栈

- Python 3.11+
- LLM: OpenAI 兼容 API（DeepSeek / Qwen / OpenAI）· 通过 `.env` 的 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` 配置
- 依赖: `openai`, `python-dotenv`, `httpx`, `pytest`
- 无 Web 框架 · 纯 CLI

## 关键数据契约

- `knowledge/raw/github-{YYYY-MM-DD}.json` · collector 产出 · 列表
- `knowledge/articles/{YYYY-MM-DD}-{NNN}.json` · organizer 产出 · 单条 article
- LLM 返回 JSON · `{summary, tags, relevance_score, category, key_insight}`

## 项目约定

- 日志用 `logging.getLogger(__name__)`
- 路径用 `pathlib.Path`
- 瞬时故障（timeout / rate / 5xx）该 retry · **但目前代码没做**
- 内容层错误（JSONDecodeError / KeyError）**不**重试
- LLM 成本追踪单位 · 人民币元 · 定价 DeepSeek 参考

## 已知 gap（本周要用 OpenSpec 修的）

- `pipeline/model_client.py::chat()` 裸调 API · 瞬时故障直接崩 pipeline
- `pipeline/pipeline.py::step_analyze` 没有 degraded 降级路径
- 成本追踪没有区分 "成功调用" vs "失败重试" 的 tokens 消耗

## 术语表（避免 AI 理解偏差）

| 词 | 本项目里指 |
|:---|:---------|
| schema | **业务 JSON schema**（article 格式、collector 输出格式），**不是** OpenSpec 工件的 schema |
| hook | **git pre-commit hook**，**不是** LangGraph / React / OpenSpec 的 hook |
| capability | OpenSpec 里的能力单元（比如 `analyzer-retry-policy`） |
| change | OpenSpec 里一次待合并的 PR（位于 `openspec/changes/<name>/`） |
| spec | 这里特指 OpenSpec 工件 · 每个 capability 一份 `spec.md` |
