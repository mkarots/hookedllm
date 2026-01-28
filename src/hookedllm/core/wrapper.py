"""
Transparent wrapper for intercepting LLM API calls.

Wraps provider clients to inject hook execution while preserving
the original SDK interface and return types.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from .protocols import HookExecutor, ScopeHookStore
from .types import CallContext, CallInput, CallOutput, CallResult


def _detect_provider_adapter(client: Any) -> Any:
    """
    Detect which provider adapter to use for a client.

    Args:
        client: The client instance to detect

    Returns:
        ProviderAdapter instance or None if no adapter matches

    Raises:
        ValueError: If no adapter can handle the client
    """
    # Import adapters here to avoid circular imports
    try:
        from ..providers.openai import OpenAIAdapter
        from ..providers.anthropic import AnthropicAdapter
    except ImportError:
        # If adapters aren't available, fall back to OpenAI detection
        # This allows the package to work even if optional deps aren't installed
        pass

    adapters = []
    # Check Anthropic first (more specific structure)
    try:
        from ..providers.anthropic import AnthropicAdapter

        adapters.append(AnthropicAdapter)
    except ImportError:
        pass

    # Then check OpenAI
    try:
        from ..providers.openai import OpenAIAdapter

        adapters.append(OpenAIAdapter)
    except ImportError:
        pass

    # Try each adapter
    for adapter in adapters:
        if adapter.detect(client):
            return adapter

    # If no adapter matches, raise an error
    raise ValueError(
        f"Unsupported client type: {type(client)}. "
        "Supported providers: OpenAI, Anthropic. "
        "Install with: pip install hookedllm[openai] or pip install hookedllm[anthropic]"
    )


class HookedClientWrapper:
    """
    Transparent proxy with all dependencies injected.

    No global state - all dependencies passed via constructor (DI).
    Intercepts provider SDK methods to inject hook execution.
    """

    def __init__(self, original_client: Any, scopes: list[ScopeHookStore], executor: HookExecutor):
        """
        Initialize wrapper with injected dependencies.

        Args:
            original_client: The original provider client
            scopes: List of scope hook stores to use
            executor: Hook executor instance
        """
        self._original = original_client
        self._scopes = scopes
        self._executor = executor
        self._adapter = _detect_provider_adapter(original_client)
        self._wrapper_path = self._adapter.get_wrapper_path(original_client)

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access.

        Wraps attributes based on the detected provider's wrapper path.
        """
        attr = getattr(self._original, name)

        # Check if this attribute is part of the wrapper path
        if len(self._wrapper_path) > 0 and name == self._wrapper_path[0]:
            # Create a dynamic wrapper for the next level
            return _create_wrapper_for_path(
                attr, self._wrapper_path[1:], self._scopes, self._executor, self._adapter
            )

        return attr


def _create_wrapper_for_path(
    obj: Any,
    remaining_path: list[str],
    scopes: list[ScopeHookStore],
    executor: HookExecutor,
    adapter: Any,
) -> Any:
    """
    Recursively create wrappers for the provider's attribute path.

    Args:
        obj: The object to wrap
        remaining_path: Remaining attribute names in the path
        scopes: List of scope hook stores
        executor: Hook executor instance
        adapter: Provider adapter instance

    Returns:
        Wrapped object or the original object if path is complete
    """
    if len(remaining_path) == 0:
        # We've reached the end of the path - create the final wrapper
        return HookedCompletionsWrapper(obj, scopes, executor, adapter)

    # Create an intermediate wrapper
    return HookedPathWrapper(obj, remaining_path, scopes, executor, adapter)


class HookedPathWrapper:
    """
    Intermediate wrapper for provider-specific attribute paths.

    Handles paths like ["chat", "completions"] for OpenAI or ["messages"] for Anthropic.
    """

    def __init__(
        self,
        original_obj: Any,
        remaining_path: list[str],
        scopes: list[ScopeHookStore],
        executor: HookExecutor,
        adapter: Any,
    ):
        """
        Initialize path wrapper.

        Args:
            original_obj: The object being wrapped
            remaining_path: Remaining attribute names to intercept
            scopes: List of scope hook stores
            executor: Hook executor instance
            adapter: Provider adapter instance
        """
        self._original = original_obj
        self._remaining_path = remaining_path
        self._scopes = scopes
        self._executor = executor
        self._adapter = adapter

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access.

        If the attribute matches the next in the path, wrap it.
        Otherwise pass through.
        """
        attr = getattr(self._original, name)

        if len(self._remaining_path) > 0 and name == self._remaining_path[0]:
            # Continue wrapping down the path
            return _create_wrapper_for_path(
                attr, self._remaining_path[1:], self._scopes, self._executor, self._adapter
            )

        return attr


class HookedCompletionsWrapper:
    """
    Wraps completions.create() with hook execution.

    All dependencies injected, no global state.
    """

    def __init__(
        self,
        original_completions: Any,
        scopes: list[ScopeHookStore],
        executor: HookExecutor,
        adapter: Any,
    ):
        """
        Initialize completions wrapper.

        Args:
            original_completions: Original completions object from SDK
            scopes: List of scope hook stores
            executor: Hook executor instance
            adapter: Provider adapter instance
        """
        self._original = original_completions
        self._scopes = scopes
        self._executor = executor
        self._adapter = adapter

    async def create(self, *, model: str, messages: list[dict], **kwargs) -> Any:
        """
        Hooked create method.

        Flow:
        1. Use adapter to normalize input (extracts tags, metadata, creates CallInput/Context)
        2. Collect all hooks from all scopes
        3. Execute before hooks
        4. Call original SDK method
        5. Use adapter to normalize output
        6. Execute after hooks (on success) or error hooks (on failure)
        7. Always execute finally hooks
        8. Return original SDK response type

        Args:
            model: Model name
            messages: List of message dicts
            **kwargs: Other parameters passed to SDK

        Returns:
            Original SDK response object
        """
        # Use adapter to normalize input
        call_input, context = self._adapter.normalize_input(
            self._adapter.PROVIDER_NAME, self._original.create, model=model, messages=messages, **kwargs
        )

        # Collect all hooks from all scopes
        all_before = []
        all_after = []
        all_error = []
        all_finally = []

        for scope in self._scopes:
            all_before.extend(scope.get_before_hooks())
            all_after.extend(scope.get_after_hooks())
            all_error.extend(scope.get_error_hooks())
            all_finally.extend(scope.get_finally_hooks())

        # Execute hook flow
        t0 = time.perf_counter()
        output = None
        error = None

        try:
            # Before hooks
            await self._executor.execute_before(all_before, call_input, context)

            # Original SDK call
            response = await self._original.create(model=model, messages=messages, **kwargs)

            # Use adapter to normalize output
            output = self._adapter.normalize_output(response)

            # After hooks
            await self._executor.execute_after(all_after, call_input, output, context)

            return response  # Return ORIGINAL SDK response!

        except BaseException as e:
            error = e
            await self._executor.execute_error(all_error, call_input, e, context)
            raise

        finally:
            elapsed = (time.perf_counter() - t0) * 1000.0
            result = CallResult(
                input=call_input,
                output=output,
                context=context,
                error=error,
                ended_at=datetime.now(timezone.utc),
                elapsed_ms=elapsed,
            )
            await self._executor.execute_finally(all_finally, result)

    def __getattr__(self, name: str) -> Any:
        """Pass through other attributes to original object."""
        return getattr(self._original, name)
