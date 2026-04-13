"""Pipeline runner · Week 2 · N6 · B 路 /opsx:apply 产出
对应 spec: week2/specs/pipeline.md

这是学员参考版 · 生产使用前请根据你项目调整:
- import 路径（Agent 实现位置）
- LOG_DIR / STATUS_DIR 常量
- 通知渠道（默认 stdout · 生产可接 Slack）
"""
from __future__ import annotations
import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable


# ─── 常量 · 按你项目改 ─────────────────────────────────────────
BASE = Path(__file__).parent.parent  # 默认 repo root
RAW_DIR     = BASE / "knowledge" / "raw"
TAGGED_DIR  = BASE / "knowledge" / "tagged"
ARTICLE_DIR = BASE / "knowledge" / "articles"
LOG_DIR     = BASE / "knowledge" / "logs"
STATUS_DIR  = BASE / "knowledge" / "status"
INCIDENT_DIR = BASE / "knowledge" / "incidents"


# ─── 错误分类（按 spec § 失败分类） ────────────────────────────
class ErrorCategory(Enum):
    NETWORK   = "network"     # retry 3 · 指数退避
    RATE      = "rate_limit"  # retry 5 · 等 Retry-After
    AUTH      = "auth"        # 不 retry · 告警
    FORMAT    = "format"      # retry 1 · 再错继续
    UNKNOWN   = "unknown"


def classify(exc: Exception) -> ErrorCategory:
    msg = str(exc).lower()
    if "429" in msg or "rate" in msg:    return ErrorCategory.RATE
    if "401" in msg or "403" in msg:     return ErrorCategory.AUTH
    if "5" in msg[:3] and "HTTPError" in type(exc).__name__:
        return ErrorCategory.NETWORK
    if isinstance(exc, (json.JSONDecodeError, ValueError)):
        return ErrorCategory.FORMAT
    return ErrorCategory.UNKNOWN


# ─── Retry 策略 ───────────────────────────────────────────────
def retry_policy(cat: ErrorCategory) -> tuple[int, Callable[[int], float]]:
    """返回 (max_retries, delay_fn)"""
    if cat == ErrorCategory.NETWORK:
        return 3, lambda n: 1 * (4 ** n)       # 1s, 4s, 16s
    if cat == ErrorCategory.RATE:
        return 5, lambda n: 10 * (n + 1)        # 读 Retry-After 更好 · 此处简化
    if cat == ErrorCategory.FORMAT:
        return 1, lambda n: 0
    return 0, lambda n: 0                        # AUTH / UNKNOWN 不 retry


@dataclass
class AgentResult:
    success: bool
    item_count: int = 0
    error_category: ErrorCategory | None = None
    error_msg: str = ""
    duration_sec: float = 0.0


def run_agent_with_retry(name: str, fn: Callable[[], int], log: logging.Logger) -> AgentResult:
    """通用 retry 包装器。fn 返回处理条目数。"""
    attempt = 0
    while True:
        start = time.time()
        try:
            n = fn()
            return AgentResult(success=True, item_count=n, duration_sec=time.time() - start)
        except Exception as e:
            cat = classify(e)
            log.warning(f"[{name}] attempt {attempt + 1} failed · {cat.value} · {e}")
            max_r, delay = retry_policy(cat)
            if attempt >= max_r:
                log.error(f"[{name}] gave up after {attempt + 1} attempts")
                return AgentResult(
                    success=False, error_category=cat,
                    error_msg=str(e), duration_sec=time.time() - start,
                )
            time.sleep(delay(attempt))
            attempt += 1


# ─── 幂等检查 ────────────────────────────────────────────────
def done_path(agent: str, date: str) -> Path:
    return RAW_DIR / f"{date}.{agent}.done"


def is_done(agent: str, date: str) -> bool:
    return done_path(agent, date).exists()


def mark_done(agent: str, date: str):
    done_path(agent, date).touch()


def mark_failed(agent: str, date: str):
    (RAW_DIR / f"{date}.{agent}.failed").touch()


# ─── 主流程 ─────────────────────────────────────────────────
def run_pipeline(date: str, force: bool = False, skip_to: str | None = None, log: logging.Logger = None) -> int:
    stages = [
        ("collector", run_collector),
        ("analyzer",  run_analyzer),
        ("organizer", run_organizer),
    ]
    start_idx = 0
    if skip_to:
        start_idx = next(i for i, (n, _) in enumerate(stages) if n == skip_to)

    any_failed = False
    for name, fn in stages[start_idx:]:
        if is_done(name, date) and not force:
            log.info(f"[{name}] skip · .done exists (use --force to rerun)")
            continue
        log.info(f"[{name}] start")
        r = run_agent_with_retry(name, lambda: fn(date), log)
        if r.success:
            mark_done(name, date)
            log.info(f"[{name}] ok · {r.item_count} items · {r.duration_sec:.1f}s")
        else:
            mark_failed(name, date)
            log.error(f"[{name}] FAILED · {r.error_category.value if r.error_category else 'unknown'}")
            write_incident(date, name, r)
            any_failed = True
            break  # 上游失败不触发下游 · 按 spec § B4

    write_status(date, stages, start_idx)
    return 1 if any_failed else 0


# ─── Agent 实现占位 · 实际需导入真实 Agent 模块 ─────────────────
def run_collector(date: str) -> int:
    # TODO: from agents.collector import run; return run(date)
    raise NotImplementedError("connect your collector here")


def run_analyzer(date: str) -> int:
    raise NotImplementedError("connect your analyzer here")


def run_organizer(date: str) -> int:
    raise NotImplementedError("connect your organizer here")


def write_incident(date: str, agent: str, r: AgentResult):
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)
    p = INCIDENT_DIR / f"{date}.md"
    with p.open("a") as f:
        f.write(f"\n## {agent} failure · {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"- category: {r.error_category.value if r.error_category else 'unknown'}\n")
        f.write(f"- msg: {r.error_msg}\n")
        f.write(f"- duration: {r.duration_sec:.1f}s\n")


def write_status(date: str, stages, start_idx):
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    p = STATUS_DIR / f"{date}.md"
    lines = [f"# {date} · pipeline status\n"]
    for i, (name, _) in enumerate(stages):
        if i < start_idx:
            lines.append(f"- {name} · ⏭ skipped (--skip-to)")
        elif is_done(name, date):
            lines.append(f"- {name} · ✓ done")
        elif (RAW_DIR / f"{date}.{name}.failed").exists():
            lines.append(f"- {name} · ✗ failed · see incidents/{date}.md")
        else:
            lines.append(f"- {name} · ⊘ not run")
    p.write_text("\n".join(lines) + "\n")


# ─── CLI ─────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    p.add_argument("--force", action="store_true")
    p.add_argument("--skip-to", choices=["collector", "analyzer", "organizer"])
    args = p.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / f"{args.date}.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    log = logging.getLogger("pipeline")
    sys.exit(run_pipeline(args.date, args.force, args.skip_to, log))


if __name__ == "__main__":
    main()
