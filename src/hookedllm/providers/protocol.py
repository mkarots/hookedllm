"""
Provider adapter protocol for multi-provider support.

Defines the interface that all provider adapters must implement,
following the Dependency Inversion Principle.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..core.types import CallContext, CallInput, CallOutput, Message


class ProviderAdapter(Protocol):
    """
    Protocol for provider-specific adapters.

    Each adapter handles:
    - Detecting if a client belongs to this provider
    - Normalizing provider-specific input/output formats
    - Extracting the callable method from the client

    This follows the Open/Closed Principle: new providers can be added
    by implementing this protocol without modifying existing code.
    """

    @staticmethod
    def detect(client: Any) -> bool:
        """
        Detect if a client belongs to this provider.

        Args:
            client: The client instance to check

        Returns:
            True if this adapter can handle the client, False otherwise
        """
        ...

    @staticmethod
    def get_callable(client: Any) -> Any:
        """
        Get the callable method from the client.

        Args:
            client: The client instance

        Returns:
            The callable method (e.g., client.chat.completions.create)

        Raises:
            AttributeError: If the callable cannot be found
        """
        ...

    @staticmethod
    def normalize_input(
        provider_name: str, callable_method: Any, *args: Any, **kwargs: Any
    ) -> tuple[CallInput, CallContext]:
        """
        Normalize provider-specific input to CallInput and CallContext.

        Args:
            provider_name: Name of the provider (e.g., "openai", "anthropic")
            callable_method: The callable method being called
            *args: Positional arguments passed to the callable
            **kwargs: Keyword arguments passed to the callable

        Returns:
            Tuple of (CallInput, CallContext)
        """
        ...

    @staticmethod
    def normalize_output(response: Any) -> CallOutput:
        """
        Normalize provider-specific response to CallOutput.

        Args:
            response: The raw response from the provider SDK

        Returns:
            Normalized CallOutput
        """
        ...

    @staticmethod
    def get_wrapper_path(client: Any) -> list[str]:
        """
        Get the attribute path to wrap (e.g., ["chat", "completions"]).

        This is used by the wrapper to intercept the correct attributes.

        Args:
            client: The client instance

        Returns:
            List of attribute names to wrap
        """
        ...
