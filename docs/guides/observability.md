# Observability Guide

Integrating HookedLLM with monitoring, logging, and tracing tools.

## Structured Logging

Use structured logging instead of print statements:

```python
import logging

logger = logging.getLogger(__name__)

async def logger_hook(call_input, call_output, context):
    logger.info("llm_call_completed", extra={
        "call_id": context.call_id,
        "model": call_input.model,
        "tokens": call_output.usage.get("total_tokens", 0),
        "duration_ms": context.elapsed_ms,
    })

hookedllm.after(logger_hook)
```

## Metrics Collection

### Prometheus

```python
from prometheus_client import Counter, Histogram

llm_calls_total = Counter("llm_calls_total", "Total LLM calls", ["model"])
llm_call_duration = Histogram("llm_call_duration_seconds", "LLM call duration", ["model"])

async def metrics_hook(result):
    model = result.input.model
    llm_calls_total.labels(model=model).inc()
    if result.output:
        llm_call_duration.labels(model=model).observe(result.elapsed_ms / 1000.0)

hookedllm.finally_(metrics_hook)
```

## Distributed Tracing

### OpenTelemetry

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def tracing_hook(call_input, call_output, context):
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.model", call_input.model)
        span.set_attribute("llm.tokens", call_output.usage.get("total_tokens", 0))
        span.set_attribute("llm.duration_ms", context.elapsed_ms)

hookedllm.after(tracing_hook)
```

## Error Tracking

### Sentry

```python
import sentry_sdk

async def error_tracking_hook(call_input, error, context):
    sentry_sdk.capture_exception(
        error,
        contexts={
            "llm": {
                "call_id": context.call_id,
                "model": call_input.model,
            }
        }
    )

hookedllm.error(error_tracking_hook)
```

See [examples/advanced.md](../examples/advanced.md) and [advanced-setup.md](../advanced-setup.md) for complete examples.
