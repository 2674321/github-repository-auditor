# Repository Health Auditor


<p align="center"><img src="docs/branding/hero-banner.svg" width="100%" alt="GitHub Repository Auditor"></p>

**Autor:** [Patricio Varela C.](https://github.com/2674321) · **ORCID:** [0009-0002-1087-9445](https://orcid.org/0009-0002-1087-9445) · **Licencia:** [MIT](LICENSE) · **Citación:** [CITATION.cff](CITATION.cff)

**Auditor de repositorios Git/GitHub · R1.0**

CLI en Python para auditar repositorios Git locales y GitHub: inventaría su estado,
evalúa controles de salud, genera diagnósticos explicables y permite exportar o comparar resultados.

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/2674321/github-repository-auditor.git
cd github-repository-auditor

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

Requiere Python 3.10 o superior.

## Alcance y limitaciones

- Auditoría de solo lectura: nunca modifica repositorios.
- No utiliza OAuth ni GitHub Apps.
- No ejecuta GitHub Actions para el propio auditor.
- No crea Issues, Pull Requests ni Releases automáticos.
- La detección de secretos es por nombre de archivo (no análisis avanzado del contenido).

## Uso

```bash
# Auditar localmente
repo-auditor .

# Solo score y resumen
repo-auditor --summary .

# Todos los detalles
repo-auditor --verbose .

# Sin colores (para CI/scripts)
repo-auditor --no-color .

# Exportar a JSON
repo-auditor --format json -o report.json

# Comparar dos auditorías
repo-auditor compare old.json new.json

# Ver ayuda
repo-auditor --help

# Ver versión
repo-auditor --version
```

### Exit Codes

| Código | Significado |
|--------|-------------|
| 0 | Auditoría OK (sin warnings) |
| 1 | Warnings detectados |
| 2 | Failures detectados |
| 3 | Error de ejecución |

### GitHub API

Para consultar la API de GitHub, exporta un token de acceso:

```bash
export GITHUB_TOKEN=ghp_tu_token_aqui
repo-auditor --github .
```

El token nunca se muestra en pantalla ni se almacena en archivos.

## Ejemplo de salida

```
Repository Health Auditor
========================================

Repositorio:
  sistema-de-guardias

Ruta:
  /home/user/proyectos/sistema-de-guardias

Git
--------------------
  Repositorio Git: ✓
  Rama actual: main
  Rama principal: main
  Commits: 52
  Último commit: a1b2c3d
  Tags: v1.0.0
  Working tree: limpio

Documentación
--------------------
  README:          ✓
  LICENSE:         ✗
  CHANGELOG:       ✓
  CITATION.cff:    ✗
  .gitignore:      ✓

Tecnologías
--------------------
  Lenguajes: JavaScript
  Frameworks: Google Apps Script, clasp

Seguridad
--------------------
  Archivos sensibles (alta): 0
  Archivos sensibles (media): 1
  Archivos grandes: 0

Reglas de validación
--------------------
  ✓ README
  ⚠ LICENSE
    No se detectó archivo de licencia
    → Agregar un archivo LICENSE para definir los términos de uso
  ✓ .gitignore
  ...

  ANÁLISIS COMPLETADO
```

## Arquitectura

```
src/repository_auditor/
├── cli.py              # Interfaz de línea de comandos
├── scanner/
│   ├── filesystem.py   # Detección de documentación
│   ├── git.py          # Información de Git
│   ├── technology.py   # Detección de tecnologías
│   └── security.py     # Detección de archivos sensibles
├── github/
│   ├── client.py       # Cliente HTTP para GitHub API (urllib)
│   ├── models.py       # Modelos de datos de GitHub
│   ├── errors.py       # Excepciones seguras (sin filtrar tokens)
│   └── url_parser.py   # Parsing de URLs de GitHub
├── models/
│   └── repository.py   # Modelos de datos internos
├── rules/
│   └── __init__.py     # Reglas de validación (locales + GitHub)
└── reports/
    └── text.py         # Generación de reporte de texto
```

El diseño separa claramente:
- **Scanners** → recopilan información
- **Models** → representan datos estructurados
- **Rules** → evalúan contra criterios
- **Reports** → formatean la salida

## Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con verbosidad
pytest -v

# Ejecutar un módulo específico
pytest tests/test_filesystem.py
```

## Roadmap

| Versión | Descripción | Estado |
|---------|-------------|--------|
| R0.5 | Auditor local | ✅ |
| R0.6 | Integración con GitHub API | ✅ |
| R0.7 | Health Score & Diagnostics | ✅ |
| R0.8 | Export & History | ✅ |
| R0.9 | Reporting & UX | ✅ |
| R1.0 | Stable Release | ✅ Actual |

