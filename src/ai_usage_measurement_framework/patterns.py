# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the MIT License

"""AI detection patterns for commit message analysis."""

import re
from typing import Optional

# AI-related patterns to detect in commit messages
AI_COMMIT_PATTERNS = [
    # GitHub Copilot patterns
    r"copilot",
    r"github\s*copilot",
    r"co-authored-by:.*copilot",
    r"generated\s*by\s*copilot",
    
    # Windsurf/Codeium patterns
    r"windsurf",
    r"codeium",
    r"cascade",
    
    # General AI patterns
    r"ai[\s-]*generated",
    r"ai[\s-]*assisted",
    r"auto[\s-]*generated",
    r"machine[\s-]*generated",
    r"llm[\s-]*generated",
    r"gpt[\s-]*generated",
    r"claude",
    r"chatgpt",
    r"openai",
    r"anthropic",
    
    # Common AI tool signatures
    r"devin",
    r"cursor",
    r"tabnine",
    r"kite",
    r"codex",
    r"amazon\s*q",
    r"cody",
    
    # AI-assisted commit message patterns
    r"refactor.*ai",
    r"fix.*suggested\s*by",
    r"implement.*generated",
]

# Tool-specific patterns with weights for confidence scoring
TOOL_PATTERNS: dict[str, dict] = {
    "GitHub Copilot": {
        "patterns": [r"copilot", r"github\s*copilot", r"co-authored-by:.*copilot"],
        "weight": 0.9,
    },
    "Windsurf": {
        "patterns": [r"windsurf"],
        "weight": 0.9,
    },
    "Codeium": {
        "patterns": [r"codeium"],
        "weight": 0.9,
    },
    "Cascade": {
        "patterns": [r"cascade"],
        "weight": 0.7,
    },
    "Cursor": {
        "patterns": [r"cursor"],
        "weight": 0.8,
    },
    "ChatGPT": {
        "patterns": [r"chatgpt", r"gpt-4", r"gpt-3"],
        "weight": 0.85,
    },
    "Claude": {
        "patterns": [r"claude", r"anthropic"],
        "weight": 0.85,
    },
    "Devin": {
        "patterns": [r"devin"],
        "weight": 0.9,
    },
    "Amazon Q": {
        "patterns": [r"amazon\s*q"],
        "weight": 0.9,
    },
    "Tabnine": {
        "patterns": [r"tabnine"],
        "weight": 0.9,
    },
    "Cody": {
        "patterns": [r"cody"],
        "weight": 0.8,
    },
}

# Generic AI patterns with lower confidence
GENERIC_AI_PATTERNS: dict[str, dict] = {
    "ai-generated": {
        "patterns": [r"ai[\s-]*generated"],
        "weight": 0.5,
    },
    "ai-assisted": {
        "patterns": [r"ai[\s-]*assisted"],
        "weight": 0.5,
    },
    "auto-generated": {
        "patterns": [r"auto[\s-]*generated"],
        "weight": 0.3,
    },
    "machine-generated": {
        "patterns": [r"machine[\s-]*generated"],
        "weight": 0.4,
    },
    "llm-generated": {
        "patterns": [r"llm[\s-]*generated"],
        "weight": 0.6,
    },
}


def detect_ai_patterns(text: str) -> list[str]:
    """Detect AI-related patterns in text.
    
    Args:
        text: The text to analyze (typically a commit message)
        
    Returns:
        List of matched pattern strings
    """
    text_lower = text.lower()
    detected = []
    for pattern in AI_COMMIT_PATTERNS:
        if re.search(pattern, text_lower):
            detected.append(pattern)
    return detected


def extract_ai_tools(text: str) -> list[str]:
    """Extract specific AI tool names from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        List of detected tool names
    """
    text_lower = text.lower()
    tools = []
    for tool_name, config in TOOL_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, text_lower):
                if tool_name not in tools:
                    tools.append(tool_name)
                break
    return tools


def calculate_confidence_score(
    patterns_matched: list[str],
    tools_detected: list[str],
    has_agents_file: bool = False,
    lines_added: int = 0,
    lines_deleted: int = 0,
) -> tuple[float, str]:
    """Calculate confidence score for AI detection.
    
    Args:
        patterns_matched: List of matched patterns
        tools_detected: List of detected tool names
        has_agents_file: Whether the repo has an Agents.md file
        lines_added: Number of lines added in the commit
        lines_deleted: Number of lines deleted in the commit
        
    Returns:
        Tuple of (confidence_score, confidence_level)
    """
    if not patterns_matched:
        return 0.0, "none"
    
    score = 0.0
    
    # Tool-specific patterns have higher weight
    for tool in tools_detected:
        if tool in TOOL_PATTERNS:
            score += TOOL_PATTERNS[tool]["weight"] * 0.5
    
    # Generic patterns add lower weight
    for pattern in patterns_matched:
        for generic_name, config in GENERIC_AI_PATTERNS.items():
            for p in config["patterns"]:
                if re.search(p, pattern):
                    score += config["weight"] * 0.3
                    break
    
    # Bonus for having Agents.md file
    if has_agents_file:
        score += 0.1
    
    # Large additions with few deletions might indicate AI generation
    if lines_added > 100 and lines_deleted < 10:
        score += 0.05
    
    # Cap at 1.0
    score = min(score, 1.0)
    
    # Determine confidence level
    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    elif score > 0:
        level = "low"
    else:
        level = "none"
    
    return score, level
