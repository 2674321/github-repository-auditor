"""Tests para los modelos de GitHub."""

from repository_auditor.github.models import (
    GitHubActionsInfo,
    GitHubAuditResult,
    GitHubReleaseInfo,
    GitHubRepositoryInfo,
)


class TestGitHubRepositoryInfo:
    def test_defaults(self):
        info = GitHubRepositoryInfo(owner="owner", name="repo", full_name="owner/repo")
        assert info.stars == 0
        assert info.forks == 0
        assert info.archived is False
        assert info.topics == []

    def test_with_values(self):
        info = GitHubRepositoryInfo(
            owner="owner", name="repo", full_name="owner/repo",
            stars=10, forks=5, visibility="public",
        )
        assert info.stars == 10
        assert info.visibility == "public"


class TestGitHubReleaseInfo:
    def test_defaults(self):
        info = GitHubReleaseInfo()
        assert info.total_count == 0
        assert info.has_published_release is False


class TestGitHubActionsInfo:
    def test_defaults(self):
        info = GitHubActionsInfo()
        assert info.has_workflows is False


class TestGitHubAuditResult:
    def test_defaults(self):
        result = GitHubAuditResult()
        assert result.repository is None
        assert result.error is None
