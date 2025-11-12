"""
Simple Demo - Your First HookedLLM Program

Shows basic usage with metrics tracking.

To run:
  pip install hookedllm[openai]
  export OPENAI_API_KEY=your-key
  python examples/simple_demo.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm
from hookedllm.hooks import MetricsHook


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("Simple Demo\n" + "=" * 50)
    
    # Setup metrics tracking
    metrics = MetricsHook()
    hookedllm.finally_(metrics)
    print("✓ Metrics tracking enabled")
    
    # Wrap client
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key))
    
    # Make LLM call
    print("\nMaking LLM call...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is Python?"}],
        max_tokens=50
    )
    
    print(f"\nResponse: {response.choices[0].message.content}")
    
    # Show metrics
    summary = metrics.summary()
    print(f"\nMetrics:")
    print(f"  Calls: {summary['total_calls']}")
    print(f"  Tokens: {summary['total_tokens']}")
    print(f"  Latency: {summary['average_latency_ms']:.0f}ms")
    
    print("\n" + "=" * 50)
    print("✓ Metrics tracked automatically!")


if __name__ == "__main__":
    asyncio.run(main())