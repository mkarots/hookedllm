"""
Scope management for isolated hook execution.

Scopes allow hooks to be registered and executed only for specific clients,
preventing interference across different application contexts.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from .protocols import BeforeHook, AfterHook, ErrorHook, FinallyHook, Rule, ScopeHookStore


class InMemoryScopeHookStore:
    """
    Concrete implementation of ScopeHookStore.
    
    Single Responsibility: Only stores hooks.
    Stores hooks in memory with their associated rules.
    """
    
    def __init__(self, scope_name: str):
        self._scope_name = scope_name
        self._before: List[Tuple[BeforeHook, Optional[Rule]]] = []
        self._after: List[Tuple[AfterHook, Optional[Rule]]] = []
        self._error: List[Tuple[ErrorHook, Optional[Rule]]] = []
        self._finally: List[Tuple[FinallyHook, Optional[Rule]]] = []
    
    @property
    def name(self) -> str:
        """Get the scope name."""
        return self._scope_name
    
    def add_before(self, hook: BeforeHook, rule: Optional[Rule] = None) -> None:
        """Add a before hook with optional execution rule."""
        self._before.append((hook, rule))
    
    def add_after(self, hook: AfterHook, rule: Optional[Rule] = None) -> None:
        """Add an after hook with optional execution rule."""
        self._after.append((hook, rule))
    
    def add_error(self, hook: ErrorHook, rule: Optional[Rule] = None) -> None:
        """Add an error hook with optional execution rule."""
        self._error.append((hook, rule))
    
    def add_finally(self, hook: FinallyHook, rule: Optional[Rule] = None) -> None:
        """Add a finally hook with optional execution rule."""
        self._finally.append((hook, rule))
    
    def get_before_hooks(self) -> List[Tuple[BeforeHook, Optional[Rule]]]:
        """Get all before hooks with their rules (returns copy)."""
        return self._before.copy()
    
    def get_after_hooks(self) -> List[Tuple[AfterHook, Optional[Rule]]]:
        """Get all after hooks with their rules (returns copy)."""
        return self._after.copy()
    
    def get_error_hooks(self) -> List[Tuple[ErrorHook, Optional[Rule]]]:
        """Get all error hooks with their rules (returns copy)."""
        return self._error.copy()
    
    def get_finally_hooks(self) -> List[Tuple[FinallyHook, Optional[Rule]]]:
        """Get all finally hooks with their rules (returns copy)."""
        return self._finally.copy()
    
    # Convenience methods that mirror the add_* interface
    def before(self, hook: BeforeHook, *, when: Optional[Rule] = None) -> None:
        """Alias for add_before with keyword 'when' parameter."""
        self.add_before(hook, when)
    
    def after(self, hook: AfterHook, *, when: Optional[Rule] = None) -> None:
        """Alias for add_after with keyword 'when' parameter."""
        self.add_after(hook, when)
    
    def error(self, hook: ErrorHook, *, when: Optional[Rule] = None) -> None:
        """Alias for add_error with keyword 'when' parameter."""
        self.add_error(hook, when)
    
    def finally_(self, hook: FinallyHook, *, when: Optional[Rule] = None) -> None:
        """Alias for add_finally with keyword 'when' parameter."""
        self.add_finally(hook, when)


class InMemoryScopeRegistry:
    """
    Concrete implementation of ScopeRegistry.
    
    Single Responsibility: Only manages scope lifecycle.
    Creates and retrieves scopes, manages global scope.
    """
    
    def __init__(self):
        self._scopes: Dict[str, InMemoryScopeHookStore] = {}
        self._global = InMemoryScopeHookStore("__global__")
    
    def get_scope(self, name: str) -> InMemoryScopeHookStore:
        """
        Get or create a named scope.
        
        Args:
            name: Scope name
            
        Returns:
            Scope hook store for the named scope
        """
        if name not in self._scopes:
            self._scopes[name] = InMemoryScopeHookStore(name)
        return self._scopes[name]
    
    def get_global_scope(self) -> InMemoryScopeHookStore:
        """
        Get the global scope (always active).
        
        Returns:
            The global scope hook store
        """
        return self._global
    
    def get_scopes_for_client(
        self,
        scope_names: Optional[List[str]] = None
    ) -> List[InMemoryScopeHookStore]:
        """
        Get list of scopes for a client.
        
        Always includes the global scope, plus any requested scopes.
        
        Args:
            scope_names: List of scope names, or None for global only
            
        Returns:
            List of scope hook stores (global + requested scopes)
        """
        scopes = [self._global]  # Always include global
        
        if scope_names:
            for name in scope_names:
                scopes.append(self.get_scope(name))
        
        return scopes
    
    def scope(self, name: str) -> InMemoryScopeHookStore:
        """Alias for get_scope for more fluent API."""
        return self.get_scope(name)