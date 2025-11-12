"""
Evaluation and Metrics - Built-in Helpers

Shows MetricsHook and EvaluationHook usage.

To run:
  pip install hookedllm[openai]
  export OPENAI_API_KEY=your-key
  python examples/evaluation_and_metrics.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm
from hookedllm.hooks import MetricsHook, EvaluationHook


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY")
        return
    
    print("Evaluation & Metrics\n" + "=" * 50)
    
    # Setup metrics
    metrics = MetricsHook()
    hookedllm.finally_(metrics)
    print("✓ Metrics tracking enabled")
    
    # Setup evaluation
    evaluator = AsyncOpenAI(api_key=api_key)
    criteria = {
        "clarity": "Is the response clear?",
        "helpfulness": "Is it helpful?"
    }
    eval_hook = EvaluationHook(evaluator, criteria, model="gpt-4o-mini")
    hookedllm.scope("eval").after(eval_hook)
    print("✓ Evaluation enabled")
    
    # Create client
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key), scope="eval")
    
    # Make call
    print("\nMaking LLM call...")
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Explain Python in one sentence"}],
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
    print("✓ Response evaluated automatically")
    print("✓ Metrics tracked automatically")


if __name__ == "__main__":
    asyncio.run(main())