"""
pipeline/model_client.py · 统一 LLM 调用接口

支持 DeepSeek / Qwen / OpenAI · 任选其一通过 .env 配置:
    LLM_API_KEY=sk-...
    LLM_BASE_URL=https://api.deepseek.com
    LLM_MODEL=deepseek-chat

注意 · 本文件不做任何 retry · 瞬时故障（timeout / rate limit）会直接向上抛。
Week 2 的 OpenSpec 实操就是要在这一层上加 retry 机制。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class ChatResponse:
    """Chat API 响应包装 · 含文本 + token usage"""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


def get_client() -> OpenAI:
    """拿 OpenAI 兼容客户端 · DeepSeek/Qwen/OpenAI 均支持"""
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    )


def chat(prompt: str, system: str = "你是一个专业的技术分析师。",
         temperature: float = 0.3, max_tokens: int = 2000) -> ChatResponse:
    """调用 LLM · 返回 ChatResponse

    ⚠️ 不做 retry · 瞬时故障直接抛:
        - APITimeoutError · 超时
        - RateLimitError · 429
        - APIConnectionError · 网络断
        - APIStatusError · 5xx

    Week 2 /opsx:apply 会给本文件加一个 with_retry 装饰器。
    """
    client = get_client()
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return ChatResponse(
        content=response.choices[0].message.content or "",
        prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
        completion_tokens=response.usage.completion_tokens if response.usage else 0,
    )


def estimate_cost(prompt_tokens: int, completion_tokens: int,
                  input_price_per_m: float = 1.0,
                  output_price_per_m: float = 2.0) -> float:
    """估算成本 · 单位元 · 默认 DeepSeek 定价"""
    return (prompt_tokens * input_price_per_m + completion_tokens * output_price_per_m) / 1_000_000
