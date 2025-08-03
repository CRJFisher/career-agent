"""
Unit tests for async LLM wrapper functionality.
"""

import asyncio
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import json

from utils.async_llm_wrapper import (
    AsyncLLMWrapper,
    RateLimiter,
    get_async_llm_wrapper,
    CachedAsyncLLMWrapper
)


class TestRateLimiter:
    """Test suite for RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_burst(self):
        """Test that rate limiter allows burst up to limit."""
        limiter = RateLimiter(rate=5, per=1.0)
        
        # Should allow 5 requests immediately
        start = asyncio.get_event_loop().time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be nearly instant
        assert elapsed < 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_throttles(self):
        """Test that rate limiter throttles after burst."""
        limiter = RateLimiter(rate=2, per=1.0)
        
        # Use up allowance
        await limiter.acquire()
        await limiter.acquire()
        
        # Next request should be delayed
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should have waited
        assert elapsed >= 0.4  # Some delay expected


class TestAsyncLLMWrapper:
    """Test suite for AsyncLLMWrapper class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test wrapper initialization."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        assert wrapper.api_key == "test-key"
        assert wrapper.default_model == "anthropic/claude-3-opus-20240229"
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_model_resolution(self):
        """Test model alias resolution."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        assert wrapper._resolve_model("gpt-4") == "openai/gpt-4"
        assert wrapper._resolve_model("claude-3-opus") == "anthropic/claude-3-opus-20240229"
        assert wrapper._resolve_model("unknown-model") == "unknown-model"
        assert wrapper._resolve_model(None) == wrapper.default_model
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_call_llm_success(self):
        """Test successful LLM call."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        # Mock the session
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test response"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.closed = False
        wrapper._session = mock_session
        
        result = await wrapper.call_llm("Test prompt")
        assert result == "Test response"
        
        # Verify API call
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0].endswith("/chat/completions")
        
        payload = call_args[1]["json"]
        assert payload["messages"][0]["content"] == "Test prompt"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 2000
    
    @pytest.mark.asyncio
    async def test_call_llm_with_system_prompt(self):
        """Test LLM call with system prompt."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Response"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        await wrapper.call_llm("User prompt", system_prompt="System prompt")
        
        payload = mock_session.post.call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "System prompt"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "User prompt"
    
    @pytest.mark.asyncio
    async def test_call_llm_batch(self):
        """Test batch LLM calls."""
        wrapper = AsyncLLMWrapper(api_key="test-key", max_concurrent=2)
        
        # Mock responses
        responses = ["Response 1", "Response 2", "Response 3"]
        call_count = 0
        
        async def mock_call_llm(prompt, **kwargs):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate API delay
            return result
        
        wrapper.call_llm = mock_call_llm
        
        prompts = [
            ("Prompt 1", None),
            ("Prompt 2", "System 2"),
            ("Prompt 3", None)
        ]
        
        results = await wrapper.call_llm_batch(prompts)
        
        assert results == responses
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting works."""
        wrapper = AsyncLLMWrapper(
            api_key="test-key",
            rate_limit=2,
            rate_period=0.5
        )
        
        # Mock fast responses
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Response"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        # Make 3 rapid calls
        start = asyncio.get_event_loop().time()
        await asyncio.gather(
            wrapper.call_llm("1"),
            wrapper.call_llm("2"),
            wrapper.call_llm("3")
        )
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should have been rate limited
        assert elapsed >= 0.2  # Some delay due to rate limiting
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in LLM calls."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        # Mock error response
        mock_session = AsyncMock()
        mock_session.post.side_effect = aiohttp.ClientError("API Error")
        wrapper._session = mock_session
        
        with pytest.raises(aiohttp.ClientError):
            await wrapper.call_llm("Test prompt")
    
    @pytest.mark.asyncio
    async def test_structured_output_yaml(self):
        """Test structured YAML output parsing."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        # Mock YAML response
        yaml_response = """```yaml
key1: value1
key2:
  - item1
  - item2
```"""
        
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": yaml_response}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        result = await wrapper.call_llm_structured(
            "Generate YAML",
            output_format="yaml"
        )
        
        assert result == {"key1": "value1", "key2": ["item1", "item2"]}
    
    @pytest.mark.asyncio
    async def test_structured_output_json(self):
        """Test structured JSON output parsing."""
        wrapper = AsyncLLMWrapper(api_key="test-key")
        
        # Mock JSON response
        json_response = """```json
{
    "name": "test",
    "value": 42
}
```"""
        
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": json_response}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        result = await wrapper.call_llm_structured(
            "Generate JSON",
            output_format="json"
        )
        
        assert result == {"name": "test", "value": 42}
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with AsyncLLMWrapper(api_key="test-key") as wrapper:
            assert wrapper._session is not None
        
        # Session should be closed after context exit
        assert wrapper._session.closed


class TestCachedAsyncLLMWrapper:
    """Test suite for cached async wrapper."""
    
    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test that caching works with async wrapper."""
        wrapper = CachedAsyncLLMWrapper(
            api_key="test-key",
            use_cache=True
        )
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Cached response"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        # First call
        result1 = await wrapper.call_llm("Test prompt")
        assert result1 == "Cached response"
        assert mock_session.post.call_count == 1
        
        # Second call should hit cache
        result2 = await wrapper.call_llm("Test prompt")
        assert result2 == "Cached response"
        assert mock_session.post.call_count == 1  # No additional call
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_cache_bypass(self):
        """Test cache bypass option."""
        wrapper = CachedAsyncLLMWrapper(
            api_key="test-key",
            use_cache=True
        )
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Response"}}]
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        wrapper._session = mock_session
        
        # Call with cache bypass
        await wrapper.call_llm("Test prompt", use_cache=False)
        await wrapper.call_llm("Test prompt", use_cache=False)
        
        # Should have made 2 API calls
        assert mock_session.post.call_count == 2
        
        await wrapper.close()


class TestGetAsyncLLMWrapper:
    """Test the factory function."""
    
    @pytest.mark.asyncio
    async def test_get_wrapper_without_cache(self):
        """Test getting wrapper without cache."""
        with patch.dict(os.environ, {"ENABLE_LLM_CACHE": "false"}):
            wrapper = await get_async_llm_wrapper(api_key="test-key")
            assert isinstance(wrapper, AsyncLLMWrapper)
            assert not isinstance(wrapper, CachedAsyncLLMWrapper)
            await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_get_wrapper_with_cache(self):
        """Test getting wrapper with cache enabled."""
        with patch.dict(os.environ, {"ENABLE_LLM_CACHE": "true"}):
            wrapper = await get_async_llm_wrapper(api_key="test-key")
            assert isinstance(wrapper, CachedAsyncLLMWrapper)
            await wrapper.close()