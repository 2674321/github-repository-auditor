"""Modelos de datos para el sistema de scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HealthRating(Enum):
    """Clasificación de salud del repositorio."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    CRITICAL = "CRITICAL"


class DiagnosticPriority(Enum):
    """Prioridad de un diagnóstico."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class RuleScore:
    """Puntuación de una regla individual."""

    rule_id: str
    name: str
    category: str
    score: float
    max_score: float
    status: str
    severity: str
    message: str = ""


@dataclass
class CategoryScore:
    """Puntuación agregada de una categoría."""

    category: str
    score: float
    max_score: float
    rules: list[RuleScore] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100


@dataclass
class Diagnostic:
    """Diagnóstico human-readable para un problema detectado."""

    title: str
    description: str
    priority: DiagnosticPriority
    category: str
    recommendation: str
    rule_id: str


@dataclass
class ScoreResult:
    """Resultado completo del scoring."""

    score: int
    max_score: int = 100
    rating: HealthRating = HealthRating.CRITICAL
    categories: list[CategoryScore] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
