"""
LangGraph 工作流图定义 — V3 知识库：6 节点 + HumanFlag 终点

【核心教学点：职责隔离的 Agent 协作】

拓扑（和 PPT 完全一致）:

    ① plan → ② collect → ③ analyze → ④ review ┬─[pass]────→ ⑥ organize → END
                                                │
                                                ├─[fail]────→ ⑤ revise → ④ review（循环）
                                                │
                                                └─[>max]────→ ⑦ human_flag → END

关键决策点（条件路由）:
- review_passed == True   → 路由到 organize（整理入库，工作流正常终点）
- review_passed == False
   - iteration < max      → 路由到 revise（LLM 定向修改后回到 review）
   - iteration >= max     → 路由到 human_flag（标记人工介入，工作流异常终点）
"""

from langgraph.graph import END, StateGraph

from workflows.analyzer import analyze_node
from workflows.collector import collect_node
from workflows.human_flag import human_flag_node
from workflows.organizer import organize_node
from workflows.planner import planner_node
from workflows.reviewer import review_node
from workflows.reviser import revise_node
from workflows.state import KBState


def route_after_review(state: KBState) -> str:
    """条件路由：review_node 之后的三个分支

    这是 V3 审核循环的决策核心。
    LangGraph 在 review 节点之后调用本函数，根据返回值选择下一个节点:

    - "organize"    → 审核通过，整理入库（正常终点）
    - "revise"      → 审核未通过但还有机会，LLM 定向修改后回到 review
    - "human_flag"  → 审核未通过且超过上限，标记人工介入（异常终点）
    """
    plan = state.get("plan", {}) or {}
    max_iter = int(plan.get("max_iterations", 3))
    iteration = state.get("iteration", 0)

    if state.get("review_passed", False):
        return "organize"
    elif iteration >= max_iter:
        return "human_flag"
    else:
        return "revise"


def build_graph() -> StateGraph:
    """构建知识库工作流图

    Returns:
        编译后的 LangGraph 应用，可通过 app.invoke() 或 app.stream() 执行
    """
    graph = StateGraph(KBState)

    # --- 注册 6 + 1 个节点 ---
    graph.add_node("plan", planner_node)
    graph.add_node("collect", collect_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("review", review_node)
    graph.add_node("revise", revise_node)
    graph.add_node("organize", organize_node)
    graph.add_node("human_flag", human_flag_node)

    # --- 线性边: plan → collect → analyze → review ---
    graph.add_edge("plan", "collect")
    graph.add_edge("collect", "analyze")
    graph.add_edge("analyze", "review")

    # --- 【关键】三路条件边: review → {organize, revise, human_flag} ---
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "organize": "organize",
            "revise": "revise",
            "human_flag": "human_flag",
        },
    )

    # --- revise 修改后回到 review（形成循环） ---
    graph.add_edge("revise", "review")

    # --- 两个终点 ---
    graph.add_edge("organize", END)
    graph.add_edge("human_flag", END)

    # --- 入口 ---
    graph.set_entry_point("plan")

    return graph


# --- 编译图，暴露 app 供外部调用 ---
app = build_graph().compile()


# --- 便捷运行入口 ---
if __name__ == "__main__":
    print("=" * 60)
    print("AI 知识库 V3 — LangGraph 工作流启动")
    print("=" * 60)

    initial_state: KBState = {
        "plan": {},
        "sources": [],
        "analyses": [],
        "articles": [],
        "review_feedback": "",
        "review_passed": False,
        "iteration": 0,
        "needs_human_review": False,
        "cost_tracker": {},
    }

    current_plan: dict = {}

    for event in app.stream(initial_state):
        node_name = list(event.keys())[0]
        print(f"\n--- [{node_name}] 完成 ---")

        node_output = event[node_name]
        if "plan" in node_output:
            current_plan = node_output["plan"] or {}
            print(f"  策略: {current_plan.get('strategy', '?')}")
        if "sources" in node_output:
            print(f"  采集数量: {len(node_output['sources'])}")
        if "analyses" in node_output:
            print(f"  分析数量: {len(node_output['analyses'])}")
        if "articles" in node_output:
            print(f"  入库数量: {len(node_output['articles'])}")
        if "review_passed" in node_output:
            max_iter = current_plan.get("max_iterations", 3)
            passed = "通过" if node_output["review_passed"] else "未通过"
            print(f"  审核结果: {passed}")
            print(f"  迭代次数: {node_output.get('iteration', '?')}/{max_iter}")
        if "needs_human_review" in node_output and node_output["needs_human_review"]:
            print(f"  ⚠️ 需要人工介入")
        if "cost_tracker" in node_output:
            cost = node_output["cost_tracker"].get("total_cost_yuan", 0)
            print(f"  累计成本: ¥{cost}")

    print("\n" + "=" * 60)
    print("工作流执行完毕")
    print("=" * 60)
