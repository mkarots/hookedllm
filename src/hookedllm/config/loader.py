"""
YAML configuration loader for hookedllm.

Loads hook configurations from YAML files and registers them.
"""

from __future__ import annotations
from typing import Any, Optional
from importlib import import_module
from pathlib import Path


def load_config(path: str, context: Optional[Any] = None) -> None:
    """
    Load hooks from a YAML configuration file.
    
    Requires pyyaml: pip install hookedllm[config]
    
    Args:
        path: Path to YAML config file
        context: Optional HookedLLMContext to use (default: uses default context)
        
    Example YAML:
        global_hooks:
          - name: metrics
            type: finally
            module: hookedllm.hooks.metrics
            class_name: MetricsHook
        
        scopes:
          evaluation:
            hooks:
              - name: evaluate
                type: after
                module: my_app.hooks
                function: evaluate_response
                when:
                  model: gpt-4
    
    Example usage:
        import hookedllm
        hookedllm.load_config("hooks.yaml")
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for config loading. "
            "Install with: pip install hookedllm[config]"
        )
    
    # Load YAML file
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(config_path) as f:
        data = yaml.safe_load(f)
    
    if not data:
        return  # Empty config
    
    # Use provided context or default
    if context is None:
        import hookedllm
        ctx = hookedllm._default_context
    else:
        ctx = context
    
    # Load global hooks
    if "global_hooks" in data and data["global_hooks"]:
        for hook_config in data["global_hooks"]:
            _register_hook_from_config(hook_config, ctx.global_scope(), ctx)
    
    # Load scoped hooks
    if "scopes" in data and data["scopes"]:
        for scope_name, scope_data in data["scopes"].items():
            scope = ctx.scope(scope_name)
            if "hooks" in scope_data:
                for hook_config in scope_data["hooks"]:
                    _register_hook_from_config(hook_config, scope, ctx)


def _register_hook_from_config(
    config: dict,
    scope: Any,
    context: Any
) -> None:
    """
    Register a single hook from config.
    
    Args:
        config: Hook configuration dict
        scope: Scope to register to
        context: HookedLLMContext
    """
    # Import the hook
    hook = _import_hook(config)
    
    # Build rule if specified
    rule = _build_rule_from_config(config.get("when"))
    
    # Register based on type
    hook_type = config["type"]
    if hook_type == "before":
        scope.add_before(hook, rule)
    elif hook_type == "after":
        scope.add_after(hook, rule)
    elif hook_type == "error":
        scope.add_error(hook, rule)
    elif hook_type == "finally":
        scope.add_finally(hook, rule)
    else:
        raise ValueError(f"Unknown hook type: {hook_type}")


def _import_hook(config: dict) -> Any:
    """
    Import a hook from module.
    
    Args:
        config: Hook configuration with 'module' and 'function' or 'class_name'
        
    Returns:
        Hook callable
    """
    module_name = config["module"]
    module = import_module(module_name)
    
    if "function" in config and config["function"]:
        # Import function
        return getattr(module, config["function"])
    elif "class_name" in config and config["class_name"]:
        # Import and instantiate class
        cls = getattr(module, config["class_name"])
        args = config.get("args", {})
        return cls(**args) if args else cls()
    else:
        raise ValueError(
            "Hook config must specify either 'function' or 'class_name'"
        )


def _build_rule_from_config(when_config: Optional[dict]) -> Optional[Any]:
    """
    Build a rule from YAML when configuration.
    
    Args:
        when_config: Dict with rule conditions
        
    Returns:
        Rule object or None
    """
    if not when_config:
        return None
    
    from ..core.rules import RuleBuilder
    when = RuleBuilder()
    
    # Check for "all_calls" shortcut
    if when_config.get("all_calls"):
        return when.always()
    
    # Build individual rules
    rules = []
    
    # Model rule
    if "model" in when_config:
        rules.append(when.model(when_config["model"]))
    elif "models" in when_config:
        rules.append(when.model(*when_config["models"]))
    
    # Tag rule
    if "tag" in when_config:
        rules.append(when.tag(when_config["tag"]))
    elif "tags" in when_config:
        rules.append(when.tag(*when_config["tags"]))
    
    # Metadata rule
    if "metadata" in when_config:
        rules.append(when.metadata(**when_config["metadata"]))
    
    # Combine rules with AND
    if len(rules) == 0:
        return None
    elif len(rules) == 1:
        return rules[0]
    else:
        # Compose with & operator
        result = rules[0]
        for r in rules[1:]:
            result = result & r
        return result