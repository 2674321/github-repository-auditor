"""Scanner de filesystem — detecta documentación y archivos relevantes.

Funciones puras que verifican la presencia de archivos en un directorio.
No modifican el sistema de archivos.
"""

from __future__ import annotations

from pathlib import Path

from repository_auditor.models.repository import DocumentationInfo


def _has_file(path: Path, filename: str) -> bool:
    """Verifica si existe un archivo (case-insensitive) en la ruta dada."""
    return any(f.name.lower() == filename.lower() for f in path.iterdir() if f.is_file())


def _has_directory(path: Path, dirname: str) -> bool:
    """Verifica si existe un directorio (case-insensitive) en la ruta dada."""
    return any(d.name.lower() == dirname.lower() for d in path.iterdir() if d.is_dir())


def has_readme(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo README."""
    return _has_file(path, "readme.md")


def has_license(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo LICENSE."""
    return _has_file(path, "license")


def has_changelog(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo CHANGELOG."""
    return _has_file(path, "changelog.md")


def has_citation(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo CITATION.cff."""
    return _has_file(path, "citation.cff")


def has_contributing(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo CONTRIBUTING."""
    return _has_file(path, "contributing.md")


def has_code_of_conduct(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo CODE_OF_CONDUCT."""
    return _has_file(path, "code_of_conduct.md")


def has_security(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo SECURITY."""
    return _has_file(path, "security.md")


def has_gitignore(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo .gitignore."""
    return _has_file(path, ".gitignore")


def has_gitattributes(path: Path) -> bool:
    """Detecta si el repositorio contiene un archivo .gitattributes."""
    return _has_file(path, ".gitattributes")


def has_github_directory(path: Path) -> bool:
    """Detecta si el repositorio contiene un directorio .github."""
    return _has_directory(path, ".github")


def has_workflows(path: Path) -> bool:
    """Detecta si el repositorio tiene workflows de GitHub Actions."""
    github_dir = path / ".github"
    if not github_dir.exists() or not github_dir.is_dir():
        return False
    workflows_dir = github_dir / "workflows"
    return workflows_dir.exists() and workflows_dir.is_dir()


def has_dependabot(path: Path) -> bool:
    """Detecta si el repositorio tiene configuración de Dependabot."""
    github_dir = path / ".github"
    if not github_dir.exists():
        return False
    dependabot_file = github_dir / "dependabot.yml"
    return dependabot_file.exists()


def has_codeql(path: Path) -> bool:
    """Detecta si el repositorio tiene workflows de CodeQL."""
    workflows_dir = path / ".github" / "workflows"
    if not workflows_dir.exists():
        return False
    for f in workflows_dir.iterdir():
        if f.is_file() and "codeql" in f.name.lower():
            return True
    return False


def scan_documentation(path: Path) -> DocumentationInfo:
    """Realiza un escaneo completo de documentación del repositorio.

    Args:
        path: Ruta al directorio raíz del repositorio.

    Returns:
        DocumentationInfo con todos los indicadores detectados.
    """
    return DocumentationInfo(
        has_readme=has_readme(path),
        has_license=has_license(path),
        has_changelog=has_changelog(path),
        has_citation=has_citation(path),
        has_contributing=has_contributing(path),
        has_code_of_conduct=has_code_of_conduct(path),
        has_security=has_security(path),
        has_gitignore=has_gitignore(path),
        has_gitattributes=has_gitattributes(path),
        has_github_directory=has_github_directory(path),
        has_workflows=has_workflows(path),
        has_dependabot=has_dependabot(path),
        has_codeql=has_codeql(path),
    )
