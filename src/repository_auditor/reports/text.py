"""Reporte de texto — genera salida legible para la consola.

Transforma AuditResult y GitHubAuditResult en texto formateado.
NO contiene lógica de análisis.
"""

from __future__ import annotations

from repository_auditor.github.models import GitHubAuditResult
from repository_auditor.models.repository import (
    AuditResult,
    RuleStatus,
)
from repository_auditor.scoring.models import ScoreResult


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
        RuleStatus.PASS: "✓",
        RuleStatus.WARN: "⚠",
        RuleStatus.FAIL: "✗",
        RuleStatus.INFO: "ℹ",
        RuleStatus.NOT_APPLICABLE: "—",
    }
    return icons.get(status, "?")


def _bool_icon(value: bool) -> str:
    """Retorna ✓ o ✗ para un valor booleano."""
    return "✓" if value else "✗"


def _format_github_section(github: GitHubAuditResult) -> list[str]:
    """Genera las líneas de la sección GitHub del reporte.

    Args:
        github: Resultado de la auditoría de GitHub.

    Returns:
        Lista de líneas formateadas.
    """
    lines = []
    lines.append("GitHub")
    lines.append("-" * 20)

    if github.error:
        lines.append(f"  Error: {github.error}")
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

    # PRs
    prs = github.pull_requests
    if prs:
        lines.append(f"  Open PRs: {prs.open_count}")

    # Releases
    releases = github.releases
    if releases and releases.latest_tag:
        lines.append(f"  Latest release: {releases.latest_tag}")
        if releases.latest_date:
            lines.append(f"  Release date: {releases.latest_date}")
    elif releases:
        lines.append("  Releases: Ninguna")

    # Actions
    actions = github.actions
    if actions and actions.has_workflows:
        status = actions.latest_run_conclusion or actions.latest_run_status or "desconocido"
        lines.append(f"  GitHub Actions: {status}")
        if actions.latest_run_name:
            lines.append(f"  Latest workflow: {actions.latest_run_name}")
    elif actions:
        lines.append("  GitHub Actions: No configurado")

    # Dependabot
    dependabot = github.dependabot
    if dependabot:
        if dependabot.requires_auth:
            lines.append("  Dependabot: Requiere autenticación")
        elif dependabot.has_alerts:
            lines.append("  Dependabot: Alertas presentes")
        else:
            lines.append("  Dependabot: Sin alertas")

    return lines


def format_report(
    result: AuditResult,
    github: GitHubAuditResult | None = None,
    score: ScoreResult | None = None,
) -> str:
    """Genera un reporte de texto formateado.

    Args:
        result: Resultado completo del análisis local.
        github: Resultado de la auditoría de GitHub (opcional).
        score: Resultado del scoring (opcional).

    Returns:
        Texto formateado para mostrar en consola.
    """
    lines = []

    lines.append("Repository Health Auditor")
    lines.append("=" * 40)
    lines.append("")

    lines.append("Repositorio:")
    lines.append(f"  {result.repository.name}")
    lines.append("")
    lines.append("Ruta:")
    lines.append(f"  {result.repository.path}")
    lines.append("")

    # Sección de Git
    lines.append("Git")
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

    # Sección de documentación
    lines.append("Documentación")
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

    # Sección de tecnologías
    lines.append("Tecnologías")
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

    # Sección de seguridad
    lines.append("Seguridad")
    lines.append("-" * 20)
    high_count = sum(1 for f in result.security_findings if f.severity == "high")
    medium_count = sum(1 for f in result.security_findings if f.severity == "medium")
    lines.append(f"  Archivos sensibles (alta): {high_count}")
    lines.append(f"  Archivos sensibles (media): {medium_count}")
    lines.append(f"  Archivos grandes: {len(result.large_files)}")
    lines.append("")

    # Sección de GitHub (si aplica)
    if github is not None:
        lines.extend(_format_github_section(github))
        lines.append("")

    # Sección de reglas
    lines.append("Reglas de validación")
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

    # Resumen
    lines.append("Estado")
    lines.append("-" * 20)
    if result.rule_results:
        pass_count = sum(1 for r in result.rule_results if r.status == RuleStatus.PASS)
        warn_count = sum(1 for r in result.rule_results if r.status == RuleStatus.WARN)
        fail_count = sum(1 for r in result.rule_results if r.status == RuleStatus.FAIL)
        lines.append(f"  Reglas evaluadas: {len(result.rule_results)}")
        lines.append(f"  Pasadas: {pass_count}")
        lines.append(f"  Advertencias: {warn_count}")
        lines.append(f"  Fallidas: {fail_count}")
    lines.append("")

    # Sección de score (si se solicita)
    if score is not None:
        lines.append("Repository Health")
        lines.append("-" * 20)
        lines.append(f"  Score: {score.score}/{score.max_score}")
        lines.append(f"  Rating: {score.rating.value}")
        lines.append("")
        for cat in score.categories:
            pct = f"{cat.percentage:.0f}%"
            lines.append(
                f"  {cat.category:<15} "
                f"{cat.score:.0f}/{cat.max_score:.0f} ({pct})"
            )
        lines.append("")

    lines.append("  ANÁLISIS COMPLETADO")

    return "\n".join(lines)
