"""Configuración y secretos. Lee variables de entorno y archivos .env sin dependencias externas."""

from __future__ import annotations

import os
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
DIR_CACHE = RAIZ_BACKEND / "cache"

# Se busca .env desde el backend hacia arriba: backend/, software/, raíz del repositorio.
_CANDIDATOS_ENV = [RAIZ_BACKEND / ".env", RAIZ_BACKEND.parent / ".env", RAIZ_BACKEND.parents[1] / ".env"]
_cargado = False


def _cargar_env() -> None:
    """Carga los .env encontrados sin pisar variables ya definidas en el entorno."""
    global _cargado
    if _cargado:
        return
    _cargado = True
    for ruta in _CANDIDATOS_ENV:
        if not ruta.exists():
            continue
        for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            clave = clave.strip()
            valor = valor.strip().strip("'\"")
            if clave and clave not in os.environ:
                os.environ[clave] = valor


def variable(nombre: str, por_defecto: str = "") -> str:
    _cargar_env()
    return os.environ.get(nombre, por_defecto)


def token_earthdata() -> str:
    """Token de NASA Earthdata Login. Se genera en https://urs.earthdata.nasa.gov/profile
    (pestaña «Generate Token») y se guarda como EARTHDATA_TOKEN en un archivo .env."""
    return variable("EARTHDATA_TOKEN").strip()


def carpeta_cache(*partes: str) -> Path:
    ruta = DIR_CACHE.joinpath(*partes)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
