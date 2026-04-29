"""
tests/test_retry.py · 验证 analyzer 重试策略
"""

from __future__ import annotations

import json
import time
from unittest.mock import Mock, patch, call

import httpx
import openai
import pytest

from pipeline.model_client import (
    RetryExhaustedError,
    chat,
    with_retry,
)
from pipeline.pipeline import step_analyze


class TestRetryDecorator:
    """测试 with_retry 装饰器"""

    def test_retry_on_timeout_and_succeed(self):
        """模拟超时后重试成功"""
        from unittest.mock import Mock

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)  # 短延迟便于测试
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise openai.APITimeoutError("模拟超时")
            # 返回一个具有 api_calls 属性的模拟对象
            mock_response = Mock()
            mock_response.api_calls = 0  # 将被装饰器覆盖
            return mock_response

        result = failing_func()
        assert isinstance(result, Mock)
        assert result.api_calls == 2  # 第二次尝试成功
        assert call_count == 2

    def test_retry_exhausted_raises_exception(self):
        """重试耗尽时抛出 RetryExhaustedError"""
        call_count = 0

        @with_retry(max_attempts=2, base_delay=0.01)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("连接失败")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_failing()
        assert exc_info.value.api_calls == 2
        assert call_count == 2

    def test_non_retriable_exception_aborts_immediately(self):
        """内容层错误不重试"""
        call_count = 0

        @with_retry(max_attempts=3)
        def json_error():
            nonlocal call_count
            call_count += 1
            raise json.JSONDecodeError("无效 JSON", "", 0)

        with pytest.raises(json.JSONDecodeError):
            json_error()
        assert call_count == 1

    def test_5xx_retry_4xx_no_retry(self):
        """5xx 错误重试，4xx 错误不重试"""
        from unittest.mock import Mock

        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.01)
        def status_error():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 创建带有 status_code 的 response mock
                response_503 = Mock()
                response_503.status_code = 503
                raise openai.APIStatusError(
                    "服务器错误",
                    response=response_503,
                    body=None,
                )
            elif call_count == 2:
                response_400 = Mock()
                response_400.status_code = 400
                raise openai.APIStatusError(
                    "客户端错误",
                    response=response_400,
                    body=None,
                )
            # 返回一个具有 api_calls 属性的模拟对象
            mock_response = Mock()
            mock_response.api_calls = 0
            return mock_response

        # 第一次 503 应重试，第二次 400 应直接抛出
        with pytest.raises(openai.APIStatusError) as exc_info:
            status_error()
        # 检查异常中的 response status_code
        assert exc_info.value.response.status_code == 400
        assert call_count == 2

    def test_jitter_adds_positive_variation(self):
        """正抖动使延迟增加"""
        delays = []

        original_sleep = time.sleep

        def record_sleep(sec):
            delays.append(sec)
            original_sleep(0)  # 不实际等待

        @with_retry(max_attempts=2, base_delay=0.1)
        def failing():
            raise openai.APITimeoutError("timeout")

        with patch("time.sleep", record_sleep):
            with pytest.raises(RetryExhaustedError):
                failing()

        assert len(delays) == 1  # 第一次重试后延迟
        # 延迟应在 0.1~0.15 之间（0.1 * 1.0~1.5）
        assert 0.1 <= delays[0] <= 0.15


class TestChatFunction:
    """测试 chat() 函数与装饰器集成"""

    @patch("pipeline.model_client.OpenAI")
    def test_chat_successful_returns_response(self, mock_openai):
        """正常调用返回 ChatResponse"""
        # 构建嵌套的 mock 结构
        mock_message = Mock()
        mock_message.content = '{"summary": "test"}'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20

        mock_completion = Mock()
        mock_completion.choices = [mock_choice]
        mock_completion.usage = mock_usage

        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        response = chat("test prompt")
        assert response.content == '{"summary": "test"}'
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.api_calls == 1

    @patch("pipeline.model_client.OpenAI")
    def test_chat_retry_exhausted_raises(self, mock_openai):
        """重试耗尽时抛出 RetryExhaustedError"""
        mock_openai.return_value.chat.completions.create.side_effect = (
            openai.APITimeoutError("timeout")
        )

        with pytest.raises(RetryExhaustedError) as exc_info:
            chat("test")
        # 默认 max_attempts=4，应尝试 4 次
        assert exc_info.value.api_calls == 4


class TestPipelineIntegration:
    """测试 pipeline 集成"""

    def test_step_analyze_handles_degraded_item(self):
        """step_analyze 正确处理降级项"""
        items = [
            {
                "title": "test/repo",
                "description": "A test repo",
                "url": "https://github.com/test/repo",
                "source": "github",
                "stars": 100,
                "collected_at": "2025-01-01T00:00:00Z",
            }
        ]

        with patch("pipeline.pipeline.chat") as mock_chat:
            mock_chat.side_effect = RetryExhaustedError("重试耗尽", api_calls=3)
            analyzed = step_analyze(items)

        assert len(analyzed) == 1
        assert analyzed[0]["status"] == "degraded"
        assert analyzed[0]["summary"] == ""
        assert analyzed[0]["tags"] == []
        assert analyzed[0]["relevance_score"] == 0.0
        assert analyzed[0]["category"] == ""
        assert analyzed[0]["key_insight"] == ""

    def test_step_analyze_continues_after_degraded(self):
        """降级项后继续处理后续项"""
        items = [
            {
                "title": "repo1",
                "description": "first",
                "url": "https://github.com/repo1",
                "source": "github",
                "stars": 100,
                "collected_at": "2025-01-01T00:00:00Z",
            },
            {
                "title": "repo2",
                "description": "second",
                "url": "https://github.com/repo2",
                "source": "github",
                "stars": 200,
                "collected_at": "2025-01-01T00:00:00Z",
            },
        ]

        call_count = 0

        def mock_chat(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RetryExhaustedError("耗尽", api_calls=2)
            # 第二个项目成功
            mock_response = Mock()
            mock_response.content = json.dumps(
                {
                    "summary": "ok",
                    "tags": ["test"],
                    "relevance_score": 0.8,
                    "category": "tool",
                    "key_insight": "insight",
                }
            )
            mock_response.prompt_tokens = 5
            mock_response.completion_tokens = 10
            mock_response.api_calls = 1
            return mock_response

        with patch("pipeline.pipeline.chat", side_effect=mock_chat):
            analyzed = step_analyze(items)

        assert len(analyzed) == 2
        assert analyzed[0]["status"] == "degraded"
        assert analyzed[1]["status"] == "ok"
        assert analyzed[1]["summary"] == "ok"

    def test_cost_tracking_counts_all_api_calls(self):
        """成本跟踪记录所有 API 调用"""
        items = [
            {
                "title": "repo",
                "description": "test",
                "url": "https://github.com/repo",
                "source": "github",
                "stars": 100,
                "collected_at": "2025-01-01T00:00:00Z",
            }
        ]

        # 模拟一个已经重试过的成功调用（api_calls=2）
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "summary": "ok",
                "tags": ["test"],
                "relevance_score": 0.8,
                "category": "tool",
                "key_insight": "insight",
            }
        )
        mock_response.prompt_tokens = 10
        mock_response.completion_tokens = 20
        mock_response.api_calls = 2  # 一次失败 + 一次成功

        # patch pipeline.pipeline.chat（step_analyze 使用的引用）
        with patch("pipeline.pipeline.chat", return_value=mock_response):
            # patch pipeline.pipeline.estimate_cost
            with patch("pipeline.pipeline.estimate_cost") as mock_estimate:
                mock_estimate.return_value = 0.01
                step_analyze(items)

        # estimate_cost 应被调用：
        # 1. 实际 token 成本 (prompt_tokens=10, completion_tokens=20)
        # 2. 零 token 成本（api_calls-1 次失败尝试）
        # 当前 step_analyze 循环 api_calls-1 次零 token 成本，加上一次实际 token 成本
        # 所以总共 api_calls = 2 次调用
        assert mock_estimate.call_count == 2
        # 检查调用参数
        calls = mock_estimate.call_args_list
        # 第一次调用应为实际 token 成本 (10, 20)
        assert calls[0] == call(10, 20)
        # 第二次调用应为零 token 成本 (0, 0)
        assert calls[1] == call(0, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
