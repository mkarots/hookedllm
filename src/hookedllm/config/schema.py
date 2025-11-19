"""
Configuration schema for YAML-based hook registration.

Defines the structure of YAML configuration files.
"""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class WhenConfig:
    """Rule configuration from YAML."""

    model: str | None = None
    models: list[str] | None = None
    tag: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    all_calls: bool = False


@dataclass
class HookConfig:
    """Single hook configuration from YAML."""

    name: str
    type: Literal["before", "after", "error", "finally"]
    module: str
    function: str | None = None
    class_name: str | None = None  # Using class_name instead of class (reserved)
    when: WhenConfig | None = None
    args: dict[str, Any] | None = None


@dataclass
class ScopeConfig:
    """Scope configuration with its hooks."""

    hooks: list[HookConfig]


@dataclass
class RootConfig:
    """Root configuration schema."""

    global_hooks: list[HookConfig] | None = None
    scopes: dict[str, ScopeConfig] | None = None
