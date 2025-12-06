# AI Usage Measurement Framework

Measure and analyze AI-assisted development in git repositories. Track usage of GitHub Copilot, Windsurf, Cursor, ChatGPT, Claude, and other AI coding tools by analyzing commit history and Agents.md files.

## Demo

Watch the demo video to see the AI Usage Measurement Framework in action:

<video src="https://github.com/user-attachments/assets/de4ea3b2-fb20-43bc-85c4-54c006768598"></video>

*Demo video file is included in the package as `demo.mp4`*


**Demo highlights using [github/awesome-copilot](https://github.com/github/awesome-copilot):**
- 377 total commits analyzed
- 86 AI-assisted commits detected (22.81%)
- 3 AI tools identified: GitHub Copilot, ChatGPT, Claude
- 159 contributors tracked

The demo shows:
- Single repository analysis with metrics dashboard
- Interactive charts (pie charts, bar charts, timeline)
- Tab navigation (Overview, Timeline, Authors, AI Commits, Agents.md Files)
- GitHub Team mode for multi-repo analysis
- Date filtering with calendar pickers

## Why Use This Framework?

Organizations adopting AI coding tools like GitHub Copilot, Windsurf, and Cursor need visibility into how these tools are being used across their development teams. This framework provides:

- **ROI Measurement**: Quantify AI tool adoption to justify investments
- **Team Insights**: Identify which teams and developers are leveraging AI assistance
- **Trend Analysis**: Track AI usage growth over time
- **Privacy-Friendly**: Analyzes local git data without sending telemetry to external services
- **Open Source**: MIT licensed, fully customizable for your organization's needs

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Web Application](#web-application)
- [Configuration](#configuration)
- [API Usage](#api-usage)
- [Detection Patterns](#detection-patterns)
- [Development](#development)
- [Task Automation](#task-automation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Commit Analysis**: Detect AI-assisted commits by analyzing commit messages for tool signatures and patterns
- **Multi-Tool Detection**: Supports GitHub Copilot, Windsurf, Codeium, Cursor, ChatGPT, Claude, Devin, Amazon Q, Tabnine, and more
- **Agents.md Parsing**: Extract AI tool usage information from Agents.md documentation files
- **GitHub Teams Integration**: Analyze all repositories under a GitHub team or organization
- **Confidence Scoring**: Assign confidence levels (high/medium/low) to AI detections
- **Timeline Analysis**: Track AI usage trends over time
- **Export Options**: Export results to JSON or CSV for further analysis
- **Web Dashboard**: Interactive Streamlit web application for visualization
- **CLI Tool**: Command-line interface for automation and scripting

## Prerequisites

Before setting up the project, ensure you have the following installed:

### Required

- **Python 3.11+**: Download from [python.org](https://www.python.org/downloads/)
- **Git**: Download from [git-scm.com](https://git-scm.com/downloads)
- **uv**: Fast Python package manager

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv

# Verify installation
uv --version
```

### Optional

- **Task**: Task runner for automation (recommended)
  ```bash
  # macOS
  brew install go-task

  # Linux
  sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

  # Windows (Scoop)
  scoop install task
  ```

- **GitHub Personal Access Token**: Required for analyzing private repositories and GitHub teams
  - Go to GitHub Settings > Developer settings > Personal access tokens
  - Create a token with `repo` and `read:org` scopes

## Local Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/ai-usage-measurement-framework/ai-usage-measurement-framework.git
cd ai-usage-measurement-framework
```

### Step 2: Install Dependencies

Using uv (recommended):

```bash
# Install all dependencies including dev tools
uv sync

# Verify installation
uv run ai-usage-measurement-framework --version
```

Using Task (if installed):

```bash
# One-command setup
task setup
```

Using pip (alternative):

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install package
pip install -e ".[dev]"
```

### Step 3: Configure Environment (Optional)

Create a `.env` file for GitHub token:

```bash
# Create .env file
echo "GITHUB_TOKEN=your_github_token_here" > .env
```

Or export directly:

```bash
export GITHUB_TOKEN=your_github_token_here
```

### Step 4: Verify Installation

```bash
# Using Task (if installed)
task check

# Or manually
uv run ai-usage-measurement-framework --help
uv run pytest
uv run ruff check .
```

## Quick Start

### Analyze a Local Repository

```bash
# Basic analysis
uv run ai-usage-measurement-framework analyze /path/to/your/repo

# With date filters
uv run ai-usage-measurement-framework analyze /path/to/repo --since 2024-01-01 --until 2024-12-31

# Specific branch
uv run ai-usage-measurement-framework analyze /path/to/repo --branch main

# Export to JSON
uv run ai-usage-measurement-framework analyze /path/to/repo --output results.json

# Export to CSV
uv run ai-usage-measurement-framework analyze /path/to/repo --output results.csv
```

### Analyze a GitHub Repository

```bash
# Public repository
uv run ai-usage-measurement-framework analyze https://github.com/owner/repo

# Private repository (requires token)
uv run ai-usage-measurement-framework analyze https://github.com/owner/private-repo --token $GITHUB_TOKEN
```

### Analyze a GitHub Team

```bash
# List teams in an organization
uv run ai-usage-measurement-framework teams my-org --token $GITHUB_TOKEN

# Analyze all repos for a team
uv run ai-usage-measurement-framework team my-org my-team --token $GITHUB_TOKEN

# Export team analysis
uv run ai-usage-measurement-framework team my-org my-team --token $GITHUB_TOKEN --output team-report.json
```

### Launch Web Dashboard

```bash
# Using CLI
uv run ai-usage-measurement-framework webapp

# Or directly with Streamlit
uv run streamlit run src/ai_usage_measurement_framework/webapp/app.py

# Using Task
task webapp
```

## CLI Commands

### `ai-usage-measurement-framework analyze`

Analyze a single git repository.

```bash
uv run ai-usage-measurement-framework analyze REPO [OPTIONS]

Arguments:
  REPO  Repository path or URL to analyze

Options:
  -b, --branch TEXT   Branch to analyze
  -s, --since TEXT    Analyze commits since date (YYYY-MM-DD)
  -u, --until TEXT    Analyze commits until date (YYYY-MM-DD)
  -t, --token TEXT    GitHub token for private repos (or set GITHUB_TOKEN env var)
  -o, --output TEXT   Output file path (JSON or CSV)
  -f, --format TEXT   Output format: table, json, csv (default: table)
```

### `ai-usage-measurement-framework teams`

List all teams in a GitHub organization.

```bash
uv run ai-usage-measurement-framework teams ORG [OPTIONS]

Arguments:
  ORG  GitHub organization name

Options:
  -t, --token TEXT  GitHub token (required, or set GITHUB_TOKEN env var)
```

### `ai-usage-measurement-framework team`

Analyze all repositories for a GitHub team.

```bash
uv run ai-usage-measurement-framework team ORG TEAM_SLUG [OPTIONS]

Arguments:
  ORG        GitHub organization name
  TEAM_SLUG  Team slug (URL-friendly name)

Options:
  -b, --branch TEXT   Branch to analyze
  -s, --since TEXT    Analyze commits since date (YYYY-MM-DD)
  -u, --until TEXT    Analyze commits until date (YYYY-MM-DD)
  -t, --token TEXT    GitHub token (required, or set GITHUB_TOKEN env var)
  -o, --output TEXT   Output file path
```

### `ai-usage-measurement-framework webapp`

Launch the Streamlit web application.

```bash
uv run ai-usage-measurement-framework webapp
```

## Web Application

The web application provides an interactive dashboard for analyzing AI usage:

### Features

1. **Single Repository Mode**: Enter a local path or GitHub URL to analyze
2. **GitHub Team Mode**: Select an organization and team to analyze all repositories
3. **Date Filtering**: Filter commits by date range with calendar pickers
4. **Visualizations**: Pie charts, bar charts, and timeline views
5. **Export**: Download results as JSON or CSV

### Running the Web App

```bash
# Default port (8501)
uv run streamlit run src/ai_usage_measurement_framework/webapp/app.py

# Custom port
uv run streamlit run src/ai_usage_measurement_framework/webapp/app.py --server.port 8080

# Allow external access
uv run streamlit run src/ai_usage_measurement_framework/webapp/app.py --server.address 0.0.0.0
```

Access the app at: http://localhost:8501

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token | For private repos/teams |

### Custom Patterns

You can extend the detection patterns by modifying `src/ai_usage_measurement_framework/patterns.py`:

```python
# Add new tool patterns
TOOL_PATTERNS["New Tool"] = {
    "patterns": [r"new-tool", r"newtool"],
    "weight": 0.9,
}

# Add generic patterns
AI_COMMIT_PATTERNS.append(r"new-ai-pattern")
```

## API Usage

### Analyze a Single Repository

```python
from ai_usage_measurement_framework.analyzers import GitAnalyzer

# Analyze a local repository
with GitAnalyzer("/path/to/repo") as analyzer:
    results = analyzer.analyze()
    print(f"Total commits: {results.total_commits}")
    print(f"AI-assisted commits: {results.ai_assisted_commits}")
    print(f"AI percentage: {results.ai_percentage}%")
    print(f"Tools detected: {results.tools_detected}")

# Analyze with filters
from datetime import datetime
with GitAnalyzer(
    repo_path="https://github.com/owner/repo",
    branch="main",
    since_date=datetime(2024, 1, 1),
    until_date=datetime(2024, 12, 31),
    github_token="your-token"
) as analyzer:
    results = analyzer.analyze()
```

### Analyze a GitHub Team

```python
from ai_usage_measurement_framework.analyzers import GitHubAnalyzer

# Initialize analyzer
gh = GitHubAnalyzer(token="your-token", org="your-org")

# List teams
teams = gh.get_teams()
for team in teams:
    print(f"{team['name']} ({team['slug']})")

# Analyze a team
results = gh.analyze_team("team-slug")
print(f"Total repos: {results.total_repos}")
print(f"Total commits: {results.total_commits}")
print(f"AI commits: {results.total_ai_commits}")
```

### Export Results

```python
from ai_usage_measurement_framework.exporters import JSONExporter, CSVExporter

# Export to JSON
JSONExporter.export(results, "output.json")

# Export to CSV
CSVExporter.export_summary(results, "summary.csv")
CSVExporter.export_detections(results, "detections.csv")
CSVExporter.export_authors(results, "authors.csv")
CSVExporter.export_timeline(results, "timeline.csv")
```

## Detection Patterns

AI Usage Measurement Framework detects the following patterns in commit messages:

| Tool | Patterns | Confidence Weight |
|------|----------|-------------------|
| GitHub Copilot | `copilot`, `github copilot`, `co-authored-by:.*copilot` | 0.9 |
| Windsurf | `windsurf` | 0.9 |
| Codeium | `codeium` | 0.9 |
| Cursor | `cursor` | 0.8 |
| ChatGPT | `chatgpt`, `gpt-4`, `gpt-3` | 0.85 |
| Claude | `claude`, `anthropic` | 0.85 |
| Devin | `devin` | 0.9 |
| Amazon Q | `amazon q` | 0.9 |
| Tabnine | `tabnine` | 0.9 |
| Cody | `cody` | 0.8 |

Generic patterns like `ai-generated`, `ai-assisted`, and `llm-generated` are also detected with lower confidence (0.3-0.6).

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ai-usage-measurement-framework/ai-usage-measurement-framework.git
cd ai-usage-measurement-framework

# Install with dev dependencies
uv sync

# Or using Task
task setup
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ai_usage_measurement_framework

# Run specific test file
uv run pytest tests/test_analyzer.py

# Or using Task
task test
```

### Linting and Type Checking

```bash
# Run linter
uv run ruff check .

# Fix linting issues
uv run ruff check . --fix

# Run type checker
uv run mypy src/

# Or using Task
task lint
task typecheck
```

### Project Structure

```
ai-usage-measurement-framework/
├── src/
│   └── ai_usage_measurement_framework/
│       ├── __init__.py          # Package exports
│       ├── models.py            # Pydantic data models
│       ├── patterns.py          # AI detection patterns
│       ├── cli.py               # Typer CLI application
│       ├── analyzers/
│       │   ├── __init__.py
│       │   ├── git_analyzer.py  # Git repository analyzer
│       │   └── github_analyzer.py # GitHub API integration
│       ├── exporters/
│       │   ├── __init__.py
│       │   ├── json_exporter.py # JSON export
│       │   └── csv_exporter.py  # CSV export
│       └── webapp/
│           └── app.py           # Streamlit web application
├── tests/                       # Test suite
├── pyproject.toml              # Project configuration (uv/pip)
├── Taskfile.yaml               # Task automation
├── LICENSE                     # MIT license
├── README.md                   # This file
└── CONTRIBUTING.md             # Contribution guidelines
```

## Task Automation

This project uses [Task](https://taskfile.dev/) for automation. Install Task and run `task --list` to see available commands.

### Available Tasks

| Task | Description |
|------|-------------|
| `task setup` | Install all dependencies |
| `task test` | Run test suite |
| `task lint` | Run linter (ruff) |
| `task lint:fix` | Fix linting issues |
| `task typecheck` | Run type checker (mypy) |
| `task check` | Run all checks (lint + typecheck + test) |
| `task webapp` | Launch Streamlit web app |
| `task analyze` | Analyze a repository (interactive) |
| `task clean` | Clean build artifacts |
| `task build` | Build package |

### Example Usage

```bash
# Full setup and verification
task setup
task check

# Development workflow
task lint:fix
task test
task webapp
```

## Troubleshooting

### Common Issues

**Issue: `uv: command not found`**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your terminal or run:
source ~/.bashrc  # or ~/.zshrc
```

**Issue: `task: command not found`**
```bash
# Install Task (macOS)
brew install go-task

# Install Task (Linux)
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
```

**Issue: `Permission denied` when cloning private repos**
```bash
# Ensure GITHUB_TOKEN is set
export GITHUB_TOKEN=your_token_here
# Or pass it directly
uv run ai-usage-measurement-framework analyze https://github.com/org/private-repo --token $GITHUB_TOKEN
```

**Issue: `Invalid git repository`**
```bash
# Ensure the path is correct and contains a .git directory
ls -la /path/to/repo/.git
```

**Issue: Streamlit app not loading**
```bash
# Check if port is in use
lsof -i :8501
# Use a different port
uv run streamlit run src/ai_usage_measurement_framework/webapp/app.py --server.port 8080
```

**Issue: `ModuleNotFoundError`**
```bash
# Reinstall dependencies
uv sync --reinstall
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project was created to help organizations measure and understand AI tool adoption in their development workflows. It provides a privacy-friendly approach by analyzing local data without sending telemetry to external services.
