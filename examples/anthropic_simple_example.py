"""
Simple example: Using Anthropic/Claude with hookedllm.

This example demonstrates how to use hookedllm with Anthropic's Claude models
to add observability hooks to your LLM calls.
"""

import asyncio
import os

# Note: This example requires the anthropic package
# Install with: pip install hookedllm[anthropic]
try:
    from anthropic import AsyncAnthropic
except ImportError:
    print("Please install anthropic: pip install hookedllm[anthropic]")
    exit(1)

import hookedllm


# Define your hooks
async def log_request(call_input, context):
    """Log every request before it's sent."""
    print(f"🔵 [BEFORE HOOK] log_request executing...")
    print(f"   📤 Request to {context.provider} ({call_input.model})")
    print(f"   Messages: {len(call_input.messages)}")


async def log_response(call_input, call_output, context):
    """Log every response after it's received."""
    print(f"🟢 [AFTER HOOK] log_response executing...")
    print(f"   📥 Response from {context.provider} ({call_input.model})")
    if call_output.text:
        print(f"   Text: {call_output.text[:50]}...")
    if call_output.usage:
        total = call_output.usage.get("total_tokens", "N/A")
        print(f"   Tokens: {total}")


async def track_metrics(result):
    """Track metrics for all calls."""
    print(f"🟡 [FINALLY HOOK] track_metrics executing...")
    if result.output:
        print(f"   ⏱️  Call {result.context.call_id[:8]}... took {result.elapsed_ms:.2f}ms")
        if result.output.usage:
            input_tokens = result.output.usage.get("input_tokens", 0)
            output_tokens = result.output.usage.get("output_tokens", 0)
            print(f"   Input tokens: {input_tokens}, Output tokens: {output_tokens}")
    else:
        print(f"   ⏱️  Call {result.context.call_id[:8]}... took {result.elapsed_ms:.2f}ms (failed)")


async def handle_error(call_input, error, context):
    """Handle errors in LLM calls."""
    print(f"🔴 [ERROR HOOK] handle_error executing...")
    print(f"   ❌ Error in {context.provider} call: {type(error).__name__}")
    print(f"   Model: {call_input.model}")
    print(f"   Error: {str(error)[:100]}")


async def main():
    """Main example function."""
    print("=" * 60)
    print("Anthropic/Claude Example with HookedLLM")
    print("=" * 60)
    print()
    
    # Get API key from environment (or use a test key)
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    
    # Create Anthropic client
    client = AsyncAnthropic(api_key=api_key)
    
    # Wrap it with hookedllm
    wrapped_client = hookedllm.wrap(client, scope="monitoring")
    
    # ========================================================================
    # Register all hooks FIRST, then make calls to see them execute
    # ========================================================================
    print("📋 Registering hooks...")
    print("-" * 60)
    
    hookedllm.scope("monitoring").before(log_request)
    print("  ✅ Registered: log_request (BEFORE hook)")
    
    hookedllm.scope("monitoring").after(log_response)
    print("  ✅ Registered: log_response (AFTER hook)")
    
    hookedllm.scope("monitoring").error(handle_error)
    print("  ✅ Registered: handle_error (ERROR hook)")
    
    hookedllm.scope("monitoring").finally_(track_metrics)
    print("  ✅ Registered: track_metrics (FINALLY hook)")
    
    print()
    
    # ========================================================================
    # Example 1: Successful call - shows BEFORE, AFTER, FINALLY hooks
    # ========================================================================
    print("=" * 60)
    print("Example 1: Successful API call")
    print("=" * 60)
    print("Expected hook execution order:")
    print("  1. 🔵 BEFORE hook (log_request)")
    print("  2. 🟢 AFTER hook (log_response)")
    print("  3. 🟡 FINALLY hook (track_metrics)")
    print()
    print("Making API call...")
    print("-" * 60)
    
    # Try multiple model names (some may not be available depending on API key tier)
    models_to_try = [
        "claude-3-haiku-20240307",      # Fast and cheap, widely available
        "claude-3-sonnet-20240229",      # Good balance (deprecated but still works)
        "claude-3-5-sonnet-20241022",   # Latest (may require newer API key tier)
    ]
    
    response = None
    model_used = None
    
    for model in models_to_try:
        try:
            response = await wrapped_client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello, Claude! Say hello back."}],
                metadata={"hookedllm_tags": ["example", "simple"]},
            )
            model_used = model
            print()
            print(f"✅ API call succeeded with model: {model}")
            if hasattr(response, "content") and response.content:
                print(f"   Response: {response.content[0].text[:50]}...")
            break
        except Exception as e:
            error_type = type(e).__name__
            # If it's a 404 (model not found), try next model
            if "404" in str(e) or "not_found" in str(e).lower():
                print(f"⚠️  Model {model} not available, trying next...")
                continue
            # For other errors (auth, rate limit, etc.), show and stop
            print()
            print(f"⚠️  API call failed ({error_type}): {str(e)[:100]}")
            print("   (This is expected if ANTHROPIC_API_KEY is not set or invalid)")
            break
    
    if not response:
        print()
        print("⚠️  Could not connect to any Anthropic model.")
        print("   Please check:")
        print("   1. ANTHROPIC_API_KEY is set correctly")
        print("   2. Your API key has access to Claude models")
        print("   3. You have sufficient API credits")
    
    print()
    print("=" * 60)
    
    # ========================================================================
    # Example 2: Error handling - shows BEFORE, ERROR, FINALLY hooks
    # ========================================================================
    print("Example 2: Error handling (demonstrates ERROR hook)")
    print("=" * 60)
    print("Expected hook execution order:")
    print("  1. 🔵 BEFORE hook (log_request)")
    print("  2. 🔴 ERROR hook (handle_error)")
    print("  3. 🟡 FINALLY hook (track_metrics)")
    print()
    print("Making API call with invalid model to trigger error...")
    print("-" * 60)
    
    try:
        await wrapped_client.messages.create(
            model="invalid-model-name",
            max_tokens=10,
            messages=[{"role": "user", "content": "This will fail"}],
        )
    except Exception:
        # Error is expected - hooks will have executed
        print()
        print("✅ Error hook executed (see output above)")
    
    print()
    print("=" * 60)
    
    # ========================================================================
    # Example 3: Conditional hooks
    # ========================================================================
    print("Example 3: Conditional hooks (only for specific models)")
    print("=" * 60)
    
    async def sonnet_only_hook(call_input, call_output, context):
        print(f"🟢 [AFTER HOOK - CONDITIONAL] sonnet_only_hook executing...")
        print(f"   🎯 Special handling for Claude Sonnet!")
    
    hookedllm.scope("monitoring").after(
        sonnet_only_hook,
        when=hookedllm.when.model("claude-3-sonnet-20240229") | 
              hookedllm.when.model("claude-3-5-sonnet-20241022"),
    )
    print("  ✅ Registered: sonnet_only_hook (AFTER hook, conditional)")
    print("     (Only runs for Sonnet models)")
    print()
    
    # ========================================================================
    # Example 4: Tag-based hooks
    # ========================================================================
    print("Example 4: Tag-based hooks")
    print("=" * 60)
    
    async def production_hook(call_input, call_output, context):
        print(f"🟢 [AFTER HOOK - TAGGED] production_hook executing...")
        print(f"   🚨 Production call detected!")
    
    hookedllm.scope("monitoring").after(
        production_hook,
        when=hookedllm.when.tag("production"),
    )
    print("  ✅ Registered: production_hook (AFTER hook, tag-based)")
    print("     (Only runs when tag='production' is present)")
    print()
    print("To trigger this hook, use:")
    print('  metadata={"hookedllm_tags": ["production"]}')
    print()
    
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)
    print()
    print("Hook execution summary:")
    print("  🔵 BEFORE hooks: Execute before the API call")
    print("  🟢 AFTER hooks: Execute after successful API call")
    print("  🔴 ERROR hooks: Execute when API call fails")
    print("  🟡 FINALLY hooks: Always execute (success or failure)")
    print()
    print("Note: Set ANTHROPIC_API_KEY environment variable to make real API calls")


if __name__ == "__main__":
    asyncio.run(main())
