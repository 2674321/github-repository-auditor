"""Scanner de tecnologías — detecta stacks basándose en archivos reales.

No inventa tecnologías. Cada detección requiere evidencia de un archivo
de configuración específico presente en el repositorio.
"""

from __future__ import annotations

import json
from pathlib import Path

from repository_auditor.models.repository import TechnologyInfo


def _read_json(path: Path) -> dict | None:
    """Lee un archivo JSON de forma segura."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _detect_languages(path: Path) -> list[str]:
    """Detecta lenguajes de programación por archivos presentes."""
    languages = []

    if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
        languages.append("Python")
    if (path / "Gemfile").exists():
        languages.append("Ruby")
    if (path / "tsconfig.json").exists():
        languages.append("TypeScript")
    elif _has_js_files(path):
        languages.append("JavaScript")

    if _has_html_files(path):
        languages.append("HTML")
    if _has_css_files(path):
        languages.append("CSS")

    if (path / "appsscript.json").exists() or (path / ".clasp.json").exists():
        if "JavaScript" not in languages:
            languages.append("JavaScript")

    return languages


def _has_js_files(path: Path) -> bool:
    """Verifica si existen archivos JavaScript en el repositorio."""
    for f in path.rglob("*.js"):
        if ".git" not in f.parts and "node_modules" not in f.parts:
            return True
    return False


def _has_html_files(path: Path) -> bool:
    """Verifica si existen archivos HTML en el repositorio."""
    for f in path.rglob("*.html"):
        if ".git" not in f.parts and "node_modules" not in f.parts:
            return True
    return False


def _has_css_files(path: Path) -> bool:
    """Verifica si existen archivos CSS en el repositorio."""
    for f in path.rglob("*.css"):
        if ".git" not in f.parts and "node_modules" not in f.parts:
            return True
    return False


def _detect_frameworks(path: Path) -> list[str]:
    """Detecta frameworks y librerías principales."""
    frameworks = []

    if (path / "Dockerfile").exists():
        frameworks.append("Docker")

    if (path / "vite.config.ts").exists() or (path / "vite.config.js").exists():
        frameworks.append("Vite")

    package_json = path / "package.json"
    if package_json.exists():
        data = _read_json(package_json)
        if data:
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))
            if "react" in deps:
                frameworks.append("React")
            if "vue" in deps:
                frameworks.append("Vue.js")
            if "svelte" in deps:
                frameworks.append("Svelte")
            if "next" in deps:
                frameworks.append("Next.js")
            if "nuxt" in deps:
                frameworks.append("Nuxt.js")
            if "express" in deps:
                frameworks.append("Express")

    if (path / ".clasp.json").exists():
        frameworks.append("clasp")
    if (path / "appsscript.json").exists():
        frameworks.append("Google Apps Script")

    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        try:
            req = path / "requirements.txt"
            if req.exists():
                content = req.read_text(encoding="utf-8")
                if "flask" in content.lower():
                    frameworks.append("Flask")
                if "django" in content.lower():
                    frameworks.append("Django")
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")
        except OSError:
            pass

    return frameworks


def _detect_tools(path: Path) -> list[str]:
    """Detecta herramientas de desarrollo y CI/CD."""
    tools = []

    if (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists():
        if "Docker" not in tools:
            tools.append("Docker")

    if (path / ".github" / "workflows").exists():
        tools.append("GitHub Actions")

    if (path / ".github" / "dependabot.yml").exists():
        tools.append("Dependabot")

    if (path / "Makefile").exists():
        tools.append("Make")

    if (path / "tox.ini").exists():
        tools.append("tox")

    return tools


def _detect_config_files(path: Path) -> list[str]:
    """Detecta archivos de configuración relevantes."""
    configs = []
    config_names = [
        "package.json",
        "tsconfig.json",
        "pyproject.toml",
        "requirements.txt",
        "Gemfile",
        "Dockerfile",
        "docker-compose.yml",
        ".clasp.json",
        "appsscript.json",
        "vite.config.ts",
        "vite.config.js",
        "vite.config.mjs",
        "next.config.js",
        "nuxt.config.js",
        "svelte.config.js",
        "webpack.config.js",
        "rollup.config.js",
        "babel.config.js",
        ".babelrc",
        ".eslintrc.js",
        ".eslintrc.json",
        "eslint.config.js",
        ".prettierrc",
        ".prettierrc.json",
        "ruff.toml",
        "setup.cfg",
        "setup.py",
        "Makefile",
        "tox.ini",
    ]

    for name in config_names:
        if (path / name).exists():
            configs.append(name)

    return configs


def scan_technologies(path: Path) -> TechnologyInfo:
    """Realiza un escaneo completo de tecnologías del repositorio.

    Args:
        path: Ruta al directorio del repositorio.

    Returns:
        TechnologyInfo con todas las tecnologías detectadas.
    """
    return TechnologyInfo(
        languages=_detect_languages(path),
        frameworks=_detect_frameworks(path),
        tools=_detect_tools(path),
        config_files=_detect_config_files(path),
    )
