"""
Protocol definitions for hooks and dependency injection.

These protocols define the interfaces that components must implement,
following the Dependency Inversion Principle.
"""

from __future__ import annotations
from typing import Protocol, Callable, Awaitable, List, Tuple, Optional
from .types import CallInput, CallOutput, CallContext, CallResult


# Hook function type aliases  
BeforeHook = Callable[[CallInput, CallContext], Awaitable[None]]
AfterHook = Callable[[CallInput, CallOutput, CallContext], Awaitable[None]]
ErrorHook = Callable[[CallInput, BaseException, CallContext], Awaitable[None]]
FinallyHook = Callable[[CallResult], Awaitable[None]]


class Rule(Protocol):
    """
    Protocol for hook execution rules.
    
    Rules determine whether a hook should execute based on the
    call input and context.
    """
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        """Check if this rule matches the given call."""
        ...
    
    def __and__(self, other: Rule) -> Rule:
        """Combine rules with AND logic."""
        ...
    
    def __or__(self, other: Rule) -> Rule:
        """Combine rules with OR logic."""
        ...
    
    def __invert__(self) -> Rule:
        """Negate the rule (NOT logic)."""
        ...


class ScopeHookStore(Protocol):
    """
    Protocol for storing hooks in a scope.
    
    Single Responsibility: Storage only, no execution logic.
    """
    
    def add_before(self, hook: BeforeHook, rule: Optional[Rule] = None) -> None:
        """Add a before hook with optional execution rule."""
        ...
    
    def add_after(self, hook: AfterHook, rule: Optional[Rule] = None) -> None:
        """Add an after hook with optional execution rule."""
        ...
    
    def add_error(self, hook: ErrorHook, rule: Optional[Rule] = None) -> None:
        """Add an error hook with optional execution rule."""
        ...
    
    def add_finally(self, hook: FinallyHook, rule: Optional[Rule] = None) -> None:
        """Add a finally hook with optional execution rule."""
        ...
    
    def get_before_hooks(self) -> List[Tuple[BeforeHook, Optional[Rule]]]:
        """Get all before hooks with their rules."""
        ...
    
    def get_after_hooks(self) -> List[Tuple[AfterHook, Optional[Rule]]]:
        """Get all after hooks with their rules."""
        ...
    
    def get_error_hooks(self) -> List[Tuple[ErrorHook, Optional[Rule]]]:
        """Get all error hooks with their rules."""
        ...
    
    def get_finally_hooks(self) -> List[Tuple[FinallyHook, Optional[Rule]]]:
        """Get all finally hooks with their rules."""
        ...


class ScopeRegistry(Protocol):
    """
    Protocol for managing scopes.
    
    Single Responsibility: Scope lifecycle management only.
    """
    
    def get_scope(self, name: str) -> ScopeHookStore:
        """Get or create a named scope."""
        ...
    
    def get_global_scope(self) -> ScopeHookStore:
        """Get the global scope (always active)."""
        ...
    
    def get_scopes_for_client(
        self,
        scope_names: Optional[List[str]]
    ) -> List[ScopeHookStore]:
        """Get list of scopes for a client."""
        ...


class HookExecutor(Protocol):
    """
    Protocol for executing hooks.
    
    Single Responsibility: Hook execution only, no storage.
    """
    
    async def execute_before(
        self,
        hooks: List[Tuple[BeforeHook, Optional[Rule]]],
        call_input: CallInput,
        context: CallContext
    ) -> None:
        """Execute before hooks with rule matching."""
        ...
    
    async def execute_after(
        self,
        hooks: List[Tuple[AfterHook, Optional[Rule]]],
        call_input: CallInput,
        call_output: CallOutput,
        context: CallContext
    ) -> None:
        """Execute after hooks with rule matching."""
        ...
    
    async def execute_error(
        self,
        hooks: List[Tuple[ErrorHook, Optional[Rule]]],
        call_input: CallInput,
        error: BaseException,
        context: CallContext
    ) -> None:
        """Execute error hooks with rule matching."""
        ...
    
    async def execute_finally(
        self,
        hooks: List[Tuple[FinallyHook, Optional[Rule]]],
        result: CallResult
    ) -> None:
        """Execute finally hooks."""
        ...