"""
Organizer Agent — 整理入库节点

职责：将通过审核的 analyses 整理成标准知识条目并持久化到磁盘。

核心原则：只整理不审核（Organize, don't review）。
Organizer 是工作流的**正常终点**——只有 Reviewer 通过后才会到达这里。
它不评价质量，只负责格式转换和写盘。

步骤:
    1. 按 plan.relevance_threshold 过滤低质条目
    2. URL 去重
    3. 格式化为标准 article 结构
    4. 写入 knowledge/articles/*.json
    5. 更新索引 index.json
"""

import json
import os
from datetime import datetime, timezone

from workflows.state import KBState


def organize_node(state: KBState) -> dict:
    """Organizer 节点：整理入库（工作流正常终点）"""
    analyses = state.get("analyses", [])
    plan = state.get("plan", {}) or {}
    tracker = state.get("cost_tracker", {})

    threshold = float(plan.get("relevance_threshold", 0.6))

    # Step 1: 相关性过滤
    qualified = [a for a in analyses if a.get("relevance_score", 0) >= threshold]

    # Step 2: URL 去重
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for item in qualified:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)

    # Step 3: 格式化为标准 article
    articles: list[dict] = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i, item in enumerate(unique):
        articles.append({
            "id": f"{today}-{i:03d}",
            "title": item.get("title", ""),
            "source": item.get("source", "unknown"),
            "url": item.get("url", ""),
            "collected_at": item.get("collected_at", ""),
            "summary": item.get("summary", ""),
            "tags": item.get("tags", []),
            "relevance_score": item.get("relevance_score", 0.5),
            "category": item.get("category", "other"),
            "key_insight": item.get("key_insight", ""),
        })

    print(f"[Organizer] 整理出 {len(articles)} 条知识条目（准备入库）")

    # Step 4 & 5: 写盘 + 更新索引
    _save_articles_to_disk(articles, tracker)

    return {"articles": articles, "cost_tracker": tracker}


def _save_articles_to_disk(articles: list[dict], tracker: dict) -> None:
    """把 articles 写入 knowledge/articles/ 并更新 index.json"""
    if not articles:
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    articles_dir = os.path.join(base_dir, "knowledge", "articles")
    os.makedirs(articles_dir, exist_ok=True)

    for article in articles:
        filepath = os.path.join(articles_dir, f"{article['id']}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

    # 更新索引（追加新条目，不重复）
    index_path = os.path.join(articles_dir, "index.json")
    index: list[dict] = []
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

    existing_ids = {entry["id"] for entry in index}
    for article in articles:
        if article["id"] not in existing_ids:
            index.append({
                "id": article["id"],
                "title": article["title"],
                "category": article.get("category", "other"),
                "relevance_score": article.get("relevance_score", 0.5),
            })

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"[Organizer] 已写入 {len(articles)} 篇到磁盘")
    print(f"[Organizer] 本次运行总成本: ¥{tracker.get('total_cost_yuan', 0)}")
