
"""
Example: OpenTelemetry Integration with hookedllm

This example shows how to integrate hookedllm with OpenTelemetry for distributed tracing.

OpenTelemetry provides:
- Distributed tracing across services
- Metrics collection
- Standard instrumentation
- Vendor-neutral observability

To run:
1. pip install hookedllm openai opentelemetry-api opentelemetry-sdk
2. export OPENAI_API_KEY=your-key
3. python examples/integrations/opentelemetry_integration.py
"""

import asyncio
import os
from openai import AsyncOpenAI

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

# Import hookedllm
import sys
sys.path.insert(0, '../../src')
import hookedllm


# ============================================================
# OpenTelemetry Integration Hooks
# ============================================================

class OpenTelemetryHooks:
    """
    Integration hooks for OpenTelemetry distributed tracing.
    
    Automatically creates spans for all LLM calls with:
    - Span names (llm.{model})
    - Attributes (model, tokens, latency)
    - Status (success/error)
    - Events (for important milestones)
    """
    
    def __init__(
        self,
        tracer_name: str = "hookedllm",
        service_name: str = "llm-service"
    ):
        """Initialize OpenTelemetry tracer."""
        self.tracer = trace.get_tracer(tracer_name)
        self.service_name = service_name
        self._spans = {}  # Map call_id to span
    
    async def before_hook(self, call_input, context):
        """
        Start OpenTelemetry span before LLM call.
        
        Creates a span with:
        - Name: llm.{model}
        - Attributes: model, provider, messages, parameters
        - Kind: CLIENT (outgoing request)
        """
        # Start span
        span = self.tracer.start_span(
            name=f"llm.{call_input.model}",
            kind=trace.SpanKind.CLIENT,
            attributes={
                # Standard OpenTelemetry semantic conventions
                "service.name": self.service_name,
                "llm.system": context.provider,
                "llm.request.model": call_input.model,
                "llm.request.temperature": call_input.params.get("temperature"),
                "llm.request.max_tokens": call_input.params.get("max_tokens"),
                "llm.request.top_p": call_input.params.get("top_p"),
                
                # Custom attributes
                "llm.call_id": context.call_id,
                "llm.tags": ",".join(context.tags) if context.tags else "",
                
                # Message count
                "llm.request.message_count": len(call_input.messages),
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
        
        # Store span
        self._spans[context.call_id] = span
        
        print(f"🔍 [OTel] Started span: llm.{call_input.model}")
    
    async def after_hook(self, call_input, call_output, context):
        """
        Update span with successful response.
        
        Adds:
        - Token usage attributes
        - Finish reason
        - Response metadata
        - Success status
        """
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
            
            # Add event for successful response
            span.add_event(
                "llm.response.received",
                attributes={
                    "finish_reason": call_output.finish_reason or "unknown",
                    "total_tokens": call_output.usage.get("total_tokens", 0) if call_output.usage else 0
                }
            )
            
            # Set success status
            span.set_status(Status(StatusCode.OK))
            
            print(f"✅ [OTel] Span successful: {call_output.usage.get('total_tokens', 0) if call_output.usage else 0} tokens")
    
    async def error_hook(self, call_input, error, context):
        """
        Mark span as failed.
        
        Adds:
        - Error status
        - Exception details
        - Error event
        """
        if context.call_id in self._spans:
            span = self._spans[context.call_id]
            
            # Set error status
            span.set_status(
                Status(StatusCode.ERROR, f"{type(error).__name__}: {str(error)}")
            )
            
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
            
            print(f"❌ [OTel] Span failed: {type(error).__name__}")
    
    async def finally_hook(self, result):
        """
        End span and add final attributes.
        
        Adds:
        - Total latency
        - Final status
        """
        if result.context.call_id in self._spans:
            span = self._spans[result.context.call_id]
            
            # Add latency
            span.set_attribute("llm.latency_ms", result.elapsed_ms)
            
            # Add event for completion
            span.add_event(
                "llm.call.completed",
                attributes={
                    "latency_ms": result.elapsed_ms,
                    "success": result.error is None
                }
            )
            
            # End span
            span.end()
            
            # Clean up
            del self._spans[result.context.call_id]
            
            print(f"🏁 [OTel] Span ended ({result.elapsed_ms:.0f}ms)")
    
    def register(self, scope: str = "opentelemetry"):
        """Register all hooks with hookedllm."""
        hookedllm.scope(scope).before(self.before_hook)
        hookedllm.scope(scope).after(self.after_hook)
        hookedllm.scope(scope).error(self.error_hook)
        hookedllm.scope(scope).finally_(self.finally_hook)
        print(f"✓ OpenTelemetry hooks registered to scope '{scope}'")


# ============================================================
# Example Usage
# ============================================================

async def main():
    """Demonstrate OpenTelemetry integration."""
    
    # Get API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        return
    
