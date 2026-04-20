"""
HumanFlag Agent — 人工介入节点（异常终点）

职责：审核循环超过 max_iterations 仍未通过时，记录现场 + 标记人工介入。

核心原则：优雅降级，不污染主知识库。
超过 3 次修改还没过，说明问题不在"质量"而在"数据"——需要人判断：
是丢弃这条数据？还是换一种处理方式？

HumanFlag 把这些数据写到独立的 knowledge/pending_review/ 目录，
不影响 knowledge/articles/ 主知识库的质量。
"""

import json
import os
from datetime import datetime, timezone

from workflows.state import KBState


def human_flag_node(state: KBState) -> dict:
    """HumanFlag 节点：循环超过 max_iterations 仍未通过时的兜底"""
    analyses = state.get("analyses", [])
    iteration = state.get("iteration", 0)
    feedback = state.get("review_feedback", "")
    plan = state.get("plan", {}) or {}
    max_iter = int(plan.get("max_iterations", 3))

    print(f"[HumanFlag] ⚠️ 达到 {max_iter} 次审核仍未通过，标记人工介入")
    print(f"[HumanFlag] 最后反馈: {feedback[:200]}")

    # 写入 pending_review 目录（不污染 articles/）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pending_dir = os.path.join(base_dir, "knowledge", "pending_review")
    os.makedirs(pending_dir, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    filepath = os.path.join(pending_dir, f"pending-{today}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": today,
                "iterations_used": iteration,
                "max_iterations": max_iter,
                "last_feedback": feedback,
                "analyses": analyses,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[HumanFlag] 已保存到 {filepath}，等待人工审核")

    return {"needs_human_review": True}
