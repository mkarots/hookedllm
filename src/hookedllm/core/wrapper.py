"""
Transparent wrapper for intercepting LLM API calls.

Wraps OpenAI-compatible clients to inject hook execution while preserving
the original SDK interface and return types.
"""

from __future__ import annotations
import time
from typing import Any, List, Dict
from datetime import datetime, timezone
from .protocols import ScopeHookStore, HookExecutor
from .types import CallInput, CallOutput, CallContext, CallResult, Message


class HookedClientWrapper:
    """
    Transparent proxy with all dependencies injected.
    
    No global state - all dependencies passed via constructor (DI).
    Intercepts OpenAI SDK methods to inject hook execution.
    """
    
    def __init__(
        self,
        original_client: Any,
        scopes: List[ScopeHookStore],
        executor: HookExecutor
    ):
        """
        Initialize wrapper with injected dependencies.
        
        Args:
            original_client: The original OpenAI-compatible client
            scopes: List of scope hook stores to use
            executor: Hook executor instance
        """
        self._original = original_client
        self._scopes = scopes
        self._executor = executor
    
    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access.
        
        If accessing 'chat', wrap it. Otherwise pass through.
        """
        attr = getattr(self._original, name)
        
        if name == "chat":
            return HookedChatWrapper(attr, self._scopes, self._executor)
        
        return attr


class HookedChatWrapper:
    """Wraps chat completions with injected dependencies."""
    
    def __init__(
        self,
        original_chat: Any,
        scopes: List[ScopeHookStore],
        executor: HookExecutor
    ):
        """
        Initialize chat wrapper.
        
        Args:
            original_chat: Original chat object from SDK
            scopes: List of scope hook stores
            executor: Hook executor instance
        """
        self._original = original_chat
        self._scopes = scopes
        self._executor = executor
    
    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access.
        
        If accessing 'completions', wrap it. Otherwise pass through.
        """
        attr = getattr(self._original, name)
        
        if name == "completions":
            return HookedCompletionsWrapper(attr, self._scopes, self._executor)
        
        return attr


class HookedCompletionsWrapper:
    """
    Wraps completions.create() with hook execution.
    
    All dependencies injected, no global state.
    """
    
    def __init__(
        self,
        original_completions: Any,
        scopes: List[ScopeHookStore],
        executor: HookExecutor
    ):
        """
        Initialize completions wrapper.
        
        Args:
            original_completions: Original completions object from SDK
            scopes: List of scope hook stores
            executor: Hook executor instance
        """
        self._original = original_completions
        self._scopes = scopes
        self._executor = executor
    
    async def create(self, *, model: str, messages: List[Dict], **kwargs) -> Any:
        """
        Hooked create method.
        
        Flow:
        1. Extract hookedllm-specific parameters (tags, metadata)
        2. Create normalized CallInput and CallContext
        3. Collect all hooks from all scopes
        4. Execute before hooks
        5. Call original SDK method
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
            Message(role=m.get("role", ""), content=m.get("content", ""))
            for m in messages
        ]
        
        # Create normalized input
        call_input = CallInput(
            model=model,
            messages=normalized_messages,
            params=kwargs,
            metadata=metadata
        )
        
        # Create context
        context = CallContext(
            provider="openai",
            model=model,
            tags=tags,
            metadata=metadata
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
            response = await self._original.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Normalize output
            output = self._normalize_output(response)
            
            # After hooks
            await self._executor.execute_after(
                all_after,
                call_input,
                output,
                context
            )
            
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
                elapsed_ms=elapsed
            )
            await self._executor.execute_finally(all_finally, result)
    
    def _normalize_output(self, response: Any) -> CallOutput:
        """
        Normalize provider response to CallOutput.
        
        Args:
            response: Original SDK response
            
        Returns:
            Normalized CallOutput
        """
        try:
            # Extract text from response
            text = None
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    text = getattr(choice.message, 'content', None)
            
            # Extract usage
            usage = None
            if hasattr(response, 'usage'):
                # Try to convert to dict
                usage_obj = response.usage
                if hasattr(usage_obj, 'model_dump'):
                    usage = usage_obj.model_dump()
                elif hasattr(usage_obj, 'dict'):
                    usage = usage_obj.dict()
                elif hasattr(usage_obj, '__dict__'):
                    usage = dict(usage_obj.__dict__)
            
            # Extract finish_reason
            finish_reason = None
            if hasattr(response, 'choices') and len(response.choices) > 0:
                finish_reason = getattr(response.choices[0], 'finish_reason', None)
            
            return CallOutput(
                text=text,
                raw=response,
                usage=usage,
                finish_reason=finish_reason
            )
        except Exception:
            # If normalization fails, return minimal output with raw response
            return CallOutput(text=None, raw=response, usage=None, finish_reason=None)
    
    def __getattr__(self, name: str) -> Any:
        """Pass through other attributes to original object."""
        return getattr(self._original, name)