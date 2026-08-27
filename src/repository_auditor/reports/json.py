"""Reporte JSON — exporta resultados estructurados.

Genera JSON válido, determinista y seguro (sin tokens).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from repository_auditor import __version__
from repository_auditor.github.models import GitHubAuditResult
from repository_auditor.models.repository import AuditResult
from repository_auditor.scoring.models import ScoreResult


def _audit_result_to_dict(result: AuditResult) -> dict[str, Any]:
    """Convierte AuditResult a diccionario serializable."""
    return {
        "repository": {
            "name": result.repository.name,
            "path": result.repository.path,
            "is_git_repository": result.repository.is_git_repository,
            "current_branch": result.repository.current_branch,
            "main_branch": result.repository.main_branch,
            "commit_count": result.repository.commit_count,
            "latest_commit": result.repository.latest_commit,
            "latest_commit_date": result.repository.latest_commit_date,
            "tags": result.repository.tags,
            "dirty_worktree": result.repository.dirty_worktree,
            "modified_files": result.repository.modified_files,
            "untracked_files": result.repository.untracked_files,
            "remote_urls": result.repository.remote_urls,
        },
        "documentation": {
            "has_readme": result.documentation.has_readme,
            "has_license": result.documentation.has_license,
            "has_changelog": result.documentation.has_changelog,
            "has_citation": result.documentation.has_citation,
            "has_contributing": result.documentation.has_contributing,
            "has_code_of_conduct": result.documentation.has_code_of_conduct,
            "has_security": result.documentation.has_security,
            "has_gitignore": result.documentation.has_gitignore,
            "has_gitattributes": result.documentation.has_gitattributes,
            "has_github_directory": result.documentation.has_github_directory,
            "has_workflows": result.documentation.has_workflows,
            "has_dependabot": result.documentation.has_dependabot,
            "has_codeql": result.documentation.has_codeql,
        },
        "technologies": {
            "languages": result.technologies.languages,
            "frameworks": result.technologies.frameworks,
            "tools": result.technologies.tools,
            "config_files": result.technologies.config_files,
        },
        "security_findings": [
            {
                "path": f.path,
                "category": f.category,
                "severity": f.severity,
                "message": f.message,
            }
            for f in result.security_findings
        ],
        "large_files": [
            {"path": f.path, "size_bytes": f.size_bytes}
            for f in result.large_files
        ],
        "rules": [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "category": r.category,
                "status": r.status.value,
                "severity": r.severity.value,
                "message": r.message,
                "recommendation": r.recommendation,
            }
            for r in result.rule_results
        ],
    }


def _github_result_to_dict(github: GitHubAuditResult) -> dict[str, Any] | None:
    """Convierte GitHubAuditResult a diccionario serializable."""
    if github is None:
        return None

    data: dict[str, Any] = {}
    if github.error:
        data["error"] = github.error

    if github.repository:
        r = github.repository
        data["repository"] = {
            "owner": r.owner,
            "name": r.name,
            "full_name": r.full_name,
            "description": r.description,
            "url": r.url,
            "default_branch": r.default_branch,
            "visibility": r.visibility,
            "archived": r.archived,
            "fork": r.fork,
            "stars": r.stars,
            "forks": r.forks,
            "open_issues": r.open_issues,
            "license": r.license,
            "topics": r.topics,
        }

    if github.releases:
        data["releases"] = {
            "total_count": github.releases.total_count,
            "latest_tag": github.releases.latest_tag,
            "latest_date": github.releases.latest_date,
            "has_published_release": github.releases.has_published_release,
        }

    if github.actions:
        data["actions"] = {
            "has_workflows": github.actions.has_workflows,
            "latest_run_conclusion": github.actions.latest_run_conclusion,
            "requires_auth": github.actions.requires_auth,
        }

    return data if data else None


def _score_result_to_dict(score: ScoreResult) -> dict[str, Any]:
    """Convierte ScoreResult a diccionario serializable."""
    return {
        "score": score.score,
        "max_score": score.max_score,
        "rating": score.rating.value,
        "categories": [
            {
                "category": c.category,
                "score": c.score,
                "max_score": c.max_score,
                "percentage": round(c.percentage, 1),
            }
            for c in score.categories
        ],
        "diagnostics": [
            {
                "title": d.title,
                "description": d.description,
                "priority": d.priority.value,
                "category": d.category,
                "recommendation": d.recommendation,
                "rule_id": d.rule_id,
            }
            for d in score.diagnostics
        ],
    }


def format_json(
    result: AuditResult,
    github: GitHubAuditResult | None = None,
    score: ScoreResult | None = None,
) -> str:
    """Genera un reporte JSON completo.

    Args:
        result: Resultado de la auditoría local.
        github: Resultado de la auditoría de GitHub (opcional).
        score: Resultado del scoring (opcional).

    Returns:
        JSON formateado como string.
    """
    data: dict[str, Any] = {
        "meta": {
            "auditor_version": __version__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "audit": _audit_result_to_dict(result),
    }

    github_data = _github_result_to_dict(github)
    if github_data is not None:
        data["github"] = github_data

    if score is not None:
        data["score"] = _score_result_to_dict(score)

    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)


def parse_audit_json(json_str: str) -> dict[str, Any]:
    """Parsea un JSON de auditoría previamente exportado.

    Args:
        json_str: String JSON a parsear.

    Returns:
        Diccionario con los datos parseados.

    Raises:
        ValueError: Si el JSON es inválido o no tiene la estructura esperada.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}") from None

    if not isinstance(data, dict):
        raise ValueError("JSON debe ser un objeto")

    if "meta" not in data or "audit" not in data:
        raise ValueError("JSON no tiene la estructura de auditoría esperada")

    return data


def compare_audits(
    old: dict[str, Any],
    new: dict[str, Any],
) -> dict[str, Any]:
    """Compara dos auditorías estructuradas.

    Args:
        old: Datos de la auditoría anterior.
        new: Datos de la auditoría nueva.

    Returns:
        Diccionario con la comparación.
    """
    old_score = old.get("score", {})
    new_score = new.get("score", {})

    old_val = old_score.get("score", 0)
    new_val = new_score.get("score", 0)

    old_rules = {r["rule_id"]: r["status"] for r in old.get("audit", {}).get("rules", [])}
    new_rules = {r["rule_id"]: r["status"] for r in new.get("audit", {}).get("rules", [])}

    all_rule_ids = set(old_rules.keys()) | set(new_rules.keys())
    new_failures = []
    resolved = []
    new_warnings = []

    for rule_id in all_rule_ids:
        old_status = old_rules.get(rule_id)
        new_status = new_rules.get(rule_id)
        if old_status != "fail" and new_status == "fail":
            new_failures.append(rule_id)
        elif old_status == "fail" and new_status != "fail":
            resolved.append(rule_id)
        if old_status != "warn" and new_status == "warn":
            new_warnings.append(rule_id)

    return {
        "score": {
            "previous": old_val,
            "current": new_val,
            "change": new_val - old_val,
        },
        "rating": {
            "previous": old_score.get("rating"),
            "current": new_score.get("rating"),
        },
        "new_failures": new_failures,
        "resolved_failures": resolved,
        "new_warnings": new_warnings,
    }
