"""Clima desde NASA POWER (Prediction Of Worldwide Energy Resources).

Dos consultas complementarias: la climatología multianual (medias por mes) y las
series horarias de los últimos años, que permiten armar la rosa de vientos y los
perfiles diarios. No requiere credenciales.

Advertencia que debe viajar con el dato: POWER es un reanálisis global. Sus celdas
son de 0,5° × 0,625° (MERRA-2, del orden de 50 a 60 km) y 1° × 1° (CERES/SYN1deg).
Es una estimación regional, no una medición en el terreno.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx

from ..config import carpeta_cache
from . import USER_AGENT

NOMBRE = "NASA POWER (Prediction Of Worldwide Energy Resources)"
LICENCIA = "Datos abiertos de la NASA; citar NASA Langley Research Center (LaRC) POWER Project"
BASE = "https://power.larc.nasa.gov/api/temporal"
RESOLUCION = "MERRA-2 0,5° × 0,625° (≈ 50–60 km) y CERES/SYN1deg 1° × 1°; estimación regional"
RELLENO = -999.0

PARAMETROS_CLIMATOLOGIA = ["T2M", "T2M_MAX", "T2M_MIN", "WS10M", "WD10M", "ALLSKY_SFC_SW_DWN", "RH2M", "PRECTOTCORR"]
PARAMETROS_HORARIOS = ["T2M", "WS10M", "WD10M", "ALLSKY_SFC_SW_DWN"]
ANIOS_POR_DEFECTO = 5


def _clave(lat: float, lon: float, sufijo: str) -> str:
    return f"{lat:.4f}_{lon:.4f}_{sufijo}"


def _cache(nombre: str) -> Path:
    return carpeta_cache("power") / f"{nombre}.json"


async def _pedir(cliente: httpx.AsyncClient, url: str, params: dict) -> dict:
    r = await cliente.get(url, params=params, timeout=180)
    r.raise_for_status()
    datos = r.json()
    if "properties" not in datos:
        raise RuntimeError(f"Respuesta inesperada de POWER: {json.dumps(datos)[:300]}")
    return datos


def ultimos_anios_completos(cantidad: int = ANIOS_POR_DEFECTO) -> tuple[int, int]:
    """POWER publica con algunos meses de retraso: se toma hasta el último año cerrado."""
    fin = date.today().year - 1
    return fin - cantidad + 1, fin


async def descargar(lat: float, lon: float, anios: int = ANIOS_POR_DEFECTO, forzar: bool = False) -> dict:
    """Devuelve {'climatologia': ..., 'horario': {anio: ...}} usando caché en disco."""
    anio_inicio, anio_fin = ultimos_anios_completos(anios)
    ruta_clim = _cache(_clave(lat, lon, "climatologia"))
    salida: dict = {"climatologia": None, "horario": {}, "anio_inicio": anio_inicio, "anio_fin": anio_fin}

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as cliente:
        if ruta_clim.exists() and not forzar:
            salida["climatologia"] = json.loads(ruta_clim.read_text(encoding="utf-8"))
        else:
            salida["climatologia"] = await _pedir(
                cliente,
                f"{BASE}/climatology/point",
                {
                    "parameters": ",".join(PARAMETROS_CLIMATOLOGIA),
                    "community": "RE",
                    "latitude": lat,
                    "longitude": lon,
                    "format": "JSON",
                },
            )
            ruta_clim.write_text(json.dumps(salida["climatologia"]), encoding="utf-8")

        for anio in range(anio_inicio, anio_fin + 1):
            ruta = _cache(_clave(lat, lon, f"horario_{anio}"))
            if ruta.exists() and not forzar:
                salida["horario"][anio] = json.loads(ruta.read_text(encoding="utf-8"))
                continue
            datos = await _pedir(
                cliente,
                f"{BASE}/hourly/point",
                {
                    "parameters": ",".join(PARAMETROS_HORARIOS),
                    "community": "RE",
                    "latitude": lat,
                    "longitude": lon,
                    "start": f"{anio}0101",
                    "end": f"{anio}1231",
                    # Hora solar local: sin esto POWER devuelve UTC y el perfil
                    # horario de temperatura quedaría desfasado respecto del sol.
                    "time-standard": "LST",
                    "format": "JSON",
                },
            )
            ruta.write_text(json.dumps(datos), encoding="utf-8")
            salida["horario"][anio] = datos
    return salida
