"""
Basic usage example for hookedllm.

Demonstrates:
- Simple hook registration
- Scoped hooks
- Conditional rules
- Global + scoped hook combination
"""

import asyncio
import hookedllm


# Define some simple hooks
async def log_call(call_input, call_output, context):
    """Log every LLM call."""
    print(f"[LOG] Model: {call_input.model}, Tokens: {call_output.usage.get('total_tokens', 0) if call_output.usage else 0}")


async def evaluate_response(call_input, call_output, context):
    """Evaluate response quality (placeholder)."""
    print(f"[EVAL] Evaluating response for: {call_input.model}")
    # In real usage, you'd call another LLM to evaluate
    context.metadata["eval_score"] = 0.9


async def track_metrics(result):
    """Track metrics in finally hook."""
    if result.output:
        print(f"[METRICS] Call {result.context.call_id} took {result.elapsed_ms:.2f}ms")


async def production_only_alert(call_input, error, context):
    """Alert on production errors."""
    print(f"[ALERT] Production error: {error}")


async def main():
    """
    Demonstrate basic hookedllm usage.
    
    Note: This example uses a mock client since we don't want
    to require actual API keys for the example.
    """
    
    # Register global hooks (run for ALL clients)
    hookedllm.finally_(track_metrics)
    
    # Register scoped hooks
    hookedllm.scope("evaluation").after(evaluate_response)
    hookedllm.scope("evaluation").after(log_call)
    
    hookedllm.scope("production").error(
        production_only_alert,
        when=hookedllm.when.tag("critical")
    )
    
    # Conditional hook - only for GPT-4
    hookedllm.scope("evaluation").after(
        lambda i, o, c: print(f"[GPT-4 ONLY] Special handling"),
        when=hookedllm.when.model("gpt-4")
    )
    
    print("=" * 60)
    print("HookedLLM Basic Usage Example")
    print("=" * 60)
    
    # Example 1: Mock evaluation client
    print("\nExample 1: Evaluation scope")
    print("-" * 60)
    
    # In real usage:
    # from openai import AsyncOpenAI
    # eval_client = hookedllm.wrap(AsyncOpenAI(), scope="evaluation")
    
    # For this example, we'll just demonstrate the API:
    print("Would create: eval_client = hookedllm.wrap(AsyncOpenAI(), scope='evaluation')")
    print("Hooks registered in 'evaluation' scope:")
    print("  - evaluate_response")
    print("  - log_call")
    print("  - GPT-4 special handler (conditional)")
    print("  - track_metrics (global)")
    
    # Example 2: Mock production client
    print("\nExample 2: Production scope")
    print("-" * 60)
    
    # In real usage:
    # prod_client = hookedllm.wrap(AsyncOpenAI(), scope="production")
    
    print("Would create: prod_client = hookedllm.wrap(AsyncOpenAI(), scope='production')")
    print("Hooks registered in 'production' scope:")
    print("  - production_only_alert (on error, only if 'critical' tag)")
    print("  - track_metrics (global)")
    
    # Example 3: Multiple scopes
    print("\nExample 3: Multiple scopes")
    print("-" * 60)
    
    # In real usage:
    # multi_client = hookedllm.wrap(AsyncOpenAI(), scope=["evaluation", "production"])
    
    print("Would create: multi_client = hookedllm.wrap(AsyncOpenAI(), scope=['evaluation', 'production'])")
    print("This client gets hooks from BOTH scopes plus global hooks")
    
    # Example 4: Rule composition
    print("\nExample 4: Complex rules")
    print("-" * 60)
    
    complex_rule = (
        hookedllm.when.model("gpt-4") & 
        hookedllm.when.tag("production") & 
        ~hookedllm.when.tag("test")
    )
    
    print("Complex rule created:")
    print("  GPT-4 AND production tag AND NOT test tag")
    print("  This demonstrates rule composition with &, |, ~")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nTo use with real OpenAI:")
    print("  1. Install: pip install hookedllm[openai]")
    print("  2. Import: from openai import AsyncOpenAI")
    print("  3. Wrap: client = hookedllm.wrap(AsyncOpenAI(api_key='...'))")
    print("  4. Use: response = await client.chat.completions.create(...)")


if __name__ == "__main__":
    asyncio.run(main())