# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2024-12-XX

### Added

- **Multi-provider support**: Added support for Anthropic/Claude models alongside OpenAI
  - Implemented provider adapter pattern for extensible multi-provider architecture
  - Created `AnthropicAdapter` for Anthropic SDK integration
  - Created `OpenAIAdapter` (refactored from existing code)
  - Added `ProviderAdapter` protocol for defining provider-specific adapters
  - Automatic provider detection when wrapping clients
  - Support for Anthropic's `client.messages.create()` API structure
  - Normalized Anthropic response format (content blocks, usage tokens, stop_reason)
  - Support for Anthropic metadata parameter (instead of extra_body)
- **Examples**: Added comprehensive examples for Anthropic usage
  - `examples/anthropic_simple_example.py`: Simple example demonstrating all hook types
  - `examples/anthropic_usage.py`: Basic usage patterns
- **Tests**: Added comprehensive test coverage for Anthropic integration
  - `tests/test_providers.py`: Unit tests for provider adapters
  - `tests/test_anthropic_integration.py`: Integration tests with hooks

### Changed

- Refactored wrapper to use provider adapter pattern
- Updated wrapper to dynamically detect and support multiple providers
- Improved error messages for unsupported client types

### Technical Details

- Provider adapters handle:
  - Client detection (identifying provider type)
  - Input normalization (converting provider-specific input to `CallInput`/`CallContext`)
  - Output normalization (converting provider responses to `CallOutput`)
  - Wrapper path configuration (e.g., `["chat", "completions"]` for OpenAI, `["messages"]` for Anthropic)
- Backward compatible: All existing OpenAI code continues to work without changes
- Optional dependency: Anthropic support requires `pip install hookedllm[anthropic]`

## [0.1.0] - Initial Release

### Added

- Core hook system with scoped execution
- OpenAI SDK integration
- Before, after, error, and finally hooks
- Conditional hook execution with rules (model, tag, metadata matching)
- Scope-based hook isolation
- Dependency injection support
- YAML configuration support (optional)
- Comprehensive documentation and examples

[0.2.1]: https://github.com/CepstrumLabs/hookedllm/compare/v0.1.0...v0.2.1
[0.1.0]: https://github.com/CepstrumLabs/hookedllm/releases/tag/v0.1.0
