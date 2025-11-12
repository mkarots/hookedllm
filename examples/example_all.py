import hookedllm
import asyncio 
from openai import AsyncOpenAI
import json
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("hookedllm")

# Pass logger to context
ctx = hookedllm.create_context(
    executor=hookedllm.DefaultHookExecutor(logger=logger))

# Define a simple hook
async def log_usage(call_input, call_output, context):
    print(f"Model: {call_input.model}")
    print(f"Tokens: {call_output.usage.get('total_tokens', 0)}")

async def log_pre_call(call_input, call_context):
    print(f"Model: {call_input.model}")
    print(f"Messages: {call_input.messages}")

async def evaluate_response(call_input, call_output, context):
    """Evaluate LLM responses for quality."""
    # Build evaluation prompt
    eval_prompt = f"""
    Evaluate this response for clarity and accuracy:
    
    Query: {call_input.messages[-1].content}
    Response: {call_output.text}
    
    type EvalResponse schema {{
        criteria: str, "name of criteria that was used for evaluation",
        score: float, "decimal between 0.00 and 1.00
    }}
    return ONLY flat valid json with schema EvalResponse
    """
    
    # Use separate evaluator client (no hooks to avoid recursion)
    evaluator = AsyncOpenAI()
    eval_result = await evaluator.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": eval_prompt}]
    )
    
    # Store evaluation in metadata
    result_raw = eval_result.choices[0].message.content
    result = json.loads(result_raw)
    context.metadata["evaluation"] = result


async def log_evaluation(call_input, call_output, context):
    print(f"Call Input: {call_input.messages}")
    print(f"Call Input: {call_output.text}")
    print(f"Call metadata: {context.metadata}")
    print(f"Evaluation criteria: {context.metadata["evaluation"].get("criteria")}")
    print(f"Evaluation score: {context.metadata["evaluation"].get("score")}")


async def log_err(call_input, error, context):
    print("error:", error)

async def log_finally(call_result):
    print("call_error:", call_result.error)
    

async def main():
    # Register hook to a scope
    ctx.scope("global").before(log_pre_call)
    ctx.scope("global").after(log_usage)
    ctx.scope("global").after(evaluate_response)
    ctx.scope("global").after(log_evaluation)
    ctx.scope("global").error(log_err)
    ctx.scope("global").finally_(log_finally)

    # Wrap your client with the scope
    client = ctx.wrap(AsyncOpenAI(), scope="global")
    

    # Use normally - hooks execute automatically!
    response_1 = await client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Explain what a type system is in under 100 chars!"}]
    )

    response_2 = await client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Explain what a cateogory theory is in under 100 chars !"}]
    )


    

if __name__ == "__main__":
    asyncio.run(main())
