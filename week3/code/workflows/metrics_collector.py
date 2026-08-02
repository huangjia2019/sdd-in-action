"""
Metrics Collector Agent — V3 知识库流水线的可观测性节点 (节点 ⑧)

职责：透明记录每个节点的执行指标（latency/cost/status/iteration），
工作流结束时序列化输出为 dashboard-ready JSON。

核心原则：对现有节点零侵入（decorator 模式），
写入失败不阻塞工作流（observability 不应影响 reliability）。

两大部分：
  - track_metrics(node_name): decorator 工厂，包装每个 LangGraph 节点函数
  - flush_metrics_node(state): LangGraph 节点，在终点前写入 metrics JSON
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Callable

from workflows.state import KBState

METRICS_DIR = "knowledge/metrics"


def track_metrics(node_name: str) -> Callable:
    """Decorator 工厂：返回一个包装 LangGraph 节点函数的 wrapper

    功能：
      1. 记录节点开始/结束时间（wall-clock）
      2. 捕获成功/异常状态
      3. 从 state 读取 cost_tracker 快照和 iteration
      4. 将 metrics 记录追加到 state["metrics"]，不覆盖已有记录

    Args:
        node_name: 节点标识名（对应 graph.py 里的 add_node 名称）

    Returns:
        包装后的函数，签名和原节点完全兼容
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(state: KBState) -> dict:
            start_time = time.time()
            start_iso = datetime.now(timezone.utc).isoformat()

            try:
                result = fn(state)
                status = "success"
            except Exception:
                status = "error"
                end_iso = datetime.now(timezone.utc).isoformat()
                latency_ms = round((time.time() - start_time) * 1000, 2)
                # 即使出错也要记录这条 metrics
                record = {
                    "node": node_name,
                    "start_time": start_iso,
                    "end_time": end_iso,
                    "latency_ms": latency_ms,
                    "status": status,
                    "cost_snapshot": state.get("cost_tracker", {}) or {},
                    "iteration": state.get("iteration", 0),
                }
                # 构建最小 state delta，但 raise 后 LangGraph 不会用它
                # 所以我们把 record 加到 state 后再 raise
                existing = list(state.get("metrics", []) or [])
                state["metrics"] = existing + [record]
                raise

            end_iso = datetime.now(timezone.utc).isoformat()
            latency_ms = round((time.time() - start_time) * 1000, 2)

            record = {
                "node": node_name,
                "start_time": start_iso,
                "end_time": end_iso,
                "latency_ms": latency_ms,
                "status": status,
                "cost_snapshot": (state.get("cost_tracker", {}) or {}).copy(),
                "iteration": state.get("iteration", 0),
            }

            existing = list(state.get("metrics", []) or [])
            result["metrics"] = existing + [record]
            return result

        return wrapper

    return decorator


def flush_metrics_node(state: KBState) -> dict:
    """LangGraph 节点：将累积的 metrics 写入磁盘

    正常终点 (organize 之后) 和异常终点 (human_flag 之后) 都会经过此节点，
    确保两条路径都输出 metrics。

    写入失败只打印 warning 到 stderr，不 raise，不阻塞 END。

    输出格式（JSON）:
        {
            "workflow_start": "ISO 8601",
            "strategy": "standard",
            "records": [...],
            "summary": {
                "total_latency_ms": float,
                "total_cost_yuan": float,
                "node_count": int,
                "review_iterations": int,
                "errors": int
            }
        }

    Returns:
        空 dict（不修改 state）
    """
    metrics = list(state.get("metrics", []) or [])
    plan = state.get("plan", {}) or {}

    if not metrics:
        return {}

    # --- 构建 summary ---
    total_latency_ms = round(sum(r.get("latency_ms", 0) for r in metrics), 2)
    total_cost_yuan = 0.0
    for r in metrics:
        snapshot = r.get("cost_snapshot", {}) or {}
        total_cost_yuan = max(total_cost_yuan, snapshot.get("total_cost_yuan", 0))

    review_iterations = max(r.get("iteration", 0) for r in metrics)
    errors = sum(1 for r in metrics if r.get("status") == "error")

    workflow_start = metrics[0]["start_time"] if metrics else "?"

    output = {
        "workflow_start": workflow_start,
        "strategy": plan.get("strategy", "unknown"),
        "records": metrics,
        "summary": {
            "total_latency_ms": total_latency_ms,
            "total_cost_yuan": total_cost_yuan,
            "node_count": len(metrics),
            "review_iterations": review_iterations,
            "errors": errors,
        },
    }

    # --- 写入文件 ---
    os.makedirs(METRICS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    filepath = os.path.join(METRICS_DIR, f"metrics-{timestamp}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"[MetricsCollector] 已写入 {filepath}")
    except (OSError, IOError) as e:
        print(f"[MetricsCollector] WARNING: 写入 metrics 失败: {e}", file=sys.stderr)

    return {}
