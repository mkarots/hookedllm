.PHONY: help install install-dev clean build test lint format type-check check dist upload-testpypi upload-pypi verify-build test-install ci docs-install docs-build docs-serve docs-check docs-clean

# Variables
PYTHON := python3
PIP := pip3
UV := uv
VENV := .venv
BUILD_ENV := build-env
DIST_DIR := dist
SRC_DIR := src
TEST_DIR := tests

# Detect if uv is available
HAS_UV := $(shell command -v $(UV) 2> /dev/null)

# Use uv if available, otherwise use standard Python tools
ifeq ($(HAS_UV),)
	PYTHON_CMD := $(PYTHON)
	PIP_CMD := $(PIP)
	INSTALL_CMD := $(PIP) install
	INSTALL_DEV_CMD := $(PIP) install -e ".[dev]"
else
	PYTHON_CMD := $(UV) run python
	PIP_CMD := $(UV) pip install
	INSTALL_CMD := $(UV) pip install
	INSTALL_DEV_CMD := $(UV) pip install -e ".[dev]"
endif

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	@echo "Installing package..."
	$(INSTALL_CMD) -e .

install-dev: ## Install package with development dependencies
	@echo "Installing package with dev dependencies..."
	$(INSTALL_DEV_CMD)

clean: ## Remove build artifacts and cache files
	@echo "Cleaning build artifacts..."
	rm -rf $(DIST_DIR)
	rm -rf build
	rm -rf $(SRC_DIR)/*.egg-info
	rm -rf $(SRC_DIR)/hookedllm.egg-info
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	rm -rf htmlcov .coverage .coverage.*
	@echo "Clean complete"

clean-all: clean ## Remove all build artifacts including virtual environments
	rm -rf $(VENV) $(BUILD_ENV)
	@echo "Clean all complete"

setup-build-env: ## Create isolated build environment
	@echo "Setting up build environment..."
	$(PYTHON) -m venv $(BUILD_ENV)
	$(BUILD_ENV)/bin/pip install --upgrade pip build twine

build: clean ## Build source distribution and wheel
	@echo "Building distribution packages..."
	@if [ -d "$(BUILD_ENV)" ]; then \
		$(BUILD_ENV)/bin/python -m build; \
	else \
		$(PYTHON_CMD) -m build; \
	fi
	@echo "Build complete. Artifacts in $(DIST_DIR)/"

verify-build: build ## Verify built packages with twine check
	@echo "Verifying build artifacts..."
	@if [ -d "$(BUILD_ENV)" ]; then \
		$(BUILD_ENV)/bin/twine check $(DIST_DIR)/*; \
	else \
		twine check $(DIST_DIR)/*; \
	fi
	@echo "Verification complete"

test: ## Run tests with pytest
	@echo "Running tests..."
	$(PYTHON_CMD) -m pytest $(TEST_DIR) -v

test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(PYTHON_CMD) -m pytest $(TEST_DIR) --cov=$(SRC_DIR)/hookedllm --cov-report=term-missing --cov-report=html -v

lint: ## Run linting checks with ruff
	@echo "Running linter..."
	$(PYTHON_CMD) -m ruff check $(SRC_DIR) $(TEST_DIR)

format-check: ## Check code formatting without making changes
	@echo "Checking code formatting..."
	$(PYTHON_CMD) -m black --check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_CMD) -m isort --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "Format check complete"

format: ## Format code with black and isort
	@echo "Formatting code..."
	$(PYTHON_CMD) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON_CMD) -m isort $(SRC_DIR) $(TEST_DIR)
	@echo "Formatting complete"

type-check: ## Run type checking with mypy
	@echo "Running type checker..."
	$(PYTHON_CMD) -m mypy $(SRC_DIR)/hookedllm
	@echo "Type check complete"

check: lint format-check type-check ## Run all code quality checks

test-install: build ## Test installing the built package locally
	@echo "Testing local installation..."
	@if [ -d "$(BUILD_ENV)" ]; then \
		$(BUILD_ENV)/bin/pip install --force-reinstall $(DIST_DIR)/*.whl; \
		$(BUILD_ENV)/bin/python -c "import hookedllm; print(f'hookedllm version: {hookedllm.__version__}')"; \
	else \
		pip install --force-reinstall $(DIST_DIR)/*.whl; \
		python -c "import hookedllm; print(f'hookedllm version: {hookedllm.__version__}')"; \
	fi
	@echo "Installation test complete"

upload-testpypi: verify-build ## Upload package to TestPyPI (reads credentials from ~/.pypirc or env vars)
	@echo "Uploading to TestPyPI..."
	@if [ -d "$(BUILD_ENV)" ]; then \
		$(BUILD_ENV)/bin/twine upload --repository testpypi $(DIST_DIR)/*; \
	else \
		twine upload --repository testpypi $(DIST_DIR)/*; \
	fi
	@echo "Upload to TestPyPI complete"

upload-pypi: verify-build ## Upload package to PyPI (production, reads credentials from ~/.pypirc)
	@echo "Uploading to PyPI..."
	@if [ ! -f ~/.pypirc ]; then \
		echo "ERROR: ~/.pypirc not found. Create it or set TWINE_USERNAME and TWINE_PASSWORD"; \
		exit 1; \
	fi
	@PYPI_USERNAME=$$(grep -A 2 '\[pypi\]' ~/.pypirc | grep username | awk '{print $$3}' || echo '__token__'); \
	PYPI_PASSWORD=$$(grep -A 2 '\[pypi\]' ~/.pypirc | grep password | awk '{print $$3}'); \
	if [ -z "$$PYPI_PASSWORD" ]; then \
		echo "ERROR: Could not read password from ~/.pypirc"; \
		exit 1; \
	fi; \
	if [ -d "$(BUILD_ENV)" ]; then \
		$(BUILD_ENV)/bin/twine upload --username "$$PYPI_USERNAME" --password "$$PYPI_PASSWORD" $(DIST_DIR)/*; \
	else \
		twine upload --username "$$PYPI_USERNAME" --password "$$PYPI_PASSWORD" $(DIST_DIR)/*; \
	fi
	@echo "Upload to PyPI complete"

dist: verify-build ## Alias for verify-build
	@echo "Distribution packages ready in $(DIST_DIR)/"

# CI/CD targets
ci: clean install-dev check test build verify-build ## Run full CI pipeline (clean, install, check, test, build)
	@echo "CI pipeline complete"

ci-test: install-dev lint type-check test ## Run CI test pipeline (no build)
	@echo "CI test pipeline complete"

ci-build: verify-build test-install ## Run CI build pipeline
	@echo "CI build pipeline complete"

# Development workflow
dev-setup: install-dev ## Set up development environment
	@echo "Development environment ready"

pre-commit: format lint type-check test ## Run pre-commit checks (format, lint, type-check, test)
	@echo "Pre-commit checks complete"

pre-publish: clean check test verify-build ## Run pre-publish checks
	@echo "Pre-publish checks complete. Ready to publish!"

# Documentation targets
docs-install: ## Install documentation dependencies
	@echo "Installing documentation dependencies..."
	$(INSTALL_CMD) -e ".[docs]"

docs-build: docs-install ## Build documentation
	@echo "Building documentation..."
	$(PYTHON_CMD) -m mkdocs build --strict
	@echo "Documentation built in site/"

docs-serve: docs-install ## Serve documentation locally (with live reload)
	@echo "Serving documentation at http://127.0.0.1:8000"
	$(PYTHON_CMD) -m mkdocs serve

docs-check: docs-install ## Check documentation (build and validate links)
	@echo "Checking documentation..."
	$(PYTHON_CMD) -m mkdocs build --strict
	@echo "Documentation check complete"

docs-clean: ## Clean documentation build artifacts
	@echo "Cleaning documentation artifacts..."
	rm -rf site/
	rm -rf .cache/
	@echo "Documentation clean complete"

