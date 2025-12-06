# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the MIT License

"""Git repository analyzer for AI usage detection."""

import os
import re
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from ai_usage_measurement_framework.models import (
    AgentsFileInfo,
    AuthorStats,
    ConfidenceLevel,
    Detection,
    RepoAnalysis,
    Signal,
    TimelineEntry,
    ToolStats,
)
from ai_usage_measurement_framework.patterns import (
    AI_COMMIT_PATTERNS,
    TOOL_PATTERNS,
    calculate_confidence_score,
    detect_ai_patterns,
    extract_ai_tools,
)


class GitAnalyzer:
    """Analyzer for git repositories to detect AI-assisted development."""

    def __init__(
        self,
        repo_path: str,
        branch: Optional[str] = None,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        github_token: Optional[str] = None,
    ):
        """Initialize the analyzer.
        
        Args:
            repo_path: Local path or remote URL to the repository
            branch: Branch to analyze (default: repository default)
            since_date: Only analyze commits after this date
            until_date: Only analyze commits before this date
            github_token: GitHub token for private repositories
        """
        self.repo_path = repo_path
        self.branch = branch
        self.since_date = since_date
        self.until_date = until_date
        self.github_token = github_token
        self._temp_dir: Optional[str] = None
        self._repo: Optional[Repo] = None

    def _is_remote_url(self, path: str) -> bool:
        """Check if the path is a remote URL."""
        return path.startswith(("http://", "https://", "git@", "ssh://"))

    def _clone_repo(self, url: str) -> str:
        """Clone a remote repository to a temporary directory."""
        self._temp_dir = tempfile.mkdtemp(prefix="ai-usage-tracker-")
        
        # Add token to URL for private repos
        if self.github_token and "github.com" in url:
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https"):
                url = f"{parsed.scheme}://{self.github_token}@{parsed.netloc}{parsed.path}"
        
        try:
            Repo.clone_from(url, self._temp_dir, depth=None)
            return self._temp_dir
        except GitCommandError as e:
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
            raise ValueError(f"Failed to clone repository: {e}")

    def _open_repo(self) -> Repo:
        """Open the repository."""
        if self._repo is not None:
            return self._repo

        if self._is_remote_url(self.repo_path):
            local_path = self._clone_repo(self.repo_path)
        else:
            local_path = self.repo_path

        try:
            self._repo = Repo(local_path)
            return self._repo
        except InvalidGitRepositoryError:
            raise ValueError(f"Invalid git repository: {local_path}")

    def _get_repo_name(self) -> str:
        """Extract repository name from path or URL."""
        if self._is_remote_url(self.repo_path):
            # Extract from URL
            path = urlparse(self.repo_path).path
            name = path.rstrip("/").split("/")[-1]
            return name.replace(".git", "")
        else:
            return Path(self.repo_path).name

    def _find_agents_files(self, repo: Repo) -> list[AgentsFileInfo]:
        """Find and parse Agents.md files in the repository."""
        agents_files = []
        repo_dir = repo.working_dir

        for root, dirs, files in os.walk(repo_dir):
            # Skip .git directory
            if ".git" in root:
                continue
            
            for filename in files:
                if filename.lower() in ("agents.md", ".agents.md", "agent.md"):
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, repo_dir)
                    
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Extract tool mentions
                        tools = extract_ai_tools(content)
                        
                        agents_files.append(AgentsFileInfo(
                            path=rel_path,
                            content=content[:5000],  # Limit content size
                            tools_mentioned=tools,
                        ))
                    except (IOError, UnicodeDecodeError):
                        continue

        return agents_files

    def analyze(self) -> RepoAnalysis:
        """Analyze the repository for AI usage.
        
        Returns:
            RepoAnalysis object with all analysis results
        """
        repo = self._open_repo()
        repo_name = self._get_repo_name()
        
        # Determine branch
        if self.branch:
            try:
                repo.git.checkout(self.branch)
            except GitCommandError:
                pass  # Branch might not exist, use current
        
        current_branch = repo.active_branch.name if not repo.head.is_detached else "HEAD"
        
        # Find Agents.md files
        agents_files = self._find_agents_files(repo)
        has_agents_file = len(agents_files) > 0
        
        # Analyze commits
        detections: list[Detection] = []
        commits_by_author: dict[str, int] = defaultdict(int)
        ai_commits_by_author: dict[str, int] = defaultdict(int)
        tools_by_author: dict[str, set] = defaultdict(set)
        timeline: dict[str, dict] = defaultdict(lambda: {"total": 0, "ai": 0, "tools": defaultdict(int)})
        all_tools: set[str] = set()
        tool_commits: dict[str, list] = defaultdict(list)
        
        # Build commit iterator with date filters
        commit_kwargs = {}
        if self.since_date:
            commit_kwargs["after"] = self.since_date.strftime("%Y-%m-%d")
        if self.until_date:
            commit_kwargs["before"] = self.until_date.strftime("%Y-%m-%d")
        
        total_commits = 0
        ai_commits = 0
        high_conf = 0
        medium_conf = 0
        low_conf = 0
        total_confidence = 0.0
        
        for commit in repo.iter_commits(**commit_kwargs):
            total_commits += 1
            author_name = commit.author.name
            author_email = commit.author.email
            commit_date = datetime.fromtimestamp(commit.committed_date)
            month_key = commit_date.strftime("%Y-%m")
            
            commits_by_author[author_name] += 1
            timeline[month_key]["total"] += 1
            
            # Check for AI patterns
            message = commit.message
            patterns_matched = detect_ai_patterns(message)
            tools_detected = extract_ai_tools(message)
            
            if patterns_matched or tools_detected:
                ai_commits += 1
                ai_commits_by_author[author_name] += 1
                timeline[month_key]["ai"] += 1
                
                # Calculate confidence
                try:
                    stats = commit.stats.total
                    lines_added = stats.get("insertions", 0)
                    lines_deleted = stats.get("deletions", 0)
                    files_changed = stats.get("files", 0)
                except Exception:
                    lines_added = 0
                    lines_deleted = 0
                    files_changed = 0
                
                confidence_score, confidence_level = calculate_confidence_score(
                    patterns_matched,
                    tools_detected,
                    has_agents_file,
                    lines_added,
                    lines_deleted,
                )
                
                total_confidence += confidence_score
                if confidence_level == "high":
                    high_conf += 1
                elif confidence_level == "medium":
                    medium_conf += 1
                elif confidence_level == "low":
                    low_conf += 1
                
                # Track tools
                for tool in tools_detected:
                    all_tools.add(tool)
                    tools_by_author[author_name].add(tool)
                    timeline[month_key]["tools"][tool] += 1
                    tool_commits[tool].append(commit_date)
                
                # Create detection record
                signals = [
                    Signal(
                        name="pattern_match",
                        value=min(len(patterns_matched) * 0.3, 1.0),
                        weight=1.0,
                        reason=f"Matched patterns: {', '.join(patterns_matched[:3])}",
                        source="commit_message",
                    )
                ]
                
                if tools_detected:
                    signals.append(Signal(
                        name="tool_detected",
                        value=0.8,
                        weight=1.0,
                        reason=f"Tools detected: {', '.join(tools_detected)}",
                        source="commit_message",
                    ))
                
                detection = Detection(
                    commit_hash=commit.hexsha,
                    author=author_name,
                    author_email=author_email,
                    date=commit_date,
                    message=message[:500],
                    tools_detected=tools_detected,
                    patterns_matched=patterns_matched,
                    signals=signals,
                    confidence_score=confidence_score,
                    confidence_level=ConfidenceLevel(confidence_level),
                    files_changed=files_changed,
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                )
                detections.append(detection)
        
        # Build author stats
        author_stats = []
        for author, total in commits_by_author.items():
            ai_count = ai_commits_by_author.get(author, 0)
            author_stats.append(AuthorStats(
                name=author,
                email="",  # Would need to track this separately
                total_commits=total,
                ai_assisted_commits=ai_count,
                ai_percentage=round(ai_count / total * 100, 2) if total > 0 else 0,
                tools_used=list(tools_by_author.get(author, set())),
            ))
        
        # Build tool stats
        tool_stats = []
        for tool in all_tools:
            commits = tool_commits[tool]
            authors_using = sum(1 for a, tools in tools_by_author.items() if tool in tools)
            tool_stats.append(ToolStats(
                name=tool,
                commit_count=len(commits),
                author_count=authors_using,
                first_seen=min(commits) if commits else None,
                last_seen=max(commits) if commits else None,
            ))
        
        # Build timeline entries
        timeline_entries = []
        for month, data in sorted(timeline.items()):
            timeline_entries.append(TimelineEntry(
                date=month,
                total_commits=data["total"],
                ai_commits=data["ai"],
                ai_percentage=round(data["ai"] / data["total"] * 100, 2) if data["total"] > 0 else 0,
                tools=dict(data["tools"]),
            ))
        
        # Calculate averages
        ai_percentage = round(ai_commits / total_commits * 100, 2) if total_commits > 0 else 0
        avg_confidence = total_confidence / ai_commits if ai_commits > 0 else 0
        
        return RepoAnalysis(
            repo_name=repo_name,
            repo_path=self.repo_path,
            branch=current_branch,
            analyzed_at=datetime.now(),
            since_date=self.since_date,
            until_date=self.until_date,
            total_commits=total_commits,
            ai_assisted_commits=ai_commits,
            ai_percentage=ai_percentage,
            total_authors=len(commits_by_author),
            ai_authors=len(ai_commits_by_author),
            tools_detected=list(all_tools),
            detections=detections,
            agents_files=agents_files,
            author_stats=author_stats,
            tool_stats=tool_stats,
            timeline=timeline_entries,
            high_confidence_count=high_conf,
            medium_confidence_count=medium_conf,
            low_confidence_count=low_conf,
            average_confidence=round(avg_confidence, 3),
        )

    def cleanup(self):
        """Clean up temporary files."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
