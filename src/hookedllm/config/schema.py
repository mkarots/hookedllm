"""
Configuration schema for YAML-based hook registration.

Defines the structure of YAML configuration files.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal


@dataclass
class WhenConfig:
    """Rule configuration from YAML."""
    model: Optional[str] = None
    models: Optional[List[str]] = None
    tag: Optional[str] = None 
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    all_calls: bool = False


@dataclass
class HookConfig:
    """Single hook configuration from YAML."""
    name: str
    type: Literal["before", "after", "error", "finally"]
    module: str
    function: Optional[str] = None
    class_name: Optional[str] = None  # Using class_name instead of class (reserved)
    when: Optional[WhenConfig] = None
    args: Optional[Dict[str, Any]] = None


@dataclass
class ScopeConfig:
    """Scope configuration with its hooks."""
    hooks: List[HookConfig]


@dataclass
class RootConfig:
    """Root configuration schema."""
    global_hooks: Optional[List[HookConfig]] = None
    scopes: Optional[Dict[str, ScopeConfig]] = None