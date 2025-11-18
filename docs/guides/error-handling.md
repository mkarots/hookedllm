# Error Handling Guide

Error handling patterns for HookedLLM.

## Error Model

**Hook failures never break your LLM calls.** Each hook's errors are isolated.

```python
async def buggy_hook(call_input, call_output, context):
    raise ValueError("Hook failed!")

hookedllm.after(buggy_hook)

# The LLM call still succeeds even if the hook fails
response = await client.chat.completions.create(...)
```

## Error Handling Patterns

### Error Logging

Log errors with context:

```python
import logging

logger = logging.getLogger(__name__)

async def error_handler(call_input, error, context):
    logger.error(
        "llm_call_failed",
        extra={
            "call_id": context.call_id,
            "model": call_input.model,
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
        exc_info=True,
    )

hookedllm.error(error_handler)
```

### Error Classification

Handle different error types:

```python
async def error_handler(call_input, error, context):
    error_type = type(error).__name__
    
    if error_type == "RateLimitError":
        logger.warning(f"Rate limit: {context.call_id}")
        await schedule_retry(context.call_id, backoff=60)
    elif error_type == "AuthenticationError":
        logger.critical(f"Auth error: {context.call_id}")
        await send_alert("Authentication failed")
```

### Rule Evaluation Errors

Rules that fail are skipped (hook doesn't execute):

```python
# Rule that might fail
def safe_rule(call_input, ctx):
    try:
        return ctx.metadata.get("key") == "value"
    except Exception:
        return False  # Don't match on error

hookedllm.after(hook, when=safe_rule)
```

See [examples/advanced.md](../examples/advanced.md) for more patterns.
