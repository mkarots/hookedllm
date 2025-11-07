"""
Core module for hookedllm.

Contains the fundamental types, protocols, and implementations.
"""

from .types import Message, CallInput, CallOutput, CallContext, CallResult
from .protocols import (
    BeforeHook,
    AfterHook,
    ErrorHook,
    FinallyHook,
    Rule,
    ScopeHookStore,
    ScopeRegistry,
    HookExecutor,
)
from .rules import (
    ModelRule,
    TagRule,
    MetadataRule,
    CustomRule,
    CompositeRule,
    NotRule,
    RuleBuilder,
)
from .scopes import InMemoryScopeHookStore, InMemoryScopeRegistry
from .executor import DefaultHookExecutor
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