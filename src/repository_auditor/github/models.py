"""Modelos de datos para la integración con GitHub API.

Estos modelos representan la información obtenida de GitHub.
Son independientes de los modelos del scanner local.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GitHubRepositoryInfo:
    """Información del repositorio obtenida de GitHub API."""

    owner: str
    name: str
    full_name: str
    description: str | None = None
    url: str | None = None
    default_branch: str | None = None
    visibility: str | None = None
    archived: bool = False
    fork: bool = False
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    pushed_at: str | None = None
    license: str | None = None
    topics: list[str] = field(default_factory=list)


@dataclass
class GitHubReleaseInfo:
    """Información sobre releases del repositorio."""

    total_count: int = 0
    latest_name: str | None = None
    latest_tag: str | None = None
    latest_date: str | None = None
    latest_prerelease: bool = False
    has_published_release: bool = False


@dataclass
class GitHubIssuesInfo:
    """Información sobre issues del repositorio."""

    open_count: int = 0


@dataclass
class GitHubPullRequestsInfo:
    """Información sobre pull requests del repositorio."""

    open_count: int = 0


@dataclass
class GitHubActionsInfo:
    """Información sobre GitHub Actions del repositorio."""

    has_workflows: bool = False
    requires_auth: bool = False
    latest_run_name: str | None = None
    latest_run_status: str | None = None
    latest_run_conclusion: str | None = None
    latest_run_branch: str | None = None
    latest_run_date: str | None = None


@dataclass
class GitHubDependabotInfo:
    """Información sobre Dependabot del repositorio."""

    has_alerts: bool | None = None
    alert_count: int | None = None
    requires_auth: bool = False


@dataclass
class GitHubAuditResult:
    """Resultado completo de la auditoría de GitHub."""

    repository: GitHubRepositoryInfo | None = None
    releases: GitHubReleaseInfo | None = None
    issues: GitHubIssuesInfo | None = None
    pull_requests: GitHubPullRequestsInfo | None = None
    actions: GitHubActionsInfo | None = None
    dependabot: GitHubDependabotInfo | None = None
    error: str | None = None
