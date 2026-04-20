"""
Supervisor 模式 — 主管 Agent 协调多个工人 Agent

Supervisor 模式的核心思想:
1. 一个 Supervisor Agent 负责任务分解和调度
2. 多个 Worker Agent 各自完成子任务
3. Supervisor 汇总结果并做最终决策

与 Router 模式的区别:
- Router: 1对1 分发（一个请求 → 一个处理器）
- Supervisor: 1对多 协调（一个任务 → 多个工人 → 汇总）
"""

import json
from dataclasses import dataclass, field

from workflows.model_client import accumulate_usage, chat, chat_json


# ---------------------------------------------------------------------------
# Worker 定义
# ---------------------------------------------------------------------------

@dataclass
class WorkerResult:
    """工人 Agent 的执行结果"""
    worker_name: str
    status: str  # "success" | "error"
    data: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)


def collector_worker(task: dict) -> WorkerResult:
    """采集工人：根据 Supervisor 指令采集特定来源的数据

    Args:
        task: {"source": "github|hackernews|arxiv", "keywords": [...], "limit": int}
    """
    source = task.get("source", "github")
    keywords = task.get("keywords", ["AI", "agent"])
    limit = task.get("limit", 5)

    prompt = f"""请模拟从 {source} 采集关于 {', '.join(keywords)} 的技术资讯。
返回 JSON 数组，每条包含 title, url, description, source 字段。
最多返回 {limit} 条。"""

    try:
        result, usage = chat_json(prompt)
        items = result if isinstance(result, list) else [result]
        return WorkerResult(
            worker_name="collector",
            status="success",
            data={"items": items, "source": source},
            usage=usage,
        )
    except Exception as e:
        return WorkerResult(
            worker_name="collector",
            status="error",
            data={"error": str(e)},
        )


def analyzer_worker(task: dict) -> WorkerResult:
    """分析工人：对给定数据进行深度分析

    Args:
        task: {"items": [...], "analysis_type": "summary|trend|comparison"}
    """
    items = task.get("items", [])
    analysis_type = task.get("analysis_type", "summary")

    prompt = f"""请对以下技术资讯进行 {analysis_type} 分析:

{json.dumps(items, ensure_ascii=False, indent=2)}

返回 JSON 格式:
{{
    "analysis_type": "{analysis_type}",
    "findings": ["发现1", "发现2", "发现3"],
    "summary": "200字以内的分析总结",
    "confidence": 0.85
}}"""

    try:
        result, usage = chat_json(prompt)
        return WorkerResult(
            worker_name="analyzer",
            status="success",
            data=result if isinstance(result, dict) else {"raw": result},
            usage=usage,
        )
    except Exception as e:
        return WorkerResult(
            worker_name="analyzer",
            status="error",
            data={"error": str(e)},
        )


def reviewer_worker(task: dict) -> WorkerResult:
    """审核工人：对分析结果进行质量审核

    Args:
        task: {"analyses": [...], "criteria": str}
    """
    analyses = task.get("analyses", [])
    criteria = task.get("criteria", "准确性、深度、实用性")

    prompt = f"""请审核以下分析结果，评估维度: {criteria}

{json.dumps(analyses, ensure_ascii=False, indent=2)}

返回 JSON 格式:
{{
    "approved": true或false,
    "score": 4.2,
    "issues": ["问题1（如有）"],
    "suggestions": ["改进建议1（如有）"]
}}"""

    try:
        result, usage = chat_json(prompt)
        return WorkerResult(
            worker_name="reviewer",
            status="success",
            data=result if isinstance(result, dict) else {"raw": result},
            usage=usage,
        )
    except Exception as e:
        return WorkerResult(
            worker_name="reviewer",
            status="error",
            data={"error": str(e)},
        )


# Worker 注册表
WORKERS = {
    "collector": collector_worker,
    "analyzer": analyzer_worker,
    "reviewer": reviewer_worker,
}


# ---------------------------------------------------------------------------
# Supervisor 核心
# ---------------------------------------------------------------------------

class Supervisor:
    """主管 Agent：分解任务、调度工人、汇总结果

    执行流程:
    1. 接收高层任务描述
    2. 用 LLM 分解为子任务并分配给工人
    3. 收集工人结果
    4. 汇总并生成最终报告
    """

    def __init__(self) -> None:
        self.cost_tracker: dict = {}
        self.execution_log: list[dict] = []

    def plan(self, task_description: str) -> list[dict]:
        """任务规划：将高层任务分解为工人子任务

        Args:
            task_description: 用户的任务描述

        Returns:
            子任务列表，每个包含 worker, task 字段
        """
        prompt = f"""你是任务调度主管。请将以下任务分解为子任务并分配给工人。

任务: {task_description}

可用工人:
- collector: 数据采集（需要 source, keywords, limit 参数）
- analyzer: 数据分析（需要 items, analysis_type 参数）
- reviewer: 质量审核（需要 analyses, criteria 参数）

请返回 JSON 数组，每个元素格式:
{{
    "step": 1,
    "worker": "collector",
    "task": {{"source": "github", "keywords": ["agent"], "limit": 5}},
    "depends_on": []
}}

注意:
- 按执行顺序排列
- depends_on 填写依赖的步骤编号
- 确保数据流合理（先采集，再分析，最后审核）"""

        try:
            result, usage = chat_json(
                prompt,
                system="你是严谨的任务调度主管。返回可执行的子任务计划。",
            )
            self.cost_tracker = accumulate_usage(self.cost_tracker, usage)

            plan = result if isinstance(result, list) else [result]
            print(f"[Supervisor] 规划了 {len(plan)} 个子任务")
            return plan

        except Exception as e:
            print(f"[Supervisor] 规划失败: {e}，使用默认计划")
            # 降级: 使用默认的 3 步计划
            return [
                {"step": 1, "worker": "collector", "task": {"source": "github", "keywords": ["AI", "agent"], "limit": 5}, "depends_on": []},
                {"step": 2, "worker": "analyzer", "task": {"items": [], "analysis_type": "summary"}, "depends_on": [1]},
                {"step": 3, "worker": "reviewer", "task": {"analyses": [], "criteria": "准确性、深度"}, "depends_on": [2]},
            ]

    def execute(self, task_description: str) -> dict:
        """执行完整的 Supervisor 工作流

        Args:
            task_description: 用户的任务描述

        Returns:
            包含所有结果和汇总的最终报告
        """
        # 1. 规划
        plan = self.plan(task_description)

        # 2. 按步骤执行（处理依赖关系）
        step_results: dict[int, WorkerResult] = {}

        for step_def in plan:
            step_num = step_def["step"]
            worker_name = step_def["worker"]
            task = step_def["task"]

            # 注入上游数据（如果有依赖）
            for dep_step in step_def.get("depends_on", []):
                if dep_step in step_results:
                    dep_data = step_results[dep_step].data
                    # 自动将上游 items 传递给下游
                    if "items" in dep_data and "items" in task:
                        task["items"] = dep_data["items"]
                    if "findings" in dep_data and "analyses" in task:
                        task["analyses"] = [dep_data]

            # 执行
            worker = WORKERS.get(worker_name)
            if not worker:
                print(f"[Supervisor] 未知工人: {worker_name}，跳过")
                continue

            print(f"[Supervisor] 步骤 {step_num}: 调度 {worker_name}")
            result = worker(task)
            step_results[step_num] = result

            # 累计成本
            if result.usage:
                self.cost_tracker = accumulate_usage(self.cost_tracker, result.usage)

            self.execution_log.append({
                "step": step_num,
                "worker": worker_name,
                "status": result.status,
            })

        # 3. 汇总
        return self._summarize(task_description, step_results)

    def _summarize(self, task_description: str, results: dict[int, WorkerResult]) -> dict:
        """汇总所有工人的结果，生成最终报告"""
        all_data = {
            step: {"worker": r.worker_name, "status": r.status, "data": r.data}
            for step, r in results.items()
        }

        prompt = f"""请汇总以下工作成果为最终报告。

原始任务: {task_description}

各步骤结果:
{json.dumps(all_data, ensure_ascii=False, indent=2)}

请返回简洁的中文汇总报告（200字以内）。"""

        summary, usage = chat(prompt, system="你是报告撰写专家。简洁、有条理。")
        self.cost_tracker = accumulate_usage(self.cost_tracker, usage)

        return {
            "task": task_description,
            "summary": summary,
            "step_results": all_data,
            "execution_log": self.execution_log,
            "cost_tracker": self.cost_tracker,
        }


# --- 命令行测试入口 ---
if __name__ == "__main__":
    import sys

    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "采集并分析今天的 AI Agent 领域最新进展"
    print(f"任务: {task}\n")

    supervisor = Supervisor()
    report = supervisor.execute(task)

    print("\n" + "=" * 60)
    print("最终报告:")
    print(report["summary"])
    print(f"\n总成本: ¥{report['cost_tracker'].get('total_cost_yuan', 0)}")
