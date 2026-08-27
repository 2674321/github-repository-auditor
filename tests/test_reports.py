"""Tests para el reporte de texto."""

from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    LargeFile,
    RepositoryInfo,
    SecurityFinding,
    TechnologyInfo,
)
from repository_auditor.reports.text import format_report
from repository_auditor.rules import evaluate_rules


def _make_result() -> AuditResult:
    """Crea un AuditResult completo para pruebas."""
    repo = RepositoryInfo(
        path="/test/my-repo",
        name="my-repo",
        is_git_repository=True,
        current_branch="main",
        main_branch="main",
        commit_count=42,
        latest_commit="abc1234",
        latest_commit_date="2026-08-26",
        tags=["v1.0.0"],
        dirty_worktree=False,
    )
    doc = DocumentationInfo(
        has_readme=True,
        has_license=True,
        has_changelog=False,
        has_citation=False,
        has_gitignore=True,
    )
    tech = TechnologyInfo(
        languages=["Python", "JavaScript"],
        frameworks=["React", "Vite"],
        tools=["GitHub Actions"],
    )
    finding = SecurityFinding(
        path=".env", category="sensitive_high",
        severity="high", message="test",
    )
    large = LargeFile(path="big.png", size_bytes=2 * 1024 * 1024)

    result = AuditResult(
        repository=repo,
        documentation=doc,
        technologies=tech,
        security_findings=[finding],
        large_files=[large],
    )
    result.rule_results = evaluate_rules(result)
    return result


class TestFormatReport:
    def test_contains_header(self):
        result = _make_result()
        report = format_report(result)
        assert "Repository Health Auditor" in report

    def test_contains_repo_name(self):
        result = _make_result()
        report = format_report(result)
        assert "my-repo" in report

    def test_contains_git_info(self):
        result = _make_result()
        report = format_report(result)
        assert "Repositorio Git" in report
        assert "main" in report
        assert "42" in report

    def test_contains_documentation(self):
        result = _make_result()
        report = format_report(result)
        assert "README" in report
        assert "LICENSE" in report

    def test_contains_technologies(self):
        result = _make_result()
        report = format_report(result)
        assert "Python" in report
        assert "JavaScript" in report
        assert "React" in report

    def test_contains_security(self):
        result = _make_result()
        report = format_report(result)
        assert "Seguridad" in report
        assert "sensibles" in report

    def test_contains_rules(self):
        result = _make_result()
        report = format_report(result)
        assert "Reglas" in report

    def test_contains_status(self):
        result = _make_result()
        report = format_report(result)
        assert "ANÁLISIS COMPLETADO" in report

    def test_not_git_repo(self):
        repo = RepositoryInfo(path="/test", name="test", is_git_repository=False)
        result = AuditResult(
            repository=repo,
            documentation=DocumentationInfo(),
            technologies=TechnologyInfo(),
        )
        result.rule_results = evaluate_rules(result)
        report = format_report(result)
        assert "No es un repositorio Git" in report
