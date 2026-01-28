"""
OpenAI provider adapter.

Handles OpenAI SDK-specific logic for detecting clients,
normalizing input/output, and extracting callable methods.
"""

from __future__ import annotations

from typing import Any

from ..core.types import CallContext, CallInput, CallOutput, Message


class OpenAIAdapter:
    """
    Adapter for OpenAI SDK clients.

    Supports both AsyncOpenAI and OpenAI clients.
    Handles the OpenAI-specific API structure: client.chat.completions.create()
    """

    PROVIDER_NAME = "openai"

    @staticmethod
    def detect(client: Any) -> bool:
        """
        Detect if a client is an OpenAI client.

        Args:
            client: The client instance to check

        Returns:
            True if client has OpenAI SDK structure, False otherwise
        """
        # Check for OpenAI structure
        # Must have chat.completions.create and it should be callable
        try:
            # Use getattr with sentinel to avoid MagicMock auto-creation
            _SENTINEL = object()

            # Check for OpenAI structure
            chat = getattr(client, "chat", _SENTINEL)
            if chat is _SENTINEL:
                return False

            completions = getattr(chat, "completions", _SENTINEL)
            if completions is _SENTINEL:
                return False

            create_method = getattr(completions, "create", _SENTINEL)
            if create_method is _SENTINEL or not callable(create_method):
                return False

            # Check if it also has Anthropic structure
            # If both exist, Anthropic should have matched first
            # But if Anthropic didn't match, it means messages.create wasn't properly set
            # So we can match OpenAI
            # However, to avoid false positives with MagicMock, we check:
            # If messages.create exists and is callable, don't match OpenAI
            # (Anthropic should have matched if it was properly set)
            messages = getattr(client, "messages", _SENTINEL)
            if messages is not _SENTINEL:
                messages_create = getattr(messages, "create", _SENTINEL)
                if messages_create is not _SENTINEL and callable(messages_create):
                    # Both structures exist - since Anthropic is checked first,
                    # if we get here, Anthropic didn't match, which means messages.create
                    # was auto-created by MagicMock. So we should still match OpenAI.
                    # But to be safe, if both are properly callable, prefer Anthropic
                    # Actually, let's be conservative: if both exist, don't match OpenAI
                    return False

            return True
        except (AttributeError, TypeError):
            pass

        return False

    @staticmethod
    def get_callable(client: Any) -> Any:
        """
        Get the OpenAI completions.create callable.

        Args:
            client: The OpenAI client instance

        Returns:
            The chat.completions.create method

        Raises:
            AttributeError: If the callable cannot be found
        """
        return client.chat.completions.create

    @staticmethod
    def normalize_input(
        provider_name: str, callable_method: Any, *args: Any, **kwargs: Any
    ) -> tuple[CallInput, CallContext]:
        """
        Normalize OpenAI input to CallInput and CallContext.

        Args:
            provider_name: Provider name (should be "openai")
            callable_method: The callable method (unused for OpenAI)
            *args: Positional arguments (unused for OpenAI)
            **kwargs: Keyword arguments including model, messages, etc.

        Returns:
            Tuple of (CallInput, CallContext)
        """
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])

        # Extract hookedllm-specific params from extra_body
        extra_body = kwargs.get("extra_body", {})
        if isinstance(extra_body, dict):
            tags = extra_body.pop("hookedllm_tags", [])
            metadata = extra_body.pop("hookedllm_metadata", {})
        else:
            tags = []
            metadata = {}

        # Normalize messages to internal format
        normalized_messages = [
            Message(role=m.get("role", ""), content=m.get("content", "")) for m in messages
        ]

        # Create normalized input
        call_input = CallInput(
            model=model, messages=normalized_messages, params=kwargs, metadata=metadata
        )

        # Create context
        context = CallContext(provider=provider_name, model=model, tags=tags, metadata=metadata)

        return call_input, context

    @staticmethod
    def normalize_output(response: Any) -> CallOutput:
        """
        Normalize OpenAI response to CallOutput.

        Args:
            response: OpenAI SDK response object

        Returns:
            Normalized CallOutput
        """
        try:
            # Extract text from response
            text = None
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message"):
                    text = getattr(choice.message, "content", None)

            # Extract usage
            usage = None
            if hasattr(response, "usage"):
                # Try to convert to dict
                usage_obj = response.usage
                if hasattr(usage_obj, "model_dump"):
                    usage = usage_obj.model_dump()
                elif hasattr(usage_obj, "dict"):
                    usage = usage_obj.dict()
                elif hasattr(usage_obj, "__dict__"):
                    usage = dict(usage_obj.__dict__)

            # Extract finish_reason
            finish_reason = None
            if hasattr(response, "choices") and len(response.choices) > 0:
                finish_reason = getattr(response.choices[0], "finish_reason", None)

            return CallOutput(text=text, raw=response, usage=usage, finish_reason=finish_reason)
        except Exception:
            # If normalization fails, return minimal output with raw response
            return CallOutput(text=None, raw=response, usage=None, finish_reason=None)

    @staticmethod
    def get_wrapper_path(client: Any) -> list[str]:
        """
        Get the attribute path to wrap for OpenAI.

        Returns:
            ["chat", "completions"] - the path to intercept
        """
        return ["chat", "completions"]
