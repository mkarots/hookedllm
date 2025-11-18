# Rules

Rules let you conditionally execute hooks based on call properties like model, tags, or metadata.

## Basic Rules

### Model Rules

Run hooks only for specific models:

```python
# Only for GPT-4
hookedllm.after(
    expensive_eval,
    when=hookedllm.when.model("gpt-4")
)

# Only for GPT-4o-mini
hookedllm.after(
    quick_eval,
    when=hookedllm.when.model("gpt-4o-mini")
)
```

### Tag Rules

Run hooks only when specific tags are present:

```python
# Only for tagged calls
hookedllm.after(
    logger_hook,
    when=hookedllm.when.tag("monitoring")
)

# Only for critical calls
hookedllm.error(
    alert_on_error,
    when=hookedllm.when.tag("critical")
)
```

To use tags, pass them in `extra_body`:

```python
response = await client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    extra_body={
        "hookedllm_tags": ["monitoring", "critical"]
    }
)
```

### Metadata Rules

Run hooks based on metadata values:

```python
# Only for premium users
hookedllm.after(
    premium_hook,
    when=lambda call_input, ctx: ctx.metadata.get("tier") == "premium"
)

# Only for specific user IDs
hookedllm.after(
    user_tracking,
    when=lambda call_input, ctx: ctx.metadata.get("user_id") == "abc123"
)
```

## Rule Composition

Combine rules with `&` (AND), `|` (OR), and `~` (NOT):

```python
# GPT-4 AND monitoring tag
hookedllm.after(
    my_hook,
    when=(
        hookedllm.when.model("gpt-4") &
        hookedllm.when.tag("monitoring")
    )
)

# Monitoring tag AND NOT test tag
hookedllm.after(
    monitoring_hook,
    when=(
        hookedllm.when.tag("monitoring") &
        ~hookedllm.when.tag("test")
    )
)

# GPT-4 OR GPT-3.5
hookedllm.after(
    gpt_hook,
    when=(
        hookedllm.when.model("gpt-4") |
        hookedllm.when.model("gpt-3.5-turbo")
    )
)

# Complex: GPT-4 AND monitoring AND NOT test
hookedllm.after(
    complex_hook,
    when=(
        hookedllm.when.model("gpt-4") &
        hookedllm.when.tag("monitoring") &
        ~hookedllm.when.tag("test")
    )
)
```

## Custom Predicates

Create custom rules with lambda functions:

```python
# Custom rule: only for calls with > 100 tokens
hookedllm.after(
    large_call_hook,
    when=lambda call_input, ctx: len(str(call_input.messages)) > 100
)

# Custom rule: only for specific models and premium users
hookedllm.after(
    premium_gpt4_hook,
    when=lambda call_input, ctx: (
        call_input.model == "gpt-4" and
        ctx.metadata.get("tier") == "premium"
    )
)
```

## Rule Examples

### Conditional Evaluation

```python
# Only evaluate expensive models
hookedllm.scope("evaluation").after(
    expensive_evaluation,
    when=hookedllm.when.model("gpt-4")
)

# Quick evaluation for cheaper models
hookedllm.scope("evaluation").after(
    quick_evaluation,
    when=hookedllm.when.model("gpt-4o-mini")
)
```

### Environment-Specific Hooks

```python
# Conditional logging
hookedllm.after(
    logger_hook,
    when=hookedllm.when.tag("monitoring")
)

# Development debugging
hookedllm.after(
    debug_logger,
    when=hookedllm.when.tag("development")
)
```

### User Tier Hooks

```python
# Premium user features
hookedllm.after(
    premium_features,
    when=lambda call_input, ctx: ctx.metadata.get("tier") == "premium"
)

# Free tier limitations
hookedllm.before(
    enforce_limits,
    when=lambda call_input, ctx: ctx.metadata.get("tier") == "free"
)
```

## Best Practices

1. **Use rules for conditional logic**: Don't check conditions inside hooks - use rules instead
2. **Combine with scopes**: Use scopes for isolation, rules for conditions
3. **Keep rules simple**: Complex logic is better in hook functions
4. **Document custom rules**: Add comments explaining complex predicates

## Examples

See [Advanced Examples](examples/advanced.md) for more rule usage patterns.

