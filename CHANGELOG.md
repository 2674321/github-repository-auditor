# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adherisce a [Semantic Versioning](https://semver.org/lang/es/).

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
