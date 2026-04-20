"""
Reviewer Agent — 质量审核节点

职责：对 analyses 进行 5 维度加权评分，决定通过或打回。

核心原则：只评估不修改（Evaluate, don't modify）。
Reviewer 看到的是 Analyzer 输出的 analyses，不做任何改动，只给分 + 反馈。

【关键设计：代码重算加权总分】
LLM 会给每个维度评分，但加权总和必须用代码计算——永远不要信任 LLM 的算术。
"""

import json

from workflows.model_client import accumulate_usage, chat_json
from workflows.state import KBState


# 权重字典：写在代码里，不写在 prompt 里
# —— 好处：改权重不用改 prompt，也不怕模型看到权重后给自己"加戏"
REVIEWER_WEIGHTS = {
    "summary_quality": 0.25,  # 摘要质量
    "technical_depth": 0.25,  # 技术深度
    "relevance":       0.20,  # 相关性
    "originality":     0.15,  # 原创性
    "formatting":      0.15,  # 格式规范
}

# 通过阈值：加权总分 ≥ 7.0 视为合格
REVIEWER_PASS_THRESHOLD = 7.0


def review_node(state: KBState) -> dict:
    """Reviewer 节点：对 analyses 进行 5 维度质量审核

    审核维度（每维 1-10 分）:
        1. summary_quality  - 摘要质量
        2. technical_depth  - 技术深度
        3. relevance        - 相关性
        4. originality      - 原创性
        5. formatting       - 格式规范

    Returns:
        review_passed: True/False（加权总分 ≥ 7.0 为 True）
        review_feedback: 具体反馈意见（含弱项维度）
        iteration: 递增的审核计数器
        cost_tracker: 更新后的成本追踪
    """
    analyses = state.get("analyses", [])
    iteration = state.get("iteration", 0)
    tracker = state.get("cost_tracker", {})

    if not analyses:
        return {
            "review_passed": True,
            "review_feedback": "没有条目需要审核",
            "iteration": iteration + 1,
        }

    # 只审核前 5 条，控制 token 消耗 + 避免长上下文降低审核质量
    sample = analyses[:5]

    prompt = f"""你是知识库质量审核员。请审核以下分析结果：

{json.dumps(sample, ensure_ascii=False, indent=2)}

请按以下维度评分（每项 1-10 分）：
1. summary_quality  - 摘要质量（准确、简洁、有洞察）
2. technical_depth  - 技术深度（原理分析、对比、实现细节）
3. relevance        - 相关性（与 AI/Agent 主题的匹配度）
4. originality      - 原创性（是否有独立见解）
5. formatting       - 格式规范（字段完整、标签清晰）

请用 JSON 格式回复：
{{
    "scores": {{
        "summary_quality": 8,
        "technical_depth": 6,
        "relevance": 9,
        "originality": 5,
        "formatting": 8
    }},
    "feedback": "具体的改进建议（指出弱项）",
    "weak_dimensions": ["technical_depth", "originality"]
}}

当前是第 {iteration + 1} 次审核。"""

    try:
        result, usage = chat_json(
            prompt,
            system="你是严格但公正的知识库质量审核员。给出具体、可操作的反馈。",
            temperature=0.1,  # 低温度保证评分一致性
        )
        tracker = accumulate_usage(tracker, usage)

        # 【关键】用代码重算加权总分，不信任模型算术
        scores = result.get("scores", {})
        weighted_total = sum(
            scores.get(dim, 0) * w for dim, w in REVIEWER_WEIGHTS.items()
        )
        weighted_total = round(weighted_total, 2)
        passed = weighted_total >= REVIEWER_PASS_THRESHOLD

        feedback = result.get("feedback", "")
        weak_dims = result.get("weak_dimensions", [])
        if weak_dims:
            feedback = f"[弱项: {', '.join(weak_dims)}] {feedback}"

        print(
            f"[Reviewer] 加权总分: {weighted_total}/10, "
            f"通过: {passed} (第 {iteration + 1} 次审核)"
        )

    except Exception as e:
        # LLM 调用失败时直接通过，不阻塞流程
        passed = True
        feedback = f"审核 LLM 调用失败: {e}，自动通过"
        print(f"[Reviewer] 审核失败，自动通过: {e}")

    return {
        "review_passed": passed,
        "review_feedback": feedback,
        "iteration": iteration + 1,
        "cost_tracker": tracker,
    }
