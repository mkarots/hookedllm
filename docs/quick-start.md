# Quick Start Guide

Get started with HookedLLM in minutes. This guide will walk you through installing and using HookedLLM to add observability to your LLM calls.

## Installation

Install HookedLLM using pip:

```bash
# Core package (zero dependencies)
pip install hookedllm

# With OpenAI support
pip install hookedllm[openai]

# With all optional dependencies
pip install hookedllm[all]
```

## Your First Hook

Let's create a simple hook that logs every LLM call:

```python
import hookedllm
from openai import AsyncOpenAI

# Define a hook function
async def log_call(call_input, call_output, context):
    """Log information about each LLM call."""
    print(f"Model: {call_input.model}")
    print(f"Tokens used: {call_output.usage.get('total_tokens', 0)}")
    print(f"Call ID: {context.call_id}")

# Register the hook globally (runs for all clients)
hookedllm.after(log_call)

# Wrap your OpenAI client
client = hookedllm.wrap(AsyncOpenAI(api_key="your-api-key"))

# Use the client normally - hooks execute automatically!
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Using Scopes

Scopes let you isolate hooks to specific parts of your application:

```python
# Register hooks to different scopes
hookedllm.scope("evaluation").after(evaluate_response)
hookedllm.scope("default").after(log_to_default)

# Create clients with specific scopes
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
default_client = hookedllm.wrap(AsyncOpenAI(), scope="default")

# Each client only runs hooks from its scope
```

## Hook Types

HookedLLM supports four hook types:

```python
# Before: runs before LLM call
async def before_hook(call_input, context):
    context.metadata["user_id"] = "abc123"

# After: runs after successful call
async def after_hook(call_input, call_output, context):
    print(f"Response: {call_output.text}")

# Error: runs on failure
async def error_hook(call_input, error, context):
    print(f"Error: {error}")

# Finally: always runs with complete result
async def finally_hook(result):
    print(f"Took {result.elapsed_ms}ms")

# Register hooks
hookedllm.before(before_hook)
hookedllm.after(after_hook)
hookedllm.error(error_hook)
hookedllm.finally_(finally_hook)
```

## Conditional Hooks

Run hooks only when conditions match:

```python
# Only for GPT-4
hookedllm.after(
    expensive_eval,
    when=hookedllm.when.model("gpt-4")
)

# Only for tagged calls
hookedllm.after(
    logger_hook,
    when=hookedllm.when.tag("monitoring")
)

# Complex rules
hookedllm.after(
    my_hook,
    when=(
        hookedllm.when.model("gpt-4") &
        hookedllm.when.tag("monitoring") &
        ~hookedllm.when.tag("test")
    )
)
```

## Next Steps

- Learn about [Scopes](scopes.md) for isolating hooks
- Explore [Hook Types](hooks.md) in detail
- See [Complete Examples](examples/basic-usage.md) for full working examples
- Check out [Advanced Setup Guide](advanced-setup.md) for complete setup with logging, error handling, and metrics
- Read [Advanced Guides](guides/dependency-injection.md) for testing and customization

