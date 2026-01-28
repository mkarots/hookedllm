"""
Integration test for Anthropic/Claude with hookedllm.

Demonstrates using hookedllm with Anthropic's Claude models.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import hookedllm


@pytest.mark.asyncio
async def test_anthropic_with_hooks():
    """Test Anthropic client with hookedllm hooks."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        pytest.skip("Anthropic SDK not installed. Install with: pip install hookedllm[anthropic]")

    # Track hook executions
    before_called = []
    after_called = []
    finally_called = []

    # Define hooks
    async def before_hook(call_input, context):
        """Hook executed before the LLM call."""
        before_called.append({
            "model": call_input.model,
            "provider": context.provider,
            "message_count": len(call_input.messages),
        })

    async def after_hook(call_input, call_output, context):
        """Hook executed after the LLM call."""
        after_called.append({
            "model": call_input.model,
            "provider": context.provider,
            "text": call_output.text,
            "usage": call_output.usage,
        })

    async def finally_hook(result):
        """Hook executed in finally block."""
        finally_called.append({
            "call_id": result.context.call_id,
            "elapsed_ms": result.elapsed_ms,
            "success": result.error is None,
        })

    # Register hooks
    hookedllm.scope("test").before(before_hook)
    hookedllm.scope("test").after(after_hook)
    hookedllm.scope("test").finally_(finally_hook)

    # Create mock Anthropic client
    mock_client = AsyncAnthropic(api_key="test-key")
    
    # Mock the messages.create method
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = "Hello! I'm Claude, an AI assistant."
    mock_response.content = [mock_content_block]

    # Create a proper usage object that the adapter can normalize
    # The adapter will try model_dump(), dict(), __dict__, then fall back to manual dict
    class MockUsage:
        def __init__(self):
            self.input_tokens = 10
            self.output_tokens = 15
    
    mock_usage = MockUsage()
    mock_response.usage = mock_usage
    mock_response.stop_reason = "end_turn"

    # Patch the create method
    with patch.object(mock_client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        # Wrap client with hookedllm
        wrapped_client = hookedllm.wrap(mock_client, scope="test")
        
        # Make a call
        response = await wrapped_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello, Claude!"}],
            metadata={"hookedllm_tags": ["test", "integration"]},
        )
        
        # Verify the original SDK method was called
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "claude-3-opus-20240229"
        assert len(call_kwargs["messages"]) == 1
        
        # Verify hooks were executed
        assert len(before_called) == 1
        assert before_called[0]["model"] == "claude-3-opus-20240229"
        assert before_called[0]["provider"] == "anthropic"
        assert before_called[0]["message_count"] == 1
        
        assert len(after_called) == 1
        assert after_called[0]["model"] == "claude-3-opus-20240229"
        assert after_called[0]["provider"] == "anthropic"
        assert after_called[0]["text"] == "Hello! I'm Claude, an AI assistant."
        assert after_called[0]["usage"]["input_tokens"] == 10
        assert after_called[0]["usage"]["output_tokens"] == 15
        
        assert len(finally_called) == 1
        assert finally_called[0]["success"] is True
        assert finally_called[0]["elapsed_ms"] > 0
        
        # Verify response is returned correctly
        assert response == mock_response


@pytest.mark.asyncio
async def test_anthropic_with_conditional_hooks():
    """Test Anthropic client with conditional hooks based on model."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        pytest.skip("Anthropic SDK not installed. Install with: pip install hookedllm[anthropic]")

    # Track hook executions
    claude_only_called = []
    all_models_called = []

    # Define conditional hook (only for Claude Opus)
    async def claude_opus_hook(call_input, call_output, context):
        claude_only_called.append(call_input.model)

    # Define hook for all models
    async def all_models_hook(call_input, call_output, context):
        all_models_called.append(call_input.model)

    # Register hooks with rules
    hookedllm.scope("test").after(
        claude_opus_hook,
        when=hookedllm.when.model("claude-3-opus-20240229"),
    )
    hookedllm.scope("test").after(all_models_hook)

    # Create mock Anthropic client
    mock_client = AsyncAnthropic(api_key="test-key")
    
    # Mock responses
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = "Response"
    mock_response.content = [mock_content_block]
    
    # Create a proper usage object that the adapter can normalize
    class MockUsage:
        def __init__(self):
            self.input_tokens = 5
            self.output_tokens = 10
    
    mock_usage = MockUsage()
    mock_response.usage = mock_usage
    mock_response.stop_reason = "end_turn"
    
    with patch.object(mock_client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        wrapped_client = hookedllm.wrap(mock_client, scope="test")
        
        # Call with Claude Opus - both hooks should fire
        await wrapped_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": "Test"}],
        )
        
        # Call with Claude Sonnet - only all_models hook should fire
        await wrapped_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": "Test"}],
        )
        
        # Verify conditional hook only called for Opus
        assert len(claude_only_called) == 1
        assert claude_only_called[0] == "claude-3-opus-20240229"
        
        # Verify all-models hook called for both
        assert len(all_models_called) == 2
        assert "claude-3-opus-20240229" in all_models_called
        assert "claude-3-sonnet-20240229" in all_models_called


@pytest.mark.asyncio
async def test_anthropic_error_handling():
    """Test Anthropic client error handling with hooks."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        pytest.skip("Anthropic SDK not installed. Install with: pip install hookedllm[anthropic]")

    # Track hook executions
    error_called = []
    finally_called = []

    # Define error hook
    async def error_hook(call_input, error, context):
        error_called.append({
            "model": call_input.model,
            "error_type": type(error).__name__,
            "provider": context.provider,
        })

    # Define finally hook
    async def finally_hook(result):
        finally_called.append({
            "success": result.error is None,
            "has_error": result.error is not None,
        })

    # Register hooks
    hookedllm.scope("test").error(error_hook)
    hookedllm.scope("test").finally_(finally_hook)

    # Create mock Anthropic client
    mock_client = AsyncAnthropic(api_key="test-key")
    
    # Mock an error
    test_error = ValueError("API error")
    
    with patch.object(mock_client.messages, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = test_error
        
        wrapped_client = hookedllm.wrap(mock_client, scope="test")
        
        # Make a call that will fail
        with pytest.raises(ValueError, match="API error"):
            await wrapped_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=100,
                messages=[{"role": "user", "content": "Test"}],
            )
        
        # Verify error hook was called
        assert len(error_called) == 1
        assert error_called[0]["error_type"] == "ValueError"
        assert error_called[0]["provider"] == "anthropic"
        
        # Verify finally hook was called
        assert len(finally_called) == 1
        assert finally_called[0]["success"] is False
        assert finally_called[0]["has_error"] is True
