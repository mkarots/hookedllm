# Release Process

This document describes the process for releasing new versions of `hookedllm` to PyPI.

## Prerequisites

1. Ensure you have a PyPI API token stored as a GitHub secret named `PYPI_API_TOKEN`
2. Ensure your local `~/.pypirc` is configured (for local releases)

## Release Steps

### 1. Update Version

Update the version in `pyproject.toml`:

```toml
version = "0.1.1"  # Update to new version
```

Also update `src/hookedllm/__init__.py`:

```python
__version__ = "0.1.1"
```

### 2. Update CHANGELOG.md

Add a new section documenting the changes in this release.

### 3. Commit and Push

```bash
git add pyproject.toml src/hookedllm/__init__.py CHANGELOG.md
git commit -m "Bump version to 0.1.1"
git push
```

### 4. Create and Push Tag

```bash
git tag v0.1.1
git push origin v0.1.1
```

### 5. Automatic Release

The GitHub Actions workflow will automatically:
- ✅ Run pre-publish checks (lint, format-check, type-check, test)
- ✅ Build distribution packages
- ✅ Verify build artifacts
- ✅ Test installation
- ✅ Publish to PyPI
- ✅ Create a GitHub release

## Manual Release (Alternative)

If you need to release manually from your local machine:

```bash
# Ensure version is updated
make pre-publish  # Run all checks
make upload-pypi  # Upload to PyPI (uses ~/.pypirc)
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Troubleshooting

### Release workflow fails

1. Check that `PYPI_API_TOKEN` secret is set in GitHub repository settings
2. Verify version in `pyproject.toml` matches the tag (e.g., tag `v0.1.1` → version `0.1.1`)
3. Ensure all tests pass locally: `make ci-test`

### PyPI upload fails

- Verify your API token has the correct permissions
- Check that the version doesn't already exist on PyPI
- Ensure build artifacts are valid: `make verify-build`

