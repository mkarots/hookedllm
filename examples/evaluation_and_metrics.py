"""
Advanced example demonstrating evaluation and metrics hooks.

This shows how to use the built-in helper hooks for:
- Automatic response evaluation
- Metrics tracking
- Conditional hook execution
"""

import asyncio
import hookedllm
from hookedllm.hooks import MetricsHook, EvaluationHook


async def main():
    """
    Demonstrate evaluation and metrics tracking.
    
    Note: This is a conceptual example. In real usage, you'd need:
    - Actual OpenAI API keys
    - from openai import AsyncOpenAI
    """
    
    print("=" * 60)
    print("HookedLLM: Evaluation & Metrics Example")
    print("=" * 60)
    
    # ========================================
    # Setup: Metrics Tracking
    # ========================================
    print("\n1. Setting up metrics tracking")
    print("-" * 60)
    
    metrics = MetricsHook()
    hookedllm.finally_(metrics)
    
    print("✓ Metrics hook registered to track:")
    print("  - Total calls")
    print("  - Token usage")
    print("  - Success/error rates")
    print("  - Average latency")
    
    # ========================================
    # Setup: Evaluation (conceptual)
    # ========================================
    print("\n2. Setting up automatic evaluation")
    print("-" * 60)
    
    # In real usage:
    # from openai import AsyncOpenAI
    # evaluator = AsyncOpenAI(api_key="...")  # Separate client for eval
    # 
    # criteria = {
    #     "clarity": "Is the response clear and easy to understand?",
    #     "accuracy": "Is the response factually accurate?",
    #     "helpfulness": "Does the response help answer the question?"
    # }
    # 
    # eval_hook = EvaluationHook(evaluator, criteria)
    # hookedllm.scope("evaluation").after(eval_hook)
    
    print("✓ Evaluation hook would be registered with criteria:")
    print("  - clarity: Is the response clear?")
    print("  - accuracy: Is the response factually accurate?")
    print("  - helpfulness: Does it answer the question?")
    
    # ========================================
    # Setup: Conditional Evaluation
    # ========================================
    print("\n3. Conditional hook execution")
    print("-" * 60)
    
    # Only evaluate GPT-4 responses
    print("✓ Evaluation configured to run only for:")
    print("  - Model: gpt-4 (using hookedllm.when.model('gpt-4'))")
    print("  - Tag: production")
    
    # In real usage:
    # hookedllm.scope("evaluation").after(
    #     eval_hook,
    #     when=hookedllm.when.model("gpt-4") & hookedllm.when.tag("production")
    # )
    
    # ========================================
    # Simulated Usage
    # ========================================
    print("\n4. Example usage flow")
    print("-" * 60)
    
    print("\nIn real application:")
    print("```python")
    print("# Create evaluation client")
    print("eval_client = hookedllm.wrap(AsyncOpenAI(), scope='evaluation')")
    print("")
    print("# Make calls - automatic evaluation happens")
    print("response = await eval_client.chat.completions.create(")
    print("    model='gpt-4',")
    print("    messages=[{'role': 'user', 'content': 'Explain Python'}],")
    print("    extra_body={'hookedllm_tags': ['production']}")
    print(")")
    print("")
    print("# Evaluation results stored in response context")
    print("# Metrics automatically tracked")
    print("```")
    
    # ========================================
    # Metrics Summary
    # ========================================
    print("\n5. Metrics summary (after calls)")
    print("-" * 60)
    
    print("\nAccess metrics anytime:")
    print("```python")
    print("summary = metrics.summary()")
    print("print(f'Total calls: {summary[\"total_calls\"]}')")
    print("print(f'Success rate: {summary[\"success_rate\"]:.1%}')")
    print("print(f'Avg latency: {summary[\"average_latency_ms\"]:.2f}ms')")
    print("print(f'Total tokens: {summary[\"total_tokens\"]}')")
    print("```")
    
    # ========================================
    # Custom Evaluation Criteria
    # ========================================
    print("\n6. Custom evaluation criteria")
    print("-" * 60)
    
    print("\nYou can define any criteria you want:")
    print("```python")
    print("criteria = {")
    print("    'tone': 'Is the tone appropriate?',")
    print("    'conciseness': 'Is the response concise?',")
    print("    'code_quality': 'Is any code well-written?',")
    print("    'safety': 'Is the response safe and appropriate?'")
    print("}")
    print("```")
    
    # ========================================
    # Multiple Scopes
    # ========================================
    print("\n7. Using multiple scopes together")
    print("-" * 60)
    
    print("\nCombine evaluation + production monitoring:")
    print("```python")
    print("# Evaluation scope")
    print("hookedllm.scope('evaluation').after(eval_hook)")
    print("")
    print("# Production monitoring scope")
    print("hookedllm.scope('production').error(alert_on_error)")
    print("hookedllm.scope('production').finally_(log_to_datadog)")
    print("")
    print("# Client with both scopes")
    print("client = hookedllm.wrap(")
    print("    AsyncOpenAI(),")
    print("    scope=['evaluation', 'production']")
    print(")")
    print("```")
    
    # ========================================
    # Complete Example
    # ========================================
    print("\n8. Complete working example")
    print("-" * 60)
    
    print("""
```python
import hookedllm
from openai import AsyncOpenAI
from hookedllm.hooks import MetricsHook, EvaluationHook

# Setup metrics
metrics = MetricsHook()
hookedllm.finally_(metrics)

# Setup evaluation
evaluator = AsyncOpenAI()  # Separate client
criteria = {
    "clarity": "Is the response clear?",
    "accuracy": "Is it factually correct?"
}
eval_hook = EvaluationHook(evaluator, criteria)
hookedllm.scope("evaluation").after(eval_hook)

# Create client
client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")

# Make calls
response = await client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain hooks"}]
)

# Access results
print(response.choices[0].message.content)
print(f"Metrics: {metrics.summary()}")
```
    """)
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. Metrics tracking is automatic with MetricsHook")
    print("  2. Evaluation happens transparently with EvaluationHook")
    print("  3. Conditional execution prevents unnecessary evaluations")
    print("  4. Multiple scopes provide flexibility and isolation")
    print("  5. All hooks run without changing your LLM call code!")


if __name__ == "__main__":
    asyncio.run(main())