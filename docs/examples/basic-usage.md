# Basic Usage Example

Complete examples demonstrating HookedLLM fundamentals. For a quick introduction, see the [Quick Start Guide](../quick-start.md).

This example shows a complete application setup combining multiple concepts: hook registration, scopes, rules, and all hook types.

## Complete Example

```python
import asyncio
import hookedllm
from openai import AsyncOpenAI

# Define hooks
async def track_metrics(result):
    """Track metrics in finally hook."""
    if result.output:
        print(f"[METRICS] Call {result.context.call_id} took {result.elapsed_ms:.2f}ms")

async def evaluate_response(call_input, call_output, context):
    """Evaluate response quality."""
    print(f"[EVAL] Evaluating response for: {call_input.model}")
    context.metadata["eval_score"] = 0.9

async def log_call(call_input, call_output, context):
    """Log every LLM call."""
    print(f"[LOG] Model: {call_input.model}")

# Register hooks
hookedllm.finally_(track_metrics)  # Global hook
hookedllm.scope("evaluation").after(evaluate_response)
hookedllm.scope("evaluation").after(log_call)

# Create client with evaluation scope
client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")

# Use the client
async def main():
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Next Steps

- Learn about [Scopes](../scopes.md) for isolating hooks
- Explore [Rules](../rules.md) for conditional execution
- See [Advanced Examples](advanced.md) for more patterns

