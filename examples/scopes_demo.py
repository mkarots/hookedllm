"""
Scopes Demo - Preventing Hook Interference

Shows how scopes isolate hooks to prevent interference.

To run:
  pip install hookedllm[openai]
  export OPENAI_API_KEY=your-key
  python examples/scopes_demo.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm


# Simple hooks for different scopes
async def dev_hook(call_input, call_output, context):
    """Development: verbose logging."""
    print(f"🔧 [DEV] {call_input.model} → {len(call_output.text or '')} chars")


async def prod_hook(call_input, call_output, context):
    """Production: minimal logging."""
    tokens = call_output.usage.get('total_tokens', 0) if call_output.usage else 0
    print(f"📊 [PROD] {tokens} tokens")


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("Scopes Demo\n" + "=" * 50)
    
    # Register hooks to different scopes
    hookedllm.scope("dev").after(dev_hook)
    hookedllm.scope("prod").after(prod_hook)
    
    # Create clients with different scopes
    dev_client = hookedllm.wrap(AsyncOpenAI(api_key=api_key), scope="dev")
    prod_client = hookedllm.wrap(AsyncOpenAI(api_key=api_key), scope="prod")
    
    # Dev client - only dev hooks run
    print("\n1. Dev client (verbose):")
    await dev_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    
    # Prod client - only prod hooks run
    print("\n2. Prod client (minimal):")
    await prod_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    
    print("\n" + "=" * 50)
    print("✓ Each client ran only its scope's hooks")
    print("✓ No interference between dev and prod!")


if __name__ == "__main__":
    asyncio.run(main())