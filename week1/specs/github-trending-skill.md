# skill: github-trending · spec v1.0

> Week 1-04 的 B 路产出示例

## 要做什么

- 抓 `github.com/trending`（HTML）· Top 50
- 过滤：repo topics 命中 `FILTER_TOPICS` 列表任一
- 输出 JSON 数组 · schema 见下

## 不做什么

- 不调 GitHub API（避开 rate limit）
- 不落库（只 stdout）
- 不做去重（由 caller 处理）
- 不做翻译

## 边界 & 验收

- 单次执行 ≤ 10s
- HTTP 超时返回空数组 · 不抛异常
- 输出必须通过 JSON Schema 验证
- 失败率 ≤ 5%（日统计）

## 怎么验证

```bash
# 在 OpenCode 会话里
> 今天 github 有什么热门 AI 项目？
# 应自动触发 skill · 返回 JSON

# 反例测试
> 帮我改 README 标题
# 不应触发
```

## FILTER_TOPICS

```yaml
topics:
  - ai
  - llm
  - agent
  - ml
  - machine-learning
  - deep-learning
  - rag
  - transformers
  - anthropic
  - openai
```

## 输出 Schema

```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["name", "url", "stars", "topics", "description"],
    "properties": {
      "name": {"type": "string"},
      "url": {"type": "string", "format": "uri"},
      "stars": {"type": "integer"},
      "topics": {"type": "array", "items": {"type": "string"}},
      "description": {"type": "string"}
    }
  }
}
```
