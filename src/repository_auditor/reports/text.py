"""Reporte de texto — genera salida legible para la consola.

Transforma AuditResult y GitHubAuditResult en texto formateado.
Soporta modos summary/verbose y colores con detección de TTY.
"""

from __future__ import annotations

import sys

from repository_auditor.github.models import GitHubAuditResult
from repository_auditor.models.repository import (
    AuditResult,
    RuleStatus,
)
from repository_auditor.scoring.models import ScoreResult

# --- Colores ANSI ---


class _Colors:
    """Códigos de color ANSI."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    DIM = "\033[2m"


_colors_enabled = False


def _enable_colors() -> None:
    global _colors_enabled
    _colors_enabled = True


def _disable_colors() -> None:
    global _colors_enabled
    _colors_enabled = False


def _c(code: str, text: str) -> str:
    """Envuelve texto con color si están habilitados."""
    if not _colors_enabled:
        return text
    return f"{code}{text}{_Colors.RESET}"


def _detect_tty() -> bool:
    """Detecta si stdout es un terminal."""
    try:
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    except Exception:
        return False


def _format_size(size_bytes: int) -> str:
    """Formatea un tamaño en bytes a formato legible."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} bytes"


def _status_icon(status: RuleStatus) -> str:
    """Retorna un ícono para un estado de regla."""
    icons = {
        RuleStatus.PASS: _c(_Colors.GREEN, "✓"),
        RuleStatus.WARN: _c(_Colors.YELLOW, "⚠"),
        RuleStatus.FAIL: _c(_Colors.RED, "✗"),
        RuleStatus.INFO: _c(_Colors.DIM, "ℹ"),
        RuleStatus.NOT_APPLICABLE: _c(_Colors.DIM, "—"),
    }
    return icons.get(status, "?")


def _bool_icon(value: bool) -> str:
    """Retorna ✓ o ✗ para un valor booleano."""
    if value:
        return _c(_Colors.GREEN, "✓")
    return _c(_Colors.RED, "✗")


def _format_github_section(github: GitHubAuditResult) -> list[str]:
    """Genera las líneas de la sección GitHub del reporte."""
    lines = []
    lines.append(_c(_Colors.BOLD, "GitHub"))
    lines.append("-" * 20)

    if github.error:
        lines.append(f"  Error: {_c(_Colors.RED, github.error)}")
        return lines

    repo = github.repository
    if repo:
        lines.append(f"  Repository: {repo.full_name}")
        if repo.visibility:
            lines.append(f"  Visibility: {repo.visibility}")
        if repo.default_branch:
            lines.append(f"  Default branch: {repo.default_branch}")
        lines.append(f"  Stars: {repo.stars}")
        lines.append(f"  Forks: {repo.forks}")
        lines.append(f"  Open issues: {repo.open_issues}")
        if repo.archived:
            lines.append(f"  Archived: {_bool_icon(True)}")
        if repo.fork:
            lines.append(f"  Fork: {_bool_icon(True)}")
        if repo.license:
            lines.append(f"  License: {repo.license}")
        if repo.topics:
            lines.append(f"  Topics: {', '.join(repo.topics)}")
    else:
        lines.append("  Repository: No disponible")

    prs = github.pull_requests
    if prs:
        lines.append(f"  Open PRs: {prs.open_count}")

    releases = github.releases
    if releases and releases.latest_tag:
        lines.append(f"  Latest release: {releases.latest_tag}")
        if releases.latest_date:
            lines.append(f"  Release date: {releases.latest_date}")
    elif releases:
        lines.append("  Releases: Ninguna")

    actions = github.actions
    if actions and actions.has_workflows:
        status = actions.latest_run_conclusion or actions.latest_run_status or "desconocido"
        lines.append(f"  GitHub Actions: {status}")
        if actions.latest_run_name:
            lines.append(f"  Latest workflow: {actions.latest_run_name}")
    elif actions:
        lines.append("  GitHub Actions: No configurado")

    dependabot = github.dependabot
    if dependabot:
        if dependabot.requires_auth:
            lines.append("  Dependabot: Requiere autenticación")
        elif dependabot.has_alerts:
            lines.append("  Dependabot: Alertas presentes")
        else:
            lines.append("  Dependabot: Sin alertas")

    return lines


def _format_summary(
    result: AuditResult,
    score: ScoreResult | None,
) -> str:
    """Genera un reporte resumido (solo score y resumen)."""
    lines = []
    lines.append(_c(_Colors.BOLD, "Repository Health"))
    lines.append("-" * 30)

    if score is not None:
        rating_color = {
            "EXCELLENT": _Colors.GREEN,
            "GOOD": _Colors.GREEN,
            "FAIR": _Colors.YELLOW,
            "POOR": _Colors.RED,
            "CRITICAL": _Colors.RED,
        }.get(score.rating.value, "")
        lines.append(
            f"  Score: {_c(_Colors.BOLD, f'{score.score}/{score.max_score}')}"
        )
        lines.append(f"  Rating: {_c(rating_color, score.rating.value)}")
        lines.append("")
        for cat in score.categories:
            pct = f"{cat.percentage:.0f}%"
            lines.append(
                f"  {cat.category:<15} "
                f"{cat.score:.0f}/{cat.max_score:.0f} ({pct})"
            )
    else:
        lines.append("  Score: No disponible")

    lines.append("")
    if result.rule_results:
        fail_count = sum(1 for r in result.rule_results if r.status == RuleStatus.FAIL)
        warn_count = sum(1 for r in result.rule_results if r.status == RuleStatus.WARN)
        if fail_count:
            lines.append(f"  {_c(_Colors.RED, f'{fail_count} failure(s)')}")
        if warn_count:
            lines.append(f"  {_c(_Colors.YELLOW, f'{warn_count} warning(s)')}")
        if not fail_count and not warn_count:
            lines.append(f"  {_c(_Colors.GREEN, 'All checks passed')}")

    return "\n".join(lines)


def _format_diagnostics(score: ScoreResult) -> list[str]:
    """Genera la sección de diagnósticos."""
    if not score.diagnostics:
        return []

    lines = []
    lines.append(_c(_Colors.BOLD, "Diagnostics"))
    lines.append("-" * 30)

    priority_icons = {
        "CRITICAL": _c(_Colors.RED, "[CRITICAL]"),
        "HIGH": _c(_Colors.RED, "[HIGH]"),
        "MEDIUM": _c(_Colors.YELLOW, "[MEDIUM]"),
        "LOW": _c(_Colors.BLUE, "[LOW]"),
        "INFO": _c(_Colors.DIM, "[INFO]"),
    }

    for diag in score.diagnostics:
        icon = priority_icons.get(diag.priority.value, "[?]")
        lines.append(f"  {icon} {diag.title}")

    lines.append("")

    has_recommendations = any(d.recommendation for d in score.diagnostics)
    if has_recommendations:
        lines.append(_c(_Colors.BOLD, "Recommendations"))
        lines.append("-" * 30)
        for i, diag in enumerate(score.diagnostics, 1):
            if diag.recommendation:
                lines.append(f"  {i}. {diag.recommendation}")
        lines.append("")

    return lines


def format_report(
    result: AuditResult,
    github: GitHubAuditResult | None = None,
    score: ScoreResult | None = None,
    *,
    summary: bool = False,
    verbose: bool = False,
    color: bool | None = None,
) -> str:
    """Genera un reporte de texto formateado.

    Args:
        result: Resultado completo del análisis local.
        github: Resultado de la auditoría de GitHub (opcional).
        score: Resultado del scoring (opcional).
        summary: Si True, solo muestra score y resumen.
        verbose: Si True, muestra todos los detalles.
        color: Si None, detecta TTY. Si True/False, fuerza color.

    Returns:
        Texto formateado para mostrar en consola.
    """
    # Configurar colores
    if color is None:
        if _detect_tty():
            _enable_colors()
        else:
            _disable_colors()
    elif color:
        _enable_colors()
    else:
        _disable_colors()

    if summary:
        return _format_summary(result, score)

    lines = []

    lines.append(_c(_Colors.BOLD, "Repository Health Auditor"))
    lines.append("=" * 40)
    lines.append("")

    lines.append(_c(_Colors.BOLD, "Repositorio:"))
    lines.append(f"  {result.repository.name}")
    lines.append("")
    lines.append(_c(_Colors.BOLD, "Ruta:"))
    lines.append(f"  {result.repository.path}")
    lines.append("")

    # Git
    lines.append(_c(_Colors.BOLD, "Git"))
    lines.append("-" * 20)
    if result.repository.is_git_repository:
        lines.append(f"  Repositorio Git: {_bool_icon(True)}")
        lines.append(f"  Rama actual: {result.repository.current_branch or 'desconocida'}")
        if result.repository.main_branch:
            lines.append(f"  Rama principal: {result.repository.main_branch}")
        lines.append(f"  Commits: {result.repository.commit_count}")
        if result.repository.latest_commit:
            lines.append(f"  Último commit: {result.repository.latest_commit}")
        if result.repository.latest_commit_date:
            lines.append(f"  Fecha: {result.repository.latest_commit_date}")
        if result.repository.tags:
            lines.append(f"  Tags: {', '.join(result.repository.tags)}")
        if result.repository.remote_urls:
            lines.append(f"  Remotes: {len(result.repository.remote_urls)}")
        dirty = result.repository.dirty_worktree
        lines.append(f"  Working tree: {'sucio' if dirty else 'limpio'}")
        if dirty and result.repository.modified_files:
            lines.append(f"  Archivos modificados: {len(result.repository.modified_files)}")
        if result.repository.untracked_files:
            lines.append(f"  Archivos sin seguimiento: {len(result.repository.untracked_files)}")
    else:
        lines.append(f"  Repositorio Git: {_bool_icon(False)}")
        lines.append("  (No es un repositorio Git)")
    lines.append("")

    # Documentación
    lines.append(_c(_Colors.BOLD, "Documentación"))
    lines.append("-" * 20)
    doc = result.documentation
    lines.append(f"  README:          {_bool_icon(doc.has_readme)}")
    lines.append(f"  LICENSE:         {_bool_icon(doc.has_license)}")
    lines.append(f"  CHANGELOG:       {_bool_icon(doc.has_changelog)}")
    lines.append(f"  CITATION.cff:    {_bool_icon(doc.has_citation)}")
    lines.append(f"  CONTRIBUTING:    {_bool_icon(doc.has_contributing)}")
    lines.append(f"  CODE_OF_CONDUCT: {_bool_icon(doc.has_code_of_conduct)}")
    lines.append(f"  SECURITY:        {_bool_icon(doc.has_security)}")
    lines.append(f"  .gitignore:      {_bool_icon(doc.has_gitignore)}")
    lines.append(f"  .gitattributes:  {_bool_icon(doc.has_gitattributes)}")
    lines.append(f"  .github/:        {_bool_icon(doc.has_github_directory)}")
    lines.append(f"  Workflows:       {_bool_icon(doc.has_workflows)}")
    lines.append(f"  Dependabot:      {_bool_icon(doc.has_dependabot)}")
    lines.append(f"  CodeQL:          {_bool_icon(doc.has_codeql)}")
    lines.append("")

    # Tecnologías
    lines.append(_c(_Colors.BOLD, "Tecnologías"))
    lines.append("-" * 20)
    tech = result.technologies
    if tech.languages:
        lines.append(f"  Lenguajes: {', '.join(tech.languages)}")
    if tech.frameworks:
        lines.append(f"  Frameworks: {', '.join(tech.frameworks)}")
    if tech.tools:
        lines.append(f"  Herramientas: {', '.join(tech.tools)}")
    if tech.config_files:
        lines.append(f"  Archivos de configuración: {len(tech.config_files)}")
    if not tech.languages and not tech.frameworks and not tech.tools:
        lines.append("  No se detectaron tecnologías")
    lines.append("")

    # Seguridad
    lines.append(_c(_Colors.BOLD, "Seguridad"))
    lines.append("-" * 20)
    high_count = sum(1 for f in result.security_findings if f.severity == "high")
    medium_count = sum(1 for f in result.security_findings if f.severity == "medium")
    lines.append(f"  Archivos sensibles (alta): {high_count}")
    lines.append(f"  Archivos sensibles (media): {medium_count}")
    lines.append(f"  Archivos grandes: {len(result.large_files)}")
    lines.append("")

    # GitHub
    if github is not None:
        lines.extend(_format_github_section(github))
        lines.append("")

    # Reglas (siempre en verbose, solo problemas en normal)
    if verbose:
        lines.append(_c(_Colors.BOLD, "Reglas de validación"))
        lines.append("-" * 20)
        if result.rule_results:
            for rule in result.rule_results:
                icon = _status_icon(rule.status)
                lines.append(f"  {icon} {rule.name}")
                if rule.status in (RuleStatus.FAIL, RuleStatus.WARN):
                    lines.append(f"    {rule.message}")
                    if rule.recommendation:
                        lines.append(f"    → {rule.recommendation}")
        else:
            lines.append("  No se evaluaron reglas")
        lines.append("")
    else:
        # Solo mostrar reglas con problemas
        problems = [
            r for r in result.rule_results
            if r.status in (RuleStatus.FAIL, RuleStatus.WARN)
        ]
        if problems:
            lines.append(_c(_Colors.BOLD, "Reglas con problemas"))
            lines.append("-" * 20)
            for rule in problems:
                icon = _status_icon(rule.status)
                lines.append(f"  {icon} {rule.name}")
                lines.append(f"    {rule.message}")
                if rule.recommendation:
                    lines.append(f"    → {rule.recommendation}")
            lines.append("")

    # Resumen
    lines.append(_c(_Colors.BOLD, "Estado"))
    lines.append("-" * 20)
    if result.rule_results:
        pass_count = sum(1 for r in result.rule_results if r.status == RuleStatus.PASS)
        warn_count = sum(1 for r in result.rule_results if r.status == RuleStatus.WARN)
        fail_count = sum(1 for r in result.rule_results if r.status == RuleStatus.FAIL)
        lines.append(f"  Reglas evaluadas: {len(result.rule_results)}")
        lines.append(f"  {_c(_Colors.GREEN, f'Pasadas: {pass_count}')}")
        if warn_count:
            lines.append(f"  {_c(_Colors.YELLOW, f'Advertencias: {warn_count}')}")
        else:
            lines.append(f"  Advertencias: {warn_count}")
        if fail_count:
            lines.append(f"  {_c(_Colors.RED, f'Fallidas: {fail_count}')}")
        else:
            lines.append(f"  Fallidas: {fail_count}")
    lines.append("")

    # Score
    if score is not None:
        lines.append(_c(_Colors.BOLD, "Repository Health"))
        lines.append("-" * 30)
        rating_color = {
            "EXCELLENT": _Colors.GREEN,
            "GOOD": _Colors.GREEN,
            "FAIR": _Colors.YELLOW,
            "POOR": _Colors.RED,
            "CRITICAL": _Colors.RED,
        }.get(score.rating.value, "")
        lines.append(
            f"  Score: {_c(_Colors.BOLD, f'{score.score}/{score.max_score}')}"
        )
        lines.append(f"  Rating: {_c(rating_color, score.rating.value)}")
        lines.append("")
        for cat in score.categories:
            pct = f"{cat.percentage:.0f}%"
            lines.append(
                f"  {cat.category:<15} "
                f"{cat.score:.0f}/{cat.max_score:.0f} ({pct})"
            )
        lines.append("")

    # Diagnósticos
    if score is not None:
        lines.extend(_format_diagnostics(score))

    lines.append(_c(_Colors.BOLD, "  ANÁLISIS COMPLETADO"))

    return "\n".join(lines)
