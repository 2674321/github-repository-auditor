"""Módulo de reglas — evalúa la información detectada contra criterios.

R0.5/R0.6: reglas simples y conservadoras.
Cada regla produce un RuleResult estructurado.
"""

from __future__ import annotations

from repository_auditor.github.models import GitHubAuditResult
from repository_auditor.models.repository import (
    AuditResult,
    RuleResult,
    RuleStatus,
    Severity,
)

# --- Reglas de auditoría local (R0.5) ---


def _rule_readme(result: AuditResult) -> RuleResult:
    """Verifica si existe un README."""
    status = RuleStatus.PASS if result.documentation.has_readme else RuleStatus.FAIL
    has = result.documentation.has_readme
    return RuleResult(
        rule_id="doc-readme",
        name="README",
        category="documentation",
        status=status,
        severity=Severity.HIGH if status == RuleStatus.FAIL else Severity.INFO,
        message="README detectado" if has else "No se detectó README",
        recommendation=(
            "Crear un archivo README.md que describa el proyecto"
            if status == RuleStatus.FAIL else ""
        ),
    )


def _rule_license(result: AuditResult) -> RuleResult:
    """Verifica si existe una licencia."""
    status = RuleStatus.WARN if not result.documentation.has_license else RuleStatus.PASS
    has = result.documentation.has_license
    return RuleResult(
        rule_id="doc-license",
        name="LICENSE",
        category="documentation",
        status=status,
        severity=Severity.MEDIUM,
        message="Licencia detectada" if has else "No se detectó archivo de licencia",
        recommendation=(
            "Agregar un archivo LICENSE para definir los términos de uso"
            if status == RuleStatus.WARN else ""
        ),
    )


def _rule_gitignore(result: AuditResult) -> RuleResult:
    """Verifica si existe un .gitignore."""
    status = RuleStatus.WARN if not result.documentation.has_gitignore else RuleStatus.PASS
    has = result.documentation.has_gitignore
    return RuleResult(
        rule_id="doc-gitignore",
        name=".gitignore",
        category="documentation",
        status=status,
        severity=Severity.MEDIUM,
        message=".gitignore detectado" if has else "No se detectó .gitignore",
        recommendation=(
            "Crear un .gitignore para evitar subir archivos no deseados"
            if status == RuleStatus.WARN else ""
        ),
    )


def _rule_changelog(result: AuditResult) -> RuleResult:
    """Verifica si existe un CHANGELOG."""
    status = RuleStatus.INFO if not result.documentation.has_changelog else RuleStatus.PASS
    has = result.documentation.has_changelog
    return RuleResult(
        rule_id="doc-changelog",
        name="CHANGELOG",
        category="documentation",
        status=status,
        severity=Severity.LOW,
        message="CHANGELOG detectado" if has else "No se detectó CHANGELOG",
        recommendation=(
            "Considerar agregar un CHANGELOG para historial de cambios"
            if status == RuleStatus.INFO else ""
        ),
    )


def _rule_citation(result: AuditResult) -> RuleResult:
    """Verifica si existe CITATION.cff."""
    status = RuleStatus.INFO if not result.documentation.has_citation else RuleStatus.PASS
    has = result.documentation.has_citation
    return RuleResult(
        rule_id="doc-citation",
        name="CITATION.cff",
        category="documentation",
        status=status,
        severity=Severity.LOW,
        message="CITATION.cff detectado" if has else "No se detectó CITATION.cff",
        recommendation=(
            "Considerar agregar CITATION.cff para citación académica"
            if status == RuleStatus.INFO else ""
        ),
    )


def _rule_security_high(result: AuditResult) -> RuleResult:
    """Verifica archivos de seguridad de alta severidad."""
    high_findings = [f for f in result.security_findings if f.severity == "high"]
    if high_findings:
        count = len(high_findings)
        return RuleResult(
            rule_id="sec-high",
            name="Archivos sensibles de alta severidad",
            category="security",
            status=RuleStatus.FAIL,
            severity=Severity.HIGH,
            message=(
                f"Se detectaron {count} archivo(s) potencialmente "
                f"sensibles de alta severidad"
            ),
            recommendation="Revisar si estos archivos deberían estar en .gitignore",
        )
    return RuleResult(
        rule_id="sec-high",
        name="Archivos sensibles de alta severidad",
        category="security",
        status=RuleStatus.PASS,
        severity=Severity.HIGH,
        message="No se detectaron archivos sensibles de alta severidad",
    )


def _rule_large_files(result: AuditResult) -> RuleResult:
    """Verifica archivos grandes."""
    if result.large_files:
        count = len(result.large_files)
        return RuleResult(
            rule_id="sec-large",
            name="Archivos grandes",
            category="security",
            status=RuleStatus.WARN,
            severity=Severity.LOW,
            message=f"Se detectaron {count} archivo(s) grandes (>1 MB)",
            recommendation="Considerar Git LFS o compresión para archivos grandes",
        )
    return RuleResult(
        rule_id="sec-large",
        name="Archivos grandes",
        category="security",
        status=RuleStatus.PASS,
        severity=Severity.LOW,
        message="No se detectaron archivos grandes",
    )


def _rule_git_valid(result: AuditResult) -> RuleResult:
    """Verifica si es un repositorio Git válido."""
    if result.repository.is_git_repository:
        return RuleResult(
            rule_id="git-valid",
            name="Repositorio Git",
            category="git",
            status=RuleStatus.PASS,
            severity=Severity.INFO,
            message="La ruta es un repositorio Git válido",
        )
    return RuleResult(
        rule_id="git-valid",
        name="Repositorio Git",
        category="git",
        status=RuleStatus.FAIL,
        severity=Severity.HIGH,
        message="La ruta NO es un repositorio Git",
        recommendation="Inicializar un repositorio con 'git init'",
    )


def _rule_dirty_worktree(result: AuditResult) -> RuleResult:
    """Verifica si hay cambios sin confirmar."""
    if not result.repository.is_git_repository:
        return RuleResult(
            rule_id="git-dirty",
            name="Working tree limpio",
            category="git",
            status=RuleStatus.NOT_APPLICABLE,
            severity=Severity.INFO,
            message="No aplica — no es repositorio Git",
        )
    if result.repository.dirty_worktree:
        count = len(result.repository.modified_files)
        return RuleResult(
            rule_id="git-dirty",
            name="Working tree limpio",
            category="git",
            status=RuleStatus.WARN,
            severity=Severity.LOW,
            message=f"Hay {count} archivo(s) modificado(s) sin confirmar",
            recommendation="Confirmar o descartar cambios pendientes",
        )
    return RuleResult(
        rule_id="git-dirty",
        name="Working tree limpio",
        category="git",
        status=RuleStatus.PASS,
        severity=Severity.INFO,
        message="Working tree limpio",
    )


ALL_RULES = [
    _rule_readme,
    _rule_license,
    _rule_gitignore,
    _rule_changelog,
    _rule_citation,
    _rule_security_high,
    _rule_large_files,
    _rule_git_valid,
    _rule_dirty_worktree,
]


def evaluate_rules(result: AuditResult) -> list[RuleResult]:
    """Evalúa todas las reglas locales sobre un resultado de auditoría.

    Args:
        result: Resultado del análisis del repositorio.

    Returns:
        Lista de resultados de reglas.
    """
    rule_results = []
    for rule_fn in ALL_RULES:
        try:
            rule_results.append(rule_fn(result))
        except Exception as e:
            rule_results.append(
                RuleResult(
                    rule_id=f"error-{rule_fn.__name__}",
                    name=rule_fn.__name__,
                    category="error",
                    status=RuleStatus.FAIL,
                    severity=Severity.MEDIUM,
                    message=f"Error ejecutando regla: {e}",
                )
            )
    return rule_results


# --- Reglas de auditoría GitHub (R0.6) ---


def _rule_github_remote(result: AuditResult, github: GitHubAuditResult) -> RuleResult:
    """Verifica si el repositorio tiene un remote de GitHub configurado."""
    if not result.repository.remote_urls:
        return RuleResult(
            rule_id="gh-remote",
            name="Remote GitHub",
            category="github",
            status=RuleStatus.WARN,
            severity=Severity.LOW,
            message="No se configuraron remotes",
            recommendation="Agregar un remote con 'git remote add origin <url>'",
        )
    return RuleResult(
        rule_id="gh-remote",
        name="Remote GitHub",
        category="github",
        status=RuleStatus.PASS,
        severity=Severity.INFO,
        message="Remote configurado",
    )


def _rule_github_repository(result: AuditResult, github: GitHubAuditResult) -> RuleResult:
    """Verifica si el repositorio es accesible en GitHub."""
    if github.error:
        return RuleResult(
            rule_id="gh-repository",
            name="Repositorio GitHub",
            category="github",
            status=RuleStatus.FAIL,
            severity=Severity.MEDIUM,
            message=f"Error accediendo a GitHub: {github.error}",
        )
    if github.repository:
        return RuleResult(
            rule_id="gh-repository",
            name="Repositorio GitHub",
            category="github",
            status=RuleStatus.PASS,
            severity=Severity.INFO,
            message=f"Repositorio accesible: {github.repository.full_name}",
        )
    return RuleResult(
        rule_id="gh-repository",
        name="Repositorio GitHub",
        category="github",
        status=RuleStatus.NOT_APPLICABLE,
        severity=Severity.INFO,
        message="Información de GitHub no disponible",
    )


def _rule_github_actions(result: AuditResult, github: GitHubAuditResult) -> RuleResult:
    """Verifica el estado de GitHub Actions."""
    if not github.actions or not github.actions.has_workflows:
        return RuleResult(
            rule_id="gh-actions",
            name="GitHub Actions",
            category="github",
            status=RuleStatus.INFO,
            severity=Severity.LOW,
            message="GitHub Actions no configurado",
        )
    conclusion = github.actions.latest_run_conclusion
    if conclusion == "success":
        return RuleResult(
            rule_id="gh-actions",
            name="GitHub Actions",
            category="github",
            status=RuleStatus.PASS,
            severity=Severity.INFO,
            message="Último workflow ejecutado exitosamente",
        )
    if conclusion in ("failure", "timed_out"):
        return RuleResult(
            rule_id="gh-actions",
            name="GitHub Actions",
            category="github",
            status=RuleStatus.FAIL,
            severity=Severity.MEDIUM,
            message=f"Último workflow terminó con: {conclusion}",
            recommendation="Revisar los logs del workflow fallido",
        )
    return RuleResult(
        rule_id="gh-actions",
        name="GitHub Actions",
        category="github",
        status=RuleStatus.INFO,
        severity=Severity.LOW,
        message=f"Último workflow: {conclusion or 'en progreso'}",
    )


def _rule_github_releases(result: AuditResult, github: GitHubAuditResult) -> RuleResult:
    """Verifica si el repositorio tiene releases publicadas."""
    if not github.releases:
        return RuleResult(
            rule_id="gh-releases",
            name="Releases",
            category="github",
            status=RuleStatus.INFO,
            severity=Severity.LOW,
            message="Información de releases no disponible",
        )
    if github.releases.has_published_release:
        tag = github.releases.latest_tag or "desconocido"
        return RuleResult(
            rule_id="gh-releases",
            name="Releases",
            category="github",
            status=RuleStatus.PASS,
            severity=Severity.INFO,
            message=f"Release publicada: {tag}",
        )
    return RuleResult(
        rule_id="gh-releases",
        name="Releases",
        category="github",
        status=RuleStatus.INFO,
        severity=Severity.LOW,
        message="No hay releases publicadas",
    )


GITHUB_RULES = [
    _rule_github_remote,
    _rule_github_repository,
    _rule_github_actions,
    _rule_github_releases,
]


def evaluate_github_rules(
    local_result: AuditResult,
    github: GitHubAuditResult,
) -> list[RuleResult]:
    """Evalúa las reglas de GitHub.

    Args:
        local_result: Resultado de la auditoría local.
        github: Resultado de la auditoría de GitHub.

    Returns:
        Lista de resultados de reglas de GitHub.
    """
    rule_results = []
    for rule_fn in GITHUB_RULES:
        try:
            rule_results.append(rule_fn(local_result, github))
        except Exception as e:
            rule_results.append(
                RuleResult(
                    rule_id=f"error-{rule_fn.__name__}",
                    name=rule_fn.__name__,
                    category="error",
                    status=RuleStatus.FAIL,
                    severity=Severity.MEDIUM,
                    message=f"Error ejecutando regla: {e}",
                )
            )
    return rule_results
