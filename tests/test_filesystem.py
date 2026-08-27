"""Tests para el scanner de filesystem (documentación)."""

import pytest

from repository_auditor.scanner.filesystem import (
    has_changelog,
    has_citation,
    has_codeql,
    has_dependabot,
    has_github_directory,
    has_gitignore,
    has_license,
    has_readme,
    has_workflows,
    scan_documentation,
)


@pytest.fixture
def tmp_repo(tmp_path):
    """Crea un repositorio temporal vacío."""
    return tmp_path


@pytest.fixture
def tmp_repo_with_readme(tmp_path):
    """Crea un repositorio temporal con README."""
    (tmp_path / "README.md").write_text("# Test\n")
    return tmp_path


@pytest.fixture
def tmp_repo_full(tmp_path):
    """Crea un repositorio temporal con documentación completa."""
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "LICENSE").write_text("MIT\n")
    (tmp_path / "CHANGELOG.md").write_text("## [0.1.0]\n")
    (tmp_path / "CITATION.cff").write_text("cff-version: 1.2.0\n")
    (tmp_path / "CONTRIBUTING.md").write_text("Contributing\n")
    (tmp_path / "CODE_OF_CONDUCT.md").write_text("Code of Conduct\n")
    (tmp_path / "SECURITY.md").write_text("Security\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / ".gitattributes").write_text("* text=auto\n")
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    workflows_dir = github_dir / "workflows"
    workflows_dir.mkdir()
    (workflows_dir / "ci.yml").write_text("name: CI\n")
    (github_dir / "dependabot.yml").write_text("version: 2\n")
    (workflows_dir / "codeql.yml").write_text("name: CodeQL\n")
    return tmp_path


class TestHasReadme:
    def test_exists(self, tmp_repo_with_readme):
        assert has_readme(tmp_repo_with_readme) is True

    def test_not_exists(self, tmp_repo):
        assert has_readme(tmp_repo) is False

    def test_case_insensitive(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Test\n")
        assert has_readme(tmp_path) is True

    def test_readme_uppercase(self, tmp_path):
        (tmp_path / "README.MD").write_text("# Test\n")
        assert has_readme(tmp_path) is True


class TestHasLicense:
    def test_exists(self, tmp_path):
        (tmp_path / "LICENSE").write_text("MIT\n")
        assert has_license(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_license(tmp_repo) is False


class TestHasChangelog:
    def test_exists(self, tmp_path):
        (tmp_path / "CHANGELOG.md").write_text("## [0.1.0]\n")
        assert has_changelog(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_changelog(tmp_repo) is False


class TestHasCitation:
    def test_exists(self, tmp_path):
        (tmp_path / "CITATION.cff").write_text("cff-version: 1.2.0\n")
        assert has_citation(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_citation(tmp_repo) is False


class TestHasGitignore:
    def test_exists(self, tmp_path):
        (tmp_path / ".gitignore").write_text("__pycache__/\n")
        assert has_gitignore(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_gitignore(tmp_repo) is False


class TestHasGitHubDirectory:
    def test_exists(self, tmp_path):
        (tmp_path / ".github").mkdir()
        assert has_github_directory(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_github_directory(tmp_repo) is False


class TestHasWorkflows:
    def test_exists(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        assert has_workflows(tmp_path) is True

    def test_no_workflows_dir(self, tmp_path):
        (tmp_path / ".github").mkdir()
        assert has_workflows(tmp_path) is False

    def test_no_github_dir(self, tmp_repo):
        assert has_workflows(tmp_repo) is False


class TestHasDependabot:
    def test_exists(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "dependabot.yml").write_text("version: 2\n")
        assert has_dependabot(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_dependabot(tmp_repo) is False


class TestHasCodeql:
    def test_exists(self, tmp_path):
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "codeql.yml").write_text("name: CodeQL\n")
        assert has_codeql(tmp_path) is True

    def test_not_exists(self, tmp_repo):
        assert has_codeql(tmp_repo) is False


class TestScanDocumentation:
    def test_empty_repo(self, tmp_repo):
        result = scan_documentation(tmp_repo)
        assert result.has_readme is False
        assert result.has_license is False
        assert result.has_changelog is False
        assert result.has_citation is False
        assert result.has_gitignore is False
        assert result.has_github_directory is False
        assert result.has_workflows is False
        assert result.has_dependabot is False
        assert result.has_codeql is False

    def test_full_repo(self, tmp_repo_full):
        result = scan_documentation(tmp_repo_full)
        assert result.has_readme is True
        assert result.has_license is True
        assert result.has_changelog is True
        assert result.has_citation is True
        assert result.has_contributing is True
        assert result.has_code_of_conduct is True
        assert result.has_security is True
        assert result.has_gitignore is True
        assert result.has_gitattributes is True
        assert result.has_github_directory is True
        assert result.has_workflows is True
        assert result.has_dependabot is True
        assert result.has_codeql is True
