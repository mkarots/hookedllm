"""
Built-in evaluation hook helper.

Provides a helper for evaluating LLM responses using another LLM.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from ..core.types import CallInput, CallOutput, CallContext
import json


class EvaluationHook:
    """
    Evaluate LLM responses using another LLM.
    
    This is an after hook that calls a separate "evaluator" LLM to assess
    the quality of responses based on configurable criteria.
    
    Usage:
        from openai import AsyncOpenAI
        
        evaluator = AsyncOpenAI()  # Separate client for evaluation
        criteria = {
            "clarity": "Is the response clear and easy to understand?",
            "accuracy": "Is the response factually accurate?",
            "relevance": "Does the response address the user's question?"
        }
        
        eval_hook = EvaluationHook(evaluator, criteria)
        hookedllm.scope("evaluation").after(eval_hook)
    """
    
    def __init__(
        self,
        evaluator_client: Any,
        criteria: Dict[str, str],
        model: str = "gpt-4o-mini",
        store_in_metadata: bool = True
    ):
        """
        Initialize evaluation hook.
        
        Args:
            evaluator_client: OpenAI-compatible client for evaluation calls
            criteria: Dict mapping criterion name to description
            model: Model to use for evaluation (default: gpt-4o-mini)
            store_in_metadata: If True, store results in context.metadata
        """
        self.evaluator = evaluator_client
        self.criteria = criteria
        self.model = model
        self.store_in_metadata = store_in_metadata
    
    async def __call__(
        self,
        call_input: CallInput,
        call_output: CallOutput,
        context: CallContext
    ) -> None:
        """
        Evaluate the LLM response.
        
        Args:
            call_input: The original call input
            call_output: The LLM response
            context: The call context
        """
        if not call_output.text:
            # Nothing to evaluate
            return
        
        # Extract the original query
        original_query = self._extract_query(call_input)
        
        # Build evaluation prompt
        eval_prompt = self._build_evaluation_prompt(
            original_query,
            call_output.text
        )
        
        try:
            # Call evaluator
            eval_response = await self.evaluator.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0.0  # Deterministic evaluation
            )
            
            # Extract evaluation result
            eval_text = eval_response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                eval_result = json.loads(eval_text)
            except json.JSONDecodeError:
                # If not JSON, store raw text
                eval_result = {"raw_evaluation": eval_text}
            
            # Store in context if requested
            if self.store_in_metadata:
                context.metadata["evaluation"] = eval_result
                context.metadata["evaluation_model"] = self.model
        
        except Exception as e:
            # Evaluation failed - don't break the main flow
            if self.store_in_metadata:
                context.metadata["evaluation_error"] = str(e)
    
    def _extract_query(self, call_input: CallInput) -> str:
        """Extract the user's query from messages."""
        # Get the last user message
        for message in reversed(call_input.messages):
            if message.role == "user":
                content = message.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Extract text from content parts
                    text_parts = [
                        part.get("text", "") 
                        for part in content 
                        if isinstance(part, dict) and part.get("type") == "text"
                    ]
                    return " ".join(text_parts)
        return "[No user query found]"
    
    def _build_evaluation_prompt(self, query: str, response: str) -> str:
        """Build the evaluation prompt."""
        criteria_text = "\n".join(
            f"- {name}: {description}"
            for name, description in self.criteria.items()
        )
        
        return f"""You are an expert evaluator. Assess the following LLM response based on the given criteria.

Original Query:
{query}

LLM Response:
{response}

Evaluation Criteria:
{criteria_text}

For each criterion, provide a score from 0.0 to 1.0, where:
- 0.0 = Completely fails the criterion
- 0.5 = Partially meets the criterion  
- 1.0 = Fully meets the criterion

Respond with a JSON object containing:
1. A score for each criterion
2. An "explanation" field with 1-2 sentences justifying the scores

Example format:
{{
  "clarity": 0.9,
  "accuracy": 0.8,
  "relevance": 1.0,
  "explanation": "The response is clear and directly addresses the question. Minor accuracy concern about..."
}}

Your evaluation (JSON only):"""