# Dependency Injection Guide

HookedLLM uses dependency injection for testability and customization.

## Basic Usage

Default context uses sensible defaults:

```python
import hookedllm

client = hookedllm.wrap(AsyncOpenAI())
```

## Custom Context

Create a custom context with injected dependencies:

```python
from hookedllm.core import InMemoryScopeRegistry, DefaultHookExecutor

registry = InMemoryScopeRegistry()
executor = DefaultHookExecutor()

ctx = hookedllm.create_context(
    registry=registry,
    executor=executor
)

client = ctx.wrap(AsyncOpenAI())
```

## Custom Executor

Customize error handling and logging:

```python
from hookedllm.core import DefaultHookExecutor
import logging

def my_error_handler(error, context):
    logger.error(f"Hook failed: {error}")

executor = DefaultHookExecutor(
    error_handler=my_error_handler,
    logger=logging.getLogger("myapp")
)

ctx = hookedllm.create_context(executor=executor)
```

## Testing with Mocks

```python
from unittest.mock import Mock

mock_executor = Mock(spec=hookedllm.HookExecutor)
ctx = hookedllm.create_context(executor=mock_executor)

ctx.scope("test").after(my_hook)
client = ctx.wrap(FakeClient(), scope="test")

# Assert
assert mock_executor.execute_after.called
```

See [testing.md](testing.md) for more patterns.
