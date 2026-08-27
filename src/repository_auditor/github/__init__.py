"""Módulo de integración con GitHub API.

Proporciona parsing de URLs, cliente HTTP y modelos para la
auditoría de repositorios en GitHub.
"""

from repository_auditor.github.client import audit_github
from repository_auditor.github.errors import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubError,
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
from repository_auditor.github.url_parser import GitHubRemote, find_github_remote, parse_github_url

__all__ = [
    "GitHubRemote",
    "audit_github",
    "find_github_remote",
    "parse_github_url",
    "GitHubAPIError",
    "GitHubAuthenticationError",
    "GitHubError",
    "GitHubNetworkError",
    "GitHubNotFoundError",
    "GitHubRateLimitError",
    "GitHubActionsInfo",
    "GitHubAuditResult",
    "GitHubDependabotInfo",
    "GitHubIssuesInfo",
    "GitHubPullRequestsInfo",
    "GitHubReleaseInfo",
    "GitHubRepositoryInfo",
]
