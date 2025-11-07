"""
Core data types for hookedllm.

These types represent the data that flows through the hook system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class Message:
    """A single message in an LLM conversation."""
    role: str
    content: Any


@dataclass
class CallInput:
    """
    Normalized input for an LLM call.
    
    This represents the input parameters in a provider-agnostic way.
    """
    model: str
    messages: Sequence[Message]
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallOutput:
    """
    Normalized output from an LLM call.
    
    This represents the response in a provider-agnostic way while
    preserving the original response object.
    """
    text: Optional[str]
    raw: Any  # Original SDK response object
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


@dataclass
class CallContext:
    """
    Context for a single LLM call lifecycle.
    
    Contains metadata about the call including timing, tags, and custom metadata.
    """
    call_id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: Optional[str] = None
    provider: str = ""
    model: str = ""
    route: str = "chat"
    tags: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallResult:
    """
    Complete result of an LLM call.
    
    Contains the input, output, context, any error that occurred,
    and timing information. This is passed to finally hooks.
    """
    input: CallInput
    output: Optional[CallOutput]
    context: CallContext
    error: Optional[BaseException]
    ended_at: datetime
    elapsed_ms: float