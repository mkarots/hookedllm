"""
Provider adapters for multi-provider support.

Each adapter handles provider-specific logic for detecting clients,
normalizing input/output, and extracting callable methods.
"""

from .protocol import ProviderAdapter

__all__ = ["ProviderAdapter"]

# Import adapters (may fail if optional dependencies aren't installed)
try:
    from .openai import OpenAIAdapter

    __all__.append("OpenAIAdapter")
except ImportError:
    pass

try:
    from .anthropic import AnthropicAdapter

    __all__.append("AnthropicAdapter")
except ImportError:
    pass
