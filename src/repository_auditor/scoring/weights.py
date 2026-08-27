"""Pesos y umbrales centralizados para el scoring.

Todos los números mágicos viven aquí.
"""

from repository_auditor.scoring.models import HealthRating

# Pesos por categoría (deben sumar 100)
CATEGORY_WEIGHTS: dict[str, int] = {
    "documentation": 20,
    "git": 20,
    "technology": 15,
    "security": 25,
    "github": 20,
}

# Puntos máximos por regla dentro de cada categoría
# Cada regla aporta 1 punto por defecto
RULE_MAX_SCORE: float = 1.0

# Clasificación de salud (límites inferiores)
RATING_THRESHOLDS: list[tuple[int, HealthRating]] = [
    (90, HealthRating.EXCELLENT),
    (75, HealthRating.GOOD),
    (60, HealthRating.FAIR),
    (40, HealthRating.POOR),
    (0, HealthRating.CRITICAL),
]

# Mapeo de severidad a prioridad de diagnóstico
SEVERITY_TO_PRIORITY: dict[str, str] = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "info": "INFO",
}

# Mapeo de status de regla a contribución al score
# PASS = max_score, WARN = 50%, FAIL = 0, INFO/NOT_APPLICABLE = no penaliza
STATUS_SCORE_MAP: dict[str, float] = {
    "pass": 1.0,
    "warn": 0.5,
    "fail": 0.0,
    "info": 1.0,
    "not_applicable": 1.0,
}
