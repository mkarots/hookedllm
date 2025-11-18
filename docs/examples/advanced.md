# Advanced Examples

This example demonstrates advanced HookedLLM patterns including evaluation, metrics, and custom error handling.

## Evaluation Hook

```python
import hookedllm
from openai import AsyncOpenAI

async def evaluate_response(call_input, call_output, context):
    """Evaluate LLM responses for quality."""
    # Build evaluation prompt
    eval_prompt = f"""
    Evaluate this response for clarity and accuracy:
    
    Query: {call_input.messages[-1].content}
    Response: {call_output.text}
    
    Return JSON: {{"clarity": 0-1, "accuracy": 0-1}}
    """
    
    # Use separate evaluator client (no hooks to avoid recursion)
    evaluator = AsyncOpenAI()
    eval_result = await evaluator.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": eval_prompt}]
    )
    
    # Store evaluation in metadata
    context.metadata["evaluation"] = eval_result.choices[0].message.content

# Register to evaluation scope
hookedllm.scope("evaluation").after(evaluate_response)

# Use with evaluation scope
eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
```

## Metrics Collection

```python
import hookedllm
from collections import defaultdict

metrics = defaultdict(int)

async def track_metrics(result):
    """Track aggregated metrics."""
    metrics["calls"] += 1
    
    if result.error:
        metrics["errors"] += 1
    
    if result.output and result.output.usage:
        metrics["tokens"] += result.output.usage.get("total_tokens", 0)
        metrics["prompt_tokens"] += result.output.usage.get("prompt_tokens", 0)
        metrics["completion_tokens"] += result.output.usage.get("completion_tokens", 0)
    
    metrics["total_time_ms"] += result.elapsed_ms

# Register globally
hookedllm.finally_(track_metrics)

# Metrics accumulate across all calls
```

## Tags and Metadata

```python
import hookedllm
from openai import AsyncOpenAI

# Hook that uses tags
async def logger_hook(call_input, call_output, context):
    if "monitoring" in context.tags:
        logger.info(f"Monitored call: {context.call_id}")

hookedllm.after(logger_hook)

# Use tags in calls
client = hookedllm.wrap(AsyncOpenAI())

response = await client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_body={
        "hookedllm_tags": ["monitoring", "critical"],
        "hookedllm_metadata": {
            "user_id": "abc123",
            "user_tier": "premium"
        }
    }
)
```

## Custom Error Handling

```python
import hookedllm
from openai import AsyncOpenAI, RateLimitError

def my_error_handler(error, context):
    """Custom handling for hook errors."""
    logger.error(f"Hook failed in {context}: {error}")

# Create custom executor with error handler
from hookedllm.core import DefaultHookExecutor

executor = DefaultHookExecutor(
    error_handler=my_error_handler,
    logger=my_logger
)

# Create context with custom executor
ctx = hookedllm.create_context(executor=executor)
client = ctx.wrap(AsyncOpenAI())
```

## Conditional Evaluation

```python
import hookedllm

# Only evaluate expensive models
hookedllm.scope("evaluation").after(
    expensive_evaluation,
    when=hookedllm.when.model("gpt-4")
)

# Quick evaluation for cheaper models
hookedllm.scope("evaluation").after(
    quick_evaluation,
    when=hookedllm.when.model("gpt-4o-mini")
)

# Only evaluate for tagged calls
hookedllm.scope("evaluation").after(
    evaluation_hook,
    when=hookedllm.when.tag("monitoring")
)
```

## Complete Example

```python
import asyncio
import hookedllm
from openai import AsyncOpenAI
from collections import defaultdict

# Metrics tracking
metrics = defaultdict(int)

async def track_metrics(result):
    metrics["calls"] += 1
    if result.output and result.output.usage:
        metrics["tokens"] += result.output.usage.get("total_tokens", 0)

async def evaluate_response(call_input, call_output, context):
    # Evaluation logic here
    context.metadata["eval_score"] = 0.9

# Register hooks
hookedllm.finally_(track_metrics)
hookedllm.scope("evaluation").after(evaluate_response)

# Create client
client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")

# Use client
async def main():
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(f"Response: {response.choices[0].message.content}")
    print(f"Metrics: {dict(metrics)}")

asyncio.run(main())
```

## Next Steps

- Learn about [Dependency Injection](../guides/dependency-injection.md) for testing
- See [Testing Guide](../guides/testing.md) for test patterns
- Check out [Architecture](../guides/architecture.md) for design details

