"""
Simple working demo of hookedllm with metrics and evaluation.

This script demonstrates:
1. Making an actual LLM call
2. Tracking metrics automatically
3. Evaluating responses automatically

To run this script:
1. Install dependencies: pip install -e .[openai]
2. Set your API key: export OPENAI_API_KEY=your-key-here
3. Run: python examples/simple_demo.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm
from hookedllm.hooks import MetricsHook, EvaluationHook


async def main():
    """
    Simple demo showing metrics tracking and evaluation.
    """
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=sk-...")
        return
    
    print("=" * 70)
    print("HookedLLM Demo: Metrics + Evaluation")
    print("=" * 70)
    
    # ========================================
    # Step 1: Setup metrics tracking
    # ========================================
    print("\nStep 1: Setting up metrics tracking")
    print("-" * 70)
    
    metrics = MetricsHook()
    hookedllm.finally_(metrics)
    
    print("✓ Metrics hook registered (tracks all calls globally)")
    
    # ========================================
    # Step 2: Setup evaluation
    # ========================================
    print("\nStep 2: Setting up automatic evaluation")
    print("-" * 70)
    
    # Create a separate client for evaluation calls
    evaluator = AsyncOpenAI(api_key=api_key)
    
    # Define evaluation criteria
    criteria = {
        "clarity": "Is the response clear and easy to understand?",
        "relevance": "Does the response directly answer the question?",
        "helpfulness": "Is the response helpful and actionable?"
    }
    
    eval_hook = EvaluationHook(evaluator, criteria, model="gpt-4o-mini")
    hookedllm.scope("demo").after(eval_hook)
    
    print("✓ Evaluation hook registered to 'demo' scope")
    print(f"✓ Criteria: {', '.join(criteria.keys())}")
    
    # ========================================
    # Step 3: Create wrapped client
    # ========================================
    print("\nStep 3: Creating hooked LLM client")
    print("-" * 70)
    
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key), scope="demo")
    
    print("✓ Client wrapped with metrics + evaluation")
    
    # ========================================
    # Step 4: Make LLM call
    # ========================================
    print("\nStep 4: Making LLM call")
    print("-" * 70)
    
    question = "What are three best practices for writing Python code?"
    
    print(f"Question: {question}")
    print("\nCalling gpt-4o-mini...")
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful Python programming assistant."},
            {"role": "user", "content": question}
        ],
        temperature=0.7
    )
    
    answer = response.choices[0].message.content
    
    print(f"\nResponse:\n{answer}")
    
    # ========================================
    # Step 5: Check metrics
    # ========================================
    print("\n" + "=" * 70)
    print("Step 5: Metrics Summary")
    print("=" * 70)
    
    summary = metrics.summary()
    
    print(f"\nTotal Calls:       {summary['total_calls']}")
    print(f"Successful Calls:  {summary['successful_calls']}")
    print(f"Failed Calls:      {summary['failed_calls']}")
    print(f"Success Rate:      {summary['success_rate']:.1%}")
    print(f"Total Tokens:      {summary['total_tokens']}")
    print(f"Prompt Tokens:     {summary['prompt_tokens']}")
    print(f"Completion Tokens: {summary['completion_tokens']}")
    print(f"Avg Latency:       {summary['average_latency_ms']:.2f}ms")
    
    # ========================================
    # Step 6: Make another call to see metrics update
    # ========================================
    print("\n" + "=" * 70)
    print("Step 6: Making a second call")
    print("=" * 70)
    
    question2 = "Explain list comprehensions in Python in one sentence."
    print(f"\nQuestion: {question2}")
    print("\nCalling gpt-4o-mini...")
    
    response2 = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": question2}
        ],
        temperature=0.5
    )
    
    answer2 = response2.choices[0].message.content
    print(f"\nResponse:\n{answer2}")
    
    # ========================================
    # Step 7: Updated metrics
    # ========================================
    print("\n" + "=" * 70)
    print("Step 7: Updated Metrics")
    print("=" * 70)
    
    summary = metrics.summary()
    
    print(f"\nTotal Calls:       {summary['total_calls']}")
    print(f"Total Tokens:      {summary['total_tokens']}")
    print(f"Avg Latency:       {summary['average_latency_ms']:.2f}ms")
    
    # ========================================
    # Done!
    # ========================================
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    
    print("\nWhat happened:")
    print("1. ✓ Both LLM calls were made normally")
    print("2. ✓ Metrics were tracked automatically")
    print("3. ✓ Each response was evaluated for clarity, relevance, helpfulness")
    print("4. ✓ Evaluation results stored in call context metadata")
    print("5. ✓ All hooks ran without any changes to your LLM call code!")
    
    print("\nKey insight:")
    print("You added observability without modifying a single line of your")
    print("existing LLM call code - just wrapped the client and registered hooks!")


if __name__ == "__main__":
    asyncio.run(main())