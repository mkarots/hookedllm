
# HookedLLM Architecture Plan - SOLID & DI Compliant

## Executive Summary

**hookedllm** is an async-first, type-safe Python package that provides
transparent observability for LLM calls through a wrapper pattern with
**scoped hook execution** and **dependency injection**. It enables 
developers to isolate hooks to specific parts of their application 
while following SOLID principles for testability and extensibility.

### Core Principles

1. **Transparent Drop-in**: `client = hookedllm.wrap(AsyncOpenAI())` - no code changes
2. **Scoped Isolation**: Named scopes prevent hook interference across application contexts  
4. **Minimal Imports**: Import just `hookedllm`, use OpenAI SDK as-is
5. **Conditional Execution**: Hooks run only when rules match (model, tags, metadata)
6. **Config or Code**: Define scopes/hooks programmatically or via YAML
7. **Type-Safe**: Protocol-based design with full type safety
8. **Async-First**: Native async, no blocking I/O
9. **Testable**: Full DI support, easy to mock dependencies
10. **Hook Isolation**: Hook failures never break LLM calls

---

## Key Concept: Named Scopes

**Problem**: Without scopes, all registered hooks run for all clients, causing unwanted side effects.

**Solution**: Named scopes create isolated namespaces. Clients explicitly opt into scopes.

```python
# Register hooks to scopes
hookedllm.scope("evaluation").after(evaluate_response)
hookedllm.scope("production").after(production_logger)

# Clients opt into specific scopes
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
prod_client = hookedllm.wrap(AsyncOpenAI(), scope="production")

# eval_client only runs evaluation hooks
# prod_client only runs production hooks
# No interference!
```

---

## Package Structure

```
hookedllm/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md
├── LICENSE
├── src/
│   └── hookedllm/
│       ├── __init__.py         # Public API
│       ├── core/
│       │   ├── __init__.py
│       │   ├── types.py        # Data models (CallInput, CallOutput, etc.)
│       │   ├── protocols.py    # Hook & DI protocols
│       │   ├── rules.py        # Rule system
│       │   ├── scopes.py       # Scope management (DI compliant)
│       │   ├── executor.py     # Hook execution (SRP compliant)
│       │   └── wrapper.py      # Client wrapper (DI injected)
│       ├── providers/
│       │   ├── __init__.py
│       │   └── openai.py       # OpenAI provider
│       ├── hooks/
│       │   ├── __init__.py
│       │   ├── evaluation.py   # Built-in evaluation hook
│       │   ├── metrics.py      # Usage tracking
│       │   └── logging.py      # Logging hook
│       └── config/
│           ├── __init__.py
│           ├── loader.py       # YAML config loader
│           └── schema.py       # Config validation
├── tests/
│   ├── test_wrapper.py
│   ├── test_scopes.py
│   ├── test_rules.py
│   ├── test_executor.py
│   └── test_integration.py
└── examples/
    ├── basic_usage.py
    ├── scoped_hooks.py
    ├── di_testing.py
    └── config_based.py
```

---

## SOLID Principles Application

### Single Responsibility Principle (SRP)

Each class has one reason to change:

- **`ScopeHookStore`**: Only stores hooks
- **`HookExecutor`**: Only executes hooks
- **`ScopeRegistry`**: Only manages scope lifecycle
- **`HookedClientWrapper`**: Only wraps and coordinates

### Open/Closed Principle (OCP)

- New hook types via Protocol (no core changes)
- New Rule types without modifying core
- New storage/execution strategies through injection

### Liskov Substitution Principle (LSP)

- Any `ScopeRegistry` implementation works
- Any `HookExecutor` implementation works
- Protocol-based ensures substitutability

### Interface Segregation Principle (ISP)

- Separate protocols for each concern
- Clients depend only on what they use

### Dependency Inversion Principle (DIP)

- High-level modules depend on abstractions
- Concrete implementations injected
- No hard-coded dependencies

---

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  Public API (Convenience Layer)                │
│  - Simple functions: wrap(), scope(), after()  │
│  - Uses default HookedLLMContext               │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│  HookedLLMContext (DI Container)               │
│  - Holds ScopeRegistry & HookExecutor          │
│  - Manages dependency lifecycle                │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│  Core Abstractions (Protocols)                 │
│  - ScopeRegistry Protocol                      │
│  - ScopeHookStore Protocol                     │
│  - HookExecutor Protocol                       │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│  Concrete Implementations                      │
│  - InMemoryScopeRegistry                       │
│  - InMemoryScopeHookStore                      │
│  - DefaultHookExecutor                         │
└─────────────────────────────────────────────────┘
```

---

## Core Protocols (Dependency Inversion)

**[`core/protocols.py`](src/hookedllm/core/protocols.py)**

```python
from typing import Protocol, List, Tuple, Optional, Any
from .types import CallInput, CallOutput, CallContext, CallResult
from .rules import Rule

# Hook function types
BeforeHook = Callable[[CallInput, CallContext], Awaitable[None]]
AfterHook = Callable[[CallInput, CallOutput, CallContext], Awaitable[None]]
ErrorHook = Callable[[CallInput, BaseException, CallContext], Awaitable[None]]
FinallyHook = Callable[[CallResult], Awaitable[None]]

class ScopeHookStore(Protocol):
    """
    Abstract interface for storing hooks in a scope.
    
    Responsibility: Storage only (SRP)
    """
    
    def add_before(self, hook: BeforeHook, rule: Optional[Rule] = None) -> None: ...
    def add_after(self, hook: AfterHook, rule: Optional[Rule] = None) -> None: ...
    def add_error(self, hook: ErrorHook, rule: Optional[Rule] = None) -> None: ...
    def add_finally(self, hook: FinallyHook, rule: Optional[Rule] = None) -> None: ...
    
    def get_before_hooks(self) -> List[Tuple[BeforeHook, Optional[Rule]]]: ...
    def get_after_hooks(self) -> List[Tuple[AfterHook, Optional[Rule]]]: ...
    def get_error_hooks(self) -> List[Tuple[ErrorHook, Optional[Rule]]]: ...
    def get_finally_hooks(self) -> List[Tuple[FinallyHook, Optional[Rule]]]: ...

class ScopeRegistry(Protocol):
    """
    Abstract interface for managing scopes.
    
    Responsibility: Scope lifecycle management (SRP)
    """
    
    def get_scope(self, name: str) -> ScopeHookStore: ...
    def get_global_scope(self) -> ScopeHookStore: ...
    def get_scopes_for_client(
        self, 
        scope_names: Optional[List[str]]
    ) -> List[ScopeHookStore]: ...

class HookExecutor(Protocol):
    """
    Abstract interface for executing hooks.
    
    Responsibility: Hook execution only (SRP)
    """
    
    async def execute_before(
        self,
        hooks: List[Tuple[BeforeHook, Optional[Rule]]],
        call_input: CallInput,
        context: CallContext
    ) -> None: ...
    
    async def execute_after(
        self,
        hooks: List[Tuple[AfterHook, Optional[Rule]]],
        call_input: CallInput,
        call_output: CallOutput,
        context: CallContext
    ) -> None: ...
    
    async def execute_error(
        self,
        hooks: List[Tuple[ErrorHook, Optional[Rule]]],
        call_input: CallInput,
        error: BaseException,
        context: CallContext
    ) -> None: ...
    
    async def execute_finally(
        self,
        hooks: List[Tuple[FinallyHook, Optional[Rule]]],
        result: CallResult
    ) -> None: ...
```

---

## Concrete Implementations

### Hook Storage

**[`core/scopes.py`](src/hookedllm/core/scopes.py)**

```python
class InMemoryScopeHookStore:
    """
    Concrete implementation of ScopeHookStore.
    
    Single Responsibility: Only stores hooks
    """
    
    def __init__(self, scope_name: str):
        self._scope_name = scope_name
        self._before: List[Tuple[BeforeHook, Optional[Rule]]] = []
        self._after: List[Tuple[AfterHook, Optional[Rule]]] = []
        self._error: List[Tuple[ErrorHook, Optional[Rule]]] = []
        self._finally: List[Tuple[FinallyHook, Optional[Rule]]] = []
    
    def add_before(self, hook: BeforeHook, rule: Optional[Rule] = None) -> None:
        self._before.append((hook, rule))
    
    def add_after(self, hook: AfterHook, rule: Optional[Rule] = None) -> None:
        self._after.append((hook, rule))
    
    def add_error(self, hook: ErrorHook, rule: Optional[Rule] = None) -> None:
        self._error.append((hook, rule))
    
    def add_finally(self, hook: FinallyHook, rule: Optional[Rule] = None) -> None:
        self._finally.append((hook, rule))
    
    def get_before_hooks(self) -> List[Tuple[BeforeHook, Optional[Rule]]]:
        return self._before.copy()  # Return copy for immutability
    
    def get_after_hooks(self) -> List[Tuple[AfterHook, Optional[Rule]]]:
        return self._after.copy()
    
    def get_error_hooks(self) -> List[Tuple[ErrorHook, Optional[Rule]]]:
        return self._error.copy()
    
    def get_finally_hooks(self) -> List[Tuple[FinallyHook, Optional[Rule]]]:
        return self._finally.copy()


class InMemoryScopeRegistry:
    """
    Concrete implementation of ScopeRegistry.
    
    Single Responsibility: Only manages scope lifecycle
    """
    
    def __init__(self):
        self._scopes: Dict[str, InMemoryScopeHookStore] = {}
        self._global = InMemoryScopeHookStore("__global__")
    
    def get_scope(self, name: str) -> InMemoryScopeHookStore:
        """Get or create a named scope."""
        if name not in self._scopes:
            self._scopes[name] = InMemoryScopeHookStore(name)
        return self._scopes[name]
    
    def get_global_scope(self) -> InMemoryScopeHookStore:
        """Get the global scope (always active)."""
        return self._global
    
    def get_scopes_for_client(
        self,
        scope_names: Optional[List[str]] = None
    ) -> List[InMemoryScopeHookStore]:
        """
        Get list of scopes for a client.
        
        Returns:
            Global scope + requested scopes
        """
        scopes = [self._global]  # Always include global
        
        if scope_names:
            for name in scope_names:
                scopes.append(self.get_scope(name))
        
        return scopes
```

### Hook Execution

**[`core/executor.py`](src/hookedllm/core/executor.py)**

```python
class DefaultHookExecutor:
    """
    Concrete hook executor with dependency injection.
    
    Single Responsibility: Only executes hooks
    Dependencies injected: error_handler, logger
    """
    
    def __init__(
        self,
        error_handler: Optional[Callable[[Exception, str], None]] = None,
        logger: Optional[Any] = None
    ):
        self._error_handler = error_handler or self._default_error_handler
        self._logger = logger
    
    async def execute_after(
        self,
        hooks: List[Tuple[AfterHook, Optional[Rule]]],
        call_input: CallInput,
        call_output: CallOutput,
        context: CallContext
    ) -> None:
        """Execute after hooks with rule matching."""
        for hook, rule in hooks:
            # Check if rule matches
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, call_output, context)
                except Exception as e:
                    self._error_handler(e, f"After hook {hook.__name__}")
                    if self._logger:
                        self._logger.error(f"After hook failed: {e}")
    
    async def execute_before(
        self,
        hooks: List[Tuple[BeforeHook, Optional[Rule]]],
        call_input: CallInput,
        context: CallContext
    ) -> None:
        """Execute before hooks with rule matching."""
        for hook, rule in hooks:
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, context)
                except Exception as e:
                    self._error_handler(e, f"Before hook {hook.__name__}")
                    if self._logger:
                        self._logger.error(f"Before hook failed: {e}")
    
    async def execute_error(
        self,
        hooks: List[Tuple[ErrorHook, Optional[Rule]]],
        call_input: CallInput,
        error: BaseException,
        context: CallContext
    ) -> None:
        """Execute error hooks."""
        for hook, rule in hooks:
            if rule is None or rule.matches(call_input, context):
                try:
                    await hook(call_input, error, context)
                except Exception as e:
                    self._error_handler(e, f"Error hook {hook.__name__}")
    
    async def execute_finally(
        self,
        hooks: List[Tuple[FinallyHook, Optional[Rule]]],
        result: CallResult
    ) -> None:
        """Execute finally hooks."""
        for hook, rule in hooks:
            # Finally hooks don't use rules (always run)
            try:
                await hook(result)
            except Exception as e:
                self._error_handler(e, f"Finally hook {hook.__name__}")
    
    def _default_error_handler(self, error: Exception, context: str) -> None:
        """Default: swallow errors, optionally log."""
        pass  # Hooks should never break the main flow
```

---

## DI Container

**[`__init__.py`](src/hookedllm/__init__.py)**

```python
from typing import Optional, Union, List
from .core.protocols import ScopeRegistry, HookExecutor
from .core.scopes import InMemoryScopeRegistry
from .core.executor import DefaultHookExecutor
from .core.wrapper import HookedClientWrapper
from .core.rules import RuleBuilder

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
        """Get a scope manager from this context."""
        return self.registry.get_scope(name)
    
    def global_scope(self):
        """Get the global scope."""
        return self.registry.get_global_scope()
    
    # Convenience methods for global scope
    def before(self, hook, *, when=None):
        """Register a global before hook."""
        self.global_scope().add_before(hook, when)
    
    def after(self, hook, *, when=None):
        """Register a global after hook."""
        self.global_scope().add_after(hook, when)
    
    def error(self, hook, *, when=None):
        """Register a global error hook."""
        self.global_scope().add_error(hook, when)
    
    def finally_(self, hook, *, when=None):
        """Register a global finally hook."""
        self.global_scope().add_finally(hook, when)


# ============================================================
# Public API - Convenience layer with default context
# ============================================================

# Default context for simple usage
_default_context = HookedLLMContext()

# Rule builder
when = RuleBuilder()

def wrap(client, scope=None):
    """
    Wrap a client with hook support (uses default context).
    
    Example:
        client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
    """
    return _default_context.wrap(client, scope)

def scope(name: str):
    """
    Get a scope manager (uses default context).
    
    Example:
        hookedllm.scope("evaluation").after(my_hook)
    """
    return _default_context.scope(name)

def before(hook, *, when=None):
    """Register a global before hook (uses default context)."""
    _default_context.before(hook, when=when)

def after(hook, *, when=None):
    """Register a global after hook (uses default context)."""
    _default_context.after(hook, when=when)

def error(hook, *, when=None):
    """Register a global error hook (uses default context)."""
    _default_context.error(hook, when=when)

def finally_(hook, *, when=None):
    """Register a global finally hook (uses default context)."""
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
    
    Example:
        ctx = hookedllm.create_context(
            executor=MyCustomExecutor(logger=my_logger)
        )
        client = ctx.wrap(AsyncOpenAI(), scope="test")
    """
    return HookedLLMContext(registry, executor)

__all__ = [
    "wrap",
    "scope",
    "before",
    "after",
    "error",
    "finally_",
    "when",
    "create_context",
    "HookedLLMContext",
]

__version__ = "0.1.0"
```

---

## Wrapper with DI

**[`core/wrapper.py`](src/hookedllm/core/wrapper.py)**

```python
class HookedClientWrapper:
    """
    Transparent proxy with all dependencies injected.
    
    No global state - all dependencies passed via constructor (DI)
    """
    
    def __init__(
        self,
        original_client: Any,
        scopes: List[ScopeHookStore],  # Injected!
        executor: HookExecutor          # Injected!
    ):
        self._original = original_client
        self._scopes = scopes
        self._executor = executor
    
    def __getattr__(self, name: str) -> Any:
        """Intercept attribute access."""
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
        self._original = original_chat
        self._scopes = scopes
        self._executor = executor  # Injected executor (DI)
    
    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._original, name)
        
        if name == "completions":
            return HookedCompletionsWrapper(
                attr,
                self._scopes,
                self._executor
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
        scopes: List[ScopeHookStore],
        executor: HookExecutor
    ):
        self._original = original_completions
        self._scopes = scopes
        self._executor = executor
    
    async def create(self, *, model: str, messages: List[Dict], **kwargs):
        """
        Hooked create method.
        
        Flow:
        1. Collect all hooks from all scopes
        2. Execute before hooks
        3. Call original SDK
        4. Execute after/error hooks
        5. Execute finally hooks
        6. Return original SDK response
        """
        import time
        from datetime import datetime, timezone
        from ..core.types import CallInput, CallOutput, CallContext, CallResult
        
        # Extract hookedllm-specific params
        extra_body = kwargs.get("extra_body", {})
        tags = extra_body.pop("hookedllm_tags", [])
        metadata = extra_body.pop("hookedllm_metadata", {})
        
        # Create context
        call_input = CallInput(
            model=model,
            messages=messages,
            params=kwargs
        )
        
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
        
        # Execute hooks
        t0 = time.perf_counter()
        output = None
        error = None
        
        try:
            # Before hooks
            await self._executor.execute_before(all_before, call_input, context)
            
            # Original call
            response = await self._original.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Normalize output
            output = CallOutput(
                text=response.choices[0].message.content,
                raw=response,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
            
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
    
    def __getattr__(self, name: str) -> Any:
        """Pass through other attributes."""
        return getattr(self._original, name)
```

---

## Usage Examples

### Simple Usage (Default DI)

```python
import hookedllm
from openai import AsyncOpenAI

# Register hooks to scopes
hookedllm.scope("evaluation").after(evaluate_hook)
hookedllm.scope("production").after(prod_logger)

# Global hook (runs for all clients)
hookedllm.after(global_metrics)

# Wrap clients with scopes
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
prod_client = hookedllm.wrap(AsyncOpenAI(), scope="production")

# Use normally
await eval_client.chat.completions.create(...)  # global_metrics + evaluate_hook
await prod_client.chat.completions.create(...)  # global_metrics + prod_logger
```

### Advanced Usage (Custom DI)

```python
import hookedllm

# Create custom executor with custom error handling
def my_error_handler(error, context):
    print(f"Hook error in {context}: {error}")

custom_executor = hookedllm.DefaultHookExecutor(
    error_handler=my_error_handler,
    logger=my_logger
)

# Create custom context
ctx = hookedllm.create_context(executor=custom_executor)

# Use custom context
ctx.scope("test").after(test_hook)
client = ctx.wrap(AsyncOpenAI(), scope="test")
```

### Testing with Mocks

```python
import hookedllm
from unittest.mock import Mock

def test_hook_execution():
    # Arrange: Create mock dependencies
    mock_registry = Mock(spec=hookedllm.ScopeRegistry)
    mock_executor = Mock(spec=hookedllm.HookExecutor)
    
    # Mock behavior
    mock_scope = Mock()
    mock_registry.get_scopes_for_client.return_value = [mock_scope]
    
    # Create context with mocks (DI!)
    ctx = hookedllm.create_context(
        registry=mock_registry,
        executor=mock_executor
    )
    
    # Act
    ctx.scope("test").after(test_hook)
    client = ctx.wrap(FakeOpenAI(), scope="test")
    await client.chat.completions.create(...)
    
    # Assert
    mock_executor.execute_after.assert_called_once()
```

### Multiple Scopes

```python
import hookedllm

# Different scopes for different concerns
hookedllm.scope("logging").finally_(log_call)
hookedllm.scope("metrics").finally_(track_metrics)
hookedllm.scope("evaluation").after(evaluate)

# Client with multiple scopes
client = hookedllm.wrap(
    AsyncOpenAI(),
    scope=["logging", "metrics", "evaluation"]
)

# This call runs: log_call + track_metrics + evaluate + global hooks
await client.chat.completions.create(...)
```

### Conditional Rules Within Scopes

```python
import hookedllm

# Expensive evaluation only for GPT-4 in eval scope
hookedllm.scope("evaluation").after(
    deep_eval,
    when=hookedllm.when.model("gpt-4")
)

# Light metrics for all models in eval scope
hookedllm.scope("evaluation").after(quick_metrics)

# GPT-4 call: runs deep_eval + quick_metrics
# GPT-3.5 call: runs quick_metrics only
```

---

## Config-Based Setup

**hookedllm.yaml:**
```yaml
# Global hooks (apply to all clients)
global_hooks:
  - name: global_error_tracking
    type: error
    module: my_app.hooks
    function: track_all_errors

# Scoped hooks
scopes:
  evaluation:
    hooks:
      - name: evaluate_gpt4
        type: after
        module: my_app.hooks
        function: evaluate_response
        when:
          model: gpt-4
  
  production:
    hooks:
      - name: prod_logger
        type: finally
        module: my_app.hooks
        function: log_production_call
      
      - name: critical_alerts
        type: error
        module: my_app.hooks
        function: page_oncall
        when:
          tags: [critical]
```

**Python:**
```python
import hookedllm

# Load all scopes and hooks
hookedllm.load_config("hookedllm.yaml")

# Clients auto-configured!
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
prod_client = hookedllm.wrap(AsyncOpenAI(), scope="production")
```

---

## SOLID Compliance Summary

✅ **Single Responsibility Principle**
- `ScopeHookStore`: Only stores hooks
- `HookExecutor`: Only executes hooks
- `ScopeRegistry`: Only manages scopes
- `HookedClientWrapper`: Only wraps and coordinates

✅ **Open/Closed Principle**
- Open for extension (new hooks, rules, strategies)
- Closed for modification (core unchanged)

✅ **Liskov Substitution Principle**
- Any `ScopeRegistry` implementation works
- Any `HookExecutor` implementation works
- Protocol-based design ensures substitutability

✅ **Interface Segregation Principle**
- Separate protocols for each concern
- Clients depend only on what they use

✅ **Dependency Inversion Principle**
- Depends on abstractions (Protocols)
- Concrete implementations injected