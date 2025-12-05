# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the Apache License, Version 2.0

"""Command-line interface for AI Usage Measurement Framework."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_usage_measurement_framework import __version__
from ai_usage_measurement_framework.analyzers.git_analyzer import GitAnalyzer
from ai_usage_measurement_framework.analyzers.github_analyzer import GitHubAnalyzer
from ai_usage_measurement_framework.exporters.csv_exporter import CSVExporter
from ai_usage_measurement_framework.exporters.json_exporter import JSONExporter

app = typer.Typer(
    name="ai-usage-tracker",
    help="Measure and analyze AI-assisted development in git repositories.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"AI Usage Measurement Framework v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit."
    ),
):
    """AI Usage Measurement Framework - Measure AI-assisted development in git repositories."""
    pass


@app.command()
def analyze(
    repo: str = typer.Argument(..., help="Repository path or URL to analyze"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to analyze"),
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Analyze commits since date (YYYY-MM-DD)"),
    until: Optional[str] = typer.Option(None, "--until", "-u", help="Analyze commits until date (YYYY-MM-DD)"),
    token: Optional[str] = typer.Option(None, "--token", "-t", envvar="GITHUB_TOKEN", help="GitHub token for private repos"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (JSON or CSV)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, csv"),
):
    """Analyze a git repository for AI-assisted development."""
    # Parse dates
    since_date = datetime.strptime(since, "%Y-%m-%d") if since else None
    until_date = datetime.strptime(until, "%Y-%m-%d") if until else None
    
    console.print(Panel.fit(
        f"[bold blue]AI Usage Measurement Framework[/bold blue]\n"
        f"Analyzing: {repo}",
        border_style="blue"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing repository...", total=None)
        
        try:
            with GitAnalyzer(
                repo_path=repo,
                branch=branch,
                since_date=since_date,
                until_date=until_date,
                github_token=token,
            ) as analyzer:
                analysis = analyzer.analyze()
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        
        progress.update(task, description="Analysis complete!")
    
    # Display results
    _display_analysis(analysis)
    
    # Export if requested
    if output:
        output_path = Path(output)
        if output_path.suffix == ".json" or format == "json":
            JSONExporter.export(analysis, output_path)
            console.print(f"\n[green]Results exported to:[/green] {output_path}")
        elif output_path.suffix == ".csv" or format == "csv":
            CSVExporter.export_summary(analysis, output_path)
            console.print(f"\n[green]Results exported to:[/green] {output_path}")


@app.command()
def team(
    org: str = typer.Argument(..., help="GitHub organization name"),
    team_slug: str = typer.Argument(..., help="Team slug (URL-friendly name)"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to analyze"),
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Analyze commits since date (YYYY-MM-DD)"),
    until: Optional[str] = typer.Option(None, "--until", "-u", help="Analyze commits until date (YYYY-MM-DD)"),
    token: str = typer.Option(..., "--token", "-t", envvar="GITHUB_TOKEN", help="GitHub token (required)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Analyze all repositories for a GitHub team."""
    since_date = datetime.strptime(since, "%Y-%m-%d") if since else None
    until_date = datetime.strptime(until, "%Y-%m-%d") if until else None
    
    console.print(Panel.fit(
        f"[bold blue]AI Usage Measurement Framework - Team Analysis[/bold blue]\n"
        f"Organization: {org}\n"
        f"Team: {team_slug}",
        border_style="blue"
    ))
    
    try:
        gh = GitHubAnalyzer(token=token, org=org)
        repos = gh.get_team_repos(team_slug)
        console.print(f"Found [bold]{len(repos)}[/bold] repositories")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing repositories...", total=len(repos))
        
        def progress_callback(current, total, repo_name):
            progress.update(task, completed=current, description=f"Analyzing {repo_name}...")
        
        try:
            analysis = gh.analyze_repos(
                repos,
                branch=branch,
                since_date=since_date,
                until_date=until_date,
                progress_callback=progress_callback,
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    
    # Display results
    _display_multi_analysis(analysis)
    
    # Export if requested
    if output:
        output_path = Path(output)
        if output_path.suffix == ".json":
            JSONExporter.export(analysis, output_path)
        else:
            CSVExporter.export_summary(analysis, output_path)
        console.print(f"\n[green]Results exported to:[/green] {output_path}")


@app.command()
def teams(
    org: str = typer.Argument(..., help="GitHub organization name"),
    token: str = typer.Option(..., "--token", "-t", envvar="GITHUB_TOKEN", help="GitHub token (required)"),
):
    """List all teams in a GitHub organization."""
    try:
        gh = GitHubAnalyzer(token=token, org=org)
        teams = gh.get_teams()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    table = Table(title=f"Teams in {org}")
    table.add_column("Name", style="cyan")
    table.add_column("Slug", style="green")
    
    for t in teams:
        table.add_row(t["name"], t["slug"])
    
    console.print(table)


@app.command()
def webapp():
    """Launch the Streamlit web application."""
    import subprocess
    import sys
    
    # Find the streamlit app
    app_path = Path(__file__).parent / "webapp" / "app.py"
    if not app_path.exists():
        console.print("[red]Error:[/red] Streamlit app not found")
        raise typer.Exit(1)
    
    console.print("[bold blue]Launching AI Usage Measurement Framework Web App...[/bold blue]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


def _display_analysis(analysis):
    """Display single repo analysis results."""
    # Summary table
    table = Table(title=f"Analysis Results: {analysis.repo_name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Commits", str(analysis.total_commits))
    table.add_row("AI-Assisted Commits", str(analysis.ai_assisted_commits))
    table.add_row("AI Percentage", f"{analysis.ai_percentage}%")
    table.add_row("Total Authors", str(analysis.total_authors))
    table.add_row("AI Authors", str(analysis.ai_authors))
    table.add_row("Tools Detected", ", ".join(analysis.tools_detected) or "None")
    table.add_row("High Confidence", str(analysis.high_confidence_count))
    table.add_row("Medium Confidence", str(analysis.medium_confidence_count))
    table.add_row("Low Confidence", str(analysis.low_confidence_count))
    
    console.print(table)
    
    # Show sample detections
    if analysis.detections:
        console.print("\n[bold]Sample AI-Assisted Commits:[/bold]")
        for d in analysis.detections[:5]:
            console.print(f"  [dim]{d.commit_hash[:8]}[/dim] - {d.author}: {d.message[:60]}...")
            if d.tools_detected:
                console.print(f"    Tools: [green]{', '.join(d.tools_detected)}[/green]")


def _display_multi_analysis(analysis):
    """Display multi-repo analysis results."""
    # Summary
    console.print(Panel.fit(
        f"[bold]Total Repositories:[/bold] {analysis.total_repos}\n"
        f"[bold]Total Commits:[/bold] {analysis.total_commits}\n"
        f"[bold]AI-Assisted Commits:[/bold] {analysis.total_ai_commits} ({analysis.overall_ai_percentage}%)\n"
        f"[bold]Tools Detected:[/bold] {', '.join(analysis.all_tools_detected) or 'None'}",
        title="Summary",
        border_style="green"
    ))
    
    # Per-repo table
    table = Table(title="Results by Repository")
    table.add_column("Repository", style="cyan")
    table.add_column("Commits", justify="right")
    table.add_column("AI Commits", justify="right")
    table.add_column("AI %", justify="right")
    table.add_column("Tools", style="green")
    
    for repo in analysis.repos:
        table.add_row(
            repo.repo_name,
            str(repo.total_commits),
            str(repo.ai_assisted_commits),
            f"{repo.ai_percentage}%",
            ", ".join(repo.tools_detected) or "-",
        )
    
    console.print(table)


if __name__ == "__main__":
    app()
