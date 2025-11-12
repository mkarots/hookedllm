"""
PostHog Integration - Product Analytics for LLM Apps

Track LLM usage, costs, and user behavior in PostHog.

To run:
  pip install hookedllm[openai] posthog
  export OPENAI_API_KEY=your-key
  export POSTHOG_API_KEY=your-posthog-key
  python examples/integrations/posthog_integration.py
"""

import asyncio
import os
from openai import AsyncOpenAI
from posthog import Posthog
import hookedllm


class PostHogHooks:
    """PostHog integration for LLM analytics."""
    
    def __init__(self, api_key: str, host: str = "https://app.posthog.com"):
        self.posthog = Posthog(api_key, host=host)
    
    async def after_hook(self, call_input, call_output, context):
        """Track LLM call as PostHog event."""
        # Calculate cost (example pricing)
        tokens = call_output.usage.get("total_tokens", 0) if call_output.usage else 0
        cost_per_1k = 0.0001  # Example: $0.0001 per 1k tokens
        estimated_cost = (tokens / 1000) * cost_per_1k
        
        # Track event
        self.posthog.capture(
            distinct_id=context.metadata.get("user_id", "anonymous"),
            event="llm_call_completed",
            properties={
                # Model info
                "model": call_input.model,
                "provider": context.provider,
                
                # Usage
                "tokens_total": tokens,
                "tokens_prompt": call_output.usage.get("prompt_tokens", 0) if call_output.usage else 0,
                "tokens_completion": call_output.usage.get("completion_tokens", 0) if call_output.usage else 0,
                
                # Cost
                "estimated_cost_usd": estimated_cost,
                
                # Performance
                "latency_ms": context.metadata.get("latency_ms", 0),
                "finish_reason": call_output.finish_reason,
                
                # Context
                "tags": context.tags,
                "session_id": context.metadata.get("session_id"),
                "feature": context.metadata.get("feature"),
                
                # Response quality
                "response_length": len(call_output.text) if call_output.text else 0,
            }
        )
        
        print(f"📊 PostHog: Tracked LLM call ({tokens} tokens, ${estimated_cost:.6f})")
    
    async def error_hook(self, call_input, error, context):
        """Track LLM errors."""
        self.posthog.capture(
            distinct_id=context.metadata.get("user_id", "anonymous"),
            event="llm_call_failed",
            properties={
                "model": call_input.model,
                "provider": context.provider,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "tags": context.tags,
            }
        )
        
        print(f"❌ PostHog: Tracked LLM error")
    
    async def finally_hook(self, result):
        """Track session metrics."""
        # Track latency as separate metric
        self.posthog.capture(
            distinct_id=result.context.metadata.get("user_id", "anonymous"),
            event="llm_latency",
            properties={
                "latency_ms": result.elapsed_ms,
                "model": result.input.model,
                "success": result.error is None,
            }
        )
    
    def shutdown(self):
        """Flush events before exit."""
        self.posthog.flush()


async def main():
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    posthog_key = os.getenv("POSTHOG_API_KEY")
    
    if not all([openai_key, posthog_key]):
        print("ERROR: Set OPENAI_API_KEY and POSTHOG_API_KEY")
        return
    
    print("PostHog Integration\n" + "=" * 60)
    
    # Setup PostHog hooks
    posthog = PostHogHooks(posthog_key)
    hookedllm.scope("posthog").after(posthog.after_hook)
    hookedllm.scope("posthog").error(posthog.error_hook)
    hookedllm.scope("posthog").finally_(posthog.finally_hook)
    print("✓ PostHog hooks registered")
    
    # Create client
    client = hookedllm.wrap(AsyncOpenAI(api_key=openai_key), scope="posthog")
    
    # Make calls with user context
    print("\nMaking LLM calls with user tracking...")
    
    # Call 1: User query
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is Python?"}],
        max_tokens=50,
        extra_body={
            "hookedllm_tags": ["chat", "onboarding"],
            "hookedllm_metadata": {
                "user_id": "user_123",
                "session_id": "session_abc",
                "feature": "chat_assistant"
            }
        }
    )
    
    # Call 2: Different user
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Explain async/await"}],
        max_tokens=50,
        extra_body={
            "hookedllm_tags": ["chat", "technical"],
            "hookedllm_metadata": {
                "user_id": "user_456",
                "session_id": "session_xyz",
                "feature": "code_help"
            }
        }
    )
    
    # Flush events
    posthog.shutdown()
    
    print("\n" + "=" * 60)
    print("PostHog Events Tracked:")
    print("  ✓ llm_call_completed (with tokens, cost, latency)")
    print("  ✓ llm_latency (performance metrics)")
    print("  ✓ User attribution (user_id, session_id)")
    print("  ✓ Feature tracking (tags, feature names)")
    print("\nAnalyze in PostHog:")
    print("  • Token usage by user/feature")
    print("  • Cost per user/session")
    print("  • Latency trends")
    print("  • Error rates")
    print("  • Feature adoption")


if __name__ == "__main__":
    asyncio.run(main())