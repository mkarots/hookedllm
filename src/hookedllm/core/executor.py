"""
Hook executor with dependency injection.

Executes hooks with rule matching while isolating failures.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .protocols import AfterHook, BeforeHook, ErrorHook, FinallyHook, Rule
from .types import CallContext, CallInput, CallOutput, CallResult


class DefaultHookExecutor:
    """
    Concrete hook executor with dependency injection.

    Single Responsibility: Only executes hooks, doesn't store them.
    Dependencies injected: error_handler, logger

    Guarantees:
    - Hook failures never break the main LLM call
    - Hooks execute in order
    - Rules are evaluated before execution
    """

    def __init__(
        self,
        error_handler: Callable[[Exception, str], None] | None = None,
        logger: Any | None = None,
    ):
        """
        Initialize executor with optional dependencies.

        Args:
            error_handler: Called when a hook fails. Signature: (error, context_str)
            logger: Logger instance (must have .error() method)
        """
        self._error_handler = error_handler or self._default_error_handler
        self._logger = logger

    async def execute_before(
        self,
        hooks: list[tuple[BeforeHook, Rule | None]],
        call_input: CallInput,
        context: CallContext,
    ) -> None:
        """
        Execute before hooks with rule matching.

        Args:
            hooks: List of (hook, rule) tuples
            call_input: The LLM call input
            context: The call context
        """
        for hook, rule in hooks:
            # Check if rule matches
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, context)
                except Exception as e:
                    hook_name = getattr(hook, "__name__", str(hook))
                    self._error_handler(e, f"Before hook {hook_name}")
                    if self._logger:
                        self._logger.error(f"Before hook {hook_name} failed: {e}")

    async def execute_after(
        self,
        hooks: list[tuple[AfterHook, Rule | None]],
        call_input: CallInput,
        call_output: CallOutput,
        context: CallContext,
    ) -> None:
        """
        Execute after hooks with rule matching.

        Args:
            hooks: List of (hook, rule) tuples
            call_input: The LLM call input
            call_output: The LLM call output
            context: The call context
        """
        for hook, rule in hooks:
            # Check if rule matches
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, call_output, context)
                except Exception as e:
                    hook_name = getattr(hook, "__name__", str(hook))
                    self._error_handler(e, f"After hook {hook_name}")
                    if self._logger:
                        self._logger.error(f"After hook {hook_name} failed: {e}")

    async def execute_error(
        self,
        hooks: list[tuple[ErrorHook, Rule | None]],
        call_input: CallInput,
        error: BaseException,
        context: CallContext,
    ) -> None:
        """
        Execute error hooks with rule matching.

        Args:
            hooks: List of (hook, rule) tuples
            call_input: The LLM call input
            error: The error that occurred
            context: The call context
        """
        for hook, rule in hooks:
            # Check if rule matches
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, error, context)
                except Exception as e:
                    hook_name = getattr(hook, "__name__", str(hook))
                    self._error_handler(e, f"Error hook {hook_name}")
                    if self._logger:
                        self._logger.error(f"Error hook {hook_name} failed: {e}")

    async def execute_finally(
        self, hooks: list[tuple[FinallyHook, Rule | None]], result: CallResult
    ) -> None:
        """
        Execute finally hooks.

        Note: Finally hooks don't use rule matching - they always run.

        Args:
            hooks: List of (hook, rule) tuples (rule is ignored for finally hooks)
            result: The complete call result
        """
        for hook, _rule in hooks:
            # Finally hooks always run, ignore rule
            try:
                await hook(result)
            except Exception as e:
                hook_name = getattr(hook, "__name__", str(hook))
                self._error_handler(e, f"Finally hook {hook_name}")
                if self._logger:
                    self._logger.error(f"Finally hook {hook_name} failed: {e}")

    def _default_error_handler(self, error: Exception, context: str) -> None:
        """
        Default error handler: swallow errors silently.

        Hook failures should never break the main LLM call flow.
        """
        pass  # Silent by default
