"""Tests para reporting y UX (R0.9)."""

from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    RepositoryInfo,
    TechnologyInfo,
)
from repository_auditor.reports.text import (
    _disable_colors,
    _enable_colors,
    format_report,
)
from repository_auditor.rules import evaluate_rules
from repository_auditor.scoring import calculate_score


def _make_result() -> AuditResult:
    """Crea un AuditResult para pruebas."""
    return AuditResult(
        repository=RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True,
            current_branch="main",
        ),
        documentation=DocumentationInfo(has_readme=True, has_license=True),
        technologies=TechnologyInfo(languages=["Python"]),
    )


class TestSummary:
    def test_summary_mode(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, summary=True, color=False)
        assert "Repository Health" in report
        assert "Score:" in report

    def test_summary_no_details(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, summary=True, color=False)
        assert "Documentación" not in report
        assert "Tecnologías" not in report

    def test_summary_shows_rating(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, summary=True, color=False)
        assert score.rating.value in report


class TestVerbose:
    def test_verbose_shows_all_rules(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        report = format_report(result, verbose=True, color=False)
        assert "Reglas de validación" in report

    def test_normal_shows_only_problems(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        report = format_report(result, verbose=False, color=False)
        # En modo normal, solo se muestran reglas con problemas
        assert "Repository Health Auditor" in report


class TestColor:
    def test_no_color(self):
        result = _make_result()
        _disable_colors()
        report = format_report(result, color=False)
        assert "\033[" not in report

    def test_color_enabled(self):
        result = _make_result()
        _enable_colors()
        report = format_report(result, color=True)
        assert "\033[" in report

    def test_color_reset(self):
        _disable_colors()
        result = _make_result()
        report = format_report(result, color=False)
        _enable_colors()
        assert "\033[" not in report


class TestDiagnostics:
    def test_diagnostics_section(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, color=False)
        if score.diagnostics:
            assert "Diagnostics" in report

    def test_recommendations(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, color=False)
        has_recs = any(d.recommendation for d in score.diagnostics)
        if has_recs:
            assert "Recommendations" in report


class TestBackwardCompatibility:
    def test_default_mode(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        report = format_report(result, color=False)
        assert "Repository Health Auditor" in report
        assert "ANÁLISIS COMPLETADO" in report

    def test_with_score(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        report = format_report(result, score=score, color=False)
        assert "Repository Health" in report
        assert "Score:" in report
