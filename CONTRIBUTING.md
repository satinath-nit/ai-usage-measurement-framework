# Contributing to AI Usage Measurement Framework

Thank you for your interest in contributing to AI Usage Measurement Framework! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all backgrounds and experience levels.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with the following information:

**For bugs:**
- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

**For feature requests:**
- Description of the feature
- Use case / motivation
- Proposed implementation (if any)

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Run tests and linting:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy src/
   ```
5. Commit your changes with a descriptive message
6. Push to your fork and submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/ai-usage-measurement-framework.git
cd ai-usage-measurement-framework

# Install dependencies with uv
uv sync

# Run the test suite
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/
```

## Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** for testing

Please ensure your code passes all checks before submitting a pull request.

### Style Guidelines

- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Follow PEP 8 naming conventions
- Keep functions focused and single-purpose
- Add tests for new functionality

## Adding New AI Tool Patterns

To add detection patterns for a new AI tool:

1. Edit `src/ai_usage_measurement_framework/patterns.py`
2. Add patterns to `TOOL_PATTERNS` dictionary:
   ```python
   TOOL_PATTERNS = {
       # ... existing patterns ...
       "New Tool": {
           "patterns": [r"new-tool", r"newtool"],
           "weight": 0.9,
       },
   }
   ```
3. Add any generic patterns to `AI_COMMIT_PATTERNS` list
4. Add tests for the new patterns
5. Update the README with the new tool

## Adding New Exporters

To add a new export format:

1. Create a new file in `src/ai_usage_measurement_framework/exporters/`
2. Implement the exporter class with `export()` method
3. Add the exporter to `src/ai_usage_measurement_framework/exporters/__init__.py`
4. Add CLI support in `src/ai_usage_measurement_framework/cli.py`
5. Add tests for the new exporter

## Testing

We use pytest for testing. Tests are located in the `tests/` directory.

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ai_usage_measurement_framework

# Run specific test file
uv run pytest tests/test_analyzer.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use fixtures for common setup
- Mock external services (GitHub API, git operations)

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions
- Update CHANGELOG.md for notable changes

## Release Process

Releases are managed by maintainers. To request a release:

1. Ensure all tests pass
2. Update version in `pyproject.toml` and `src/ai_usage_measurement_framework/__init__.py`
3. Update CHANGELOG.md
4. Create a pull request with the version bump
5. After merge, maintainers will create a release tag

## Questions?

If you have questions about contributing, feel free to open an issue or reach out to the maintainers.

Thank you for contributing!
