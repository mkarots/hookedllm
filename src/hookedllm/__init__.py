"""
HookedLLM - Scoped observability for LLM calls with SOLID/DI architecture.

Simple usage:
    import hookedllm
    from openai import AsyncOpenAI
    
    # Register hooks to scopes
    hookedllm.scope("evaluation").after(evaluate_hook)
    
    # Wrap client with scope
    client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
    
    # Use normally - hooks auto-execute!
    response = await client.chat.completions.create(...)

Advanced usage (custom DI):
    ctx = hookedllm.create_context(
        executor=CustomExecutor(logger=my_logger)
    )
    client = ctx.wrap(AsyncOpenAI(), scope="test")
"""

from __future__ import annotations
from typing import Optional, Union, List, Any
from .core import (
    ScopeRegistry,
    HookExecutor,
    InMemoryScopeRegistry,
    DefaultHookExecutor,
    HookedClientWrapper,
    RuleBuilder,
    BeforeHook,
    AfterHook,
    ErrorHook,
    FinallyHook,
    Rule,
)


class HookedLLMContext:
    """
    Dependency Injection container for hookedllm.
    
    Holds all dependencies (registry, executor) and provides
    factory methods for creating wrapped clients and accessing scopes.
    
    Benefits:
    - Testable: inject mock dependencies
    - Flexible: swap implementations
    - Explicit: dependencies are clear
    """
    
    def __init__(
        self,
        registry: Optional[ScopeRegistry] = None,
        executor: Optional[HookExecutor] = None
    ):
        """
        Initialize context with optional dependency injection.
        
        Args:
            registry: Custom scope registry (default: InMemoryScopeRegistry)
            executor: Custom hook executor (default: DefaultHookExecutor)
        """
        # Allow injection of custom implementations (DIP)
        self.registry = registry or InMemoryScopeRegistry()
        self.executor = executor or DefaultHookExecutor()
    
    def wrap(
        self,
        client: Any,
        scope: Optional[Union[str, List[str]]] = None
    ) -> HookedClientWrapper:
        """
        Wrap a client using this context's dependencies.
        
        Args:
            client: OpenAI-compatible client
            scope: None, single scope name, or list of scope names
            
        Returns:
            Wrapped client with injected dependencies
            
        Example:
            client = ctx.wrap(AsyncOpenAI(), scope="evaluation")
        """
        # Convert scope to list
        if scope is None:
            scope_list = None
        elif isinstance(scope, str):
            scope_list = [scope]
        else:
            scope_list = scope
        
        # Get scopes from registry
        scopes = self.registry.get_scopes_for_client(scope_list)
        
        # Create wrapper with injected dependencies (DI!)
        return HookedClientWrapper(
            client,
            scopes,
            self.executor
        )
    
    def scope(self, name: str):
        """
        Get a scope manager from this context.
        
        Args:
            name: Scope name
            
        Returns:
            Scope hook store
            
        Example:
            ctx.scope("evaluation").after(my_hook)
        """
        return self.registry.get_scope(name)
    
    def global_scope(self):
        """
        Get the global scope (always active).
        
        Returns:
            Global scope hook store
        """
        return self.registry.get_global_scope()
    
    # Convenience methods for global scope
    def before(self, hook: BeforeHook, *, when: Optional[Rule] = None) -> None:
        """Register a global before hook."""
        self.global_scope().add_before(hook, when)
    
    def after(self, hook: AfterHook, *, when: Optional[Rule] = None) -> None:
        """Register a global after hook."""
        self.global_scope().add_after(hook, when)
    
    def error(self, hook: ErrorHook, *, when: Optional[Rule] = None) -> None:
        """Register a global error hook."""
        self.global_scope().add_error(hook, when)
    
    def finally_(self, hook: FinallyHook, *, when: Optional[Rule] = None) -> None:
        """Register a global finally hook."""
        self.global_scope().add_finally(hook, when)


# ============================================================
# Public API - Convenience layer with default context
# ============================================================

# Default context for simple usage
_default_context = HookedLLMContext()

# Rule builder instance
when = RuleBuilder()


def wrap(client: Any, scope: Optional[Union[str, List[str]]] = None) -> HookedClientWrapper:
    """
    Wrap a client with hook support (uses default context).
    
    Args:
        client: OpenAI-compatible client
        scope: None, single scope name, or list of scope names
        
    Returns:
        Wrapped client
        
    Example:
        from openai import AsyncOpenAI
        client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
    """
    return _default_context.wrap(client, scope)


def scope(name: str):
    """
    Get a scope manager (uses default context).
    
    Args:
        name: Scope name
        
    Returns:
        Scope hook store
        
    Example:
        hookedllm.scope("evaluation").after(my_hook)
    """
    return _default_context.scope(name)


def before(hook: BeforeHook, *, when: Optional[Rule] = None) -> None:
    """
    Register a global before hook (uses default context).
    
    Args:
        hook: Before hook function
        when: Optional rule for conditional execution
        
    Example:
        hookedllm.before(my_hook, when=hookedllm.when.model("gpt-4"))
    """
    _default_context.before(hook, when=when)


def after(hook: AfterHook, *, when: Optional[Rule] = None) -> None:
    """
    Register a global after hook (uses default context).
    
    Args:
        hook: After hook function
        when: Optional rule for conditional execution
        
    Example:
        hookedllm.after(my_hook, when=hookedllm.when.tag("production"))
    """
    _default_context.after(hook, when=when)


def error(hook: ErrorHook, *, when: Optional[Rule] = None) -> None:
    """
    Register a global error hook (uses default context).
    
    Args:
        hook: Error hook function
        when: Optional rule for conditional execution
        
    Example:
        hookedllm.error(my_hook)
    """
    _default_context.error(hook, when=when)


def finally_(hook: FinallyHook, *, when: Optional[Rule] = None) -> None:
    """
    Register a global finally hook (uses default context).
    
    Args:
        hook: Finally hook function
        when: Optional rule for conditional execution
        
    Example:
        hookedllm.finally_(my_hook)
    """
    _default_context.finally_(hook, when=when)


def create_context(
    registry: Optional[ScopeRegistry] = None,
    executor: Optional[HookExecutor] = None
) -> HookedLLMContext:
    """
    Create a custom context with injected dependencies.
    
    Use this for:
    - Testing (inject mocks)
    - Custom implementations  
    - Isolated environments
    
    Args:
        registry: Custom scope registry
        executor: Custom hook executor
        
    Returns:
        New context instance
        
    Example:
        ctx = hookedllm.create_context(
            executor=MyCustomExecutor(logger=my_logger)
        )
        client = ctx.wrap(AsyncOpenAI(), scope="test")
    """
    return HookedLLMContext(registry, executor)


# Export commonly used types and implementations for advanced users
from .core import (
    InMemoryScopeRegistry,
    DefaultHookExecutor,
)

# Config loader (optional - requires pyyaml)
try:
    from .config.loader import load_config as _load_config
    
    def load_config(path: str) -> None:
        """
        Load hooks from YAML configuration file.
        
        Requires: pip install hookedllm[config]
        
        Args:
            path: Path to YAML config file
            
        Example:
            hookedllm.load_config("hooks.yaml")
        """
        _load_config(path, context=_default_context)
    
    __has_config = True
except ImportError:
    def load_config(path: str) -> None:
        raise ImportError(
            "YAML config loading requires pyyaml. "
            "Install with: pip install hookedllm[config]"
        )
    __has_config = False

__all__ = [
    # Main functions (simple API)
    "wrap",
    "scope",
    "before",
    "after",
    "error",
    "finally_",
    "when",
    "create_context",
    "load_config",
    # DI container
    "HookedLLMContext",
    # Implementations (for advanced users)
    "InMemoryScopeRegistry",
    "DefaultHookExecutor",
]

__version__ = "0.1.0"