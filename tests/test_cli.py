"""Tests para la CLI."""

import subprocess
import sys

import pytest

from repository_auditor.cli import run_local_audit


@pytest.fixture
def git_repo(tmp_path):
    """Crea un repositorio Git temporal."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True,
    )
    (tmp_path / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path, capture_output=True,
    )
    return tmp_path


class TestRunAudit:
    def test_returns_audit_result(self, git_repo):
        result = run_local_audit(str(git_repo))
        assert result.repository.is_git_repository is True
        assert result.documentation.has_readme is True
        assert len(result.rule_results) > 0

    def test_nonexistent_path(self):
        with pytest.raises(SystemExit):
            run_local_audit("/nonexistent/path")


class TestCLI:
    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "repository_auditor.cli", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "repo-auditor" in result.stdout

    def test_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "repository_auditor.cli", "--version"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_audit_repo(self, git_repo):
        result = subprocess.run(
            [sys.executable, "-m", "repository_auditor.cli", str(git_repo)],
            capture_output=True, text=True,
        )
        assert result.returncode in (0, 1)
        assert "Repository Health Auditor" in result.stdout
        assert "ANÁLISIS COMPLETADO" in result.stdout
