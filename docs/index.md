# HookedLLM

**Async-first, scoped hook system for LLM observability with SOLID/DI architecture**

HookedLLM provides transparent observability for LLM calls through a powerful hook system. Add evaluation, logging, metrics, and custom behaviors to your LLM applications without modifying core application logic.

## Key Features

- **Config or Code**: Define hooks programmatically or via YAML
- **Scoped Isolation**: Named scopes prevent hook interference across application contexts
- **Conditional Execution**: Run hooks only when rules match (model, tags, metadata)
- **Async-First**: Built for modern async LLM SDKs
- **Resilient**: Hook failures never break your LLM calls
- **Type-Safe**: Full type hints and IDE autocomplete support

## Quick Example

```python
import hookedllm
from openai import AsyncOpenAI

# Define a simple hook
async def log_usage(call_input, call_output, context):
    print(f"Model: {call_input.model}")
    print(f"Tokens: {call_output.usage.get('total_tokens', 0)}")

# Register hook to a scope
hookedllm.scope("evaluation").after(log_usage)

# Wrap your client with the scope
client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")

# Use normally - hooks execute automatically!
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Installation

```bash
# Core package (zero dependencies)
pip install hookedllm

# With OpenAI support
pip install hookedllm[openai]

# With all optional dependencies
pip install hookedllm[all]
```

## What's Next?

- [Quick Start Guide](quick-start.md) - Get up and running in minutes
- [Advanced Setup Guide](advanced-setup.md) - Complete setup with logging, error handling, and metrics
- [Core Concepts](scopes.md) - Understand scopes, hooks, and rules
- [Examples](examples/basic-usage.md) - See real-world usage patterns
- [Advanced Guides](guides/performance.md) - Performance, observability, and more
- [API Reference](api/index.md) - Complete API documentation
- [Architecture Guide](guides/architecture.md) - Deep dive into design

## License

MIT License - see [LICENSE](https://github.com/CepstrumLabs/hookedllm/blob/main/LICENSE) file for details.

