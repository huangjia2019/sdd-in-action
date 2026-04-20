"""
Reviser Agent — 定向修改节点

职责：根据 Reviewer 的反馈，用 LLM 定向修改 analyses 的弱项。

核心原则：只修改不评估（Modify, don't evaluate）。
Reviser 和 Reviewer 是两个**完全独立的 Agent**——避免"自己给自己打高分"的利益冲突。

Reviser 读取 state["review_feedback"]，把弱项和具体建议注入修改 prompt，
让 LLM 定向改 analyses。改完后通过 `revise → review` 边回到 Reviewer 重新评分。
"""

import json

from workflows.model_client import accumulate_usage, chat_json
from workflows.state import KBState


def revise_node(state: KBState) -> dict:
    """Reviser 节点：根据 Reviewer 反馈，定向修改 analyses

    Args:
        state: 必须包含 analyses + review_feedback（由 Reviewer 生成）

    Returns:
        更新后的 analyses（如果修改成功）+ 更新后的 cost_tracker
    """
    analyses = state.get("analyses", [])
    feedback = state.get("review_feedback", "")
    iteration = state.get("iteration", 0)
    tracker = state.get("cost_tracker", {})

    # 防御：没有可修改内容或没有反馈，直接跳过
    if not analyses or not feedback:
        print("[Reviser] 无可修改内容，跳过")
        return {}

    prompt = f"""你是知识库编辑。以下是审核员的反馈，请据此修改这些分析结果。

【审核反馈】
{feedback}

【当前分析结果】
{json.dumps(analyses, ensure_ascii=False, indent=2)}

【修改要求】
- 重点改进反馈中提到的弱项维度
- 保留已经不错的部分，不要过度修改
- 保持相同的字段结构和类型
- 返回修改后的 JSON 数组（和输入格式一致）"""

    try:
        improved, usage = chat_json(
            prompt,
            system="你是经验丰富的知识库编辑。根据反馈定向修改，不要过度发散。",
            temperature=0.4,  # 略高温度允许创造性改写
        )
        tracker = accumulate_usage(tracker, usage)

        if isinstance(improved, list) and improved:
            print(
                f"[Reviser] 定向修改 {len(improved)} 条 analyses (迭代 {iteration})"
            )
            return {"analyses": improved, "cost_tracker": tracker}
    except Exception as e:
        print(f"[Reviser] 修改失败: {e}，沿用原 analyses")

    return {"cost_tracker": tracker}
