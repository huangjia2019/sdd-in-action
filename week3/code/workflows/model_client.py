"""
模型客户端 — 统一的 LLM 调用接口

注意：这里 import 的 openai 包是作为**通用客户端**使用，并非只能调用 OpenAI 模型。
DeepSeek、Qwen、智谱等国产大模型都兼容 OpenAI API 格式，因此可以直接复用 openai SDK，
只需在 .env 中配置对应的 base_url 和 api_key 即可切换到不同模型提供商。

所有节点通过此模块调用 LLM，便于统一管理 token 用量和成本。
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_client() -> OpenAI:
    """获取 OpenAI 兼容客户端（openai SDK 可连接任何兼容 API，不限于 OpenAI）"""
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    )


def chat(
    prompt: str,
    system: str = "你是一个专业的 AI 技术分析师。",
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> tuple[str, dict]:
    """调用 LLM 并返回 (回复文本, token用量信息)

    Args:
        prompt: 用户 prompt
        system: 系统 prompt
        model: 模型名，默认从环境变量读取
        temperature: 采样温度
        max_tokens: 最大输出 token 数

    Returns:
        (response_text, usage_dict) 其中 usage_dict 包含 prompt_tokens, completion_tokens
    """
    client = get_client()
    model_name = model or os.getenv("LLM_MODEL", "deepseek-chat")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    text = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }

    return text, usage


def chat_json(
    prompt: str,
    system: str = "你是一个专业的 AI 技术分析师。请用 JSON 格式回复。",
    **kwargs: Any,
) -> tuple[dict | list, dict]:
    """调用 LLM 并解析 JSON 响应（带容错）

    容错策略:
    1. 去掉 markdown 代码块包裹
    2. 直接 json.loads
    3. 失败则用正则匹配第一个 {...} 或 [...] 结构
    4. 再失败才抛出

    Returns:
        (parsed_json, usage_dict)

    Raises:
        json.JSONDecodeError: 三种策略都失败时
    """
    import re

    text, usage = chat(prompt, system=system, **kwargs)

    # 策略 1: 去掉 markdown 代码块包裹
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # 可能是 ```json 或 ``` 开头
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        cleaned = "\n".join(lines[start:end])

    # 策略 2: 直接解析
    try:
        return json.loads(cleaned), usage
    except json.JSONDecodeError:
        pass

    # 策略 3: 正则提取第一个完整 JSON 结构（处理 "Extra data" / 前后缀文本）
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        match = re.search(pattern, cleaned)
        if match:
            try:
                return json.loads(match.group()), usage
            except json.JSONDecodeError:
                continue

    # 三种都失败 —— 抛原始异常
    return json.loads(cleaned), usage


def accumulate_usage(tracker: dict, new_usage: dict) -> dict:
    """累加 token 用量到 cost_tracker

    Args:
        tracker: 现有的 cost_tracker
        new_usage: 本次调用的 usage_dict

    Returns:
        更新后的 cost_tracker（包含累计 token 数和成本估算）
    """
    prompt = tracker.get("prompt_tokens", 0) + new_usage.get("prompt_tokens", 0)
    completion = tracker.get("completion_tokens", 0) + new_usage.get("completion_tokens", 0)

    # DeepSeek 定价: 输入 ¥1/百万token, 输出 ¥2/百万token（近似）
    input_price = float(os.getenv("PRICE_INPUT_PER_MILLION", "1.0"))
    output_price = float(os.getenv("PRICE_OUTPUT_PER_MILLION", "2.0"))
    total_cost = (prompt * input_price + completion * output_price) / 1_000_000

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_cost_yuan": round(total_cost, 6),
    }
