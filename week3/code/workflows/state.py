"""
LangGraph 状态定义 — AI 知识库工作流的核心数据结构

所有节点共享同一个 KBState，通过 TypedDict 保证类型安全。
每个节点只修改自己负责的字段，实现职责隔离。
"""

from typing import TypedDict


class KBState(TypedDict):
    """知识库工作流的全局状态

    数据流向: plan → sources → analyses → review ─[pass]→ organize → END
                                            ↓
                                          revise → review（循环）
                                            ↓[>max]
                                          human_flag → END

    Fields:
        plan: Planner 节点输出的执行策略 {strategy, per_source_limit, relevance_threshold, max_iterations, rationale}
        sources: 原始采集数据，来自 GitHub API / RSS 等
        analyses: 经 LLM 分析后的结构化结果（Reviewer 审的是这个，Reviser 改的也是这个）
        articles: 格式化、去重后的知识条目（只在 Organizer 通过后才产生，工作流正常终点的产出）
        review_feedback: 审核 Agent 的反馈意见（中文），Reviser 读这个决定怎么改
        review_passed: 审核是否通过（决定走 organize 还是 revise）
        iteration: 当前审核循环次数（0 起算）
        needs_human_review: 超过 max_iterations 仍未通过时置 True（human_flag 终点标记）
        cost_tracker: Token 用量追踪，格式 {"prompt_tokens": int, "completion_tokens": int, "total_cost_yuan": float}
    """

    plan: dict
    sources: list[dict]
    analyses: list[dict]
    articles: list[dict]
    review_feedback: str
    review_passed: bool
    iteration: int
    needs_human_review: bool
    cost_tracker: dict
