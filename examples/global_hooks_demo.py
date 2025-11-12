"""
Global Hooks Demo - Framework Data

Shows what data the framework provides to hooks.

To run:
  pip install hookedllm[openai]
  export OPENAI_API_KEY=your-key
  python examples/global_hooks_demo.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm


async def before_hook(call_input, context):
    """Before hook - shows input data."""
    print(f"\n🔵 BEFORE:")
    print(f"   Model: {call_input.model}")
    print(f"   Messages: {len(call_input.messages)}")
    print(f"   Call ID: {context.call_id[:8]}...")


async def after_hook(call_input, call_output, context):
    """After hook - shows output data."""
    print(f"🟢 AFTER:")
    print(f"   Response: {len(call_output.text or '')} chars")
    print(f"   Tokens: {call_output.usage.get('total_tokens', 0) if call_output.usage else 0}")


async def finally_hook(result):
    """Finally hook - shows complete result."""
    print(f"⚪ FINALLY:")
    print(f"   Latency: {result.elapsed_ms:.0f}ms")
    print(f"   Success: {result.error is None}")


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("Global Hooks Demo\n" + "=" * 50)
    
    # Register global hooks
    hookedllm.before(before_hook)
    hookedllm.after(after_hook)
    hookedllm.finally_(finally_hook)
    
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key))
    
    # Make 3 calls
    for i in range(1, 4):
        print(f"\n{'='*50}\nCall {i}:")
        await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Say hello {i}"}],
            max_tokens=10
        )
    
    print("\n" + "=" * 50)
    print("✓ All hooks ran for every call")
    print("✓ Framework provides: input, output, context, result")


if __name__ == "__main__":
    asyncio.run(main())