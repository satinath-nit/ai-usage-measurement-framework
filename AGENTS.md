# AGENTS.md

## Commands
- **Setup**: `uv sync` (or `task setup`)
- **Lint**: `uv run ruff check .` (fix: `uv run ruff check . --fix`)
- **Format**: `uv run ruff format .`
- **Typecheck**: `uv run mypy src/`
- **Test**: `uv run pytest` (single test: `uv run pytest tests/test_file.py::test_name -v`)
- **All checks**: `task check` (runs lint, typecheck, test)
- **Run webapp**: `task webapp` (Streamlit on port 8501)

## Architecture
- **src/ai_usage_measurement_framework/**: Main package
  - `analyzers/`: Git and GitHub analysis (`GitAnalyzer`, `GitHubAnalyzer`)
  - `exporters/`: Output formats (CSV, JSON)
  - `webapp/`: Streamlit dashboard (`app.py`)
  - `cli.py`: Typer CLI entry point
  - `models.py`: Pydantic data models
  - `patterns.py`: Regex patterns for AI tool detection

## Code Style
- Python 3.11+, use `uv` for package management
- Imports: stdlib first, then third-party, then local (ruff handles sorting)
- Types: Use Pydantic for models, `Optional` from typing for nullable types
- Line length: 100 chars (ruff config)
- Use absolute imports from `ai_usage_measurement_framework`
