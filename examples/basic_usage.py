"""
Basic Usage - Core Concepts

Shows hooks, scopes, and conditional rules.

To run:
  pip install hookedllm[openai]
  export OPENAI_API_KEY=your-key
  python examples/basic_usage.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm


async def log_hook(call_input, call_output, context):
    """Log every call."""
    tokens = call_output.usage.get('total_tokens', 0) if call_output.usage else 0
    print(f"📝 {call_input.model}: {tokens} tokens")


async def gpt4_only_hook(call_input, call_output, context):
    """Only runs for GPT-4."""
    print(f"🎯 GPT-4 special handling")


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("Basic Usage\n" + "=" * 50)
    
    # Global hook (runs for all calls)
    hookedllm.after(log_hook)
    
    # Conditional hook (only for GPT-4)
    hookedllm.after(gpt4_only_hook, when=hookedllm.when.model("gpt-4"))
    
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key))
    
    # Call 1: GPT-4 mini (log_hook runs)
    print("\n1. GPT-4 mini:")
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    
    # Call 2: GPT-4 (both hooks run)
    print("\n2. GPT-4:")
    await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    
    print("\n" + "=" * 50)
    print("✓ Global hook ran for both")
    print("✓ Conditional hook ran only for GPT-4")


if __name__ == "__main__":
    asyncio.run(main())