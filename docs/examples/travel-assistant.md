# Travel Assistant Example

Minimal example: Adding logging, metrics, and evaluation to a travel assistant app.

## Application

```python
# app.py
from openai import AsyncOpenAI
import hookedllm
import os

# Setup client
client = hookedllm.wrap(
    AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")),
    scope="default"
)

async def travel_assistant(query: str) -> str:
    """Simple travel assistant that calls LLM."""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful travel assistant."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content
```

## Setup: Logging, Metrics, Evaluation

```python
# hooks.py
import logging
from prometheus_client import Counter, Histogram
import hookedllm

# Prometheus metrics
llm_calls_total = Counter("llm_calls_total", "Total LLM calls", ["model", "scope"])
llm_call_duration = Histogram("llm_call_duration_seconds", "LLM call duration", ["model"])
llm_tokens_total = Counter("llm_tokens_total", "Total tokens", ["model", "type"])

# Structured logging (for Loki)
logger = logging.getLogger(__name__)

# Logging hook
async def log_hook(call_input, call_output, context):
    logger.info("llm_call", extra={
        "call_id": context.call_id,
        "model": call_input.model,
        "tokens": call_output.usage.get("total_tokens", 0) if call_output.usage else 0,
        "duration_ms": context.elapsed_ms,
        "query": call_input.messages[-1]["content"][:100],  # First 100 chars
    })

# Metrics hook
async def metrics_hook(result):
    model = result.input.model
    llm_calls_total.labels(model=model, scope="default").inc()
    
    if result.output:
        llm_call_duration.labels(model=model).observe(result.elapsed_ms / 1000.0)
        if result.output.usage:
            llm_tokens_total.labels(model=model, type="prompt").inc(
                result.output.usage.get("prompt_tokens", 0)
            )
            llm_tokens_total.labels(model=model, type="completion").inc(
                result.output.usage.get("completion_tokens", 0)
            )

# Evaluation hook
async def eval_hook(call_input, call_output, context):
    """Evaluate response quality."""
    response_text = call_output.text.lower()
    
    # Simple checks
    has_location = any(word in response_text for word in ["hotel", "flight", "restaurant", "attraction"])
    has_action = any(word in response_text for word in ["book", "reserve", "find", "recommend"])
    
    # Store evaluation in metadata
    context.metadata["eval_score"] = 1.0 if (has_location and has_action) else 0.5
    context.metadata["eval_has_location"] = has_location
    context.metadata["eval_has_action"] = has_action
    
    logger.info("evaluation", extra={
        "call_id": context.call_id,
        "score": context.metadata["eval_score"],
        "has_location": has_location,
        "has_action": has_action,
    })

# Register hooks
hookedllm.scope("default").after(log_hook)
hookedllm.scope("default").after(eval_hook)
hookedllm.finally_(metrics_hook)
```

## Complete Setup

```python
# main.py
import logging
from prometheus_client import start_http_server
import asyncio
from app import travel_assistant

# Configure logging for Loki
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", %(extra)s}',
    handlers=[
        logging.StreamHandler(),  # Or use Loki handler
    ]
)

# Start Prometheus metrics server
start_http_server(8000)  # Metrics available at http://localhost:8000/metrics

# Import hooks to register them
import hooks

async def main():
    result = await travel_assistant("Find hotels in Paris")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Docker Compose (Optional)

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
  
  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
  
  app:
    build: .
    ports:
      - "8000:8000"  # Prometheus metrics
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

## Grafana Dashboards

**Metrics Dashboard** (Prometheus):
- `llm_calls_total` - Total calls over time
- `llm_call_duration_seconds` - P50, P95, P99 latencies
- `llm_tokens_total` - Token usage by type

**Logs Dashboard** (Loki):
- Query: `{job="travel-assistant"} |= "llm_call"`
- Filter by model, duration, tokens

**Evaluation Dashboard**:
- Query: `{job="travel-assistant"} |= "evaluation"`
- Track eval scores over time

## Usage

```bash
# Run app
python main.py

# View metrics
curl http://localhost:8000/metrics

# Query logs (Loki)
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="travel-assistant"}' \
  --data-urlencode 'start=1h'
```

This setup provides:
- ✅ **Logging**: All LLM calls logged to Loki
- ✅ **Metrics**: Prometheus metrics for monitoring
- ✅ **Evaluation**: Response quality checks
- ✅ **Observability**: Full visibility into LLM usage

