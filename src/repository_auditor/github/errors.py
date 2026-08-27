"""Excepciones específicas para errores de la API de GitHub.

Todos los errores son seguros: nunca filtran tokens, credenciales ni datos sensibles.
"""

from __future__ import annotations


class GitHubError(Exception):
    """Error base para todas las excepciones de GitHub."""


class GitHubAuthenticationError(GitHubError):
    """Error de autenticación — token inválido o ausente."""

    def __init__(self, message: str = "Autenticación requerida o token inválido") -> None:
        super().__init__(message)


class GitHubNotFoundError(GitHubError):
    """Recurso no encontrado (404)."""

    def __init__(self, resource: str = "recurso") -> None:
        super().__init__(f"{resource} no encontrado en GitHub")


class GitHubRateLimitError(GitHubError):
    """Límite de tasa alcanzado (403/429)."""

    def __init__(
        self,
        message: str = "Límite de tasa de GitHub alcanzado",
        reset_at: str | None = None,
    ) -> None:
        self.reset_at = reset_at
        super().__init__(message)


class GitHubAPIError(GitHubError):
    """Error general de la API de GitHub."""

    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        detail = f" (HTTP {status_code})" if status_code else ""
        base = f"Error de la API de GitHub{detail}"
        msg = f"{base}: {message}" if message else base
        super().__init__(msg)


class GitHubNetworkError(GitHubError):
    """Error de red — no se pudo conectar a GitHub."""

    def __init__(self, message: str = "No se pudo conectar a GitHub") -> None:
        super().__init__(message)
