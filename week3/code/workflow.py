"""LangGraph workflow · Week 3 · N10 · B 路 /opsx:apply 产出
对应 spec: week3/specs/state-graph.md

学员参考版 · 生产使用前请:
- 对接真实 Agent 函数（当前是 placeholder）
- 对接 OpenTelemetry tracer（Week 3 N12）
- 按你项目调 RESULT 的 schema
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict


# ─── 统一错误契约（spec § 错误分类） ────────────────────────
class ErrorKind(Enum):
    NETWORK = "network"
    LOGIC   = "logic"
    BUDGET  = "budget"
    AUTH    = "auth"


@dataclass
class Result:
    ok: bool
    data: Any = None
    error_kind: ErrorKind | None = None
    error_msg: str = ""


# ─── State Schema ──────────────────────────────────────────
class WorkflowState(TypedDict):
    date: str
    force: bool
    collector_result: Result | None
    analyzer_result: Result | None
    organizer_result: Result | None
    should_exit: bool


# ─── 节点函数（占位 · 对接真实 Agent） ────────────────────
def collector_node(state: WorkflowState) -> dict:
    """Collector · 返回 Result"""
    # TODO: from agents.collector import run; r = run(state["date"])
    r = Result(ok=True, data={"items": 42})
    return {"collector_result": r}


def analyzer_node(state: WorkflowState) -> dict:
    # TODO: 真实实现
    r = Result(ok=True, data={"tagged": 42})
    return {"analyzer_result": r}


def organizer_node(state: WorkflowState) -> dict:
    # TODO: 真实实现
    r = Result(ok=True, data={"articles": 1})
    return {"organizer_result": r}


# ─── 条件边（spec § Failure Transition） ───────────────────
def after_collector(state: WorkflowState) -> str:
    r = state["collector_result"]
    if r and r.ok:
        return "analyzer"
    # 失败 · 按 spec 跳过当日
    return END


def after_analyzer(state: WorkflowState) -> str:
    r = state["analyzer_result"]
    if r and r.ok:
        return "organizer"
    # partial 也继续 organizer（因为 organizer 能处理空数据）
    if r and r.error_kind in (None, ErrorKind.LOGIC):
        return "organizer"
    return END


def after_organizer(state: WorkflowState) -> str:
    # organizer 无论 ok / fallback 都结束
    return END


# ─── 构建 graph ────────────────────────────────────────────
def build_graph():
    g = StateGraph(WorkflowState)
    g.add_node("collector", collector_node)
    g.add_node("analyzer",  analyzer_node)
    g.add_node("organizer", organizer_node)

    g.set_entry_point("collector")

    g.add_conditional_edges("collector", after_collector, {
        "analyzer": "analyzer",
        END: END,
    })
    g.add_conditional_edges("analyzer", after_analyzer, {
        "organizer": "organizer",
        END: END,
    })
    g.add_conditional_edges("organizer", after_organizer, {END: END})

    return g.compile()


if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    g = build_graph()
    final = g.invoke({"date": date, "force": False, "should_exit": False,
                      "collector_result": None, "analyzer_result": None, "organizer_result": None})
    print(f"final state: {final}")
