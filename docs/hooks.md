# Hooks

Hooks are functions that execute at specific points in the LLM call lifecycle. HookedLLM supports four hook types: `before`, `after`, `error`, and `finally`.

## Hook Types

### Before Hooks

Run **before** the LLM call executes. Use them to:
- Modify the call input
- Add metadata to the context
- Validate inputs
- Set up tracking

```python
async def before_hook(call_input, context):
    """Run before LLM call."""
    # Add user ID to metadata
    context.metadata["user_id"] = get_current_user_id()
    
    # Modify call parameters
    call_input.params["temperature"] = 0.7
    
    # Log the request
    logger.info(f"Starting call {context.call_id}")

hookedllm.before(before_hook)
```

### After Hooks

Run **after** a successful LLM call. Use them to:
- Process the response
- Log results
- Evaluate quality
- Store metrics

```python
async def after_hook(call_input, call_output, context):
    """Run after successful LLM call."""
    # Log the response
    print(f"Response: {call_output.text}")
    
    # Track token usage
    tokens = call_output.usage.get("total_tokens", 0)
    metrics.record_tokens(tokens)
    
    # Store evaluation
    context.metadata["response_length"] = len(call_output.text)

hookedllm.after(after_hook)
```

### Error Hooks

Run when an **error** occurs during the LLM call. Use them to:
- Log errors
- Send alerts
- Track error rates
- Handle failures gracefully

```python
async def error_hook(call_input, error, context):
    """Run when LLM call fails."""
    # Log the error
    logger.error(f"Call {context.call_id} failed: {error}")
    
    # Send alert for critical errors
    if isinstance(error, RateLimitError):
        alerting.send_alert("Rate limit exceeded")
    
    # Track error metrics
    metrics.record_error(type(error).__name__)

hookedllm.error(error_hook)
```

### Finally Hooks

Run **always**, regardless of success or failure. Use them to:
- Track metrics
- Clean up resources
- Log completion
- Record timing

```python
async def finally_hook(result):
    """Run after call completes (success or failure)."""
    # Track timing
    metrics.record_duration(result.elapsed_ms)
    
    # Log completion
    logger.info(f"Call {result.context.call_id} completed in {result.elapsed_ms}ms")
    
    # Clean up
    cleanup_resources(result.context.call_id)

hookedllm.finally_(finally_hook)
```

## Hook Execution Order

For a single LLM call, hooks execute in this order:

1. **Before hooks** (in registration order)
2. **LLM call** executes
3. **After hooks** (if successful) OR **Error hooks** (if failed)
4. **Finally hooks** (always)

```python
# Registration order matters within each hook type
hookedllm.before(hook1)  # Runs first
hookedllm.before(hook2)  # Runs second

hookedllm.after(hook3)   # Runs first (if successful)
hookedllm.after(hook4)   # Runs second (if successful)
```

## Hook Signatures

Each hook type has a specific signature:

```python
# Before hook
async def before_hook(call_input: CallInput, context: CallContext) -> None:
    ...

# After hook
async def after_hook(
    call_input: CallInput,
    call_output: CallOutput,
    context: CallContext
) -> None:
    ...

# Error hook
async def error_hook(
    call_input: CallInput,
    error: BaseException,
    context: CallContext
) -> None:
    ...

# Finally hook
async def finally_hook(result: CallResult) -> None:
    ...
```

## Hook Failures

**Hook failures never break your LLM calls.** If a hook raises an exception, it's caught and logged, but the LLM call continues normally.

```python
async def buggy_hook(call_input, call_output, context):
    raise ValueError("Something went wrong!")

# This hook failure won't affect the LLM call
hookedllm.after(buggy_hook)

# The call still succeeds
response = await client.chat.completions.create(...)
```

## Examples

See [Basic Usage Examples](examples/basic-usage.md) for complete hook examples, or [Advanced Examples](examples/advanced.md) for complex patterns.

