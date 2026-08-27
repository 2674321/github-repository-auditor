"""Tests para el scanner de tecnologías."""

import json

import pytest

from repository_auditor.scanner.technology import scan_technologies


@pytest.fixture
def python_repo(tmp_path):
    """Crea un repositorio Python."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    return tmp_path


@pytest.fixture
def nodejs_repo(tmp_path):
    """Crea un repositorio Node.js."""
    package_json = {
        "name": "test",
        "version": "1.0.0",
        "dependencies": {"express": "^4.18.0"},
    }
    (tmp_path / "package.json").write_text(json.dumps(package_json))
    (tmp_path / "index.js").write_text("console.log('hello');\n")
    return tmp_path


@pytest.fixture
def typescript_repo(tmp_path):
    """Crea un repositorio TypeScript."""
    (tmp_path / "tsconfig.json").write_text("{}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("console.log('hello');\n")
    return tmp_path


@pytest.fixture
def react_repo(tmp_path):
    """Crea un repositorio React."""
    package_json = {
        "name": "test",
        "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
        "devDependencies": {"vite": "^5.0.0"},
    }
    (tmp_path / "package.json").write_text(json.dumps(package_json))
    (tmp_path / "vite.config.ts").write_text("export default {}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.js").write_text("console.log('hello');\n")
    return tmp_path


@pytest.fixture
def docker_repo(tmp_path):
    """Crea un repositorio Docker."""
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
    (tmp_path / "app.py").write_text("print('hello')\n")
    return tmp_path


@pytest.fixture
def apps_script_repo(tmp_path):
    """Crea un repositorio de Google Apps Script."""
    (tmp_path / ".clasp.json").write_text(json.dumps({"scriptId": "abc123"}))
    (tmp_path / "appsscript.json").write_text(json.dumps({"timeZone": "America/Santiago"}))
    (tmp_path / "main.js").write_text("function myFunction() {}\n")
    return tmp_path


@pytest.fixture
def ruby_repo(tmp_path):
    """Crea un repositorio Ruby."""
    (tmp_path / "Gemfile").write_text('gem "rails"\n')
    (tmp_path / "app.rb").write_text("puts 'hello'\n")
    return tmp_path


@pytest.fixture
def html_repo(tmp_path):
    """Crea un repositorio HTML/CSS."""
    (tmp_path / "index.html").write_text("<html></html>\n")
    (tmp_path / "style.css").write_text("body {}")
    return tmp_path


@pytest.fixture
def empty_repo(tmp_path):
    """Crea un repositorio vacío."""
    return tmp_path


class TestPythonDetection:
    def test_detects_python(self, python_repo):
        result = scan_technologies(python_repo)
        assert "Python" in result.languages
        assert "pyproject.toml" in result.config_files

    def test_requirements_txt(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask==2.0\n")
        result = scan_technologies(tmp_path)
        assert "Python" in result.languages


class TestNodeJsDetection:
    def test_detects_nodejs(self, nodejs_repo):
        result = scan_technologies(nodejs_repo)
        assert "JavaScript" in result.languages
        assert "Express" in result.frameworks


class TestTypeScriptDetection:
    def test_detects_typescript(self, typescript_repo):
        result = scan_technologies(typescript_repo)
        assert "TypeScript" in result.languages
        assert "tsconfig.json" in result.config_files


class TestReactDetection:
    def test_detects_react(self, react_repo):
        result = scan_technologies(react_repo)
        assert "React" in result.frameworks
        assert "Vite" in result.frameworks
        assert "JavaScript" in result.languages


class TestDockerDetection:
    def test_detects_docker(self, docker_repo):
        result = scan_technologies(docker_repo)
        assert "Docker" in result.frameworks
        assert "Dockerfile" in result.config_files


class TestAppsScriptDetection:
    def test_detects_apps_script(self, apps_script_repo):
        result = scan_technologies(apps_script_repo)
        assert "JavaScript" in result.languages
        assert "clasp" in result.frameworks
        assert "Google Apps Script" in result.frameworks


class TestRubyDetection:
    def test_detects_ruby(self, ruby_repo):
        result = scan_technologies(ruby_repo)
        assert "Ruby" in result.languages


class TestHtmlDetection:
    def test_detects_html(self, html_repo):
        result = scan_technologies(html_repo)
        assert "HTML" in result.languages
        assert "CSS" in result.languages


class TestEmptyRepo:
    def test_no_technologies(self, empty_repo):
        result = scan_technologies(empty_repo)
        assert result.languages == []
        assert result.frameworks == []
        assert result.tools == []
