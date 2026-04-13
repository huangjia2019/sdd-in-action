---
name: github-trending
description: Fetch today's GitHub trending repos filtered by AI/LLM/agent/ML topics. Use when user asks about popular AI projects, what's hot on GitHub today, trending open-source releases, or daily tech radar.
allowed-tools: [Bash, WebFetch]
---

# GitHub Trending · AI Filter

抓 github.com/trending 的 Top 50 · 过滤 AI 相关。

## 流程

1. 读 `specs/github-trending-skill.md` 里的 `FILTER_TOPICS` 列表
2. WebFetch `https://github.com/trending` (HTML)
3. 解析 top 50 repo 的 [name, url, stars, topics, description]
4. 过滤 topics 命中 FILTER_TOPICS 任一的 repo
5. 输出 JSON 到 stdout · schema 见 spec

## Failure Mode

- HTTP 超时（>10s）· 返回空数组 `[]` · 不抛异常
- HTML 结构变化（解析失败）· 日志 warn · 返回空数组
- 绝不输出非 JSON 内容

## Time Budget

≤ 10s total。if HTTP timeout, abort immediately with empty result.

## 自测

- "给我今天的 AI trending" → 应触发
- "帮我读 README" → 不应触发
- "上周热门" → 不应触发（本 skill 只做今日）
