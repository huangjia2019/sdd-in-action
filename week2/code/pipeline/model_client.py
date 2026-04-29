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
import random
import time
from dataclasses import dataclass
from functools import wraps

import httpx
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    OpenAI,
    RateLimitError,
)

load_dotenv()


@dataclass
class ChatResponse:
    """Chat API 响应包装 · 含文本 + token usage + 调用次数"""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    api_calls: int = 1  # 本次成功调用所花费的 API 调用次数（含重试）


class RetryExhaustedError(Exception):
    """重试耗尽异常 · 携带 API 调用次数"""

    def __init__(self, message: str, api_calls: int = 0):
        super().__init__(message)
        self.api_calls = api_calls


def with_retry(max_attempts: int = 4, base_delay: float = 1.0, max_delay: float = 20.0):
    """装饰器：指数退避重试 LLM API 调用

    可重试异常：
    - openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError
    - httpx.TimeoutException, httpx.ConnectError
    - openai.APIStatusError 且 status_code >= 500

    不可重试异常（内容层错误）：
    - json.JSONDecodeError, KeyError, ValueError
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_calls = 0
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                api_calls += 1
                try:
                    response = func(*args, **kwargs)
                    # 成功 · 设置调用次数并返回响应
                    response.api_calls = attempt
                    return response
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # 内容层错误 · 不重试 · 直接抛（api_calls 已记录）
                    raise e
                except (
                    APITimeoutError,
                    APIConnectionError,
                    RateLimitError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                ) as e:
                    # 可重试异常 · 记录并检查是否还有重试机会
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    # 计算延迟并等待
                    delay = base_delay * (2 ** (attempt - 1))
                    delay = min(delay, max_delay)
                    jitter = random.uniform(1.0, 1.5)
                    time.sleep(delay * jitter)
                    continue
                except APIStatusError as e:
                    # 仅重试 5xx 错误
                    if e.status_code >= 500:
                        last_exception = e
                        if attempt == max_attempts:
                            break
                        delay = base_delay * (2 ** (attempt - 1))
                        delay = min(delay, max_delay)
                        jitter = random.uniform(1.0, 1.5)
                        time.sleep(delay * jitter)
                        continue
                    else:
                        # 4xx 错误不重试
                        raise e

            # 重试耗尽 · 抛出携带 API 调用次数的异常
            raise RetryExhaustedError(
                f"重试耗尽（{max_attempts} 次尝试）: {last_exception}",
                api_calls=api_calls,
            )

        return wrapper

    return decorator


def get_client() -> OpenAI:
    """拿 OpenAI 兼容客户端 · DeepSeek/Qwen/OpenAI 均支持"""
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    )


@with_retry()
def chat(
    prompt: str,
    system: str = "你是一个专业的技术分析师。",
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> ChatResponse:
    """调用 LLM · 返回 ChatResponse（带指数退避重试）

    可重试异常（最多 4 次尝试，延迟 1s/2s/4s + 正抖动）:
        - APITimeoutError · 超时
        - RateLimitError · 429
        - APIConnectionError · 网络断
        - APIStatusError · 5xx
        - httpx.TimeoutException, httpx.ConnectError

    不重试的内容层错误:
        - json.JSONDecodeError · 响应不是合法 JSON
        - KeyError, ValueError · 缺少字段或无效值
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


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_m: float = 1.0,
    output_price_per_m: float = 2.0,
) -> float:
    """估算成本 · 单位元 · 默认 DeepSeek 定价"""
    return (
        prompt_tokens * input_price_per_m + completion_tokens * output_price_per_m
    ) / 1_000_000
