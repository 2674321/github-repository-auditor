"""Parser de URLs de GitHub — extrae owner y repository desde URLs de remote.

Soporta:
- HTTPS: https://github.com/owner/repo.git
- HTTPS sin .git: https://github.com/owner/repo
- SSH: git@github.com:owner/repo.git
- SSH URL: ssh://git@github.com/owner/repo.git

No asumir que todos los remotes son GitHub.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GitHubRemote:
    """Resultado del parsing de una URL de remote."""

    is_github: bool
    owner: str | None = None
    repository: str | None = None
    url: str = ""


# Patrones de URLs de GitHub
_GITHUB_HTTPS_PATTERNS = [
    # https://github.com/owner/repo.git or https://github.com/owner/repo.git/
    re.compile(r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?(?:/)?$"),
    # https://github.com/owner/repo (sin .git)
]

_GITHUB_SSH_PATTERNS = [
    # git@github.com:owner/repo.git
    re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"),
    # ssh://git@github.com/owner/repo.git
    re.compile(r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$"),
]


def parse_github_url(url: str) -> GitHubRemote:
    """Parsea una URL de remote y extrae owner/repo si es de GitHub.

    Args:
        url: URL del remote (HTTPS o SSH).

    Returns:
        GitHubRemote con la información extraída.
    """
    url = url.strip()

    for pattern in _GITHUB_HTTPS_PATTERNS:
        match = pattern.match(url)
        if match:
            return GitHubRemote(
                is_github=True,
                owner=match.group("owner"),
                repository=match.group("repo"),
                url=url,
            )

    for pattern in _GITHUB_SSH_PATTERNS:
        match = pattern.match(url)
        if match:
            return GitHubRemote(
                is_github=True,
                owner=match.group("owner"),
                repository=match.group("repo"),
                url=url,
            )

    return GitHubRemote(is_github=False, url=url)


def find_github_remote(remote_urls: list[str]) -> GitHubRemote | None:
    """Busca un remote de GitHub en la lista de URLs configuradas.

    Args:
        remote_urls: Lista de URLs de remotes del repositorio.

    Returns:
        GitHubRemote si se encontró un remote de GitHub, None en caso contrario.
    """
    for url in remote_urls:
        result = parse_github_url(url)
        if result.is_github:
            return result
    return None
