"""
Built-in metrics tracking hook.

Tracks token usage, call counts, and error rates across LLM calls.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from ..core.types import CallResult


class MetricsHook:
    """
    Track metrics across LLM calls.
    
    This is a finally hook that aggregates metrics including:
    - Total calls
    - Total tokens used
    - Error count
    - Average latency
    
    Usage:
        metrics = MetricsHook()
        hookedllm.finally_(metrics)
        
        # Later, access metrics
        print(metrics.stats)
    """
    
    def __init__(self, stats: Optional[Dict[str, Any]] = None):
        """
        Initialize metrics hook.
        
        Args:
            stats: Optional existing stats dict to update.
                   If None, creates a new dict.
        """
        if stats is None:
            self.stats = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_latency_ms": 0.0,
            }
        else:
            self.stats = stats
    
    async def __call__(self, result: CallResult) -> None:
        """
        Update metrics based on call result.
        
        Args:
            result: The complete call result
        """
        # Increment total calls
        self.stats["total_calls"] += 1
        
        # Track success/failure
        if result.error is None:
            self.stats["successful_calls"] += 1
        else:
            self.stats["failed_calls"] += 1
        
        # Track tokens
        if result.output and result.output.usage:
            usage = result.output.usage
            self.stats["total_tokens"] += usage.get("total_tokens", 0)
            self.stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
            self.stats["completion_tokens"] += usage.get("completion_tokens", 0)
        
        # Track latency
        self.stats["total_latency_ms"] += result.elapsed_ms
    
    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.stats["total_calls"] == 0:
            return 0.0
        return self.stats["total_latency_ms"] / self.stats["total_calls"]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.stats["total_calls"] == 0:
            return 0.0
        return self.stats["successful_calls"] / self.stats["total_calls"]
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate (0.0 to 1.0)."""
        return 1.0 - self.success_rate
    
    def reset(self) -> None:
        """Reset all metrics to zero."""
        for key in self.stats:
            self.stats[key] = 0 if isinstance(self.stats[key], int) else 0.0
    
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of metrics including calculated values.
        
        Returns:
            Dict with all metrics plus calculated averages
        """
        return {
            **self.stats,
            "average_latency_ms": self.average_latency_ms,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
        }