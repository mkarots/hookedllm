"""
Anthropic/Claude usage example for hookedllm.

Demonstrates how to use hookedllm with Anthropic's Claude models.
"""

import asyncio
import hookedllm


# Define hooks
async def log_call(call_input, call_output, context):
    """Log every LLM call."""
    print(f"[LOG] Provider: {context.provider}, Model: {call_input.model}")
    if call_output.usage:
        print(f"      Tokens: {call_output.usage.get('total_tokens', 'N/A')}")


async def track_metrics(result):
    """Track metrics in finally hook."""
    if result.output:
        print(f"[METRICS] Call {result.context.call_id} took {result.elapsed_ms:.2f}ms")
        if result.output.usage:
            print(f"          Input tokens: {result.output.usage.get('input_tokens', 'N/A')}")
            print(f"          Output tokens: {result.output.usage.get('output_tokens', 'N/A')}")


async def main():
    """
    Demonstrate Anthropic/Claude usage with hookedllm.
    
    Note: This example uses a mock client since we don't want
    to require actual API keys for the example.
    """
    
    # Register global hooks
    hookedllm.global_scope().after(log_call)
    hookedllm.global_scope().finally_(track_metrics)
    
    # Register scoped hooks
    hookedllm.scope("evaluation").after(
        lambda i, o, c: print(f"[EVAL] Evaluating Claude response")
    )
    
    print("=" * 60)
    print("HookedLLM Anthropic/Claude Usage Example")
    print("=" * 60)
    
    # Example: Using Anthropic client
    print("\nExample: Anthropic client with hooks")
    print("-" * 60)
    
    # In real usage:
    # from anthropic import AsyncAnthropic
    # client = hookedllm.wrap(AsyncAnthropic(api_key='...'), scope="evaluation")
    # response = await client.messages.create(
    #     model="claude-3-opus-20240229",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": "Hello, Claude!"}],
    #     metadata={"hookedllm_tags": ["test"], "hookedllm_metadata": {"user_id": "123"}}
    # )
    
    print("Would create: client = hookedllm.wrap(AsyncAnthropic(api_key='...'), scope='evaluation')")
    print("Hooks registered:")
    print("  - log_call (global)")
    print("  - track_metrics (global)")
    print("  - evaluation hook (scoped)")
    
    print("\nKey differences from OpenAI:")
    print("  - Use client.messages.create() instead of client.chat.completions.create()")
    print("  - Pass metadata via metadata parameter (not extra_body)")
    print("  - Response structure: response.content[0].text")
    print("  - Usage: response.usage.input_tokens and response.usage.output_tokens")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nTo use with real Anthropic:")
    print("  1. Install: pip install hookedllm[anthropic]")
    print("  2. Import: from anthropic import AsyncAnthropic")
    print("  3. Wrap: client = hookedllm.wrap(AsyncAnthropic(api_key='...'))")
    print("  4. Use: response = await client.messages.create(...)")


if __name__ == "__main__":
    asyncio.run(main())
