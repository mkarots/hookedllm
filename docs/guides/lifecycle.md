# Lifecycle & Concurrency Guide

Hook registration, memory management, and thread safety.

## Hook Registration

Register hooks at application startup (before concurrent access):

```python
# app/startup.py
import hookedllm

def initialize_hooks():
    hookedllm.scope("default").after(default_logger)
    hookedllm.scope("default").error(error_handler)
    hookedllm.finally_(metrics_collector)

initialize_hooks()  # Call during app startup
```

**Thread Safety**: The default registry is **NOT thread-safe**. Register hooks before concurrent access.

## Hook Unregistration

HookedLLM doesn't provide built-in hook unregistration. Use conditional execution or separate contexts:

```python
# Conditional execution
ENABLE_EVALUATION = os.getenv("ENABLE_EVALUATION", "false") == "true"
if ENABLE_EVALUATION:
    hookedllm.scope("evaluation").after(evaluator)

# Or use separate contexts
evaluation_ctx = hookedllm.create_context()
default_ctx = hookedllm.create_context()
```

## Concurrency

**Hook execution is safe for concurrent LLM calls** - each call has its own context.

```python
# ✅ Safe: Multiple concurrent calls
async def make_call(client):
    return await client.chat.completions.create(...)

await asyncio.gather(
    make_call(client1),
    make_call(client2),
    make_call(client3),
)
```

**Shared state**: Use thread-safe structures if hooks access shared data:

```python
import asyncio

counter = asyncio.Lock()
count = 0

async def safe_hook(call_input, call_output, context):
    async with counter:
        global count
        count += 1
```

## Memory Management

**Best practices:**
- Don't store large objects in hooks or contexts
- Use bounded storage for accumulating data
- Clean up resources in finally hooks

```python
# ✅ Good: Bounded storage
from collections import deque
call_history = deque(maxlen=1000)

async def hook(result):
    call_history.append(result)  # Bounded size
```

## Scope Lifecycle

Scopes are created on-demand and stored in memory (don't persist across restarts).

```python
# Scope created when first accessed
hookedllm.scope("default").after(hook)
```

See [examples/advanced.md](../examples/advanced.md) for more patterns.
