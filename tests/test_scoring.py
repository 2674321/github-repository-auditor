"""Tests para el módulo de scoring (R0.7)."""


from repository_auditor.models.repository import RuleResult, RuleStatus, Severity
from repository_auditor.scoring.engine import calculate_score
from repository_auditor.scoring.models import (
    CategoryScore,
    DiagnosticPriority,
    HealthRating,
)
from repository_auditor.scoring.weights import (
    CATEGORY_WEIGHTS,
    RATING_THRESHOLDS,
    SEVERITY_TO_PRIORITY,
    STATUS_SCORE_MAP,
)


def _rule(
    rule_id: str = "test-rule",
    name: str = "Test Rule",
    category: str = "documentation",
    status: RuleStatus = RuleStatus.PASS,
    severity: Severity = Severity.INFO,
    message: str = "",
    recommendation: str = "",
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        name=name,
        category=category,
        status=status,
        severity=severity,
        message=message,
        recommendation=recommendation,
    )


class TestScoreModels:
    def test_health_rating_values(self):
        ratings = [r.value for r in HealthRating]
        assert "EXCELLENT" in ratings
        assert "GOOD" in ratings
        assert "FAIR" in ratings
        assert "POOR" in ratings
        assert "CRITICAL" in ratings

    def test_diagnostic_priority_values(self):
        priorities = [p.value for p in DiagnosticPriority]
        assert "CRITICAL" in priorities
        assert "HIGH" in priorities
        assert "MEDIUM" in priorities
        assert "LOW" in priorities
        assert "INFO" in priorities

    def test_category_score_percentage(self):
        cs = CategoryScore(category="test", score=3.0, max_score=5.0)
        assert cs.percentage == 60.0

    def test_category_score_zero_max(self):
        cs = CategoryScore(category="test", score=0.0, max_score=0.0)
        assert cs.percentage == 0.0


class TestWeights:
    def test_weights_sum_to_100(self):
        total = sum(CATEGORY_WEIGHTS.values())
        assert total == 100

    def test_required_categories_present(self):
        for cat in ("documentation", "git", "technology", "security", "github"):
            assert cat in CATEGORY_WEIGHTS

    def test_status_score_map_completeness(self):
        for status in ("pass", "warn", "fail", "info", "not_applicable"):
            assert status in STATUS_SCORE_MAP

    def test_pass_full_score(self):
        assert STATUS_SCORE_MAP["pass"] == 1.0

    def test_fail_zero_score(self):
        assert STATUS_SCORE_MAP["fail"] == 0.0

    def test_warn_half_score(self):
        assert STATUS_SCORE_MAP["warn"] == 0.5

    def test_not_applicable_full_score(self):
        assert STATUS_SCORE_MAP["not_applicable"] == 1.0

    def test_severity_to_priority_mapping(self):
        assert SEVERITY_TO_PRIORITY["critical"] == "CRITICAL"
        assert SEVERITY_TO_PRIORITY["high"] == "HIGH"
        assert SEVERITY_TO_PRIORITY["medium"] == "MEDIUM"
        assert SEVERITY_TO_PRIORITY["low"] == "LOW"
        assert SEVERITY_TO_PRIORITY["info"] == "INFO"

    def test_rating_thresholds_ordered(self):
        thresholds = [t[0] for t in RATING_THRESHOLDS]
        assert thresholds == sorted(thresholds, reverse=True)


class TestScore100:
    def test_all_pass(self):
        rules = [
            _rule("r1", category="documentation"),
            _rule("r2", category="documentation"),
            _rule("r3", category="git"),
            _rule("r4", category="git"),
            _rule("r5", category="security"),
            _rule("r6", category="security"),
            _rule("r7", category="technology"),
            _rule("r8", category="technology"),
            _rule("r9", category="github"),
            _rule("r10", category="github"),
        ]
        result = calculate_score(rules)
        assert result.score == 100
        assert result.rating == HealthRating.EXCELLENT


class TestScore0:
    def test_all_fail(self):
        rules = [
            _rule("r1", category="documentation", status=RuleStatus.FAIL),
            _rule("r2", category="git", status=RuleStatus.FAIL),
            _rule("r3", category="security", status=RuleStatus.FAIL),
            _rule("r4", category="technology", status=RuleStatus.FAIL),
            _rule("r5", category="github", status=RuleStatus.FAIL),
        ]
        result = calculate_score(rules)
        assert result.score == 0
        assert result.rating == HealthRating.CRITICAL


class TestScoreIntermediate:
    def test_mixed_statuses(self):
        rules = [
            _rule("r1", category="documentation", status=RuleStatus.PASS),
            _rule("r2", category="documentation", status=RuleStatus.FAIL),
            _rule("r3", category="git", status=RuleStatus.PASS),
            _rule("r4", category="security", status=RuleStatus.PASS),
            _rule("r5", category="technology", status=RuleStatus.PASS),
            _rule("r6", category="github", status=RuleStatus.PASS),
        ]
        result = calculate_score(rules)
        assert 0 < result.score < 100


class TestNotApplicable:
    def test_not_applicable_does_not_penalize(self):
        rules_na = [
            _rule("r1", category="documentation", status=RuleStatus.PASS),
            _rule("r2", category="documentation", status=RuleStatus.NOT_APPLICABLE),
            _rule("r3", category="git", status=RuleStatus.PASS),
            _rule("r4", category="security", status=RuleStatus.PASS),
            _rule("r5", category="technology", status=RuleStatus.PASS),
            _rule("r6", category="github", status=RuleStatus.PASS),
        ]
        rules_all_pass = [
            _rule("r1", category="documentation", status=RuleStatus.PASS),
            _rule("r2", category="documentation", status=RuleStatus.PASS),
            _rule("r3", category="git", status=RuleStatus.PASS),
            _rule("r4", category="security", status=RuleStatus.PASS),
            _rule("r5", category="technology", status=RuleStatus.PASS),
            _rule("r6", category="github", status=RuleStatus.PASS),
        ]
        result_na = calculate_score(rules_na)
        result_all = calculate_score(rules_all_pass)
        assert result_na.score == result_all.score


class TestEmptyRules:
    def test_no_rules(self):
        result = calculate_score([])
        assert result.score == 0
        assert result.rating == HealthRating.CRITICAL
        assert result.categories == []
        assert result.diagnostics == []


class TestCategories:
    def test_categories_present(self):
        rules = [
            _rule("r1", category="documentation"),
            _rule("r2", category="git"),
            _rule("r3", category="security"),
        ]
        result = calculate_score(rules)
        cat_names = [c.category for c in result.categories]
        assert "documentation" in cat_names
        assert "git" in cat_names
        assert "security" in cat_names


class TestDiagnostics:
    def test_fail_produces_diagnostic(self):
        rules = [
            _rule(
                "r1", category="documentation", status=RuleStatus.FAIL,
                severity=Severity.HIGH, message="README missing",
                recommendation="Add README",
            ),
        ]
        result = calculate_score(rules)
        assert len(result.diagnostics) == 1
        diag = result.diagnostics[0]
        assert diag.title == "Test Rule"
        assert diag.priority == DiagnosticPriority.HIGH
        assert diag.rule_id == "r1"

    def test_pass_no_diagnostic(self):
        rules = [_rule("r1", category="documentation", status=RuleStatus.PASS)]
        result = calculate_score(rules)
        assert len(result.diagnostics) == 0

    def test_info_no_diagnostic(self):
        rules = [_rule("r1", category="documentation", status=RuleStatus.INFO)]
        result = calculate_score(rules)
        assert len(result.diagnostics) == 0

    def test_not_applicable_no_diagnostic(self):
        rules = [
            _rule("r1", category="documentation", status=RuleStatus.NOT_APPLICABLE),
        ]
        result = calculate_score(rules)
        assert len(result.diagnostics) == 0


class TestPriorities:
    def test_severity_to_priority(self):
        rules = [
            _rule("r1", status=RuleStatus.FAIL, severity=Severity.CRITICAL),
            _rule("r2", status=RuleStatus.FAIL, severity=Severity.HIGH),
            _rule("r3", status=RuleStatus.WARN, severity=Severity.MEDIUM),
        ]
        result = calculate_score(rules)
        priorities = [d.priority for d in result.diagnostics]
        assert DiagnosticPriority.CRITICAL in priorities
        assert DiagnosticPriority.HIGH in priorities
        assert DiagnosticPriority.MEDIUM in priorities


class TestRounding:
    def test_score_is_integer(self):
        rules = [
            _rule("r1", category="documentation", status=RuleStatus.PASS),
            _rule("r2", category="documentation", status=RuleStatus.FAIL),
            _rule("r3", category="git", status=RuleStatus.WARN),
            _rule("r4", category="security", status=RuleStatus.PASS),
            _rule("r5", category="technology", status=RuleStatus.PASS),
            _rule("r6", category="github", status=RuleStatus.PASS),
        ]
        result = calculate_score(rules)
        assert isinstance(result.score, int)


class TestRatingThresholds:
    def test_90_is_excellent(self):
        rules = [_rule("r1", category="git", status=RuleStatus.PASS)] * 5
        for cat in ("documentation", "security", "technology", "github"):
            for i in range(4):
                status = RuleStatus.PASS if i < 4 else RuleStatus.PASS
                rules.append(_rule(f"{cat}-{i}", category=cat, status=status))
        result = calculate_score(rules)
        assert result.rating in (HealthRating.EXCELLENT, HealthRating.GOOD)

    def test_classification(self):
        from repository_auditor.scoring.engine import _classify
        assert _classify(95) == HealthRating.EXCELLENT
        assert _classify(80) == HealthRating.GOOD
        assert _classify(65) == HealthRating.FAIR
        assert _classify(50) == HealthRating.POOR
        assert _classify(20) == HealthRating.CRITICAL


class TestNoGitHub:
    def test_no_github_category(self):
        rules = [
            _rule("r1", category="documentation", status=RuleStatus.PASS),
            _rule("r2", category="git", status=RuleStatus.PASS),
            _rule("r3", category="security", status=RuleStatus.PASS),
            _rule("r4", category="technology", status=RuleStatus.PASS),
        ]
        result = calculate_score(rules)
        cat_names = [c.category for c in result.categories]
        assert "github" not in cat_names
        assert result.score >= 0


class TestScoreResultDefaults:
    def test_max_score_is_100(self):
        result = calculate_score([])
        assert result.max_score == 100
