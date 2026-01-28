"""
Tests for provider adapters.

Tests the provider adapter pattern for multi-provider support.
"""

import pytest
from unittest.mock import MagicMock

from hookedllm.core.types import CallContext, CallInput, Message


class TestOpenAIAdapter:
    """Test OpenAI adapter."""

    def test_detect_openai_client(self):
        """Test detecting OpenAI client."""
        try:
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("OpenAI adapter not available")

        # Create mock OpenAI client
        # Use a custom class to prevent MagicMock auto-creation
        class MockOpenAIClient:
            def __init__(self):
                self.chat = MagicMock()
                self.chat.completions = MagicMock()
                self.chat.completions.create = lambda: None  # Make it callable
        
        mock_client = MockOpenAIClient()
        # messages attribute doesn't exist - accessing it will raise AttributeError

        assert OpenAIAdapter.detect(mock_client) is True

    def test_detect_non_openai_client(self):
        """Test that non-OpenAI clients are not detected."""
        try:
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("OpenAI adapter not available")

        # Create mock non-OpenAI client (Anthropic-like)
        # Use spec to limit what MagicMock creates
        mock_client = MagicMock(spec=["messages"])
        mock_client.messages = MagicMock()
        mock_client.messages.create = lambda: None  # Make it callable

        assert OpenAIAdapter.detect(mock_client) is False

    def test_normalize_input(self):
        """Test normalizing OpenAI input."""
        try:
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("OpenAI adapter not available")

        kwargs = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "extra_body": {"hookedllm_tags": ["test"], "hookedllm_metadata": {"key": "value"}},
        }

        call_input, context = OpenAIAdapter.normalize_input(
            "openai", None, **kwargs
        )

        assert call_input.model == "gpt-4"
        assert len(call_input.messages) == 1
        assert call_input.messages[0].role == "user"
        assert call_input.messages[0].content == "Hello"
        assert context.provider == "openai"
        assert context.model == "gpt-4"
        assert "test" in context.tags
        assert context.metadata["key"] == "value"

    def test_normalize_output(self):
        """Test normalizing OpenAI output."""
        try:
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("OpenAI adapter not available")

        # Create mock OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello, world!"
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]

        mock_usage = MagicMock()
        mock_usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        mock_response.usage = mock_usage

        output = OpenAIAdapter.normalize_output(mock_response)

        assert output.text == "Hello, world!"
        assert output.finish_reason == "stop"
        assert output.usage["total_tokens"] == 30

    def test_get_wrapper_path(self):
        """Test getting wrapper path for OpenAI."""
        try:
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("OpenAI adapter not available")

        mock_client = MagicMock()
        path = OpenAIAdapter.get_wrapper_path(mock_client)

        assert path == ["chat", "completions"]


class TestAnthropicAdapter:
    """Test Anthropic adapter."""

    def test_detect_anthropic_client(self):
        """Test detecting Anthropic client."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        # Create mock Anthropic client
        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = MagicMock()

        assert AnthropicAdapter.detect(mock_client) is True

    def test_detect_non_anthropic_client(self):
        """Test that non-Anthropic clients are not detected."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        # Create mock non-Anthropic client (OpenAI-like)
        # Use spec to limit what MagicMock creates
        mock_client = MagicMock(spec=["chat"])
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = lambda: None  # Make it callable

        assert AnthropicAdapter.detect(mock_client) is False

    def test_normalize_input(self):
        """Test normalizing Anthropic input."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        kwargs = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
            "metadata": {"hookedllm_tags": ["test"], "hookedllm_metadata": {"key": "value"}},
        }

        call_input, context = AnthropicAdapter.normalize_input(
            "anthropic", None, **kwargs
        )

        assert call_input.model == "claude-3-opus-20240229"
        assert len(call_input.messages) == 1
        assert call_input.messages[0].role == "user"
        assert call_input.messages[0].content == "Hello"
        assert context.provider == "anthropic"
        assert context.model == "claude-3-opus-20240229"
        assert "test" in context.tags
        assert context.metadata["key"] == "value"

    def test_normalize_input_with_content_blocks(self):
        """Test normalizing Anthropic input with content blocks."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        kwargs = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello from block"}],
                }
            ],
        }

        call_input, context = AnthropicAdapter.normalize_input(
            "anthropic", None, **kwargs
        )

        assert len(call_input.messages) == 1
        assert call_input.messages[0].content == "Hello from block"

    def test_normalize_output(self):
        """Test normalizing Anthropic output."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        # Create mock Anthropic response
        mock_response = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = "Hello, Claude!"
        mock_response.content = [mock_content_block]

        # Create usage object without model_dump/dict methods so it falls through to manual dict
        class MockUsage:
            def __init__(self):
                self.input_tokens = 10
                self.output_tokens = 20

        mock_usage = MockUsage()
        mock_response.usage = mock_usage
        mock_response.stop_reason = "end_turn"

        output = AnthropicAdapter.normalize_output(mock_response)

        assert output.text == "Hello, Claude!"
        assert output.finish_reason == "end_turn"
        assert output.usage["input_tokens"] == 10
        assert output.usage["output_tokens"] == 20
        assert output.usage["total_tokens"] == 30

    def test_normalize_output_with_dict_content(self):
        """Test normalizing Anthropic output with dict content blocks."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        # Create mock Anthropic response with dict content
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello from dict"}]

        mock_usage = MagicMock()
        mock_usage.input_tokens = 5
        mock_usage.output_tokens = 10
        mock_response.usage = mock_usage
        mock_response.stop_reason = "stop_sequence"

        output = AnthropicAdapter.normalize_output(mock_response)

        assert output.text == "Hello from dict"
        assert output.finish_reason == "stop_sequence"

    def test_get_wrapper_path(self):
        """Test getting wrapper path for Anthropic."""
        try:
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Anthropic adapter not available")

        mock_client = MagicMock()
        path = AnthropicAdapter.get_wrapper_path(mock_client)

        assert path == ["messages"]


class TestProviderDetection:
    """Test provider detection in wrapper."""

    def test_detect_openai_in_wrapper(self):
        """Test that OpenAI client is detected correctly."""
        try:
            from hookedllm.core.wrapper import _detect_provider_adapter
            from hookedllm.providers.openai import OpenAIAdapter
        except ImportError:
            pytest.skip("Required adapters not available")

        # Create mock OpenAI client
        # Use a custom class to prevent MagicMock auto-creation
        class MockOpenAIClient:
            def __init__(self):
                self.chat = MagicMock()
                self.chat.completions = MagicMock()
                self.chat.completions.create = lambda: None  # Make it callable
        
        mock_client = MockOpenAIClient()
        # messages attribute doesn't exist - accessing it will raise AttributeError

        adapter = _detect_provider_adapter(mock_client)

        assert adapter == OpenAIAdapter

    def test_detect_anthropic_in_wrapper(self):
        """Test that Anthropic client is detected correctly."""
        try:
            from hookedllm.core.wrapper import _detect_provider_adapter
            from hookedllm.providers.anthropic import AnthropicAdapter
        except ImportError:
            pytest.skip("Required adapters not available")

        # Create mock Anthropic client
        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = MagicMock()

        adapter = _detect_provider_adapter(mock_client)

        assert adapter == AnthropicAdapter

    def test_detect_unsupported_client(self):
        """Test that unsupported clients raise ValueError."""
        try:
            from hookedllm.core.wrapper import _detect_provider_adapter
        except ImportError:
            pytest.skip("Wrapper not available")

        # Create a simple object without provider-specific attributes
        # Use a regular object instead of MagicMock to avoid false positives
        class UnsupportedClient:
            pass

        unsupported_client = UnsupportedClient()

        with pytest.raises(ValueError, match="Unsupported client type"):
            _detect_provider_adapter(unsupported_client)
