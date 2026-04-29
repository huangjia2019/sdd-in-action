"""
pipeline/pipeline.py · 四步流水线（基线版本 · 无 retry）

Step 1: collect · 从 GitHub Trending 采集
Step 2: analyze · LLM 逐条分析
Step 3: organize · 去重 + 格式化
Step 4: save · 写入 knowledge/articles/

⚠️ 已知问题 · Step 2 调 LLM 时瞬时故障（timeout / rate limit / 5xx）会**直接崩溃**:
- 当前代码没有 retry · 第 N 条挂掉整个 pipeline 就没了
- 前 N-1 条的 token 成本沉没 · 当天知识库空
- 修复方法 · Week 2 的 OpenSpec 实操 · 走一个 add-analyzer-retry-policy change

运行方式:
    python3 -m pipeline.pipeline --limit 20
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from pipeline.model_client import RetryExhaustedError, chat, estimate_cost

logger = logging.getLogger(__name__)

# ── 目录 ──────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
RAW_DIR = BASE / "knowledge" / "raw"
ARTICLES_DIR = BASE / "knowledge" / "articles"


# ── Step 1: 采集 ──────────────────────────────────────────────
def step_collect(limit: int = 20) -> list[dict]:
    """从 GitHub Search API 抓 AI/Agent 相关热门项目"""
    one_week_ago = (
        datetime.now(timezone.utc) - __import__("datetime").timedelta(days=7)
    ).strftime("%Y-%m-%d")
    query = f"ai agent llm stars:>100 pushed:>{one_week_ago}"
    url = (
        f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}"
        f"&sort=stars&per_page={limit}"
    )

    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    items = []
    for repo in data.get("items", []):
        items.append(
            {
                "source": "github",
                "title": repo["full_name"],
                "url": repo["html_url"],
                "description": repo.get("description", "") or "",
                "stars": repo.get("stargazers_count", 0),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    with open(RAW_DIR / f"github-{today}.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"[Collect] {len(items)} 条 · 保存到 knowledge/raw/github-{today}.json")
    return items


# ── Step 2: 分析 ──────────────────────────────────────────────
def step_analyze(items: list[dict]) -> list[dict]:
    """逐条 LLM 分析 · 带指数退避重试和降级处理"""
    analyzed: list[dict] = []
    total_cost = 0.0

    for i, item in enumerate(items, 1):
        prompt = f"""请分析以下技术项目，用 JSON 格式返回：

项目: {item["title"]}
描述: {item.get("description", "")}
URL: {item.get("url", "")}

返回格式：
{{
    "summary": "200字以内中文摘要",
    "tags": ["标签1","标签2","标签3"],
    "relevance_score": 0.85,
    "category": "llm / agent / rag / framework / tool",
    "key_insight": "一句话洞察"
}}"""

        try:
            response = chat(prompt)
            # 成功调用 · 累计成本（基于实际 tokens）
            total_cost += estimate_cost(
                response.prompt_tokens, response.completion_tokens
            )
            # 记录 API 调用次数（用于成本跟踪）
            api_calls = response.api_calls
            # 前 api_calls-1 次失败尝试的零 token 成本
            for _ in range(api_calls - 1):
                total_cost += estimate_cost(0, 0)  # 零 token 成本（仅计数）

            try:
                # 解析 LLM 返回的 JSON · 去掉 markdown 包裹
                text = response.content.strip()
                if text.startswith("```"):
                    text = "\n".join(text.split("\n")[1:-1])
                analysis = json.loads(text)
                analyzed.append(
                    {
                        **item,
                        **analysis,
                        "status": "ok",
                        "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                print(
                    f"[Analyze] {i}/{len(items)} · {item['title']} (尝试 {api_calls} 次)"
                )
            except json.JSONDecodeError as e:
                # 内容层错误 · 降级默认值（但不 retry · 重试也是坏 JSON）
                logger.warning("分析结果解析失败: %s - %s", item["title"], e)
                analyzed.append(
                    {
                        **item,
                        "summary": item.get("description", "")[:200],
                        "tags": ["unknown"],
                        "relevance_score": 0.5,
                        "category": "unknown",
                        "key_insight": "",
                        "status": "parse_failed",
                        "analyzed_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        except RetryExhaustedError as e:
            # 重试耗尽 · 降级处理
            logger.warning("重试耗尽: %s - %s", item["title"], e)
            # 累计零 token 成本（每次 API 调用）
            for _ in range(e.api_calls):
                total_cost += estimate_cost(0, 0)
            # 生成占位符摘要（空值）
            analyzed.append(
                {
                    **item,
                    "summary": "",
                    "tags": [],
                    "relevance_score": 0.0,
                    "category": "",
                    "key_insight": "",
                    "status": "degraded",
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            print(
                f"[Analyze] {i}/{len(items)} · {item['title']} (降级，尝试 {e.api_calls} 次)"
            )

        except Exception as e:
            # 其他未预期的异常（应极少发生）· 仍降级处理
            logger.error("未预期异常: %s - %s", item["title"], e)
            analyzed.append(
                {
                    **item,
                    "summary": "",
                    "tags": [],
                    "relevance_score": 0.0,
                    "category": "",
                    "key_insight": "",
                    "status": "error",
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            print(f"[Analyze] {i}/{len(items)} · {item['title']} (错误)")

    print(f"[Analyze] 完成 {len(analyzed)} 条 · 成本 ¥{total_cost:.4f}")
    return analyzed


# ── Step 3: 整理 ──────────────────────────────────────────────
def step_organize(items: list[dict], min_score: float = 0.6) -> list[dict]:
    """按 relevance_score 过滤 + URL 去重 + 标准格式"""
    # 去重
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        if item.get("relevance_score", 0) < min_score:
            continue
        url = item.get("url", "")
        if url in seen:
            continue
        seen.add(url)
        unique.append(item)

    # 标准化
    articles: list[dict] = []
    today = datetime.now().strftime("%Y-%m-%d")
    for i, item in enumerate(unique):
        articles.append(
            {
                "id": f"{today}-{i:03d}",
                "title": item["title"],
                "url": item["url"],
                "source": item.get("source", "github"),
                "summary": item["summary"],
                "tags": item["tags"],
                "relevance_score": item["relevance_score"],
                "category": item["category"],
                "key_insight": item.get("key_insight", ""),
                "collected_at": item["collected_at"],
                "analyzed_at": item.get("analyzed_at", ""),
            }
        )

    print(f"[Organize] 过滤 + 去重后 {len(articles)} 条")
    return articles


# ── Step 4: 保存 ──────────────────────────────────────────────
def step_save(articles: list[dict]) -> None:
    """写入 knowledge/articles/ + 更新 index.json"""
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for article in articles:
        with open(ARTICLES_DIR / f"{article['id']}.json", "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

    # 更新 index
    index_path = ARTICLES_DIR / "index.json"
    index = json.load(open(index_path, encoding="utf-8")) if index_path.exists() else []
    existing_ids = {e["id"] for e in index}
    for a in articles:
        if a["id"] not in existing_ids:
            index.append(
                {"id": a["id"], "title": a["title"], "category": a["category"]}
            )
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"[Save] 写入 {len(articles)} 条 → {ARTICLES_DIR}")


# ── 主流程 ────────────────────────────────────────────────────
def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="四步知识库流水线（基线版 · 无 retry）"
    )
    parser.add_argument("--limit", type=int, default=20, help="采集上限")
    parser.add_argument("--min-score", type=float, default=0.6, help="相关性阈值")
    args = parser.parse_args()

    items = step_collect(limit=args.limit)
    analyzed = step_analyze(items)  # ← 这里会因为瞬时故障 crash
    articles = step_organize(analyzed, min_score=args.min_score)
    step_save(articles)

    print("\n✅ 流水线完成")


if __name__ == "__main__":
    main()
