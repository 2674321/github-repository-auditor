"""Tests para exportación JSON y comparación (R0.8)."""

import json

from repository_auditor.github.models import GitHubAuditResult
from repository_auditor.models.repository import (
    AuditResult,
    DocumentationInfo,
    RepositoryInfo,
    RuleResult,
    RuleStatus,
    Severity,
    TechnologyInfo,
)
from repository_auditor.reports.json import (
    compare_audits,
    format_json,
    parse_audit_json,
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


def _make_github() -> GitHubAuditResult:
    """Crea un GitHubAuditResult para pruebas."""
    from repository_auditor.github.models import GitHubRepositoryInfo
    return GitHubAuditResult(
        repository=GitHubRepositoryInfo(
            owner="owner", name="repo", full_name="owner/repo",
            stars=10,
        ),
    )


class TestJsonFormat:
    def test_valid_json(self):
        result = _make_result()
        output = format_json(result)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_has_meta(self):
        result = _make_result()
        output = format_json(result)
        data = json.loads(output)
        assert "meta" in data
        assert "auditor_version" in data["meta"]
        assert "timestamp" in data["meta"]

    def test_has_audit(self):
        result = _make_result()
        output = format_json(result)
        data = json.loads(output)
        assert "audit" in data

    def test_has_repository(self):
        result = _make_result()
        output = format_json(result)
        data = json.loads(output)
        assert data["audit"]["repository"]["name"] == "test"

    def test_has_rules(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        output = format_json(result)
        data = json.loads(output)
        assert len(data["audit"]["rules"]) > 0

    def test_with_github(self):
        result = _make_result()
        github = _make_github()
        output = format_json(result, github)
        data = json.loads(output)
        assert "github" in data
        assert data["github"]["repository"]["full_name"] == "owner/repo"

    def test_without_github(self):
        result = _make_result()
        output = format_json(result)
        data = json.loads(output)
        assert "github" not in data

    def test_with_score(self):
        result = _make_result()
        result.rule_results = evaluate_rules(result)
        score = calculate_score(result.rule_results)
        output = format_json(result, score=score)
        data = json.loads(output)
        assert "score" in data
        assert "score" in data["score"]
        assert "rating" in data["score"]

    def test_no_tokens(self):
        result = _make_result()
        output = format_json(result)
        assert "ghp_" not in output
        assert "GITHUB_TOKEN" not in output

    def test_deterministic_keys(self):
        result = _make_result()
        output1 = format_json(result)
        data1 = json.loads(output1)
        data2 = json.loads(format_json(result))
        assert list(data1.keys()) == list(data2.keys())

    def test_unicode_safe(self):
        result = _make_result()
        output = format_json(result)
        assert isinstance(output, str)


class TestParseAuditJson:
    def test_valid_json(self):
        result = _make_result()
        output = format_json(result)
        data = parse_audit_json(output)
        assert "meta" in data
        assert "audit" in data

    def test_invalid_json(self):
        import pytest
        with pytest.raises(ValueError, match="JSON inválido"):
            parse_audit_json("not json")

    def test_not_dict(self):
        import pytest
        with pytest.raises(ValueError, match="JSON debe ser un objeto"):
            parse_audit_json("[1,2,3]")

    def test_missing_structure(self):
        import pytest
        with pytest.raises(ValueError, match="estructura"):
            parse_audit_json('{"key": "value"}')


class TestCompareAudits:
    def _audit_data(self, score_val: int, rules: dict[str, str]) -> dict:
        """Crea datos de auditoría mock para comparación."""
        rule_list = [
            {"rule_id": k, "status": v, "name": k, "category": "test",
             "severity": "info", "message": "", "recommendation": ""}
            for k, v in rules.items()
        ]
        return {
            "meta": {"auditor_version": "0.1.0"},
            "audit": {"repository": {"name": "test"}, "rules": rule_list},
            "score": {"score": score_val, "rating": "GOOD", "max_score": 100,
                      "categories": [], "diagnostics": []},
        }

    def test_score_improvement(self):
        old = self._audit_data(70, {"r1": "fail"})
        new = self._audit_data(85, {"r1": "pass"})
        result = compare_audits(old, new)
        assert result["score"]["change"] == 15

    def test_score_regression(self):
        old = self._audit_data(85, {"r1": "pass"})
        new = self._audit_data(70, {"r1": "fail"})
        result = compare_audits(old, new)
        assert result["score"]["change"] == -15

    def test_new_failures(self):
        old = self._audit_data(80, {"r1": "pass", "r2": "pass"})
        new = self._audit_data(60, {"r1": "pass", "r2": "fail", "r3": "fail"})
        result = compare_audits(old, new)
        assert "r2" in result["new_failures"]
        assert "r3" in result["new_failures"]

    def test_resolved_failures(self):
        old = self._audit_data(60, {"r1": "fail", "r2": "fail"})
        new = self._audit_data(80, {"r1": "pass", "r2": "pass"})
        result = compare_audits(old, new)
        assert "r1" in result["resolved_failures"]
        assert "r2" in result["resolved_failures"]

    def test_new_warnings(self):
        old = self._audit_data(80, {"r1": "pass"})
        new = self._audit_data(75, {"r1": "warn"})
        result = compare_audits(old, new)
        assert "r1" in result["new_warnings"]

    def test_same_audit(self):
        old = self._audit_data(80, {"r1": "pass"})
        new = self._audit_data(80, {"r1": "pass"})
        result = compare_audits(old, new)
        assert result["score"]["change"] == 0
        assert len(result["new_failures"]) == 0
        assert len(result["resolved_failures"]) == 0


class TestExitCodes:
    def test_exit_ok(self):
        from repository_auditor.cli import _determine_exit_code
        result = AuditResult(
            repository=RepositoryInfo(path="/test", name="test", is_git_repository=True),
            documentation=DocumentationInfo(has_readme=True, has_license=True),
            technologies=TechnologyInfo(),
        )
        result.rule_results = [
            RuleResult(
                rule_id="r1", name="test", category="documentation",
                status=RuleStatus.PASS, severity=Severity.INFO, message="ok",
            ),
        ]
        code = _determine_exit_code(result)
        assert code == 0

    def test_exit_warnings(self):
        from repository_auditor.cli import _determine_exit_code
        result = AuditResult(
            repository=RepositoryInfo(path="/test", name="test", is_git_repository=True),
            documentation=DocumentationInfo(),
            technologies=TechnologyInfo(),
        )
        result.rule_results = [
            RuleResult(
                rule_id="r1", name="test", category="documentation",
                status=RuleStatus.WARN, severity=Severity.MEDIUM, message="warn",
            ),
        ]
        code = _determine_exit_code(result)
        assert code == 1

    def test_exit_failures(self):
        from repository_auditor.cli import _determine_exit_code
        result = AuditResult(
            repository=RepositoryInfo(path="/test", name="test", is_git_repository=True),
            documentation=DocumentationInfo(),
            technologies=TechnologyInfo(),
        )
        result.rule_results = [
            RuleResult(
                rule_id="r1", name="test", category="documentation",
                status=RuleStatus.FAIL, severity=Severity.HIGH, message="fail",
            ),
        ]
        code = _determine_exit_code(result)
        assert code == 2

    def test_exit_code_constants(self):
        from repository_auditor.cli import EXIT_ERROR, EXIT_FAILURES, EXIT_OK, EXIT_WARNINGS
        assert EXIT_OK == 0
        assert EXIT_WARNINGS == 1
        assert EXIT_FAILURES == 2
        assert EXIT_ERROR == 3
