"""
成本守卫 — Token 用量追踪与预算控制

生产环境中 LLM 调用成本是核心关注点。
本模块提供三级防护:
1. 追踪（Track）: 记录每次调用的 token 用量
2. 预警（Alert）: 接近预算上限时发出警告
3. 熔断（Stop）: 超出预算时硬停止
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CostRecord:
    """单次 LLM 调用的成本记录"""
    timestamp: float
    node_name: str
    prompt_tokens: int
    completion_tokens: int
    cost_yuan: float
    model: str = ""


class CostGuard:
    """成本守卫：追踪、预警、熔断

    使用方式:
        guard = CostGuard(budget_yuan=1.0)
        guard.record("analyze", usage)   # 记录每次调用
        guard.check()                     # 检查是否超标

    Args:
        budget_yuan: 单次运行的预算上限（人民币元）
        alert_threshold: 预警阈值（占预算的比例，默认 0.8 = 80%）
        input_price_per_million: 输入 token 单价（元/百万 token）
        output_price_per_million: 输出 token 单价（元/百万 token）
    """

    def __init__(
        self,
        budget_yuan: float = 1.0,
        alert_threshold: float = 0.8,
        input_price_per_million: float = 1.0,
        output_price_per_million: float = 2.0,
    ) -> None:
        self.budget_yuan = budget_yuan
        self.alert_threshold = alert_threshold
        self.input_price = input_price_per_million
        self.output_price = output_price_per_million

        self.records: list[CostRecord] = []
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_cost_yuan: float = 0.0
        self._alert_fired: bool = False

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """计算单次调用成本"""
        return (
            prompt_tokens * self.input_price + completion_tokens * self.output_price
        ) / 1_000_000

    def record(self, node_name: str, usage: dict, model: str = "") -> CostRecord:
        """记录一次 LLM 调用的 token 用量

        Args:
            node_name: 调用方节点名称（如 "analyze", "review"）
            usage: {"prompt_tokens": int, "completion_tokens": int}
            model: 模型名称

        Returns:
            CostRecord 对象

        Raises:
            BudgetExceededError: 如果已超出预算
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = self.calculate_cost(prompt_tokens, completion_tokens)

        record = CostRecord(
            timestamp=time.time(),
            node_name=node_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_yuan=cost,
            model=model,
        )
        self.records.append(record)

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_yuan += cost

        return record

    def check(self) -> dict[str, Any]:
        """检查预算状态

        Returns:
            {
                "status": "ok" | "warning" | "exceeded",
                "total_cost": float,
                "budget": float,
                "usage_ratio": float,
                "message": str,
            }

        Raises:
            BudgetExceededError: 如果成本已超出预算
        """
        ratio = self.total_cost_yuan / self.budget_yuan if self.budget_yuan > 0 else 0

        if self.total_cost_yuan >= self.budget_yuan:
            raise BudgetExceededError(
                f"成本已超出预算！当前: ¥{self.total_cost_yuan:.4f}, "
                f"预算: ¥{self.budget_yuan:.2f}"
            )

        if ratio >= self.alert_threshold and not self._alert_fired:
            self._alert_fired = True
            status = "warning"
            message = (
                f"[预警] 成本已达预算的 {ratio:.0%}！"
                f"当前: ¥{self.total_cost_yuan:.4f}, 预算: ¥{self.budget_yuan:.2f}"
            )
            print(f"\033[93m{message}\033[0m")  # 黄色警告
        else:
            status = "ok"
            message = f"成本正常: ¥{self.total_cost_yuan:.4f} / ¥{self.budget_yuan:.2f} ({ratio:.0%})"

        return {
            "status": status,
            "total_cost": round(self.total_cost_yuan, 6),
            "budget": self.budget_yuan,
            "usage_ratio": round(ratio, 4),
            "message": message,
        }

    def get_report(self) -> dict:
        """生成成本报告"""
        by_node: dict[str, float] = {}
        for r in self.records:
            by_node[r.node_name] = by_node.get(r.node_name, 0) + r.cost_yuan

        return {
            "total_cost_yuan": round(self.total_cost_yuan, 6),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_calls": len(self.records),
            "budget_yuan": self.budget_yuan,
            "cost_by_node": {k: round(v, 6) for k, v in by_node.items()},
        }

    def save_report(self, path: str | None = None) -> str:
        """保存成本报告到 JSON 文件"""
        if path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "knowledge", "cost-report.json")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        report = self.get_report()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return path


class BudgetExceededError(Exception):
    """预算超标异常 — 触发熔断"""
    pass
