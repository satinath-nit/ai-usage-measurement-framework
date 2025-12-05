# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the Apache License, Version 2.0

"""CSV exporter for analysis results."""

import csv
from pathlib import Path
from typing import Union

from ai_usage_measurement_framework.models import MultiRepoAnalysis, RepoAnalysis


class CSVExporter:
    """Export analysis results to CSV format."""

    @classmethod
    def export_summary(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        output_path: Union[str, Path],
    ) -> Path:
        """Export summary metrics to a CSV file.
        
        Args:
            analysis: The analysis results to export
            output_path: Path to the output file
            
        Returns:
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            if isinstance(analysis, MultiRepoAnalysis):
                writer.writerow([
                    "Repository", "Total Commits", "AI Commits", "AI %",
                    "Authors", "AI Authors", "Tools Detected"
                ])
                for repo in analysis.repos:
                    writer.writerow([
                        repo.repo_name,
                        repo.total_commits,
                        repo.ai_assisted_commits,
                        repo.ai_percentage,
                        repo.total_authors,
                        repo.ai_authors,
                        ", ".join(repo.tools_detected),
                    ])
                # Add totals row
                writer.writerow([
                    "TOTAL",
                    analysis.total_commits,
                    analysis.total_ai_commits,
                    analysis.overall_ai_percentage,
                    analysis.all_authors,
                    analysis.ai_authors,
                    ", ".join(analysis.all_tools_detected),
                ])
            else:
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Repository", analysis.repo_name])
                writer.writerow(["Branch", analysis.branch])
                writer.writerow(["Total Commits", analysis.total_commits])
                writer.writerow(["AI-Assisted Commits", analysis.ai_assisted_commits])
                writer.writerow(["AI Percentage", f"{analysis.ai_percentage}%"])
                writer.writerow(["Total Authors", analysis.total_authors])
                writer.writerow(["AI Authors", analysis.ai_authors])
                writer.writerow(["Tools Detected", ", ".join(analysis.tools_detected)])
                writer.writerow(["High Confidence", analysis.high_confidence_count])
                writer.writerow(["Medium Confidence", analysis.medium_confidence_count])
                writer.writerow(["Low Confidence", analysis.low_confidence_count])
                writer.writerow(["Average Confidence", analysis.average_confidence])
        
        return output_path

    @classmethod
    def export_detections(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        output_path: Union[str, Path],
    ) -> Path:
        """Export individual AI detections to a CSV file.
        
        Args:
            analysis: The analysis results to export
            output_path: Path to the output file
            
        Returns:
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Repository", "Commit Hash", "Author", "Date",
                "Tools Detected", "Confidence", "Confidence Level",
                "Files Changed", "Lines Added", "Lines Deleted", "Message"
            ])
            
            if isinstance(analysis, MultiRepoAnalysis):
                for repo in analysis.repos:
                    for d in repo.detections:
                        writer.writerow([
                            repo.repo_name,
                            d.commit_hash[:8],
                            d.author,
                            d.date.strftime("%Y-%m-%d %H:%M"),
                            ", ".join(d.tools_detected),
                            d.confidence_score,
                            d.confidence_level.value,
                            d.files_changed,
                            d.lines_added,
                            d.lines_deleted,
                            d.message[:100].replace("\n", " "),
                        ])
            else:
                for d in analysis.detections:
                    writer.writerow([
                        analysis.repo_name,
                        d.commit_hash[:8],
                        d.author,
                        d.date.strftime("%Y-%m-%d %H:%M"),
                        ", ".join(d.tools_detected),
                        d.confidence_score,
                        d.confidence_level.value,
                        d.files_changed,
                        d.lines_added,
                        d.lines_deleted,
                        d.message[:100].replace("\n", " "),
                    ])
        
        return output_path

    @classmethod
    def export_authors(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        output_path: Union[str, Path],
    ) -> Path:
        """Export author statistics to a CSV file.
        
        Args:
            analysis: The analysis results to export
            output_path: Path to the output file
            
        Returns:
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Repository", "Author", "Total Commits", "AI Commits",
                "AI %", "Tools Used"
            ])
            
            if isinstance(analysis, MultiRepoAnalysis):
                for repo in analysis.repos:
                    for author in repo.author_stats:
                        writer.writerow([
                            repo.repo_name,
                            author.name,
                            author.total_commits,
                            author.ai_assisted_commits,
                            author.ai_percentage,
                            ", ".join(author.tools_used),
                        ])
            else:
                for author in analysis.author_stats:
                    writer.writerow([
                        analysis.repo_name,
                        author.name,
                        author.total_commits,
                        author.ai_assisted_commits,
                        author.ai_percentage,
                        ", ".join(author.tools_used),
                    ])
        
        return output_path

    @classmethod
    def export_timeline(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        output_path: Union[str, Path],
    ) -> Path:
        """Export timeline data to a CSV file.
        
        Args:
            analysis: The analysis results to export
            output_path: Path to the output file
            
        Returns:
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Repository", "Month", "Total Commits", "AI Commits", "AI %"
            ])
            
            if isinstance(analysis, MultiRepoAnalysis):
                for repo in analysis.repos:
                    for entry in repo.timeline:
                        writer.writerow([
                            repo.repo_name,
                            entry.date,
                            entry.total_commits,
                            entry.ai_commits,
                            entry.ai_percentage,
                        ])
            else:
                for entry in analysis.timeline:
                    writer.writerow([
                        analysis.repo_name,
                        entry.date,
                        entry.total_commits,
                        entry.ai_commits,
                        entry.ai_percentage,
                    ])
        
        return output_path
