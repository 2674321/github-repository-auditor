"""CLI — interfaz de línea de comandos para el auditor de repositorios.

Ejecuta el análisis completo de un repositorio local y, opcionalmente,
complementa con información de GitHub.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repository_auditor import __version__
from repository_auditor.github import (
    GitHubAuditResult,
    find_github_remote,
)
from repository_auditor.github.client import audit_github
from repository_auditor.models.repository import AuditResult
from repository_auditor.reports.text import format_report
from repository_auditor.rules import evaluate_github_rules, evaluate_rules
from repository_auditor.scanner.filesystem import scan_documentation
from repository_auditor.scanner.git import scan_git
from repository_auditor.scanner.security import scan_security
from repository_auditor.scanner.technology import scan_technologies
from repository_auditor.scoring import calculate_score


def run_local_audit(path: str) -> AuditResult:
    """Ejecuta el análisis local de un repositorio.

    Args:
        path: Ruta al directorio del repositorio.

    Returns:
        AuditResult con toda la información recopilada.
    """
    repo_path = Path(path).resolve()

    if not repo_path.exists():
        print(f"Error: La ruta '{path}' no existe.", file=sys.stderr)
        sys.exit(1)

    if not repo_path.is_dir():
        print(f"Error: La ruta '{path}' no es un directorio.", file=sys.stderr)
        sys.exit(1)

    git_info = scan_git(str(repo_path))
    doc_info = scan_documentation(repo_path)
    tech_info = scan_technologies(repo_path)
    security_findings, large_files = scan_security(repo_path)

    result = AuditResult(
        repository=git_info,
        documentation=doc_info,
        technologies=tech_info,
        security_findings=security_findings,
        large_files=large_files,
    )

    result.rule_results = evaluate_rules(result)

    return result


def run_github_audit(local_result: AuditResult) -> GitHubAuditResult | None:
    """Ejecuta la auditoría de GitHub si es posible.

    Args:
        local_result: Resultado de la auditoría local.

    Returns:
        GitHubAuditResult si se pudo conectar, None en caso contrario.
    """
    if not local_result.repository.remote_urls:
        return None

    remote = find_github_remote(local_result.repository.remote_urls)
    if remote is None or not remote.is_github:
        return None

    if not remote.owner or not remote.repository:
        return None

    try:
        return audit_github(remote.owner, remote.repository)
    except Exception as e:
        error_result = GitHubAuditResult()
        error_result.error = str(e)
        return error_result


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada principal de la CLI."""
    parser = argparse.ArgumentParser(
        prog="repo-auditor",
        description="Repository Health Auditor — Auditor de repositorios Git/GitHub",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Ruta al repositorio a auditar (por defecto: directorio actual)",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        default=False,
        help="Incluir auditoría de GitHub (requiere remote configurado)",
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        default=False,
        help="Desactivar explícitamente la integración con GitHub",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        default=False,
        help="Mostrar score de salud del repositorio",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    local_result = run_local_audit(args.path)

    github_result = None
    if args.github and not args.no_github:
        github_result = run_github_audit(local_result)

    if github_result is not None:
        github_rules = evaluate_github_rules(local_result, github_result)
        local_result.rule_results.extend(github_rules)

    score_result = calculate_score(local_result.rule_results)

    report = format_report(local_result, github_result, score_result)
    print(report)


if __name__ == "__main__":
    main()
