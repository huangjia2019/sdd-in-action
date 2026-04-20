"""
Analyzer Agent — 内容分析节点

职责：对采集到的每条原始数据做 LLM 分析，生成 summary/tags/relevance/category/key_insight。

核心原则：一次一条（Analyze one at a time）。
Analyzer 不做跨条目的聚合——每条数据独立分析，保持职责单一。
"""

import json

from workflows.model_client import accumulate_usage, chat_json
from workflows.state import KBState


def analyze_node(state: KBState) -> dict:
    """分析节点：对采集到的原始数据进行 LLM 分析

    为每条数据生成:
    - 中文技术摘要 (200 字以内)
    - 相关标签 (英文)
    - 相关性评分 (0.0 - 1.0)
    - 技术领域分类
    - 一句话核心洞察
    """
    sources = state["sources"]
    analyses: list[dict] = []
    tracker = state.get("cost_tracker", {})

    for item in sources:
        # 跳过错误条目
        if item.get("title", "").startswith("[ERROR]"):
            continue

        prompt = f"""请分析以下技术项目/文章，用 JSON 格式返回：

项目名: {item['title']}
描述: {item.get('description', '无描述')}
来源: {item['source']}
URL: {item.get('url', '')}

请返回以下格式的 JSON:
{{
    "summary": "200字以内的中文技术摘要",
    "tags": ["标签1", "标签2", "标签3"],
    "relevance_score": 0.8,
    "category": "分类（如: llm, agent, rag, tool, framework）",
    "key_insight": "一句话核心洞察"
}}"""

        try:
            result, usage = chat_json(prompt)
            tracker = accumulate_usage(tracker, usage)

            analyses.append({
                **item,
                "summary": result.get("summary", ""),
                "tags": result.get("tags", []),
                "relevance_score": result.get("relevance_score", 0.5),
                "category": result.get("category", "other"),
                "key_insight": result.get("key_insight", ""),
            })
        except Exception as e:
            print(f"[Analyzer] 分析失败: {item['title']} - {e}")
            analyses.append({
                **item,
                "summary": f"分析失败: {e}",
                "tags": [],
                "relevance_score": 0.0,
                "category": "error",
                "key_insight": "",
            })

    print(f"[Analyzer] 完成 {len(analyses)} 条分析")
    return {"analyses": analyses, "cost_tracker": tracker}
