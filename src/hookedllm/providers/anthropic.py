"""
Anthropic provider adapter.

Handles Anthropic SDK-specific logic for detecting clients,
normalizing input/output, and extracting callable methods.
"""

from __future__ import annotations

from typing import Any

from ..core.types import CallContext, CallInput, CallOutput, Message
from .protocol import ProviderAdapter


class AnthropicAdapter:
    """
    Adapter for Anthropic SDK clients.

    Supports both AsyncAnthropic and Anthropic clients.
    Handles the Anthropic-specific API structure: client.messages.create()
    """

    PROVIDER_NAME = "anthropic"

    @staticmethod
    def detect(client: Any) -> bool:
        """
        Detect if a client is an Anthropic client.

        Args:
            client: The client instance to check

        Returns:
            True if client has Anthropic SDK structure, False otherwise
        """
        # Check for Anthropic structure
        # Must have messages.create and it should be callable
        try:
            if hasattr(client, "messages") and hasattr(client.messages, "create"):
                # Verify it's actually callable (not just a MagicMock attribute)
                create_method = getattr(client.messages, "create", None)
                if callable(create_method):
                    # Additional check: if client also has OpenAI structure (chat.completions.create),
                    # we need to prefer Anthropic only if messages.create was explicitly set
                    # For MagicMock, check if chat.completions.create exists - if it does and is callable,
                    # we need to verify which one was set explicitly
                    # Since Anthropic is checked first, if both exist, prefer Anthropic
                    # But we should verify messages.create is the primary structure
                    return True
        except (AttributeError, TypeError):
            pass
        
        return False

    @staticmethod
    def get_callable(client: Any) -> Any:
        """
        Get the Anthropic messages.create callable.

        Args:
            client: The Anthropic client instance

        Returns:
            The messages.create method

        Raises:
            AttributeError: If the callable cannot be found
        """
        return client.messages.create

    @staticmethod
    def normalize_input(
        provider_name: str, callable_method: Any, *args: Any, **kwargs: Any
    ) -> tuple[CallInput, CallContext]:
        """
        Normalize Anthropic input to CallInput and CallContext.

        Args:
            provider_name: Provider name (should be "anthropic")
            callable_method: The callable method (unused for Anthropic)
            *args: Positional arguments (unused for Anthropic)
            **kwargs: Keyword arguments including model, messages, etc.

        Returns:
            Tuple of (CallInput, CallContext)
        """
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])

        # Anthropic uses metadata parameter instead of extra_body
        metadata_dict = kwargs.get("metadata", {})
        if isinstance(metadata_dict, dict):
            tags = metadata_dict.pop("hookedllm_tags", [])
            custom_metadata = metadata_dict.pop("hookedllm_metadata", {})
        else:
            tags = []
            custom_metadata = {}

        # Normalize messages to internal format
        # Anthropic messages have role and content fields
        normalized_messages = []
        for m in messages:
            role = m.get("role", "")
            # Anthropic content can be a string or list of content blocks
            content = m.get("content", "")
            if isinstance(content, list) and len(content) > 0:
                # Extract text from first text block if it's a list
                first_block = content[0]
                if isinstance(first_block, dict) and first_block.get("type") == "text":
                    content = first_block.get("text", "")
                elif isinstance(first_block, str):
                    content = first_block
            normalized_messages.append(Message(role=role, content=content))

        # Create normalized input
        call_input = CallInput(
            model=model, messages=normalized_messages, params=kwargs, metadata=custom_metadata
        )

        # Create context
        context = CallContext(
            provider=provider_name, model=model, tags=tags, metadata=custom_metadata
        )

        return call_input, context

    @staticmethod
    def normalize_output(response: Any) -> CallOutput:
        """
        Normalize Anthropic response to CallOutput.

        Args:
            response: Anthropic SDK response object

        Returns:
            Normalized CallOutput
        """
        try:
            # Extract text from response
            # Anthropic response has content as a list of content blocks
            text = None
            if hasattr(response, "content") and isinstance(response.content, list):
                if len(response.content) > 0:
                    first_content = response.content[0]
                    if isinstance(first_content, dict):
                        text = first_content.get("text")
                    elif hasattr(first_content, "text"):
                        text = first_content.text

            # Extract usage
            # Anthropic uses input_tokens and output_tokens
            usage = None
            if hasattr(response, "usage"):
                usage_obj = response.usage
                if hasattr(usage_obj, "input_tokens") and hasattr(usage_obj, "output_tokens"):
                    # Convert to dict format
                    if hasattr(usage_obj, "model_dump"):
                        usage = usage_obj.model_dump()
                    elif hasattr(usage_obj, "dict"):
                        usage = usage_obj.dict()
                    elif hasattr(usage_obj, "__dict__"):
                        usage = dict(usage_obj.__dict__)
                    else:
                        # Fallback: create dict manually
                        usage = {
                            "input_tokens": usage_obj.input_tokens,
                            "output_tokens": usage_obj.output_tokens,
                            "total_tokens": usage_obj.input_tokens + usage_obj.output_tokens,
                        }
                    # Ensure total_tokens is present
                    if usage and "total_tokens" not in usage:
                        usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get(
                            "output_tokens", 0
                        )

            # Extract stop_reason (Anthropic's finish_reason)
            finish_reason = None
            if hasattr(response, "stop_reason"):
                finish_reason = response.stop_reason

            return CallOutput(text=text, raw=response, usage=usage, finish_reason=finish_reason)
        except Exception:
            # If normalization fails, return minimal output with raw response
            return CallOutput(text=None, raw=response, usage=None, finish_reason=None)

    @staticmethod
    def get_wrapper_path(client: Any) -> list[str]:
        """
        Get the attribute path to wrap for Anthropic.

        Returns:
            ["messages"] - the path to intercept
        """
        return ["messages"]
