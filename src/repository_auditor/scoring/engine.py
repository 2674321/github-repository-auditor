"""Motor de scoring — calcula la salud del repositorio."""

from __future__ import annotations

from repository_auditor.models.repository import RuleResult
from repository_auditor.scoring.models import (
    CategoryScore,
    Diagnostic,
    DiagnosticPriority,
    HealthRating,
    RuleScore,
    ScoreResult,
)
from repository_auditor.scoring.weights import (
    CATEGORY_WEIGHTS,
    RATING_THRESHOLDS,
    SEVERITY_TO_PRIORITY,
    STATUS_SCORE_MAP,
)


def _score_rule(rule: RuleResult) -> RuleScore:
    """Calcula el score de una regla individual."""
    multiplier = STATUS_SCORE_MAP.get(rule.status.value, 1.0)
    score = 1.0 * multiplier

    return RuleScore(
        rule_id=rule.rule_id,
        name=rule.name,
        category=rule.category,
        score=score,
        max_score=1.0,
        status=rule.status.value,
        severity=rule.severity.value,
        message=rule.message,
    )


def _make_diagnostic(rule: RuleResult) -> Diagnostic | None:
    """Genera un diagnóstico si la regla tiene un problema."""
    if rule.status.value in ("pass", "info", "not_applicable"):
        return None

    priority_str = SEVERITY_TO_PRIORITY.get(rule.severity.value, "LOW")
    try:
        priority = DiagnosticPriority(priority_str)
    except ValueError:
        priority = DiagnosticPriority.LOW

    return Diagnostic(
        title=rule.name,
        description=rule.message,
        priority=priority,
        category=rule.category,
        recommendation=rule.recommendation,
        rule_id=rule.rule_id,
    )


def _classify(score: int) -> HealthRating:
    """Clasifica un score numérico en una categoría de salud."""
    for threshold, rating in RATING_THRESHOLDS:
        if score >= threshold:
            return rating
    return HealthRating.CRITICAL


def calculate_score(rule_results: list[RuleResult]) -> ScoreResult:
    """Calcula el score global a partir de los resultados de reglas.

    Args:
        rule_results: Lista de resultados de reglas evaluadas.

    Returns:
        ScoreResult con el score global, categorías y diagnósticos.
    """
    if not rule_results:
        return ScoreResult(
            score=0,
            max_score=100,
            rating=HealthRating.CRITICAL,
            categories=[],
            diagnostics=[],
        )

    # Agrupar reglas por categoría
    by_category: dict[str, list[RuleResult]] = {}
    for rule in rule_results:
        cat = rule.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rule)

    category_scores: list[CategoryScore] = []
    diagnostics: list[Diagnostic] = []

    for cat_name, cat_rules in by_category.items():
        rule_scores = [_score_rule(r) for r in cat_rules]
        cat_total = sum(rs.score for rs in rule_scores)
        cat_max = float(len(cat_rules))

        category_scores.append(
            CategoryScore(
                category=cat_name,
                score=cat_total,
                max_score=cat_max,
                rules=rule_scores,
            )
        )

        for rule in cat_rules:
            diag = _make_diagnostic(rule)
            if diag is not None:
                diagnostics.append(diag)

    # Calcular score global ponderado
    total_weighted = 0.0
    total_weight = 0

    for cs in category_scores:
        weight = CATEGORY_WEIGHTS.get(cs.category, 0)
        if weight == 0:
            continue

        cat_pct = cs.percentage / 100.0
        total_weighted += cat_pct * weight
        total_weight += weight

    if total_weight > 0:
        raw_score = (total_weighted / total_weight) * 100
    else:
        raw_score = 0.0

    final_score = max(0, min(100, round(raw_score)))
    rating = _classify(final_score)

    return ScoreResult(
        score=final_score,
        max_score=100,
        rating=rating,
        categories=category_scores,
        diagnostics=diagnostics,
    )
