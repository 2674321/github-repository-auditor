"""Tests para las reglas de GitHub."""


from repository_auditor.github.models import (
    GitHubActionsInfo,
    GitHubAuditResult,
    GitHubReleaseInfo,
    GitHubRepositoryInfo,
)
from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    RepositoryInfo,
    RuleStatus,
    TechnologyInfo,
)
from repository_auditor.rules import evaluate_github_rules


def _make_local_result(**kwargs) -> AuditResult:
    """Crea un AuditResult local para pruebas."""
    repo = kwargs.get(
        "repository",
        RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True,
            remote_urls=["https://github.com/owner/repo.git"],
        ),
    )
    return AuditResult(
        repository=repo,
        documentation=DocumentationInfo(),
        technologies=TechnologyInfo(),
    )


def _make_github_result(**kwargs) -> GitHubAuditResult:
    """Crea un GitHubAuditResult para pruebas."""
    return GitHubAuditResult(**kwargs)


class TestGitHubRemoteRule:
    def test_pass_with_remote(self):
        local = _make_local_result()
        github = _make_github_result()
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-remote")
        assert rule.status == RuleStatus.PASS

    def test_warn_no_remote(self):
        repo = RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True, remote_urls=[],
        )
        local = _make_local_result(repository=repo)
        github = _make_github_result()
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-remote")
        assert rule.status == RuleStatus.WARN


class TestGitHubRepositoryRule:
    def test_pass_accessible(self):
        local = _make_local_result()
        github = _make_github_result(
            repository=GitHubRepositoryInfo(
                owner="owner", name="repo", full_name="owner/repo",
            ),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-repository")
        assert rule.status == RuleStatus.PASS

    def test_fail_error(self):
        local = _make_local_result()
        github = _make_github_result(error="Not found")
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-repository")
        assert rule.status == RuleStatus.FAIL


class TestGitHubActionsRule:
    def test_pass_success(self):
        local = _make_local_result()
        github = _make_github_result(
            actions=GitHubActionsInfo(
                has_workflows=True,
                latest_run_conclusion="success",
            ),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-actions")
        assert rule.status == RuleStatus.PASS

    def test_fail_failure(self):
        local = _make_local_result()
        github = _make_github_result(
            actions=GitHubActionsInfo(
                has_workflows=True,
                latest_run_conclusion="failure",
            ),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-actions")
        assert rule.status == RuleStatus.FAIL

    def test_info_no_workflows(self):
        local = _make_local_result()
        github = _make_github_result(
            actions=GitHubActionsInfo(has_workflows=False),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-actions")
        assert rule.status == RuleStatus.INFO


class TestGitHubReleasesRule:
    def test_pass_with_release(self):
        local = _make_local_result()
        github = _make_github_result(
            releases=GitHubReleaseInfo(
                has_published_release=True,
                latest_tag="v1.0.0",
            ),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-releases")
        assert rule.status == RuleStatus.PASS

    def test_info_no_releases(self):
        local = _make_local_result()
        github = _make_github_result(
            releases=GitHubReleaseInfo(has_published_release=False),
        )
        rules = evaluate_github_rules(local, github)
        rule = next(r for r in rules if r.rule_id == "gh-releases")
        assert rule.status == RuleStatus.INFO
