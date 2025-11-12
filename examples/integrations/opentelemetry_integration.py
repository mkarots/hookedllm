"""
OpenTelemetry Integration - Rich Distributed Tracing

Shows comprehensive span data capture for LLM calls.

To run:
  pip install hookedllm[openai] opentelemetry-api opentelemetry-sdk
  export OPENAI_API_KEY=your-key
  python examples/integrations/opentelemetry_integration.py
"""

import asyncio
import os
from openai import AsyncOpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode, SpanKind
import hookedllm


class RichOpenTelemetryHooks:
    """Comprehensive OpenTelemetry integration with rich span data."""
    
    def __init__(self):
        self.tracer = trace.get_tracer("hookedllm", "1.0.0")
        self._spans = {}
    
    async def before_hook(self, call_input, context):
        """Start span with comprehensive attributes."""
        span = self.tracer.start_span(
            name=f"llm.chat.{call_input.model}",
            kind=SpanKind.CLIENT,
            attributes={
                # LLM-specific attributes
                "llm.system": context.provider,
                "llm.request.model": call_input.model,
                "llm.request.temperature": call_input.params.get("temperature"),
                "llm.request.max_tokens": call_input.params.get("max_tokens"),
                "llm.request.top_p": call_input.params.get("top_p"),
                
                # Message metadata
                "llm.request.message_count": len(call_input.messages),
                "llm.request.first_message_role": call_input.messages[0].role if call_input.messages else None,
                
                # Context
                "llm.call_id": context.call_id,
                "llm.tags": ",".join(context.tags) if context.tags else "",
                
                # Custom metadata
                **{f"llm.metadata.{k}": str(v) for k, v in context.metadata.items()}
            }
        )
        
        # Add event for request start
        span.add_event(
            "llm.request.started",
            attributes={
                "model": call_input.model,
                "message_count": len(call_input.messages)
            }
        )
        
        self._spans[context.call_id] = span
        print(f"🔍 OTel: Started rich span for {call_input.model}")
    
    async def after_hook(self, call_input, call_output, context):
        """End span with comprehensive output data."""
        if context.call_id in self._spans:
            span = self._spans[context.call_id]
            
            # Add usage attributes
            if call_output.usage:
                span.set_attribute("llm.usage.prompt_tokens", 
                                 call_output.usage.get("prompt_tokens", 0))
                span.set_attribute("llm.usage.completion_tokens",
                                 call_output.usage.get("completion_tokens", 0))
                span.set_attribute("llm.usage.total_tokens",
                                 call_output.usage.get("total_tokens", 0))
            
            # Add response attributes
            span.set_attribute("llm.response.finish_reason", 
                             call_output.finish_reason or "unknown")
            
            if call_output.text:
                span.set_attribute("llm.response.length", len(call_output.text))
                # First 100 chars as sample
                span.set_attribute("llm.response.sample", call_output.text[:100])
            
            # Add event for successful response
            span.add_event(
                "llm.response.received",
                attributes={
                    "finish_reason": call_output.finish_reason or "unknown",
                    "total_tokens": call_output.usage.get("total_tokens", 0) if call_output.usage else 0
                }
            )
            
            # Set success status
            span.set_status(Status(StatusCode.OK, "LLM call completed successfully"))
            span.end()
            
            del self._spans[context.call_id]
            print(f"✅ OTel: Rich span completed with full metadata")
    
    async def error_hook(self, call_input, error, context):
        """Handle errors with detailed span data."""
        if context.call_id in self._spans:
            span = self._spans[context.call_id]
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(error)))
            
            # Record exception
            span.record_exception(error)
            
            # Add error event
            span.add_event(
                "llm.error",
                attributes={
                    "error.type": type(error).__name__,
                    "error.message": str(error)
                }
            )
            
            span.end()
            del self._spans[context.call_id]
            print(f"❌ OTel: Error span recorded")
    
    async def finally_hook(self, result):
        """Add final timing data."""
        # Note: Span already ended in after/error hooks
        # This is just for demonstration of finally hook
        print(f"⏱️  OTel: Call took {result.elapsed_ms:.0f}ms")


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("OpenTelemetry Rich Integration\n" + "=" * 60)
    
    # Setup OpenTelemetry
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    print("✓ OpenTelemetry configured with console exporter")
    
    # Setup comprehensive hooks
    otel = RichOpenTelemetryHooks()
    hookedllm.scope("otel").before(otel.before_hook)
    hookedllm.scope("otel").after(otel.after_hook)
    hookedllm.scope("otel").error(otel.error_hook)
    hookedllm.scope("otel").finally_(otel.finally_hook)
    print("✓ Rich OTel hooks registered")
    
    # Create client
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key), scope="otel")
    
    # Make call with metadata
    print("\nMaking LLM call with rich context...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain Python in one sentence."}
        ],
        temperature=0.7,
        max_tokens=50,
        extra_body={
            "hookedllm_tags": ["demo", "otel"],
            "hookedllm_metadata": {
                "user_id": "demo_user",
                "session_id": "session_123",
                "environment": "development"
            }
        }
    )
    
    print(f"\nResponse: {response.choices[0].message.content}")
    
    print("\n" + "=" * 60)
    print("Span Data Captured:")
    print("  ✓ Model, provider, parameters")
    print("  ✓ Token usage (prompt, completion, total)")
    print("  ✓ Response metadata (finish_reason, length, sample)")
    print("  ✓ Custom tags and metadata")
    print("  ✓ Events (request started, response received)")
    print("  ✓ Timing (latency)")
    print("  ✓ Status (success/error)")
    print("\nCheck console output above for full span details!")


if __name__ == "__main__":
    asyncio.run(main())
