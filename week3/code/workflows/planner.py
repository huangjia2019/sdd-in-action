"""
Planner Agent — V3 知识库流水线的动态规划节点（节点 ①）

Planner 是这条流水线的"总指挥"：不负责执行，只负责决定"怎么做"。
它的输出（state["plan"]）被下游的 Collector / Organizer / Reviewer 共同消费。

【教学重点】
- Planner 只规划不执行（Plan, don't execute）
- 规划结果写入 state["plan"]，下游节点按策略行事
- 最小可运行实现：只读一个目标采集量，输出 3 档策略之一

实际生产中可扩展为：
- 基于数据密度、历史成本、时段、质量目标等多维度决策
- 调用 LLM 生成自然语言计划（而不是硬编码分支）
- 支持中途重规划（Replanner）

【为什么在 workflows/ 而不在 patterns/】
workflows/ 里每个文件对应 V3 流水线的一个 Agent 节点（一 Agent = 一文件）。
patterns/ 是和本流水线解耦的通用 Agent 设计模式演示（Router / Supervisor）。
Planner 是本流水线的节点 ①，所以放 workflows/，和其他 6 个节点一起。
"""

import os
from typing import Any


def plan_strategy(target_count: int | None = None) -> dict:
    """根据目标采集量选择执行策略

    这是最小可运行的 Planner 示例 —— 只读环境变量或传入参数，
    输出一个策略字典。其他节点通过 state["plan"] 读取。

    策略矩阵:
    - full:     每源抓 20 条，分析阈值 0.4，Review 迭代上限 3 次（深度优先）
    - standard: 每源抓 10 条，分析阈值 0.5，Review 迭代上限 2 次（平衡）
    - lite:     每源抓 5 条，分析阈值 0.7，Review 迭代上限 1 次（成本优先）

    Args:
        target_count: 期望采集总量，用于决定策略。None 时从环境变量读取。

    Returns:
        {
            "strategy": str,          # "full" | "standard" | "lite"
            "per_source_limit": int,  # 每个数据源最大采集条数
            "relevance_threshold": float,  # organize 节点的相关性过滤阈值
            "max_iterations": int,    # review_loop 的最大迭代次数
            "rationale": str,         # 决策理由（人类可读）
        }
    """
    if target_count is None:
        target_count = int(os.getenv("PLANNER_TARGET_COUNT", "10"))

    if target_count >= 20:
        return {
            "strategy": "full",
            "per_source_limit": 20,
            "relevance_threshold": 0.4,
            "max_iterations": 3,
            "rationale": f"目标 {target_count} 条，启用深度模式（质量优先）",
        }
    elif target_count >= 10:
        return {
            "strategy": "standard",
            "per_source_limit": 10,
            "relevance_threshold": 0.5,
            "max_iterations": 2,
            "rationale": f"目标 {target_count} 条，启用标准模式（平衡模式）",
        }
    else:
        return {
            "strategy": "lite",
            "per_source_limit": 5,
            "relevance_threshold": 0.7,
            "max_iterations": 1,
            "rationale": f"目标 {target_count} 条，启用精简模式（成本优先）",
        }


def planner_node(state: dict) -> dict:
    """LangGraph 节点包装：把 plan_strategy 的结果写入 state["plan"]

    这是 Planner 作为 LangGraph 节点的最简实现。
    挂在 graph 的入口，之后 collect/organize/review 都能读取 state["plan"]。
    """
    plan = plan_strategy()
    print(
        f"[Planner] 策略={plan['strategy']}, 每源={plan['per_source_limit']} 条, "
        f"阈值={plan['relevance_threshold']}, {plan['rationale']}"
    )
    return {"plan": plan}


if __name__ == "__main__":
    import json

    print("=" * 60)
    print("Planner 模式演示 — 3 种目标采集量的策略输出")
    print("=" * 60)
    for tc in [5, 15, 30]:
        print(f"\n【target_count={tc}】")
        print(json.dumps(plan_strategy(tc), ensure_ascii=False, indent=2))
