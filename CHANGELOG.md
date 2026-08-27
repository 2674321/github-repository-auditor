# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adherisce a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-08-27

### R1.0 — Stable Release

Versión estable del Repository Health Auditor.

#### Funcionalidades completas

- **R0.5:** Auditor local (filesystem, git, technology, security, rules)
- **R0.6:** Integración GitHub API (client, models, errors, url_parser)
- **R0.7:** Health Score & Diagnostics (scoring engine, weights, categories)
- **R0.8:** Export & History (JSON, compare, exit codes)
- **R0.9:** Reporting & UX (summary, verbose, colors, diagnostics, recommendations)

#### CLI

- `repo-auditor [path]` — auditoría completa
- `repo-auditor audit [path]` — subcomando explícito
- `repo-auditor compare old.json new.json` — comparar auditorías
- `--github` / `--no-github` — integración GitHub
- `--score` — mostrar score
- `--format json` — exportar JSON
- `-o file` — guardar en archivo
- `--summary` / `--verbose` — modos de reporte
- `--no-color` — deshabilitar colores
- Exit codes: 0=ok, 1=warnings, 2=failures, 3=error

#### Scoring

- Score global 0–100
- 5 categorías ponderadas: documentation(20), git(20), technology(15), security(25), github(20)
- Ratings: EXCELLENT(90+), GOOD(75+), FAIR(60+), POOR(40+), CRITICAL(<40)
- NOT_APPLICABLE no penaliza injustificadamente

#### Seguridad

- GITHUB_TOKEN nunca filtrado en errores, logs, reportes o JSON
- Sin dependencias externas en producción
- Python >= 3.10

#### Tests

- 230 tests pasando
- 0 tests fallidos
- Ruff limpio

## [0.5.0] - 2026-08-27

### Añadido

- Modos de reporte: `--summary` (solo score), `--verbose` (todos los detalles)
- Soporte de colores ANSI con detección de TTY
- Flag `--no-color` para deshabilitar colores
- Sección de Diagnósticos en reporte de texto
- Sección de Recommendations derivadas de reglas
- 12 tests nuevos (summary, verbose, color, diagnostics) — 230 totales

## [0.4.0] - 2026-08-27

### Añadido

- Exportación JSON: `--format json` con metadatos, reglas, score, GitHub
- Archivo de salida: `-o`/`--output` para text y JSON
- Subcomando `compare`: compara dos auditorías JSON (score, reglas nuevas/resueltas)
- Exit codes: 0=ok, 1=warnings, 2=failures, 3=error
- Backward compatible: `repo-auditor /path` sigue funcionando sin subcomando
- 25 tests nuevos (JSON export, parse, compare, exit codes) — 218 totales

## [0.3.0] - 2026-08-27

### Añadido

- Motor de scoring: `scoring/` module con engine, models, weights
- Score global 0–100 con clasificación (EXCELLENT/GOOD/FAIR/POOR/CRITICAL)
- 5 categorías ponderadas: documentation, git, technology, security, github
- Diagnósticos con prioridades (CRITICAL/HIGH/MEDIUM/LOW/INFO)
- Flag `--score` en CLI
- Sección "Repository Health" en reporte de texto
- 29 tests nuevos (scoring engine, weights, models, diagnostics) — 193 totales
- NOT_APPLICABLE no penaliza el score injustificadamente

## [0.2.0] - 2026-08-27

### Añadido

- Módulo `github/`: cliente HTTP con urllib, modelos tipados, jerarquía de errores seguros, parser de URLs (HTTPS/SSH)
- Flags `--github` / `--no-github` en CLI
- 4 reglas de GitHub: remote disponible, repo accesible, Actions, releases
- Sección GitHub en reporte de texto
- 78 tests nuevos (url_parser, client, models, errors, rules, report) — 164 totales
- GITHUB_TOKEN nunca filtrado en errores, logs ni tests

## [0.1.0] - 2026-08-26

### Añadido

- Estructura inicial del proyecto con pyproject.toml
- Scanner de filesystem: detección de documentación (README, LICENSE, CHANGELOG, CITATION.cff, .gitignore, .github/, workflows, Dependabot, CodeQL)
- Scanner de Git: información básica de repositorios Git locales (rama, commits, tags, remotes, working tree)
- Scanner de tecnologías: detección basada en archivos reales (Python, JavaScript, TypeScript, React, Vite, Docker, Google Apps Script, clasp, Ruby, etc.)
- Scanner de seguridad: detección de archivos potencialmente sensibles (.env, claves, credenciales) y archivos grandes
- Motor de reglas básico con estados (PASS, WARN, FAIL, INFO, NOT_APPLICABLE)
- CLI con interfaz de línea de comandos
- Reporte de texto formateado para consola
- Tests automatizados para filesystem, git, tecnologías, seguridad, reglas, reportes y CLI
- README en español con documentación completa
- CHANGELOG en español
- .gitignore para Python
