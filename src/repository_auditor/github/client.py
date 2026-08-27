"""Cliente HTTP para la API de GitHub — utiliza stdlib (urllib).

Encapsula la comunicación con la API REST de GitHub.
Soporta autenticación mediante GITHUB_TOKEN.
Nunca filtra tokens en errores o mensajes.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from repository_auditor.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from repository_auditor.github.models import (
    GitHubActionsInfo,
    GitHubAuditResult,
    GitHubDependabotInfo,
    GitHubIssuesInfo,
    GitHubPullRequestsInfo,
    GitHubReleaseInfo,
    GitHubRepositoryInfo,
)

DEFAULT_API_URL = "https://api.github.com"


def _get_token() -> str | None:
    """Obtiene el token de autenticación de la variable de entorno.

    Returns:
        Token si existe, None en caso contrario.
    """
    return os.environ.get("GITHUB_TOKEN")


def _get_api_url() -> str:
    """Obtiene la URL base de la API de GitHub."""
    return os.environ.get("GITHUB_API_URL", DEFAULT_API_URL)


def _make_request(
    endpoint: str,
    token: str | None = None,
    timeout: int = 15,
) -> dict[str, Any] | list[Any] | None:
    """Realiza una petición GET a la API de GitHub.

    Args:
        endpoint: Endpoint relativo (ej: /repos/owner/repo).
        token: Token de autenticación. Si no se provee, se busca en GITHUB_TOKEN.
        timeout: Timeout en segundos.

    Returns:
        Respuesta JSON parseada o None si la respuesta está vacía.

    Raises:
        GitHubAuthenticationError: Si el token es inválido o ausente.
        GitHubNotFoundError: Si el recurso no existe (404).
        GitHubRateLimitError: Si se alcanzó el límite de tasa.
        GitHubAPIError: Para otros errores HTTP.
        GitHubNetworkError: Si no se pudo conectar.
    """
    if token is None:
        token = _get_token()

    api_url = _get_api_url()
    url = f"{api_url}{endpoint}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "repository-auditor/0.1.0",
    }

    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            if not data.strip():
                return None
            return json.loads(data)
    except urllib.error.HTTPError as e:
        status = e.code
        if status == 401:
            raise GitHubAuthenticationError(
                "Token inválido o expirado"
            ) from None
        if status == 403:
            reset = (
                e.headers.get("X-RateLimit-Reset") if e.headers else None
            )
            raise GitHubRateLimitError(reset_at=reset) from None
        if status == 404:
            raise GitHubNotFoundError(
                "Repositorio o recurso"
            ) from None
        if status == 429:
            reset = (
                e.headers.get("X-RateLimit-Reset") if e.headers else None
            )
            raise GitHubRateLimitError(reset_at=reset) from None
        raise GitHubAPIError(status_code=status) from None
    except urllib.error.URLError:
        raise GitHubNetworkError() from None
    except json.JSONDecodeError:
        raise GitHubAPIError(
            status_code=0, message="Respuesta JSON inválida"
        ) from None


def fetch_repository(owner: str, repo: str) -> GitHubRepositoryInfo:
    """Consulta la información del repositorio.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubRepositoryInfo con la información obtenida.
    """
    data = _make_request(f"/repos/{owner}/{repo}")

    if not data or not isinstance(data, dict):
        raise GitHubAPIError(status_code=0, message="Respuesta vacía o inválida")

    license_info = data.get("license")
    license_name = license_info.get("spdx_id") if isinstance(license_info, dict) else None

    return GitHubRepositoryInfo(
        owner=data.get("owner", {}).get("login", owner),
        name=data.get("name", repo),
        full_name=data.get("full_name", f"{owner}/{repo}"),
        description=data.get("description"),
        url=data.get("html_url"),
        default_branch=data.get("default_branch"),
        visibility=data.get("visibility"),
        archived=data.get("archived", False),
        fork=data.get("fork", False),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        open_issues=data.get("open_issues_count", 0),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        pushed_at=data.get("pushed_at"),
        license=license_name,
        topics=data.get("topics", []),
    )


def fetch_releases(owner: str, repo: str) -> GitHubReleaseInfo:
    """Consulta las releases del repositorio.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubReleaseInfo con la información de releases.
    """
    try:
        data = _make_request(f"/repos/{owner}/{repo}/releases?per_page=10")
    except (GitHubNotFoundError, GitHubAPIError):
        return GitHubReleaseInfo()

    if not data or not isinstance(data, list) or len(data) == 0:
        return GitHubReleaseInfo(total_count=0)

    latest = data[0]
    has_published = any(not r.get("draft", False) for r in data)

    return GitHubReleaseInfo(
        total_count=len(data),
        latest_name=latest.get("name") or latest.get("tag_name"),
        latest_tag=latest.get("tag_name"),
        latest_date=latest.get("published_at"),
        latest_prerelease=latest.get("prerelease", False),
        has_published_release=has_published,
    )


def fetch_issues(owner: str, repo: str) -> GitHubIssuesInfo:
    """Consulta issues abiertas del repositorio.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubIssuesInfo con la información de issues.
    """
    try:
        data = _make_request(f"/repos/{owner}/{repo}/issues?state=open&per_page=1")
    except (GitHubNotFoundError, GitHubAPIError):
        return GitHubIssuesInfo()

    if not data or not isinstance(data, list):
        return GitHubIssuesInfo()

    return GitHubIssuesInfo(open_count=len(data))


def fetch_pull_requests(owner: str, repo: str) -> GitHubPullRequestsInfo:
    """Consulta PRs abiertas del repositorio.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubPullRequestsInfo con la información de PRs.
    """
    try:
        data = _make_request(f"/repos/{owner}/{repo}/pulls?state=open&per_page=1")
    except (GitHubNotFoundError, GitHubAPIError):
        return GitHubPullRequestsInfo()

    if not data or not isinstance(data, list):
        return GitHubPullRequestsInfo()

    return GitHubPullRequestsInfo(open_count=len(data))


def fetch_actions(owner: str, repo: str) -> GitHubActionsInfo:
    """Consulta la información de GitHub Actions.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubActionsInfo con la información de workflows.
    """
    try:
        data = _make_request(f"/repos/{owner}/{repo}/actions/runs?per_page=1")
    except GitHubAuthenticationError:
        return GitHubActionsInfo(has_workflows=False, requires_auth=True)
    except (GitHubNotFoundError, GitHubAPIError):
        return GitHubActionsInfo()

    if not data or not isinstance(data, dict):
        return GitHubActionsInfo()

    runs = data.get("workflow_runs", [])
    if not runs:
        return GitHubActionsInfo(has_workflows=False)

    latest = runs[0]
    return GitHubActionsInfo(
        has_workflows=True,
        latest_run_name=latest.get("name"),
        latest_run_status=latest.get("status"),
        latest_run_conclusion=latest.get("conclusion"),
        latest_run_branch=latest.get("head_branch"),
        latest_run_date=latest.get("updated_at"),
    )


def fetch_dependabot(owner: str, repo: str) -> GitHubDependabotInfo:
    """Consulta la información de Dependabot.

    Nota: El endpoint de Dependabot alerts requiere autenticación
    y permisos de seguridad. Si no es posible acceder, se retorna
    información parcial.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubDependabotInfo con la información disponible.
    """
    try:
        data = _make_request(
            f"/repos/{owner}/{repo}/vulnerability-alerts",
        )
        if data and isinstance(data, dict):
            return GitHubDependabotInfo(
                has_alerts=True,
                requires_auth=False,
            )
        return GitHubDependabotInfo(has_alerts=False, requires_auth=False)
    except GitHubAuthenticationError:
        return GitHubDependabotInfo(requires_auth=True)
    except (GitHubNotFoundError, GitHubAPIError):
        return GitHubDependabotInfo(requires_auth=True)


def audit_github(owner: str, repo: str) -> GitHubAuditResult:
    """Ejecuta una auditoría completa del repositorio en GitHub.

    Args:
        owner: Propietario del repositorio.
        repo: Nombre del repositorio.

    Returns:
        GitHubAuditResult con toda la información recopilada.
    """
    result = GitHubAuditResult()

    try:
        result.repository = fetch_repository(owner, repo)
    except Exception as e:
        result.error = str(e)
        return result

    try:
        result.releases = fetch_releases(owner, repo)
    except Exception:
        result.releases = GitHubReleaseInfo()

    try:
        result.issues = fetch_issues(owner, repo)
    except Exception:
        result.issues = GitHubIssuesInfo()

    try:
        result.pull_requests = fetch_pull_requests(owner, repo)
    except Exception:
        result.pull_requests = GitHubPullRequestsInfo()

    try:
        result.actions = fetch_actions(owner, repo)
    except Exception:
        result.actions = GitHubActionsInfo()

    try:
        result.dependabot = fetch_dependabot(owner, repo)
    except Exception:
        result.dependabot = GitHubDependabotInfo()

    return result
