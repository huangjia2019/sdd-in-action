"""
pipeline/model_client.py · 统一 LLM 调用接口

支持 DeepSeek / Qwen / OpenAI · 任选其一通过 .env 配置:
    LLM_API_KEY=sk-...
    LLM_BASE_URL=https://api.deepseek.com
    LLM_MODEL=deepseek-chat

Week 2: 本文件实现了 with_retry 装饰器，对 transient 故障进行指数退避重试。
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from functools import wraps

from dotenv import load_dotenv
from openai import APITimeoutError, RateLimitError, APIStatusError, APIConnectionError
from openai import OpenAI
import httpx

logger = logging.getLogger(__name__)

TRANSIENT_EXCEPTIONS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
    httpx.TimeoutException,
    httpx.ConnectError,
)

CONTENT_EXCEPTIONS = (
    json.JSONDecodeError,
    KeyError,
    ValueError,
)

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


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
    jitter: float = 0.5,
    retry_on: tuple[type[Exception], ...] = TRANSIENT_EXCEPTIONS,
):
    """指数退避重试装饰器"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            while True:
                try:
                    result = fn(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            "[retry] success attempt=%d/%d prompt_tokens=%d completion_tokens=%d cost=¥%.6f",
                            attempt, max_retries, result.prompt_tokens, result.completion_tokens,
                            estimate_cost(result.prompt_tokens, result.completion_tokens)
                        )
                    return result
                except CONTENT_EXCEPTIONS:
                    raise
                except retry_on as e:
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(
                            "[retry] exhausted %d attempts, last exception: %s",
                            max_retries, e.__class__.__name__
                        )
                        raise
                    if isinstance(e, APIStatusError) and e.status_code < 500:
                        raise
                    jitter_amount = random.uniform(0, jitter)
                    sleep_time = delay + jitter_amount
                    logger.warning(
                        "[retry] attempt=%d/%d delay=%.2fs exception=%s",
                        attempt, max_retries, sleep_time, e.__class__.__name__
                    )
                    time.sleep(sleep_time)
                    delay = min(delay * 2, max_delay)
        return wrapper
    return decorator


@with_retry(max_retries=3, base_delay=1.0, max_delay=20.0, jitter=0.5)
def chat(prompt: str, system: str = "你是一个专业的技术分析师。",
         temperature: float = 0.3, max_tokens: int = 2000) -> ChatResponse:
    """调用 LLM · 返回 ChatResponse"""
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
