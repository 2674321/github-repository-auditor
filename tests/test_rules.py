"""Tests para las reglas de validación."""

from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    LargeFile,
    RepositoryInfo,
    RuleStatus,
    SecurityFinding,
    TechnologyInfo,
)
from repository_auditor.rules import evaluate_rules


def _make_result(**kwargs) -> AuditResult:
    """Crea un AuditResult para pruebas."""
    repo = kwargs.get(
        "repository",
        RepositoryInfo(path="/test", name="test", is_git_repository=True),
    )
    doc = kwargs.get("documentation", DocumentationInfo())
    tech = kwargs.get("technologies", TechnologyInfo())
    security = kwargs.get("security_findings", [])
    large = kwargs.get("large_files", [])
    return AuditResult(
        repository=repo,
        documentation=doc,
        technologies=tech,
        security_findings=security,
        large_files=large,
    )


class TestReadmeRule:
    def test_pass(self):
        result = _make_result(documentation=DocumentationInfo(has_readme=True))
        rules = evaluate_rules(result)
        readme_rule = next(r for r in rules if r.rule_id == "doc-readme")
        assert readme_rule.status == RuleStatus.PASS

    def test_fail(self):
        result = _make_result(documentation=DocumentationInfo(has_readme=False))
        rules = evaluate_rules(result)
        readme_rule = next(r for r in rules if r.rule_id == "doc-readme")
        assert readme_rule.status == RuleStatus.FAIL


class TestLicenseRule:
    def test_pass(self):
        result = _make_result(documentation=DocumentationInfo(has_license=True))
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "doc-license")
        assert rule.status == RuleStatus.PASS

    def test_warn(self):
        result = _make_result(documentation=DocumentationInfo(has_license=False))
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "doc-license")
        assert rule.status == RuleStatus.WARN


class TestGitignoreRule:
    def test_pass(self):
        result = _make_result(documentation=DocumentationInfo(has_gitignore=True))
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "doc-gitignore")
        assert rule.status == RuleStatus.PASS

    def test_warn(self):
        result = _make_result(documentation=DocumentationInfo(has_gitignore=False))
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "doc-gitignore")
        assert rule.status == RuleStatus.WARN


class TestSecurityHighRule:
    def test_pass(self):
        result = _make_result(security_findings=[])
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "sec-high")
        assert rule.status == RuleStatus.PASS

    def test_fail(self):
        finding = SecurityFinding(
            path=".env", category="sensitive_high",
            severity="high", message="test",
        )
        result = _make_result(security_findings=[finding])
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "sec-high")
        assert rule.status == RuleStatus.FAIL


class TestLargeFilesRule:
    def test_pass(self):
        result = _make_result(large_files=[])
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "sec-large")
        assert rule.status == RuleStatus.PASS

    def test_warn(self):
        large = LargeFile(path="big.png", size_bytes=2 * 1024 * 1024)
        result = _make_result(large_files=[large])
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "sec-large")
        assert rule.status == RuleStatus.WARN


class TestGitValidRule:
    def test_pass(self):
        repo = RepositoryInfo(
            path="/test", name="test", is_git_repository=True,
        )
        result = _make_result(repository=repo)
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "git-valid")
        assert rule.status == RuleStatus.PASS

    def test_fail(self):
        repo = RepositoryInfo(
            path="/test", name="test", is_git_repository=False,
        )
        result = _make_result(repository=repo)
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "git-valid")
        assert rule.status == RuleStatus.FAIL


class TestDirtyWorktreeRule:
    def test_clean(self):
        repo = RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True, dirty_worktree=False,
        )
        result = _make_result(repository=repo)
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "git-dirty")
        assert rule.status == RuleStatus.PASS

    def test_dirty(self):
        repo = RepositoryInfo(
            path="/test", name="test",
            is_git_repository=True,
            dirty_worktree=True, modified_files=["file.txt"],
        )
        result = _make_result(repository=repo)
        rules = evaluate_rules(result)
        rule = next(r for r in rules if r.rule_id == "git-dirty")
        assert rule.status == RuleStatus.WARN


class TestEvaluateRules:
    def test_all_rules_evaluated(self):
        result = _make_result()
        rules = evaluate_rules(result)
        assert len(rules) > 0
        rule_ids = {r.rule_id for r in rules}
        expected = {
            "doc-readme", "doc-license", "doc-gitignore",
            "doc-changelog", "doc-citation", "sec-high",
            "sec-large", "git-valid", "git-dirty",
        }
        assert expected.issubset(rule_ids)
