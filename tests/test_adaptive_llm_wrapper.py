"""Tests for AdaptiveLLMWrapper.

This module tests the dual-mode LLM wrapper that supports both
MCP sampling and direct API calls.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from utils.adaptive_llm_wrapper import AdaptiveLLMWrapper, get_adaptive_llm_wrapper


class TestAdaptiveLLMWrapper:
    """Test suite for AdaptiveLLMWrapper."""
    
    @pytest.fixture
    def mock_mcp_context(self):
        """Create a mock MCP context."""
        context = Mock()
        context.sample = AsyncMock()
        context.info = AsyncMock()
        return context
    
    @pytest.fixture
    def mock_standalone_wrapper(self):
        """Create a mock standalone LLM wrapper."""
        wrapper = Mock()
        wrapper.call_llm_sync = Mock(return_value="Standalone response")
        wrapper.generate_async = AsyncMock(return_value="Async standalone response")
        return wrapper
    
    def test_init_mcp_mode(self, mock_mcp_context):
        """Test initialization in MCP mode."""
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        assert wrapper.mcp_context == mock_mcp_context
        assert wrapper.standalone_wrapper is None
        assert wrapper.mode == "mcp"
        assert wrapper.is_mcp_mode()
        assert not wrapper.is_standalone_mode()
    
    def test_init_standalone_mode(self, mock_standalone_wrapper):
        """Test initialization in standalone mode."""
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper', 
                   return_value=mock_standalone_wrapper):
            wrapper = AdaptiveLLMWrapper()
        
        assert wrapper.mcp_context is None
        assert wrapper.standalone_wrapper == mock_standalone_wrapper
        assert wrapper.mode == "standalone"
        assert not wrapper.is_mcp_mode()
        assert wrapper.is_standalone_mode()
    
    @pytest.mark.asyncio
    async def test_generate_async_mcp_mode(self, mock_mcp_context):
        """Test async generation in MCP mode."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = "MCP sampling response"
        mock_mcp_context.sample.return_value = mock_response
        
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        result = await wrapper.generate_async("Test prompt", temperature=0.5)
        
        assert result == "MCP sampling response"
        mock_mcp_context.sample.assert_called_once()
        call_args = mock_mcp_context.sample.call_args
        assert "Test prompt" in call_args[0]
        assert call_args[1].get('temperature') == 0.5
    
    @pytest.mark.asyncio
    async def test_generate_async_standalone_mode(self, mock_standalone_wrapper):
        """Test async generation in standalone mode."""
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper', 
                   return_value=mock_standalone_wrapper):
            wrapper = AdaptiveLLMWrapper()
        
        result = await wrapper.generate_async("Test prompt")
        
        assert result == "Async standalone response"
        mock_standalone_wrapper.generate_async.assert_called_once_with(
            "Test prompt"
        )
    
    def test_call_llm_sync_standalone(self, mock_standalone_wrapper):
        """Test sync generation in standalone mode."""
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper', 
                   return_value=mock_standalone_wrapper):
            wrapper = AdaptiveLLMWrapper()
        
        result = wrapper.call_llm_sync("Test prompt", max_tokens=100)
        
        assert result == "Standalone response"
        mock_standalone_wrapper.call_llm_sync.assert_called_once_with(
            "Test prompt", 100, 0.7
        )
    
    @pytest.mark.asyncio
    async def test_mcp_generate_with_different_response_types(self, mock_mcp_context):
        """Test MCP generation with various response types."""
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        # Test with object having .text attribute
        mock_response = Mock()
        mock_response.text = "Response text"
        mock_mcp_context.sample.return_value = mock_response
        result = await wrapper._mcp_generate("Prompt 1")
        assert result == "Response text"
        
        # Test with dict response
        mock_mcp_context.sample.return_value = {"text": "Dict response"}
        result = await wrapper._mcp_generate("Prompt 2")
        assert result == "Dict response"
        
        # Test with string response
        mock_mcp_context.sample.return_value = "String response"
        result = await wrapper._mcp_generate("Prompt 3")
        assert result == "String response"
    
    @pytest.mark.asyncio
    async def test_mcp_generate_error_handling(self, mock_mcp_context):
        """Test error handling in MCP generation."""
        mock_mcp_context.sample.side_effect = Exception("Sampling denied by user")
        
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        with pytest.raises(RuntimeError) as exc_info:
            await wrapper._mcp_generate("Test prompt")
        
        assert "MCP sampling failed" in str(exc_info.value)
        assert "denied by the user" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_structured_mcp(self, mock_mcp_context):
        """Test structured generation in MCP mode."""
        # Mock response with JSON
        mock_response = Mock()
        mock_response.text = '{"name": "John", "age": 30}'
        mock_mcp_context.sample.return_value = mock_response
        
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            }
        }
        
        result = await wrapper.generate_structured("Generate a person", schema)
        
        assert result == {"name": "John", "age": 30}
        
        # Verify prompt includes schema
        call_args = mock_mcp_context.sample.call_args[0][0]
        assert "Generate a person" in call_args
        assert "JSON" in call_args
        assert "schema" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_structured_json_extraction(self, mock_mcp_context):
        """Test JSON extraction from various response formats."""
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        schema = {"properties": {"result": {"type": "string"}}}
        
        # Test with JSON in code block
        mock_response = Mock()
        mock_response.text = 'Here is the result:\n```json\n{"result": "success"}\n```'
        mock_mcp_context.sample.return_value = mock_response
        
        result = await wrapper.generate_structured("Test", schema)
        assert result == {"result": "success"}
        
        # Test with plain JSON
        mock_response.text = '{"result": "plain"}'
        mock_mcp_context.sample.return_value = mock_response
        
        result = await wrapper.generate_structured("Test", schema)
        assert result == {"result": "plain"}
    
    @pytest.mark.asyncio
    async def test_generate_batch_mcp(self, mock_mcp_context):
        """Test batch generation in MCP mode."""
        # Mock responses
        responses = [Mock(), Mock()]
        responses[0].text = "Response 1"
        responses[1].text = "Response 2"
        mock_mcp_context.sample.side_effect = responses
        
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        prompts = ["Prompt 1", "Prompt 2"]
        results = await wrapper.generate_batch(prompts)
        
        assert results == ["Response 1", "Response 2"]
        assert mock_mcp_context.sample.call_count == 2
        assert mock_mcp_context.info.call_count == 2  # Progress updates
    
    @pytest.mark.asyncio
    async def test_generate_batch_error_handling(self, mock_mcp_context):
        """Test batch generation with errors."""
        # First succeeds, second fails
        mock_response = Mock()
        mock_response.text = "Success"
        mock_mcp_context.sample.side_effect = [
            mock_response,
            Exception("Failed")
        ]
        
        wrapper = AdaptiveLLMWrapper(mcp_context=mock_mcp_context)
        
        results = await wrapper.generate_batch(["Prompt 1", "Prompt 2"])
        
        assert results[0] == "Success"
        assert "Error:" in results[1]
        assert "Failed" in results[1]
    
    def test_compatibility_methods(self, mock_standalone_wrapper):
        """Test compatibility method aliases."""
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper', 
                   return_value=mock_standalone_wrapper):
            wrapper = AdaptiveLLMWrapper()
        
        # Test call_llm alias
        result = wrapper.call_llm("Test")
        assert result == "Standalone response"
        
        # Test generate alias
        result = wrapper.generate("Test")
        assert result == "Standalone response"
    
    def test_create_default_from_schema(self, mock_standalone_wrapper):
        """Test default value creation from schema."""
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper', 
                   return_value=mock_standalone_wrapper):
            wrapper = AdaptiveLLMWrapper()
        
        schema = {
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "tags": {"type": "array"},
                "metadata": {"type": "object"},
                "active": {"type": "boolean"}
            }
        }
        
        result = wrapper._create_default_from_schema(schema)
        
        assert result == {
            "name": "",
            "age": 0,
            "tags": [],
            "metadata": {},
            "active": False
        }
    
    def test_factory_function(self, mock_mcp_context):
        """Test the factory function."""
        # Test with MCP context
        wrapper = get_adaptive_llm_wrapper(mock_mcp_context)
        assert isinstance(wrapper, AdaptiveLLMWrapper)
        assert wrapper.is_mcp_mode()
        
        # Test without MCP context
        with patch('utils.adaptive_llm_wrapper.get_default_llm_wrapper'):
            wrapper = get_adaptive_llm_wrapper()
            assert isinstance(wrapper, AdaptiveLLMWrapper)
            assert wrapper.is_standalone_mode()