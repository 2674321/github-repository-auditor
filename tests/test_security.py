"""Tests para el scanner de seguridad."""


import pytest

from repository_auditor.scanner.security import LARGE_FILE_THRESHOLD, scan_security


@pytest.fixture
def safe_repo(tmp_path):
    """Crea un repositorio seguro."""
    (tmp_path / "README.md").write_text("# Test\n")
    (tmp_path / "app.py").write_text("print('hello')\n")
    return tmp_path


@pytest.fixture
def repo_with_env(tmp_path):
    """Crea un repositorio con archivos .env."""
    (tmp_path / ".env").write_text("SECRET=abc123\n")
    (tmp_path / ".env.local").write_text("LOCAL=true\n")
    return tmp_path


@pytest.fixture
def repo_with_sensitive(tmp_path):
    """Crea un repositorio con archivos sensibles."""
    (tmp_path / "credentials.json").write_text("{}")
    (tmp_path / "service-account.json").write_text("{}")
    (tmp_path / "id_rsa").write_text("private key\n")
    return tmp_path


@pytest.fixture
def repo_with_large_file(tmp_path):
    """Crea un repositorio con un archivo grande."""
    (tmp_path / "big_image.png").write_bytes(b"\x00" * (LARGE_FILE_THRESHOLD + 1000))
    return tmp_path


@pytest.fixture
def repo_with_medium_sensitive(tmp_path):
    """Crea un repositorio con archivos de severidad media."""
    (tmp_path / ".clasprc.json").write_text("{}")
    (tmp_path / "data.db").write_bytes(b"\x00" * 100)
    return tmp_path


@pytest.fixture
def repo_in_gitignore(tmp_path):
    """Crea un repositorio con archivos que normalmente se ignoran."""
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.js").write_text("module.exports = {};\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "module.cpython-312.pyc").write_bytes(b"\x00" * 100)
    return tmp_path


class TestSafeRepo:
    def test_no_findings(self, safe_repo):
        findings, large_files = scan_security(safe_repo)
        assert len(findings) == 0
        assert len(large_files) == 0


class TestEnvFiles:
    def test_detects_env(self, repo_with_env):
        findings, _ = scan_security(repo_with_env)
        env_findings = [f for f in findings if ".env" in f.path]
        assert len(env_findings) > 0
        for f in env_findings:
            assert f.severity == "high"


class TestSensitiveFiles:
    def test_detects_credentials(self, repo_with_sensitive):
        findings, _ = scan_security(repo_with_sensitive)
        assert len(findings) >= 3
        severities = {f.severity for f in findings}
        assert "high" in severities


class TestLargeFiles:
    def test_detects_large(self, repo_with_large_file):
        _, large_files = scan_security(repo_with_large_file)
        assert len(large_files) == 1
        assert large_files[0].size_bytes > LARGE_FILE_THRESHOLD


class TestMediumSensitive:
    def test_detects_clasprc(self, repo_with_medium_sensitive):
        findings, _ = scan_security(repo_with_medium_sensitive)
        medium_findings = [f for f in findings if f.severity == "medium"]
        assert len(medium_findings) > 0


class TestGitignoreFiles:
    def test_detects_node_modules(self, repo_in_gitignore):
        findings, _ = scan_security(repo_in_gitignore)
        node_findings = [f for f in findings if "node_modules" in f.path]
        assert len(node_findings) == 0  # node_modules está excluido del escaneo


class TestEmptyRepo:
    def test_no_findings(self, tmp_path):
        findings, large_files = scan_security(tmp_path)
        assert len(findings) == 0
        assert len(large_files) == 0
