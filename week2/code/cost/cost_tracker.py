"""Cost tracker · Week 2 · N8 · B 路 /opsx:apply 产出
对应 spec: week2/specs/cost-budget.md

用法:
    from cost_tracker import track_llm_call, CostTracker

    tracker = CostTracker.instance()

    @track_llm_call
    def call_claude(prompt):
        resp = anthropic.messages.create(...)
        return resp  # cost_tracker 自动从 usage 里抽 token 数

    # 每日结束
    tracker.finalize_day()
"""
from __future__ import annotations
import functools
import json
import logging
import os
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger(__name__)

# ─── 价格表（2026-04 快照 · 按需更新） ──────────────────────
PRICE = {
    # USD per million tokens
    "claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
    "claude-haiku-4.5":  {"input": 0.25, "output": 1.25},
}

# ─── 配置 ────────────────────────────────────────────────
BASE = Path(os.getenv("COST_DATA_DIR", "cost"))
BASE.mkdir(parents=True, exist_ok=True)

DAILY_BUDGET_USD   = float(os.getenv("DAILY_BUDGET_USD", "5.0"))
MONTHLY_BUDGET_USD = float(os.getenv("MONTHLY_BUDGET_USD", "100.0"))
SINGLE_CALL_WARN   = 0.02


@dataclass
class Call:
    timestamp: str
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CostTracker:
    """单例 · 线程安全累计"""
    _inst = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls) -> "CostTracker":
        if cls._inst is None:
            with cls._lock:
                if cls._inst is None:
                    cls._inst = cls()
        return cls._inst

    def __init__(self):
        self.today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._lock = threading.Lock()

    def _file(self) -> Path:
        return BASE / f"{self.today}.jsonl"

    def record(self, call: Call):
        with self._lock:
            with self._file().open("a") as f:
                f.write(json.dumps(asdict(call), ensure_ascii=False) + "\n")
        self._check_budget(call)

    def today_total(self) -> float:
        p = self._file()
        if not p.exists():
            return 0.0
        total = 0.0
        for line in p.read_text().splitlines():
            total += json.loads(line)["cost_usd"]
        return total

    def _check_budget(self, latest: Call):
        if latest.cost_usd > SINGLE_CALL_WARN:
            log.warning(f"单次调用 ${latest.cost_usd:.4f} 超阈值 ${SINGLE_CALL_WARN}")
        pct = self.today_total() / DAILY_BUDGET_USD
        if pct >= 1.2:
            log.critical(f"日预算 120% · 停 pipeline")
            raise BudgetExceededError("daily 120%")
        elif pct >= 1.0:
            log.error(f"日预算 100% · Slack critical · 降级跳过非关键 agent")
            _notify_slack("critical: daily 100%")
        elif pct >= 0.8:
            log.warning(f"日预算 80% · 自动切 Haiku")
            _set_model_downgrade(True)


class BudgetExceededError(Exception):
    pass


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICE.get(model)
    if not p:
        log.warning(f"未知模型 {model} · 成本按 0 记（需要更新 PRICE 表）")
        return 0.0
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def track_llm_call(fn: Callable[..., Any]):
    """装饰器 · 自动从返回值的 usage 字段抽 token 数"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        resp = fn(*args, **kwargs)
        try:
            model = getattr(resp, "model", "unknown")
            usage = getattr(resp, "usage", None)
            if usage is None:
                return resp
            call = Call(
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent=os.getenv("AGENT_NAME", "unknown"),
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cost_usd=compute_cost(model, usage.input_tokens, usage.output_tokens),
            )
            CostTracker.instance().record(call)
        except Exception as e:
            log.exception(f"cost tracking failed · {e}")
        return resp
    return wrapper


# ─── 占位实现 · 按你环境对接 ───────────────────────────────
def _notify_slack(msg: str):
    log.info(f"[mock slack] {msg}")


def _set_model_downgrade(on: bool):
    # TODO: 实际实现应写环境变量或全局状态 · 让下游 agent 切模型
    log.info(f"[mock downgrade] Haiku mode: {on}")
