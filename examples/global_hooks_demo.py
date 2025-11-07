"""
Demo: Global Hooks with Multiple LLM Calls

This script demonstrates:
1. Registering global before/after hooks that run for ALL calls
2. Making 5 different LLM calls
3. Showing what data the framework provides to hooks

To run:
1. pip install -e .[openai]
2. export OPENAI_API_KEY=your-key-here
3. python examples/global_hooks_demo.py
"""

import asyncio
import os
from openai import AsyncOpenAI
import hookedllm


# Track all calls globally
call_log = []


async def before_hook(call_input, context):
    """
    Before hook - runs BEFORE each LLM call.
    
    The framework provides:
    - call_input: Contains model, messages, params, metadata
    - context: Contains call_id, provider, tags, started_at, metadata
    """
    print(f"\n🔵 BEFORE Hook - Call #{len(call_log) + 1}")
    print(f"   Call ID: {context.call_id}")
    print(f"   Model: {call_input.model}")
    print(f"   Messages: {len(call_input.messages)} message(s)")
    print(f"   First message: {call_input.messages[0].content if call_input.messages else 'N/A'}")
    print(f"   Params: {call_input.params}")
    print(f"   Context tags: {context.tags}")
    print(f"   Context metadata: {context.metadata}")


async def after_hook(call_input, call_output, context):
    """
    After hook - runs AFTER successful LLM call.
    
    The framework provides:
    - call_input: The original input (same as before hook)
    - call_output: Contains text, raw response, usage, finish_reason
    - context: Updated context with any modifications from before hooks
    """
    print(f"\n🟢 AFTER Hook - Call #{len(call_log) + 1}")
    print(f"   Call ID: {context.call_id}")
    print(f"   Response text length: {len(call_output.text) if call_output.text else 0} chars")
    print(f"   Response preview: {call_output.text[:100] if call_output.text else 'N/A'}...")
    print(f"   Usage: {call_output.usage}")
    print(f"   Finish reason: {call_output.finish_reason}")
    print(f"   Raw response type: {type(call_output.raw).__name__}")
    
    # Log the call
    call_log.append({
        "call_id": context.call_id,
        "model": call_input.model,
        "tokens": call_output.usage.get("total_tokens", 0) if call_output.usage else 0,
        "response_length": len(call_output.text) if call_output.text else 0
    })


async def main():
    """Make 5 different LLM calls with global hooks."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        return
    
    print("=" * 80)
    print("Global Hooks Demo: 5 LLM Calls")
    print("=" * 80)
    
    # Register global hooks (run for ALL calls)
    print("\n📌 Registering global hooks...")
    hookedllm.before(before_hook)
    hookedllm.after(after_hook)
    print("✓ Global before hook registered")
    print("✓ Global after hook registered")
    
    # Create wrapped client
    client = hookedllm.wrap(AsyncOpenAI(api_key=api_key))
    
    print("\n" + "=" * 80)
    print("Making 5 LLM calls...")
    print("=" * 80)
    
    # Call 1: Simple question
    print("\n📞 Call 1: Simple factual question")
    print("-" * 80)
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is Python?"}],
        max_tokens=50
    )
    
    # Call 2: Creative task
    print("\n📞 Call 2: Creative writing")
    print("-" * 80)
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Write a haiku about programming"}],
        temperature=0.9,
        max_tokens=30
    )
    
    # Call 3: With system message
    print("\n📞 Call 3: With system message")
    print("-" * 80)
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "Explain what is a derivative?"}
        ],
        max_tokens=60
    )
    
    # Call 4: With tags and metadata (via extra_body)
    print("\n📞 Call 4: With tags and metadata")
    print("-" * 80)
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "List 3 Python libraries"}],
        max_tokens=40,
        extra_body={
            "hookedllm_tags": ["test", "demo"],
            "hookedllm_metadata": {"user_id": "demo_user", "session": "example"}
        }
    )
    
    # Call 5: Different temperature
    print("\n📞 Call 5: Low temperature for consistency")
    print("-" * 80)
    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is 2+2?"}],
        temperature=0.0,
        max_tokens=20
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    print(f"\nTotal calls made: {len(call_log)}")
    print(f"Total tokens used: {sum(c['tokens'] for c in call_log)}")
    print(f"Average tokens per call: {sum(c['tokens'] for c in call_log) / len(call_log):.1f}")
    
    print("\nCall details:")
    for i, call in enumerate(call_log, 1):
        print(f"  {i}. {call['call_id'][:8]}... - {call['tokens']} tokens - "
              f"{call['response_length']} chars")
    
    print("\n" + "=" * 80)
    print("Key Takeaways")
    print("=" * 80)
    print("""
1. Global hooks run for EVERY call automatically
2. Before hooks receive: call_input (model, messages, params) + context
3. After hooks receive: call_input + call_output (text, usage, raw) + context
4. Context includes: call_id, provider, tags, metadata, timestamps  
5. You can pass tags/metadata via extra_body
6. Hooks see all this data WITHOUT any changes to your LLM code!
    """)


if __name__ == "__main__":
    asyncio.run(main())