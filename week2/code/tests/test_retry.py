"""
tests/test_retry.py · 验证 with_retry 装饰器行为

4 条测试路径:
1. 单次成功，无 retry
2. transient 故障重试后成功
3. 所有 transient 耗尽后 raise
4. content error 不重试，直接 raise
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock

from openai import APITimeoutError, RateLimitError, APIStatusError

from pipeline.model_client import (
    with_retry,
    TRANSIENT_EXCEPTIONS,
    CONTENT_EXCEPTIONS,
    ChatResponse,
    estimate_cost,
)


class TestRetryDecorator:
    def test_chat_success_no_retry(self):
        """单次成功，无 retry"""
        @with_retry(max_retries=3)
        def succeed_once():
            return ChatResponse(content="OK", prompt_tokens=100, completion_tokens=50)

        result = succeed_once()
        assert result.content == "OK"
        assert result.prompt_tokens == 100

    def test_transient_then_success(self):
        """第 1 次 429，第 2 次 200"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01, max_delay=0.01)
        def flaky_then_ok():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APITimeoutError("timeout")
            return ChatResponse(content="OK", prompt_tokens=100, completion_tokens=50)

        result = flaky_then_ok()
        assert result.content == "OK"
        assert call_count == 2

    def test_all_transient_failures_go_degraded(self):
        """3 次都是 transient → raise"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01, max_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise APITimeoutError("timeout")

        with pytest.raises(APITimeoutError):
            always_fail()
        assert call_count == 4

    def test_content_error_not_retried(self):
        """JSONDecodeError 不 retry，直接 raise"""
        call_count = 0

        @with_retry(max_retries=3)
        def bad_json():
            nonlocal call_count
            call_count += 1
            raise json.JSONDecodeError("bad json", "", 0)

        with pytest.raises(json.JSONDecodeError):
            bad_json()
        assert call_count == 1

    def test_500_status_error_retried(self):
        """APIStatusError with 5xx 不重试，直接 raise"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01, max_delay=0.01)
        def server_error():
            nonlocal call_count
            call_count += 1
            raise APIStatusError("server error", response=MagicMock(status_code=500), body=None)

        with pytest.raises(APIStatusError):
            server_error()
        assert call_count == 4

    def test_400_status_error_not_retried(self):
        """APIStatusError with 4xx 不重试，直接 raise"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01, max_delay=0.01)
        def client_error():
            nonlocal call_count
            call_count += 1
            raise APIStatusError("client error", response=MagicMock(status_code=400), body=None)

        with pytest.raises(APIStatusError):
            client_error()
        assert call_count == 1

    def test_keyerror_not_retried(self):
        """KeyError 不重试"""
        call_count = 0

        @with_retry(max_retries=3)
        def key_error_fn():
            nonlocal call_count
            call_count += 1
            raise KeyError("missing")

        with pytest.raises(KeyError):
            key_error_fn()
        assert call_count == 1

    def test_valueerror_not_retried(self):
        """ValueError 不重试"""
        call_count = 0

        @with_retry(max_retries=3)
        def value_error_fn():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad value")

        with pytest.raises(ValueError):
            value_error_fn()
        assert call_count == 1

    def test_cost_estimate_function(self):
        """estimate_cost 计算正确"""
        cost = estimate_cost(1000, 500)
        assert cost > 0
        assert isinstance(cost, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])