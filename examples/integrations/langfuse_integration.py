"""
Example: Langfuse Integration with hookedllm

This example shows how to integrate hookedllm with Langfuse for LLM observability.

Langfuse provides:
- Trace visualization
- Generation tracking
- Cost analysis
- Quality scoring
- User feedback

To run:
1. pip install hookedllm langfuse openai
2. Set environment variables:
   export OPENAI_API_KEY=your-key
   export LANGFUSE_PUBLIC_KEY=pk-...
   export LANGFUSE_SECRET_KEY=sk-...
3. python examples/integrations/langfuse_integration.py
"""

import asyncio
import os
from openai import AsyncOpenAI
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

# Import hookedllm (assuming it's installed or in path)
import sys
sys.path.insert(0, '../../src')
import hookedllm


# ============================================================
# Langfuse Integration Hooks
# ============================================================

class LangfuseHooks:
    """
    Integration hooks for Langfuse observability platform.
    
    Automatically tracks all LLM calls in Langfuse with:
    - Traces (request flows)
    - Generations (LLM calls)
    - Scores (quality metrics)
    - Usage tracking (tokens, cost)
    """
    
    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com"
    ):
        """Initialize Langfuse client."""
        self.client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        self._generations = {}  # Map call_id to generation
    
    async def before_hook(self, call_input, context):
        """
        Create Langfuse generation before LLM call.
        
        This captures:
        - Model name
        - Input messages
        - Parameters (temperature, max_tokens, etc.)
        - Metadata (tags, user info, etc.)
        """
        # Create generation
        generation = self.client.generation(
            name=f"{call_input.model}",
            model=call_input.model,
            input=[
                {"role": m.role, "content": m.content}
                for m in call_input.messages
            ],
            metadata={
                "provider": context.provider,
                "tags": context.tags,
                "call_id": context.call_id,
                **context.metadata,
                **call_input.params
            }
        )
        
        # Store for later
        self._generations[context.call_id] = generation
        
        print(f"📊 [Langfuse] Started tracking generation: {context.call_id[:8]}...")
    
    async def after_hook(self, call_input, call_output, context):
        """
        Update Langfuse generation with output and usage.
        
        This captures:
        - Response text
        - Token usage
        - Finish reason
        - Latency (added in finally hook)
        """
        if context.call_id in self._generations:
            generation = self._generations[context.call_id]
            
            # Update with output
            generation.update(
                output=call_output.text,
                usage={
                    "input": call_output.usage.get("prompt_tokens", 0) if call_output.usage else 0,
                    "output": call_output.usage.get("completion_tokens", 0) if call_output.usage else 0,
                    "total": call_output.usage.get("total_tokens", 0) if call_output.usage else 0,
                    "unit": "TOKENS"
                } if call_output.usage else None,
                metadata={
                    "finish_reason": call_output.finish_reason
                }
            )
            
            print(f"✅ [Langfuse] Updated generation with output")
    
    async def error_hook(self, call_input, error, context):
        """
        Mark generation as failed in Langfuse.
        
        This captures:
        - Error type
        - Error message
        - Stack trace (optional)
        """
        if context.call_id in self._generations:
            generation = self._generations[context.call_id]
            
            generation.update(
                level="ERROR",
                status_message=f"{type(error).__name__}: {str(error)}",
                metadata={
                    "error_type": type(error).__name__,
                    "error_message": str(error)
                }
            )
            
            print(f"❌ [Langfuse] Marked generation as failed: {error}")
    
    async def finally_hook(self, result):
        """
        Finalize generation and flush to Langfuse.
        
        This captures:
        - Total latency
        - Final status
        """
        if result.context.call_id in self._generations:
            generation = self._generations[result.context.call_id]
            
            # Add latency
            generation.update(
                metadata={
                    "latency_ms": result.elapsed_ms
                }
            )
            
            # End generation
            generation.end()
            
            # Clean up
            del self._generations[result.context.call_id]
            
            print(f"🏁 [Langfuse] Finalized generation ({result.elapsed_ms:.0f}ms)")
        
        # Flush to Langfuse
        self.client.flush()
    
    def register(self, scope: str = "langfuse"):
        """Register all hooks with hookedllm."""
        hookedllm.scope(scope).before(self.before_hook)
        hookedllm.scope(scope).after(self.after_hook)
        hookedllm.scope(scope).error(self.error_hook)
        hookedllm.scope(scope).finally_(self.finally_hook)
        print(f"✓ Langfuse hooks registered to scope '{scope}'")


# ============================================================
# Example Usage
# ============================================================

async def main():
    """Demonstrate Langfuse integration."""
    
    # Get API keys from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    
    if not all([openai_key, langfuse_public, langfuse_secret]):
        print("ERROR: Set OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, and LANGFUSE_SECRET_KEY")
        return
    
    print("=" * 80)
    print("Langfuse Integration Example")
    print("=" * 80)
    
    # Setup Langfuse integration
    print("\n📌 Setting up Langfuse integration...")
    langfuse = LangfuseHooks(
        public_key=langfuse_public,
        secret_key=langfuse_secret
    )
    langfuse.register()
    
    # Create wrapped OpenAI client
    print("\n📌 Creating wrapped OpenAI client...")
    client = hookedllm.wrap(
        AsyncOpenAI(api_key=openai_key),
        scope="langfuse"
    )
    
    # Example 1: Simple chat completion
    print("\n" + "=" * 80)
    print("Example 1: Simple Chat Completion")
    print("=" * 80)
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        max_tokens=50
    )
    
    print(f"\n💬 Response: {response.choices[0].message.content}")
    print(f"📊 Tokens: {response.usage.total_tokens}")
    
    # Example 2: Chat with metadata
    print("\n" + "=" * 80)
    print("Example 2: Chat with Metadata (User Tracking)")
    print("=" * 80)
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Explain quantum computing in one sentence."}
        ],
        max_tokens=100,
        extra_body={
            "hookedllm_tags": ["quantum", "education"],
            "hookedllm_metadata": {
                "user_id": "user-123",
                "session_id": "session-456",
                "feature": "chat"
            }
        }
    )
    
    print(f"\n💬 Response: {response.choices[0].message.content}")
    
    # Example 3: Error handling
    print("\n" + "=" * 80)
    print("Example 3: Error Handling (Invalid Model)")
    print("=" * 80)
    
    try:
        response = await client.chat.completions.create(
            model="invalid-model-name",
            messages=[{"role": "user", "content": "This will fail"}]
        )
    except Exception as e:
        print(f"\n❌ Expected error: {type(e).__name__}: {str(e)[:100]}")
        print("✓ Error was tracked in Langfuse")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("""
✨ All LLM calls are now tracked in Langfuse!

Visit your Langfuse dashboard to see:
- 📊 Traces: Complete request flows
- 🤖 Generations: Individual LLM calls
- 💰 Costs: Token usage and pricing
- ⏱️  Latency: Response times
- 🏷️  Metadata: Tags, user IDs, sessions
- ❌ Errors: Failed calls with details

Next steps:
1. Add quality scores using Langfuse SDK
2. Collect user feedback
3. Analyze patterns and optimize
4. Set up alerts for errors/costs
    """)


if __name__ == "__main__":
    asyncio.run(main())