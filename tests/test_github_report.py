"""Tests para el reporte de texto con sección GitHub."""

from repository_auditor.github.models import (
    GitHubActionsInfo,
    GitHubAuditResult,
    GitHubPullRequestsInfo,
    GitHubReleaseInfo,
    GitHubRepositoryInfo,
)
from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    RepositoryInfo,
    TechnologyInfo,
)
from repository_auditor.reports.text import format_report


def _make_local_result() -> AuditResult:
    """Crea un AuditResult local para pruebas."""
    return AuditResult(
        repository=RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True,
        ),
        documentation=DocumentationInfo(),
        technologies=TechnologyInfo(),
    )


def _make_github_result() -> GitHubAuditResult:
    """Crea un GitHubAuditResult para pruebas."""
    return GitHubAuditResult(
        repository=GitHubRepositoryInfo(
            owner="owner", name="repo",
            full_name="owner/repo",
            visibility="public",
            stars=10,
            forks=3,
            open_issues=2,
        ),
        releases=GitHubReleaseInfo(
            latest_tag="v1.0.0",
            has_published_release=True,
        ),
        pull_requests=GitHubPullRequestsInfo(open_count=1),
        actions=GitHubActionsInfo(
            has_workflows=True,
            latest_run_conclusion="success",
        ),
    )


class TestReportWithoutGitHub:
    def test_no_github_section(self):
        result = _make_local_result()
        report = format_report(result)
        assert "GitHub" not in report or report.count("GitHub") <= 1

    def test_backward_compatible(self):
        result = _make_local_result()
        report = format_report(result)
        assert "Repository Health Auditor" in report
        assert "ANÁLISIS COMPLETADO" in report


class TestReportWithGitHub:
    def test_github_section_present(self):
        result = _make_local_result()
        github = _make_github_result()
        report = format_report(result, github)
        assert "owner/repo" in report

    def test_shows_stars(self):
        result = _make_local_result()
        github = _make_github_result()
        report = format_report(result, github)
        assert "Stars: 10" in report

    def test_shows_releases(self):
        result = _make_local_result()
        github = _make_github_result()
        report = format_report(result, github)
        assert "v1.0.0" in report

    def test_shows_actions(self):
        result = _make_local_result()
        github = _make_github_result()
        report = format_report(result, github)
        assert "success" in report


class TestReportGitHubError:
    def test_shows_error(self):
        result = _make_local_result()
        github = GitHubAuditResult(error="Connection failed")
        report = format_report(result, github)
        assert "Connection failed" in report
