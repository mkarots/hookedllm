"""
Core module for hookedllm.

Contains the fundamental types, protocols, and implementations.
"""

from .executor import DefaultHookExecutor
from .protocols import (
    AfterHook,
    BeforeHook,
    ErrorHook,
    FinallyHook,
    HookExecutor,
    Rule,
    ScopeHookStore,
    ScopeRegistry,
)
from .rules import (
    CompositeRule,
    CustomRule,
    MetadataRule,
    ModelRule,
    NotRule,
    RuleBuilder,
    TagRule,
)
from .scopes import InMemoryScopeHookStore, InMemoryScopeRegistry
from .types import CallContext, CallInput, CallOutput, CallResult, Message
from .wrapper import HookedClientWrapper

__all__ = [
    # Types
    "Message",
    "CallInput",
    "CallOutput",
    "CallContext",
    "CallResult",
    # Protocols
    "BeforeHook",
    "AfterHook",
    "ErrorHook",
    "FinallyHook",
    "Rule",
    "ScopeHookStore",
    "ScopeRegistry",
    "HookExecutor",
    # Rules
    "ModelRule",
    "TagRule",
    "MetadataRule",
    "CustomRule",
    "CompositeRule",
    "NotRule",
    "RuleBuilder",
    # Implementations
    "InMemoryScopeHookStore",
    "InMemoryScopeRegistry",
    "DefaultHookExecutor",
    "HookedClientWrapper",
]
