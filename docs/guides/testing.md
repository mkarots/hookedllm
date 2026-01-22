# Testing Guide

HookedLLM is fully testable through dependency injection.

## Testing Hooks

Test hooks in isolation:

```python
import pytest
from hookedllm.core import CallInput, CallOutput, CallContext

async def test_log_hook():
    call_input = CallInput(model="gpt-4", messages=[{"role": "user", "content": "Hello"}])
    call_output = CallOutput(text="Hi there!")
    context = CallContext()
    
    await log_hook(call_input, call_output, context)
    
    assert context.metadata.get("logged") == True
```

## Testing Hook Execution

Use mocks to test execution:

```python
from unittest.mock import Mock, AsyncMock

mock_executor = Mock(spec=hookedllm.HookExecutor)
mock_executor.execute_after = AsyncMock()

ctx = hookedllm.create_context(executor=mock_executor)
ctx.scope("test").after(my_hook)
client = ctx.wrap(FakeClient(), scope="test")

await client.chat.completions.create(...)

assert mock_executor.execute_after.called
```

## Testing Rules

Test conditional rules:

```python
hookedllm.after(
    my_hook,
    when=hookedllm.when.model("gpt-4")
)

# Test with matching/non-matching models
```

## Testing Error Handling

```python
error_triggered = False

async def error_hook(call_input, error, context):
    nonlocal error_triggered
    error_triggered = True

hookedllm.error(error_hook)
client = hookedllm.wrap(FailingClient())

with pytest.raises(Exception):
    await client.chat.completions.create(...)

assert error_triggered
```

See [dependency-injection.md](dependency-injection.md) for DI patterns.
