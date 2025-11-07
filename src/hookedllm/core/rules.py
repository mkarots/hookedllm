"""
Rule system for conditional hook execution.

Rules determine when hooks should execute based on call input and context.
Supports composition via AND, OR, NOT operations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Literal
from .types import CallInput, CallContext


@dataclass
class ModelRule:
    """Match specific model(s)."""
    models: List[str]
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        return call_input.model in self.models
    
    def __and__(self, other: ModelRule) -> CompositeRule:
        return CompositeRule([self, other], "and")
    
    def __or__(self, other: ModelRule) -> CompositeRule:
        return CompositeRule([self, other], "or")
    
    def __invert__(self) -> NotRule:
        return NotRule(self)


@dataclass
class TagRule:
    """Match if context has specific tag(s)."""
    tags: List[str]
    require_all: bool = False
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        if self.require_all:
            return all(tag in context.tags for tag in self.tags)
        return any(tag in context.tags for tag in self.tags)
    
    def __and__(self, other: TagRule) -> CompositeRule:
        return CompositeRule([self, other], "and")
    
    def __or__(self, other: TagRule) -> CompositeRule:
        return CompositeRule([self, other], "or")
    
    def __invert__(self) -> NotRule:
        return NotRule(self)


@dataclass
class MetadataRule:
    """Match based on metadata key-value pairs."""
    conditions: Dict[str, Any]
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        for key, value in self.conditions.items():
            if context.metadata.get(key) != value:
                return False
        return True
    
    def __and__(self, other: MetadataRule) -> CompositeRule:
        return CompositeRule([self, other], "and")
    
    def __or__(self, other: MetadataRule) -> CompositeRule:
        return CompositeRule([self, other], "or")
    
    def __invert__(self) -> NotRule:
        return NotRule(self)


@dataclass
class CustomRule:
    """Custom predicate function."""
    predicate: Callable[[CallInput, CallContext], bool]
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        return self.predicate(call_input, context)
    
    def __and__(self, other: CustomRule) -> CompositeRule:
        return CompositeRule([self, other], "and")
    
    def __or__(self, other: CustomRule) -> CompositeRule:
        return CompositeRule([self, other], "or")
    
    def __invert__(self) -> NotRule:
        return NotRule(self)


@dataclass
class CompositeRule:
    """Combine multiple rules with AND/OR logic."""
    rules: List[Any]  # List of any rule type
    operator: Literal["and", "or"]
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        if self.operator == "and":
            return all(r.matches(call_input, context) for r in self.rules)
        else:  # or
            return any(r.matches(call_input, context) for r in self.rules)
    
    def __and__(self, other: Any) -> CompositeRule:
        # Flatten nested AND compositions
        if isinstance(other, CompositeRule) and other.operator == "and":
            return CompositeRule(self.rules + other.rules, "and")
        return CompositeRule(self.rules + [other], "and")
    
    def __or__(self, other: Any) -> CompositeRule:
        # Flatten nested OR compositions
        if isinstance(other, CompositeRule) and other.operator == "or":
            return CompositeRule(self.rules + other.rules, "or")
        return CompositeRule(self.rules + [other], "or")
    
    def __invert__(self) -> NotRule:
        return NotRule(self)


@dataclass
class NotRule:
    """Negate a rule."""
    rule: Any  # Any rule type
    
    def matches(self, call_input: CallInput, context: CallContext) -> bool:
        return not self.rule.matches(call_input, context)
    
    def __and__(self, other: Any) -> CompositeRule:
        return CompositeRule([self, other], "and")
    
    def __or__(self, other: Any) -> CompositeRule:
        return CompositeRule([self, other], "or")
    
    def __invert__(self) -> Any:
        # Double negation returns original rule
        return self.rule


class RuleBuilder:
    """
    Fluent API for building rules.
    
    Used via the 'when' global instance.
    """
    
    @staticmethod
    def model(*models: str) -> ModelRule:
        """
        Match specific model(s).
        
        Example:
            when.model("gpt-4", "gpt-4-turbo")
        """
        return ModelRule(list(models))
    
    @staticmethod
    def tag(*tags: str, all_: bool = False) -> TagRule:
        """
        Match if context has tag(s).
        
        Args:
            *tags: Tag names to match
            all_: If True, all tags must be present. If False, any tag matches.
        
        Example:
            when.tag("production", "critical")
        """
        return TagRule(list(tags), require_all=all_)
    
    @staticmethod
    def metadata(**conditions: Any) -> MetadataRule:
        """
        Match metadata conditions.
        
        Example:
            when.metadata(user_tier="premium", region="us-east")
        """
        return MetadataRule(conditions)
    
    @staticmethod
    def custom(predicate: Callable[[CallInput, CallContext], bool]) -> CustomRule:
        """
        Custom predicate function.
        
        Example:
            when.custom(lambda i, c: c.metadata.get("score", 0) > 0.8)
        """
        return CustomRule(predicate)
    
    @staticmethod
    def always() -> CustomRule:
        """Always matches."""
        return CustomRule(lambda i, c: True)
    
    @staticmethod
    def never() -> CustomRule:
        """Never matches."""
        return CustomRule(lambda i, c: False)