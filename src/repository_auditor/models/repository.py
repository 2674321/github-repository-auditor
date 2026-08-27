"""Modelos de datos para el auditor de repositorios.

Estos modelos representan la información estructurada que produce el análisis.
Son independientes de la salida de consola y pueden reutilizarse en futuras
versiones (GitHub API, informes HTML, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Severidad de un hallazgo."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleStatus(Enum):
    """Resultado de una regla de validación."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class RepositoryInfo:
    """Información básica del repositorio y su historial Git."""

    path: str
    name: str
    is_git_repository: bool = False
    current_branch: str | None = None
    main_branch: str | None = None
    remote_urls: list[str] = field(default_factory=list)
    commit_count: int = 0
    latest_commit: str | None = None
    latest_commit_date: str | None = None
    tags: list[str] = field(default_factory=list)
    dirty_worktree: bool = False
    modified_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)


@dataclass
class DocumentationInfo:
    """Indicadores de documentación encontrada en el repositorio."""

    has_readme: bool = False
    has_license: bool = False
    has_changelog: bool = False
    has_citation: bool = False
    has_contributing: bool = False
    has_code_of_conduct: bool = False
    has_security: bool = False
    has_gitignore: bool = False
    has_gitattributes: bool = False
    has_github_directory: bool = False
    has_workflows: bool = False
    has_dependabot: bool = False
    has_codeql: bool = False


@dataclass
class TechnologyInfo:
    """Tecnologías detectadas en el repositorio basándose en archivos reales."""

    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)


@dataclass
class SecurityFinding:
    """Un hallazgo potencialmente sensible detectado."""

    path: str
    category: str
    severity: str
    message: str


@dataclass
class LargeFile:
    """Un archivo grande detectado en el repositorio."""

    path: str
    size_bytes: int


@dataclass
class RuleResult:
    """Resultado de una regla de validación."""

    rule_id: str
    name: str
    category: str
    status: RuleStatus
    severity: Severity
    message: str
    recommendation: str = ""


@dataclass
class AuditResult:
    """Resultado completo del análisis de un repositorio."""

    repository: RepositoryInfo
    documentation: DocumentationInfo
    technologies: TechnologyInfo
    security_findings: list[SecurityFinding] = field(default_factory=list)
    large_files: list[LargeFile] = field(default_factory=list)
    rule_results: list[RuleResult] = field(default_factory=list)
