"""Scanner de seguridad — detecta archivos potencialmente sensibles.

NO analiza el contenido de archivos. Solo detecta por nombre y ubicación.
Distingue entre "archivo potencialmente sensible" y "secreto confirmado".
"""

from __future__ import annotations

from pathlib import Path

from repository_auditor.models.repository import LargeFile, SecurityFinding

LARGE_FILE_THRESHOLD = 1 * 1024 * 1024  # 1 MB

SENSITIVE_PATTERNS_HIGH = {
    ".env": "Archivo de variables de entorno",
    ".env.local": "Archivo de variables de entorno local",
    ".env.production": "Archivo de variables de entorno de producción",
    ".env.development": "Archivo de variables de entorno de desarrollo",
    "credentials.json": "Archivo de credenciales",
    "credentials.yml": "Archivo de credenciales",
    "credentials.yaml": "Archivo de credenciales",
    "service-account.json": "Cuenta de servicio",
    "secret.json": "Archivo de secretos",
    "secrets.json": "Archivo de secretos",
    "secrets.yml": "Archivo de secretos",
    "secrets.yaml": "Archivo de secretos",
    "id_rsa": "Clave privada SSH",
    "id_ed25519": "Clave privada SSH",
    "id_dsa": "Clave privada SSH",
    "id_ecdsa": "Clave privada SSH",
    "*.pem": "Certificado/certificado privado",
    "*.key": "Clave privada",
    "*.p12": "Certificado PKCS#12",
    "*.pfx": "Certificado PKCS#12",
    "*.jks": "Java KeyStore",
}

SENSITIVE_PATTERNS_MEDIUM = {
    ".clasprc.json": "Token de autenticación de clasp",
    "*.db": "Base de datos SQLite",
    "*.sqlite": "Base de datos SQLite",
    "*.sqlite3": "Base de datos SQLite",
    "clasp.json": "Configuración de clasp (contiene IDs de proyectos)",
    "appsscript.json": "Configuración de Apps Script (contiene IDs de proyecto)",
}

SENSITIVE_PATTERNS_LOW = {
    "node_modules": "Directorio de dependencias",
    "__pycache__": "Caché de Python",
    ".pytest_cache": "Caché de pytest",
    ".mypy_cache": "Caché de mypy",
    ".ruff_cache": "Caché de ruff",
    ".DS_Store": "Archivo de sistema macOS",
    "Thumbs.db": "Archivo de sistema Windows",
    "*.log": "Archivo de log",
    "*.tmp": "Archivo temporal",
    "*.bak": "Archivo de respaldo",
    "*.swp": "Archivo de swap",
}


def _get_file_size(path: Path) -> int:
    """Obtiene el tamaño de un archivo en bytes."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _check_sensitive_files(path: Path) -> list[SecurityFinding]:
    """Busca archivos potencialmente sensibles en el repositorio."""
    findings = []

    for f in path.rglob("*"):
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        if not f.is_file():
            continue

        filename = f.name
        relative = str(f.relative_to(path))

        for pattern, description in SENSITIVE_PATTERNS_HIGH.items():
            if pattern.startswith("*"):
                ext = pattern[1:]
                if filename.endswith(ext):
                    findings.append(
                        SecurityFinding(
                            path=relative,
                            category="sensitive_high",
                            severity="high",
                            message=f"Archivo potencialmente sensible: {description}",
                        )
                    )
                    break
            elif filename.lower() == pattern.lower():
                findings.append(
                    SecurityFinding(
                        path=relative,
                        category="sensitive_high",
                        severity="high",
                        message=f"Archivo potencialmente sensible: {description}",
                    )
                )
                break

        for pattern, description in SENSITIVE_PATTERNS_MEDIUM.items():
            if pattern.startswith("*"):
                ext = pattern[1:]
                if filename.endswith(ext):
                    findings.append(
                        SecurityFinding(
                            path=relative,
                            category="sensitive_medium",
                            severity="medium",
                            message=f"Archivo potencialmente sensible: {description}",
                        )
                    )
                    break
            elif filename.lower() == pattern.lower():
                findings.append(
                    SecurityFinding(
                        path=relative,
                        category="sensitive_medium",
                        severity="medium",
                        message=f"Archivo potencialmente sensible: {description}",
                    )
                )
                break

    return findings


def _check_large_files(path: Path, threshold: int = LARGE_FILE_THRESHOLD) -> list[LargeFile]:
    """Busca archivos grandes en el repositorio."""
    large_files = []

    for f in path.rglob("*"):
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        if not f.is_file():
            continue

        size = _get_file_size(f)
        if size > threshold:
            large_files.append(
                LargeFile(
                    path=str(f.relative_to(path)),
                    size_bytes=size,
                )
            )

    return large_files


def scan_security(path: Path) -> tuple[list[SecurityFinding], list[LargeFile]]:
    """Realiza un escaneo de seguridad del repositorio.

    Args:
        path: Ruta al directorio del repositorio.

    Returns:
        Tupla con (hallazgos de seguridad, archivos grandes).
    """
    findings = _check_sensitive_files(path)
    large_files = _check_large_files(path)
    return findings, large_files
