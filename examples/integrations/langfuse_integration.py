"""
Langfuse Integration - LLM Observability

Automatically track LLM calls in Langfuse.

To run:
  pip install hookedllm[openai] langfuse
  export OPENAI_API_KEY=your-key
  export LANGFUSE_PUBLIC_KEY=pk-...
  export LANGFUSE_SECRET_KEY=sk-...
  python examples/integrations/langfuse_integration.py
"""

import asyncio
import os
from openai import AsyncOpenAI
from langfuse import Langfuse
import hookedllm


class LangfuseHooks:
    """Simple Langfuse integration."""
    
    def __init__(self, public_key: str, secret_key: str):
        self.client = Langfuse(public_key=public_key, secret_key=secret_key)
        self._generations = {}
    
    async def before_hook(self, call_input, context):
        """Create Langfuse generation."""
        generation = self.client.generation(
            name=call_input.model,
            model=call_input.model,
            input=[{"role": m.role, "content": m.content} for m in call_input.messages]
        )
        self._generations[context.call_id] = generation
        print(f"📊 Langfuse: Started tracking {context.call_id[:8]}...")
    
    async def after_hook(self, call_input, call_output, context):
        """Update with output."""
        if context.call_id in self._generations:
            generation = self._generations[context.call_id]
            generation.update(
                output=call_output.text,
                usage=call_output.usage
            )
            generation.end()
            del self._generations[context.call_id]
            print(f"✅ Langfuse: Tracked successfully")
        
        self.client.flush()


async def main():
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    
    if not all([openai_key, langfuse_public, langfuse_secret]):
        print("ERROR: Set OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY")
        return
    
    print("Langfuse Integration\n" + "=" * 50)
    
    # Setup Langfuse hooks
    langfuse = LangfuseHooks(langfuse_public, langfuse_secret)
    hookedllm.scope("langfuse").before(langfuse.before_hook)
    hookedllm.scope("langfuse").after(langfuse.after_hook)
    
    # Create client
    client = hookedllm.wrap(AsyncOpenAI(api_key=openai_key), scope="langfuse")
    
    # Make call
    print("\nMaking LLM call...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is Python?"}],
        max_tokens=50
    )
    
    print(f"\nResponse: {response.choices[0].message.content}")
    
    print("\n" + "=" * 50)
    print("✓ Call tracked in Langfuse dashboard")
    print("✓ Visit https://cloud.langfuse.com to see traces")


if __name__ == "__main__":
    asyncio.run(main())