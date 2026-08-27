"""Módulo de scoring — calcula la salud del repositorio."""

from repository_auditor.scoring.engine import calculate_score
from repository_auditor.scoring.models import (
    CategoryScore,
    Diagnostic,
    DiagnosticPriority,
    HealthRating,
    RuleScore,
    ScoreResult,
)

__all__ = [
    "calculate_score",
    "CategoryScore",
    "Diagnostic",
    "DiagnosticPriority",
    "HealthRating",
    "RuleScore",
    "ScoreResult",
]
