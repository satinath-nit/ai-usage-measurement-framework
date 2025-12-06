# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the MIT License

"""Data models for AI Usage Measurement Framework."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for AI detection."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class Signal(BaseModel):
    """A signal contributing to AI detection confidence."""

    name: str
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0)
    reason: str
    source: str  # Which analyzer produced this signal


class Detection(BaseModel):
    """A single AI usage detection."""

    commit_hash: str
    author: str
    author_email: str
    date: datetime
    message: str
    tools_detected: list[str] = Field(default_factory=list)
    patterns_matched: list[str] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.NONE
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0


class AgentsFileInfo(BaseModel):
    """Information extracted from an Agents.md file."""

    path: str
    content: str
    tools_mentioned: list[str] = Field(default_factory=list)
    last_modified: Optional[datetime] = None


class AuthorStats(BaseModel):
    """Statistics for a single author."""

    name: str
    email: str
    total_commits: int = 0
    ai_assisted_commits: int = 0
    ai_percentage: float = 0.0
    tools_used: list[str] = Field(default_factory=list)
    first_ai_commit: Optional[datetime] = None
    last_ai_commit: Optional[datetime] = None


class ToolStats(BaseModel):
    """Statistics for a single AI tool."""

    name: str
    commit_count: int = 0
    author_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    estimated_cost: Optional[float] = None


class TimelineEntry(BaseModel):
    """A single entry in the timeline."""

    date: str  # YYYY-MM format
    total_commits: int = 0
    ai_commits: int = 0
    ai_percentage: float = 0.0
    tools: dict[str, int] = Field(default_factory=dict)


class RepoAnalysis(BaseModel):
    """Complete analysis results for a repository."""

    repo_name: str
    repo_path: str
    branch: str = "main"
    analyzed_at: datetime = Field(default_factory=datetime.now)
    since_date: Optional[datetime] = None
    until_date: Optional[datetime] = None

    # Summary metrics
    total_commits: int = 0
    ai_assisted_commits: int = 0
    ai_percentage: float = 0.0
    total_authors: int = 0
    ai_authors: int = 0
    tools_detected: list[str] = Field(default_factory=list)

    # Detailed data
    detections: list[Detection] = Field(default_factory=list)
    agents_files: list[AgentsFileInfo] = Field(default_factory=list)
    author_stats: list[AuthorStats] = Field(default_factory=list)
    tool_stats: list[ToolStats] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)

    # Confidence metrics
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    average_confidence: float = 0.0

    # Cost estimation
    estimated_total_cost: Optional[float] = None


class MultiRepoAnalysis(BaseModel):
    """Analysis results across multiple repositories."""

    analyzed_at: datetime = Field(default_factory=datetime.now)
    repos: list[RepoAnalysis] = Field(default_factory=list)

    # Aggregate metrics
    total_repos: int = 0
    total_commits: int = 0
    total_ai_commits: int = 0
    overall_ai_percentage: float = 0.0
    all_tools_detected: list[str] = Field(default_factory=list)
    all_authors: int = 0
    ai_authors: int = 0
