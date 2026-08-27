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
from repository_auditor.models.repository import AuditResult, RuleStatus
from repository_auditor.reports.json import (
    compare_audits,
    format_json,
    parse_audit_json,
)
from repository_auditor.reports.text import format_report
from repository_auditor.rules import evaluate_github_rules, evaluate_rules
from repository_auditor.scanner.filesystem import scan_documentation
from repository_auditor.scanner.git import scan_git
from repository_auditor.scanner.security import scan_security
from repository_auditor.scanner.technology import scan_technologies
from repository_auditor.scoring import calculate_score

# Exit codes
EXIT_OK = 0
EXIT_WARNINGS = 1
EXIT_FAILURES = 2
EXIT_ERROR = 3


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
        sys.exit(EXIT_ERROR)

    if not repo_path.is_dir():
        print(f"Error: La ruta '{path}' no es un directorio.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

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


def _determine_exit_code(result: AuditResult) -> int:
    """Determina el exit code basado en los resultados de las reglas."""
    has_fail = any(r.status == RuleStatus.FAIL for r in result.rule_results)
    has_warn = any(r.status == RuleStatus.WARN for r in result.rule_results)

    if has_fail:
        return EXIT_FAILURES
    if has_warn:
        return EXIT_WARNINGS
    return EXIT_OK


def _cmd_audit(args: argparse.Namespace) -> None:
    """Ejecuta el comando principal de auditoría."""
    local_result = run_local_audit(args.path)

    github_result = None
    if args.github and not args.no_github:
        github_result = run_github_audit(local_result)

    if github_result is not None:
        github_rules = evaluate_github_rules(local_result, github_result)
        local_result.rule_results.extend(github_rules)

    score_result = calculate_score(local_result.rule_results)

    if args.format == "json":
        output = format_json(local_result, github_result, score_result)
    else:
        output = format_report(local_result, github_result, score_result)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)

    sys.exit(_determine_exit_code(local_result))


def _cmd_compare(args: argparse.Namespace) -> None:
    """Ejecuta el comando de comparación de auditorías."""
    old_path = Path(args.old)
    new_path = Path(args.new)

    if not old_path.exists():
        print(f"Error: '{args.old}' no existe.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if not new_path.exists():
        print(f"Error: '{args.new}' no existe.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    try:
        old_data = parse_audit_json(old_path.read_text(encoding="utf-8"))
        new_data = parse_audit_json(new_path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    comparison = compare_audits(old_data, new_data)

    lines = []
    lines.append("Audit Comparison")
    lines.append("-" * 30)
    lines.append("")

    score = comparison["score"]
    lines.append("Score")
    lines.append(f"  Previous: {score['previous']}")
    lines.append(f"  Current:  {score['current']}")
    change = score["change"]
    sign = "+" if change > 0 else ""
    lines.append(f"  Change:   {sign}{change}")
    lines.append("")

    rating = comparison["rating"]
    lines.append("Rating")
    lines.append(f"  Previous: {rating['previous']}")
    lines.append(f"  Current:  {rating['current']}")
    lines.append("")

    new_failures = comparison["new_failures"]
    resolved = comparison["resolved_failures"]
    new_warnings = comparison["new_warnings"]

    lines.append(f"New failures:     {len(new_failures)}")
    lines.append(f"Resolved failures: {len(resolved)}")
    lines.append(f"New warnings:     {len(new_warnings)}")
    lines.append("")

    report = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
    else:
        print(report)


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada principal de la CLI."""
    parser = argparse.ArgumentParser(
        prog="repo-auditor",
        description="Repository Health Auditor — Auditor de repositorios Git/GitHub",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Subcomando: audit
    audit_parser = subparsers.add_parser(
        "audit",
        help="Auditar un repositorio",
    )
    audit_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Ruta al repositorio a auditar (por defecto: directorio actual)",
    )
    audit_parser.add_argument(
        "--github",
        action="store_true",
        default=False,
        help="Incluir auditoría de GitHub (requiere remote configurado)",
    )
    audit_parser.add_argument(
        "--no-github",
        action="store_true",
        default=False,
        help="Desactivar explícitamente la integración con GitHub",
    )
    audit_parser.add_argument(
        "--score",
        action="store_true",
        default=False,
        help="Mostrar score de salud del repositorio",
    )
    audit_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Formato de salida (por defecto: text)",
    )
    audit_parser.add_argument(
        "-o", "--output",
        help="Guardar resultado en archivo",
    )

    # Subcomando: compare
    compare_parser = subparsers.add_parser(
        "compare",
        help="Comparar dos auditorías previas",
    )
    compare_parser.add_argument(
        "old",
        help="Ruta al JSON de la auditoría anterior",
    )
    compare_parser.add_argument(
        "new",
        help="Ruta al JSON de la auditoría nueva",
    )
    compare_parser.add_argument(
        "-o", "--output",
        help="Guardar comparación en archivo",
    )

    # Soporte para uso directo sin subcomando (backward compatible)
    # Si el primer argumento no es un subcomando conocido, asumir "audit"
    args = argv if argv is not None else sys.argv[1:]

    # --version y --help van al parser principal (sin subcomando)
    if not args or (
        args[0] not in ("audit", "compare")
        and args[0] not in ("--version", "-V", "--help", "-h")
    ):
        args = ["audit"] + args

    parsed = parser.parse_args(args)

    if parsed.command == "compare":
        _cmd_compare(parsed)
    else:
        _cmd_audit(parsed)


if __name__ == "__main__":
    main()
