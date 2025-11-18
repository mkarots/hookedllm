# Contributing to HookedLLM

Thank you for your interest in contributing to HookedLLM! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Python version and relevant package versions
- Code snippets or examples if applicable
- Any relevant error messages or stack traces

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- A clear description of the enhancement
- Use cases and examples
- Potential implementation approach (if you have ideas)
- Any breaking changes or compatibility considerations

### Pull Requests

1. **Fork the repository** and create a branch from `main` (or the default branch)

2. **Follow the coding standards**:
   - Use type hints throughout
   - Follow PEP 8 style guidelines (enforced by `black` and `ruff`)
   - Write docstrings for public functions and classes
   - Keep functions focused and small (Single Responsibility Principle)

3. **Write tests**:
   - Add tests for new functionality
   - Ensure all tests pass: `pytest`
   - Maintain or improve code coverage

4. **Update documentation**:
   - Update README.md if adding new features
   - Add docstrings to new functions/classes
   - Update examples if applicable

5. **Run linting and formatting**:
   ```bash
   black src/ tests/ examples/
   ruff check src/ tests/ examples/
   isort src/ tests/ examples/
   mypy src/
   ```

6. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference issue numbers if applicable

7. **Push and create a Pull Request**:
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## Development Setup

### Prerequisites

- Python 3.10 or higher
- `uv` or `pip` for package management

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourorg/hookedllm.git
   cd hookedllm
   ```

2. Install in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   # or with uv
   uv pip install -e ".[dev]"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hookedllm --cov-report=html

# Run specific test file
pytest tests/test_basic.py
```

### Code Quality Tools

The project uses several tools for code quality:

- **black**: Code formatting
- **ruff**: Fast linting
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework

Run all checks:
```bash
black --check src/ tests/ examples/
ruff check src/ tests/ examples/
isort --check src/ tests/ examples/
mypy src/
pytest
```

## Architecture Guidelines

HookedLLM follows SOLID principles:

- **Single Responsibility**: Each module/class has one clear purpose
- **Open/Closed**: Extend via hooks and rules without modifying core
- **Liskov Substitution**: Protocol-based abstractions
- **Interface Segregation**: Focused, minimal interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed design documentation.

## Project Structure

```
hookedllm/
├── src/hookedllm/       # Main package
│   ├── core/           # Core functionality (executor, wrapper, scopes)
│   ├── hooks/          # Built-in hooks (metrics, evaluation)
│   ├── config/         # Configuration loading
│   └── providers/      # Provider integrations
├── tests/              # Test suite
├── examples/           # Usage examples
└── docs/              # Documentation (if applicable)
```

## Questions?

Feel free to open an issue for questions or discussions. We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

