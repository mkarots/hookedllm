# Scopes Example

Real-world examples demonstrating scope usage patterns. For basic scope concepts, see the [Scopes guide](../scopes.md).

## Real-World Example

```python
import hookedllm
from openai import AsyncOpenAI

# Development scope - verbose logging
hookedllm.scope("development").after(
    lambda i, o, c: print(f"[DEV] {c.call_id}: {o.text[:50]}")
)

# Testing scope - mock responses
hookedllm.scope("testing").before(
    lambda i, c: setattr(c, "skip_call", True)
)

# Default scope - minimal logging
hookedllm.scope("default").finally_(
    lambda r: logger.info(f"Call {r.context.call_id} completed")
)

# Create clients for different environments
dev_client = hookedllm.wrap(AsyncOpenAI(), scope="development")
test_client = hookedllm.wrap(AsyncOpenAI(), scope="testing")
default_client = hookedllm.wrap(AsyncOpenAI(), scope="default")
```

## Next Steps

- Learn more about [Scopes](../scopes.md)
- See [Advanced Examples](advanced.md) for more patterns

