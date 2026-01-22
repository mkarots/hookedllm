# Scopes

Scopes are named isolation boundaries for hooks. They prevent hook interference across different parts of your application.

## Why Scopes?

Imagine you have two parts of your application:

1. **Evaluation**: Runs expensive evaluation hooks on every call
2. **Default**: Runs lightweight logging hooks

Without scopes, evaluation hooks would run on default calls (wasteful) and default hooks would run on evaluation calls (noisy). Scopes solve this by isolating hooks to specific contexts.

## Basic Usage

```python
import hookedllm

# Register hooks to different scopes
hookedllm.scope("evaluation").after(evaluate_response)
hookedllm.scope("evaluation").after(calculate_metrics)

hookedllm.scope("default").after(default_logger)
hookedllm.scope("default").error(alert_on_error)

# Create clients with specific scopes
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
default_client = hookedllm.wrap(AsyncOpenAI(), scope="default")

# Each client only runs hooks from its scope
# eval_client runs: evaluate_response + calculate_metrics
# default_client runs: default_logger + alert_on_error
```

## Multiple Scopes

A client can use multiple scopes:

```python
hookedllm.scope("logging").finally_(log_call)
hookedllm.scope("metrics").finally_(track_metrics)
hookedllm.scope("evaluation").after(evaluate)

# Client with all three scopes
client = hookedllm.wrap(
    AsyncOpenAI(),
    scope=["logging", "metrics", "evaluation"]
)

# Runs hooks from all three scopes:
# log_call + track_metrics + evaluate
```

## Global vs Scoped Hooks

Global hooks run for **all** clients, regardless of scope:

```python
# Global hook - runs for ALL clients
hookedllm.finally_(track_all_metrics)

# Scoped hooks - only for specific clients
hookedllm.scope("evaluation").after(evaluate)
hookedllm.scope("default").error(alert)

# Evaluation client gets: track_all_metrics + evaluate
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")

# Default client gets: track_all_metrics + alert
default_client = hookedllm.wrap(AsyncOpenAI(), scope="default")
```

## Scope Best Practices

1. **Use descriptive names**: `"evaluation"`, `"default"`, `"testing"` are better than `"scope1"`, `"scope2"`

2. **Keep scopes focused**: Each scope should have a clear purpose

3. **Combine scopes when needed**: Use multiple scopes for cross-cutting concerns

4. **Use global hooks sparingly**: Only for hooks that truly need to run everywhere

## Examples

See [Scopes Examples](examples/scopes.md) for real-world scope usage patterns.

