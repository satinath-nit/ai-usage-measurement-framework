# Copyright 2024 AI Usage Measurement Framework Contributors
# Licensed under the MIT License

"""JSON exporter for analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Union

from ai_usage_measurement_framework.models import MultiRepoAnalysis, RepoAnalysis


class JSONExporter:
    """Export analysis results to JSON format."""

    @staticmethod
    def _serialize_datetime(obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    @classmethod
    def export(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        output_path: Union[str, Path],
        indent: int = 2,
    ) -> Path:
        """Export analysis results to a JSON file.
        
        Args:
            analysis: The analysis results to export
            output_path: Path to the output file
            indent: JSON indentation level
            
        Returns:
            Path to the created file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = analysis.model_dump()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=cls._serialize_datetime)
        
        return output_path

    @classmethod
    def to_string(
        cls,
        analysis: Union[RepoAnalysis, MultiRepoAnalysis],
        indent: int = 2,
    ) -> str:
        """Convert analysis results to a JSON string.
        
        Args:
            analysis: The analysis results to convert
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        data = analysis.model_dump()
        return json.dumps(data, indent=indent, default=cls._serialize_datetime)
