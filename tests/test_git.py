"""Tests para el scanner de Git."""

import subprocess

import pytest

from repository_auditor.scanner.git import (
    get_commit_count,
    get_current_branch,
    get_latest_commit,
    get_main_branch,
    get_tags,
    get_untracked_files,
    is_dirty,
    is_git_repository,
    scan_git,
)


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


@pytest.fixture
def git_repo_with_tags(git_repo):
    """Crea un repositorio Git con tags."""
    subprocess.run(
        ["git", "tag", "v1.0.0"], cwd=git_repo, capture_output=True,
    )
    subprocess.run(
        ["git", "tag", "v0.9.0"], cwd=git_repo, capture_output=True,
    )
    return git_repo


@pytest.fixture
def git_repo_dirty(git_repo):
    """Crea un repositorio Git con cambios sin confirmar."""
    (git_repo / "README.md").write_text("# Modified\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=git_repo, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "modify readme"],
        cwd=git_repo, capture_output=True,
    )
    (git_repo / "untracked.txt").write_text("new\n")
    return git_repo


@pytest.fixture
def not_git_repo(tmp_path):
    """Crea un directorio que no es repositorio Git."""
    (tmp_path / "README.md").write_text("# Test\n")
    return tmp_path


class TestIsGitRepository:
    def test_valid_repo(self, git_repo):
        assert is_git_repository(str(git_repo)) is True

    def test_not_git_repo(self, not_git_repo):
        assert is_git_repository(str(not_git_repo)) is False


class TestGetCurrentBranch:
    def test_on_main(self, git_repo):
        branch = get_current_branch(str(git_repo))
        assert branch in ("main", "master")

    def test_not_git(self, not_git_repo):
        assert get_current_branch(str(not_git_repo)) is None


class TestGetMainBranch:
    def test_detects_main(self, git_repo):
        main = get_main_branch(str(git_repo))
        assert main in ("main", "master")


class TestGetCommitCount:
    def test_one_commit(self, git_repo):
        count = get_commit_count(str(git_repo))
        assert count >= 1

    def test_not_git(self, not_git_repo):
        assert get_commit_count(str(not_git_repo)) == 0


class TestGetLatestCommit:
    def test_returns_hash(self, git_repo):
        commit = get_latest_commit(str(git_repo))
        assert commit is not None
        assert len(commit) > 0

    def test_not_git(self, not_git_repo):
        assert get_latest_commit(str(not_git_repo)) is None


class TestGetTags:
    def test_with_tags(self, git_repo_with_tags):
        tags = get_tags(str(git_repo_with_tags))
        assert "v1.0.0" in tags
        assert "v0.9.0" in tags

    def test_no_tags(self, git_repo):
        tags = get_tags(str(git_repo))
        assert tags == []


class TestIsDirty:
    def test_clean(self, git_repo):
        assert is_dirty(str(git_repo)) is False

    def test_dirty(self, git_repo_dirty):
        assert is_dirty(str(git_repo_dirty)) is True


class TestGetUntrackedFiles:
    def test_no_untracked(self, git_repo):
        files = get_untracked_files(str(git_repo))
        assert files == []

    def test_with_untracked(self, git_repo_dirty):
        files = get_untracked_files(str(git_repo_dirty))
        assert "untracked.txt" in files


class TestScanGit:
    def test_valid_repo(self, git_repo):
        result = scan_git(str(git_repo))
        assert result.is_git_repository is True
        assert result.name == git_repo.name
        assert result.current_branch is not None
        assert result.commit_count >= 1
        assert result.latest_commit is not None

    def test_not_git(self, not_git_repo):
        result = scan_git(str(not_git_repo))
        assert result.is_git_repository is False
        assert result.commit_count == 0
        assert result.tags == []
