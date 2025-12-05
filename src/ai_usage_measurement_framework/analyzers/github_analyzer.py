# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the Apache License, Version 2.0

"""GitHub API analyzer for team and organization analysis."""

from datetime import datetime
from typing import Optional

import requests

from ai_usage_measurement_framework.analyzers.git_analyzer import GitAnalyzer
from ai_usage_measurement_framework.models import MultiRepoAnalysis, RepoAnalysis


class GitHubAnalyzer:
    """Analyzer for GitHub organizations and teams."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: str, org: Optional[str] = None):
        """Initialize the GitHub analyzer.
        
        Args:
            token: GitHub personal access token
            org: GitHub organization name
        """
        self.token = token
        self.org = org
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, endpoint: str, params: Optional[dict] = None) -> dict | list:
        """Make a request to the GitHub API."""
        url = f"{self.API_BASE}{endpoint}"
        resp = requests.get(url, headers=self._headers, params=params or {})
        
        if resp.status_code == 401:
            raise ValueError("Invalid GitHub token. Please check your token and try again.")
        if resp.status_code == 403:
            raise ValueError("Access forbidden. Token may lack required scopes or org access.")
        if resp.status_code == 404:
            raise ValueError(f"Resource not found: {endpoint}")
        if resp.status_code != 200:
            raise ValueError(f"GitHub API error: {resp.status_code} - {resp.text}")
        
        return resp.json()

    def _paginate(self, endpoint: str, params: Optional[dict] = None) -> list:
        """Paginate through all results from an endpoint."""
        params = params or {}
        params["per_page"] = 100
        page = 1
        results = []
        
        while True:
            params["page"] = page
            data = self._request(endpoint, params)
            if not data:
                break
            results.extend(data)
            if len(data) < 100:
                break
            page += 1
        
        return results

    def get_teams(self) -> list[dict]:
        """Get all teams in the organization.
        
        Returns:
            List of team dictionaries with name, slug, and id
        """
        if not self.org:
            raise ValueError("Organization name is required to list teams")
        
        teams = self._paginate(f"/orgs/{self.org}/teams")
        return [
            {"name": t["name"], "slug": t["slug"], "id": t["id"]}
            for t in teams
        ]

    def get_team_repos(self, team_slug: str) -> list[dict]:
        """Get all repositories for a team.
        
        Args:
            team_slug: The team's slug (URL-friendly name)
            
        Returns:
            List of repository dictionaries
        """
        if not self.org:
            raise ValueError("Organization name is required to list team repos")
        
        repos = self._paginate(f"/orgs/{self.org}/teams/{team_slug}/repos")
        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "clone_url": r["clone_url"],
                "private": r["private"],
                "default_branch": r.get("default_branch", "main"),
            }
            for r in repos
        ]

    def get_org_repos(self) -> list[dict]:
        """Get all repositories in the organization.
        
        Returns:
            List of repository dictionaries
        """
        if not self.org:
            raise ValueError("Organization name is required to list org repos")
        
        repos = self._paginate(f"/orgs/{self.org}/repos")
        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "clone_url": r["clone_url"],
                "private": r["private"],
                "default_branch": r.get("default_branch", "main"),
            }
            for r in repos
        ]

    def analyze_repos(
        self,
        repos: list[dict],
        branch: Optional[str] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        progress_callback: Optional[callable] = None,
    ) -> MultiRepoAnalysis:
        """Analyze multiple repositories.
        
        Args:
            repos: List of repository dictionaries (from get_team_repos or get_org_repos)
            branch: Branch to analyze (default: repository default)
            since_date: Only analyze commits after this date
            until_date: Only analyze commits before this date
            progress_callback: Optional callback(current, total, repo_name) for progress updates
            
        Returns:
            MultiRepoAnalysis with aggregated results
        """
        results: list[RepoAnalysis] = []
        total = len(repos)
        
        for i, repo in enumerate(repos):
            if progress_callback:
                progress_callback(i, total, repo["name"])
            
            try:
                with GitAnalyzer(
                    repo_path=repo["clone_url"],
                    branch=branch or repo.get("default_branch"),
                    since_date=since_date,
                    until_date=until_date,
                    github_token=self.token,
                ) as analyzer:
                    analysis = analyzer.analyze()
                    results.append(analysis)
            except Exception as e:
                # Log error but continue with other repos
                print(f"Error analyzing {repo['name']}: {e}")
                continue
        
        if progress_callback:
            progress_callback(total, total, "Complete")
        
        # Aggregate results
        all_tools = set()
        all_authors = set()
        ai_authors = set()
        
        for r in results:
            all_tools.update(r.tools_detected)
            for author in r.author_stats:
                all_authors.add(author.name)
                if author.ai_assisted_commits > 0:
                    ai_authors.add(author.name)
        
        total_commits = sum(r.total_commits for r in results)
        total_ai_commits = sum(r.ai_assisted_commits for r in results)
        
        return MultiRepoAnalysis(
            analyzed_at=datetime.now(),
            repos=results,
            total_repos=len(results),
            total_commits=total_commits,
            total_ai_commits=total_ai_commits,
            overall_ai_percentage=round(total_ai_commits / total_commits * 100, 2) if total_commits > 0 else 0,
            all_tools_detected=list(all_tools),
            all_authors=len(all_authors),
            ai_authors=len(ai_authors),
        )

    def analyze_team(
        self,
        team_slug: str,
        branch: Optional[str] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        progress_callback: Optional[callable] = None,
    ) -> MultiRepoAnalysis:
        """Analyze all repositories for a team.
        
        Args:
            team_slug: The team's slug
            branch: Branch to analyze
            since_date: Only analyze commits after this date
            until_date: Only analyze commits before this date
            progress_callback: Optional progress callback
            
        Returns:
            MultiRepoAnalysis with aggregated results
        """
        repos = self.get_team_repos(team_slug)
        return self.analyze_repos(repos, branch, since_date, until_date, progress_callback)

    def analyze_org(
        self,
        branch: Optional[str] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        progress_callback: Optional[callable] = None,
    ) -> MultiRepoAnalysis:
        """Analyze all repositories in the organization.
        
        Args:
            branch: Branch to analyze
            since_date: Only analyze commits after this date
            until_date: Only analyze commits before this date
            progress_callback: Optional progress callback
            
        Returns:
            MultiRepoAnalysis with aggregated results
        """
        repos = self.get_org_repos()
        return self.analyze_repos(repos, branch, since_date, until_date, progress_callback)
