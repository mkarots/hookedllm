# Performance Guide

Performance characteristics and optimization strategies for HookedLLM.

## Execution Model

Hooks execute sequentially (not in parallel). Each hook's execution time adds to total latency.

```python
hookedllm.before(hook1)  # Runs first
hookedllm.before(hook2)  # Runs second (waits for hook1)
```

**Total latency = LLM call time + sum of all hook execution times**

Async benefits: non-blocking I/O, concurrent LLM calls, efficient resource usage.

## Performance Overhead

- **Wrapper overhead**: ~0.1ms per call
- **Scope lookup**: ~0.05ms per scope
- **Rule evaluation**: ~0.01-0.1ms per rule

## Rule Performance

Rules are evaluated synchronously before hook execution. They are **not cached** - evaluated for every call.

```python
# ✅ Fast: Simple rule
hookedllm.after(hook, when=hookedllm.when.model("gpt-4"))

# ⚠️ Moderate: Composed rule
hookedllm.after(
    hook,
    when=hookedllm.when.model("gpt-4") & hookedllm.when.tag("monitoring")
)

# ❌ Slow: Complex lambda
hookedllm.after(
    hook,
    when=lambda call_input, ctx: expensive_computation(ctx)
)
```

**Best practices:**
- Keep rules simple
- Use built-in rules when possible
- Cache expensive computations in rule functions
- Handle rule errors (failed rules skip the hook)

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_check(model: str, tier: str) -> bool:
    return complex_check(model, tier)

hookedllm.after(
    hook,
    when=lambda call_input, ctx: expensive_check(
        call_input.model,
        ctx.metadata.get("tier", "")
    )
)
```

## Optimization Strategies

### Keep Hooks Fast

Hooks should complete quickly (<10ms ideally):

```python
# ✅ Good: Fast, non-blocking
async def fast_logging_hook(call_input, call_output, context):
    logger.info("llm_call", extra={
        "call_id": context.call_id,
        "model": call_input.model,
    })

# ❌ Bad: Slow, blocking
async def slow_hook(call_input, call_output, context):
    await database.save_call_details(call_input, call_output)
    await analytics.track(call_output)
```

### Use Background Tasks

Offload heavy operations:

```python
import asyncio
from queue import Queue

background_queue = Queue()

async def metrics_hook(result):
    """Fast hook that queues work for background processing."""
    background_queue.put({
        "call_id": result.context.call_id,
        "tokens": result.output.usage.get("total_tokens", 0),
    })

# Background worker processes the queue
async def background_worker():
    while True:
        item = await background_queue.get()
        await process_metrics(item)  # Slow operation, doesn't block calls
```

### Minimize Hook Count

Fewer hooks = lower latency:

```python
# ❌ Bad: Many small hooks
hookedllm.after(log_model)
hookedllm.after(log_tokens)
hookedllm.after(log_duration)

# ✅ Good: One comprehensive hook
async def comprehensive_logging(call_input, call_output, context):
    logger.info("llm_call", extra={
        "model": call_input.model,
        "tokens": call_output.usage.get("total_tokens", 0),
        "duration_ms": context.elapsed_ms,
    })
```

### Use Scopes

Scopes prevent hooks from running when not needed:

```python
# Evaluation hooks only run for evaluation clients
hookedllm.scope("evaluation").after(expensive_evaluation)

# Default scope hooks only run for default clients
hookedllm.scope("default").after(default_logging)
```

## Monitoring

Track hook execution time:

```python
import time

async def monitored_hook(call_input, call_output, context):
    start = time.perf_counter()
    try:
        # Your hook logic here
        await do_work(call_input, call_output, context)
    finally:
        duration = (time.perf_counter() - start) * 1000
        if duration > 10:
            logger.warning(f"Slow hook: {duration:.2f}ms")
```

## Performance Targets

- **Before hooks**: <5ms total
- **After hooks**: <10ms total
- **Finally hooks**: <5ms total
- **Rule evaluation**: <0.1ms per rule

See [examples/advanced.md](../examples/advanced.md) for more patterns.
