"""
Core data types for hookedllm.

These types represent the data that flows through the hook system.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
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
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CallOutput:
    """
    Normalized output from an LLM call.

    This represents the response in a provider-agnostic way while
    preserving the original response object.
    """

    text: str | None
    raw: Any  # Original SDK response object
    usage: dict[str, Any] | None = None
    finish_reason: str | None = None


@dataclass
class CallContext:
    """
    Context for a single LLM call lifecycle.

    Contains metadata about the call including timing, tags, and custom metadata.
    """

    call_id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: str | None = None
    provider: str = ""
    model: str = ""
    route: str = "chat"
    tags: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CallResult:
    """
    Complete result of an LLM call.

    Contains the input, output, context, any error that occurred,
    and timing information. This is passed to finally hooks.
    """

    input: CallInput
    output: CallOutput | None
    context: CallContext
    error: BaseException | None
    ended_at: datetime
    elapsed_ms: float
