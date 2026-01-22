# Advanced Setup Guide

Complete setup with logging, error handling, and metrics.

## Installation

```bash
pip install hookedllm[openai]
# Or: pip install hookedllm[all]
```

## Setup

### 1. Environment Configuration

```python
import os
from openai import AsyncOpenAI
import hookedllm

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = hookedllm.wrap(
    AsyncOpenAI(api_key=api_key),
    scope=os.getenv("HOOKEDLLM_SCOPE", "default")
)
```

### 2. Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

async def logger_hook(call_input, call_output, context):
    logger.info("llm_call_completed", extra={
        "call_id": context.call_id,
        "model": call_input.model,
        "tokens": call_output.usage.get("total_tokens", 0) if call_output.usage else 0,
        "duration_ms": context.elapsed_ms,
    })

hookedllm.scope("default").after(logger_hook)
```

### 3. Error Handling

```python
async def error_handler(call_input, error, context):
    logger.error("llm_call_failed", extra={
        "call_id": context.call_id,
        "model": call_input.model,
        "error_type": type(error).__name__,
    }, exc_info=True)

hookedllm.scope("default").error(error_handler)
```

### 4. Metrics

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

## Application Structure

```
your_app/
├── app/
│   ├── hooks/
│   │   ├── __init__.py      # Register hooks
│   │   ├── logging.py       # Logging hooks
│   │   └── metrics.py       # Metrics hooks
│   └── llm.py               # LLM client setup
└── main.py                  # Application entry point
```

## Environment Variables

- `OPENAI_API_KEY`: OpenAI API key (required)
- `HOOKEDLLM_SCOPE`: Default scope (default: "default")
- `LOG_LEVEL`: Logging level (default: "INFO")

See [examples/advanced.md](examples/advanced.md) for complete examples.
