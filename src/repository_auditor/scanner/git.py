"""Scanner de Git — obtiene información de repositorios Git locales.

Utiliza subprocess para ejecutar comandos git de solo lectura.
Nunca ejecuta comandos destructivos.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from repository_auditor.models.repository import RepositoryInfo


def _run_git(args: list[str], cwd: str) -> str | None:
    """Ejecuta un comando git de forma segura.

    Args:
        args: Argumentos del comando git (sin 'git').
        cwd: Directorio de trabajo.

    Returns:
        Salida del comando o None si falla.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def is_git_repository(path: str) -> bool:
    """Verifica si la ruta es un repositorio Git válido."""
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return result == "true"


def get_current_branch(path: str) -> str | None:
    """Obtiene la rama actual del repositorio."""
    return _run_git(["branch", "--show-current"], cwd=path)


def get_main_branch(path: str) -> str | None:
    """Intenta determinar la rama principal del repositorio.

    Primero busca 'main', luego 'master'.
    """
    branches_output = _run_git(["branch", "-a"], cwd=path)
    if not branches_output:
        return None

    branches = [line.strip().lstrip("* ") for line in branches_output.split("\n") if line.strip()]

    if "main" in branches:
        return "main"
    if "master" in branches:
        return "master"
    if branches:
        return branches[0]
    return None


def get_commit_count(path: str) -> int:
    """Obtiene el número aproximado de commits."""
    result = _run_git(["rev-list", "--count", "HEAD"], cwd=path)
    if result is not None:
        try:
            return int(result)
        except ValueError:
            pass
    return 0


def get_latest_commit(path: str) -> str | None:
    """Obtiene el hash del último commit."""
    return _run_git(["rev-parse", "--short", "HEAD"], cwd=path)


def get_latest_commit_date(path: str) -> str | None:
    """Obtiene la fecha del último commit en formato ISO."""
    return _run_git(["log", "-1", "--format=%ci"], cwd=path)


def get_tags(path: str) -> list[str]:
    """Obtiene la lista de tags del repositorio."""
    result = _run_git(["tag", "--sort=-version:refname"], cwd=path)
    if not result:
        return []
    return [tag.strip() for tag in result.split("\n") if tag.strip()]


def get_remote_urls(path: str) -> list[str]:
    """Obtiene las URLs de los remotes configurados."""
    result = _run_git(["remote", "-v"], cwd=path)
    if not result:
        return []
    urls = []
    for line in result.split("\n"):
        if "\t" in line:
            url = line.split("\t")[1].split(" ")[0]
            if url not in urls:
                urls.append(url)
    return urls


def is_dirty(path: str) -> bool:
    """Verifica si el working tree tiene cambios sin confirmar."""
    result = _run_git(["status", "--porcelain"], cwd=path)
    return bool(result)


def get_modified_files(path: str) -> list[str]:
    """Obtiene la lista de archivos modificados sin confirmar."""
    result = _run_git(["status", "--porcelain"], cwd=path)
    if not result:
        return []
    files = []
    for line in result.split("\n"):
        if line.strip():
            status = line[:2].strip()
            filename = line[3:].strip()
            if status in ("M", "A", "D", "R", "C"):
                files.append(filename)
    return files


def get_untracked_files(path: str) -> list[str]:
    """Obtiene la lista de archivos sin seguimiento."""
    result = _run_git(["status", "--porcelain"], cwd=path)
    if not result:
        return []
    files = []
    for line in result.split("\n"):
        if line.strip() and line.startswith("??"):
            filename = line[3:].strip()
            files.append(filename)
    return files


def scan_git(path: str) -> RepositoryInfo:
    """Realiza un escaneo completo de información Git del repositorio.

    Args:
        path: Ruta al directorio del repositorio.

    Returns:
        RepositoryInfo con toda la información detectada.
    """
    repo_path = Path(path)
    is_git = is_git_repository(path)

    info = RepositoryInfo(
        path=str(repo_path.resolve()),
        name=repo_path.name,
        is_git_repository=is_git,
    )

    if not is_git:
        return info

    info.current_branch = get_current_branch(path)
    info.main_branch = get_main_branch(path)
    info.remote_urls = get_remote_urls(path)
    info.commit_count = get_commit_count(path)
    info.latest_commit = get_latest_commit(path)
    info.latest_commit_date = get_latest_commit_date(path)
    info.tags = get_tags(path)
    info.dirty_worktree = is_dirty(path)
    info.modified_files = get_modified_files(path)
    info.untracked_files = get_untracked_files(path)

    return info
