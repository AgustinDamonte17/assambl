"""Relieve desde NASADEM (NASA JPL, MEaSUREs), 1 arcosegundo ≈ 30 m.

Localización de mosaicos por el catálogo CMR de Earthdata (sin credenciales) y
descarga desde LP DAAC (requiere token de Earthdata Login). Los posts se usan tal
como los publica la fuente: no se interpola ni se suaviza el relieve.

Referencia: NASA JPL (2021). NASADEM Merged DEM Global 1 arc second V001.
DOI 10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001
"""

from __future__ import annotations

import asyncio
import io
import math
import zipfile
from pathlib import Path

import httpx
import numpy as np

from ..config import carpeta_cache, token_earthdata
from ..modelo.sitio import MallaDem
from . import USER_AGENT

NOMBRE = "NASADEM Merged DEM Global 1 arc second V001 (NASA JPL / LP DAAC)"
DOI = "10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001"
LICENCIA = "Datos abiertos de la NASA; citar el DOI y el LP DAAC"
RESOLUCION = "1 arcosegundo (≈ 30 m); modelo de elevación, no mensura"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
# El depósito del LP DAAC publica un objeto por mosaico con un nombre previsible.
# Se arma la URL en vez de buscarla: el catálogo agrega un viaje de ida y vuelta y
# su índice de gránulos se cae con cierta frecuencia (verificado el 23/09/2026,
# HTTP 500 y timeouts mientras las colecciones respondían en un segundo).
LPDAAC = "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/NASADEM_HGT.001"

POSTS_POR_GRADO = 3600
LADO_HGT = POSTS_POR_GRADO + 1  # 3601 × 3601 posts por mosaico de 1°
SIN_DATO = -32768
MAX_TESELAS = 9


class SinCobertura(RuntimeError):
    """NASADEM no publica mosaico para esa zona (por ejemplo, mar abierto)."""


class FaltaCredencial(RuntimeError):
    """La descarga necesita un token de NASA Earthdata Login."""


class CatalogoCaido(RuntimeError):
    """El mosaico no está en la ruta conocida y el catálogo no responde, así que no
    se puede distinguir falta de cobertura de un cambio de ruta del LP DAAC."""


def nombre_tesela(lat_sur: int, lon_oeste: int) -> str:
    ns = "n" if lat_sur >= 0 else "s"
    ew = "e" if lon_oeste >= 0 else "w"
    return f"{ns}{abs(lat_sur):02d}{ew}{abs(lon_oeste):03d}"


def teselas_necesarias(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> list[tuple[int, int]]:
    return [
        (la, lo)
        for la in range(math.floor(lat_min), math.floor(lat_max) + 1)
        for lo in range(math.floor(lon_min), math.floor(lon_max) + 1)
    ]


async def _con_reintentos(hacer, intentos: int = 3, espera_s: float = 2.0):
    """Reintenta ante fallos de conexión. Los cortes de DNS momentáneos son comunes
    y un mosaico tarda minutos: no vale la pena perder la descarga por uno."""
    for intento in range(intentos):
        try:
            return await hacer()
        except (httpx.ConnectError, httpx.ConnectTimeout):
            if intento == intentos - 1:
                raise
            await asyncio.sleep(espera_s * (intento + 1))


def url_descarga(tesela: str) -> str:
    """URL del mosaico en el depósito del LP DAAC. Requiere token para bajarlo."""
    return f"{LPDAAC}/NASADEM_HGT_{tesela}/NASADEM_HGT_{tesela}.zip"


async def _url_catalogo(cliente: httpx.AsyncClient, tesela: str) -> str | None:
    """Consulta de respaldo al catálogo CMR, solo si la ruta conocida da 404.

    Devuelve None si el catálogo confirma que no hay gránulo (no hay cobertura) y
    levanta CatalogoCaido si no se le puede preguntar: decir «sin cobertura» sin
    haberlo verificado sería inventar un diagnóstico.
    """
    try:
        r = await cliente.get(
            CMR,
            params={"short_name": "NASADEM_HGT", "granule_ur": f"NASADEM_HGT_{tesela}", "page_size": 1},
            timeout=20,
        )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise CatalogoCaido(
            f"El LP DAAC no tiene {tesela} en la ruta conocida y el catálogo CMR no responde "
            f"({type(e).__name__}): no se puede saber si falta cobertura o si cambió la ruta"
        ) from e
    entradas = r.json().get("feed", {}).get("entry", [])
    if not entradas:
        return None
    for enlace in entradas[0].get("links", []):
        href = enlace.get("href", "")
        if href.startswith("https://") and href.endswith(".zip"):
            return href
    return None


def _leer_hgt(datos: bytes) -> np.ndarray:
    """Devuelve el mosaico como matriz de alturas con la fila 0 al sur."""
    esperado = LADO_HGT * LADO_HGT * 2
    if len(datos) != esperado:
        raise RuntimeError(f"Mosaico .hgt de tamaño inesperado: {len(datos)} bytes (se esperaban {esperado})")
    matriz = np.frombuffer(datos, dtype=">i2").reshape(LADO_HGT, LADO_HGT)
    return np.flipud(matriz).astype(np.float64)  # el archivo viene con la fila 0 al norte


async def _descargar_tesela(cliente: httpx.AsyncClient, tesela: str, token: str) -> np.ndarray:
    cache = carpeta_cache("nasadem") / f"{tesela}.hgt"
    if cache.exists():
        return _leer_hgt(cache.read_bytes())
    if not token:
        raise FaltaCredencial(
            "Falta EARTHDATA_TOKEN: generalo en https://urs.earthdata.nasa.gov/profile y guardalo en un archivo .env"
        )
    auth = {"Authorization": f"Bearer {token}"}
    r = await _con_reintentos(
        lambda: cliente.get(url_descarga(tesela), headers=auth, follow_redirects=True, timeout=300)
    )
    if r.status_code == 404:
        # O no hay cobertura (mar abierto, o fuera de la banda 60° N – 56° S) o el
        # LP DAAC reorganizó el depósito. Solo el catálogo puede decir cuál de las dos.
        url = await _url_catalogo(cliente, tesela)
        if url is None:
            raise SinCobertura(f"NASADEM no publica el mosaico {tesela}")
        r = await cliente.get(url, headers=auth, follow_redirects=True, timeout=300)
    if r.status_code in (401, 403):
        raise FaltaCredencial(f"Earthdata rechazó el token al pedir {tesela} (HTTP {r.status_code}); verificá que no esté vencido")
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        miembros = [n for n in z.namelist() if n.lower().endswith(".hgt")]
        if not miembros:
            raise RuntimeError(f"El paquete de {tesela} no contiene un archivo .hgt")
        crudo = z.read(miembros[0])
    cache.write_bytes(crudo)
    return _leer_hgt(crudo)


async def descargar_recorte(lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> MallaDem:
    """Malla de posts nativos de NASADEM que cubre el rectángulo pedido.

    El recorte se extiende al post inmediatamente exterior en cada borde para que
    el área pedida quede contenida por completo.
    """
    teselas = teselas_necesarias(lat_min, lat_max, lon_min, lon_max)
    if len(teselas) > MAX_TESELAS:
        raise RuntimeError(f"El área pedida abarca {len(teselas)} mosaicos de NASADEM; reducí el margen")

    # Índices globales en arcosegundos: cada post está en un múltiplo exacto.
    i_lat0 = math.floor(lat_min * POSTS_POR_GRADO)
    i_lat1 = math.ceil(lat_max * POSTS_POR_GRADO)
    i_lon0 = math.floor(lon_min * POSTS_POR_GRADO)
    i_lon1 = math.ceil(lon_max * POSTS_POR_GRADO)
    ny = i_lat1 - i_lat0 + 1
    nx = i_lon1 - i_lon0 + 1
    salida = np.full((ny, nx), np.nan)

    token = token_earthdata()
    usadas: list[str] = []
    async with httpx.AsyncClient(timeout=120, headers={"User-Agent": USER_AGENT}) as cliente:
        for lat_sur, lon_oeste in teselas:
            nombre = nombre_tesela(lat_sur, lon_oeste)
            matriz = await _descargar_tesela(cliente, nombre, token)
            usadas.append(nombre)
            base_lat = lat_sur * POSTS_POR_GRADO
            base_lon = lon_oeste * POSTS_POR_GRADO
            r0 = max(i_lat0, base_lat)
            r1 = min(i_lat1, base_lat + POSTS_POR_GRADO)
            c0 = max(i_lon0, base_lon)
            c1 = min(i_lon1, base_lon + POSTS_POR_GRADO)
            if r0 > r1 or c0 > c1:
                continue
            bloque = matriz[r0 - base_lat : r1 - base_lat + 1, c0 - base_lon : c1 - base_lon + 1]
            salida[r0 - i_lat0 : r1 - i_lat0 + 1, c0 - i_lon0 : c1 - i_lon0 + 1] = bloque

    salida[salida == SIN_DATO] = np.nan
    huecos = int(np.isnan(salida).sum())
    if huecos:
        if huecos == salida.size:
            raise SinCobertura("El recorte de NASADEM no tiene ningún post con dato")
        salida[np.isnan(salida)] = float(np.nanmedian(salida))

    return MallaDem(
        lat_sur=i_lat0 / POSTS_POR_GRADO,
        lon_oeste=i_lon0 / POSTS_POR_GRADO,
        paso_deg=1 / POSTS_POR_GRADO,
        nx=nx,
        ny=ny,
        alturas_msnm=[round(v, 2) for v in salida.ravel().tolist()],
        huecos=huecos,
        teselas=usadas,
    )


def malla_provisional(lat: float, lon: float, margen_m: float, cota: float = 0.0) -> MallaDem:
    """Escena plana de reemplazo cuando NASADEM no está disponible. Queda marcada
    como provisional para que la interfaz no la presente como relieve real."""
    paso = 1 / POSTS_POR_GRADO
    grados_lat = margen_m / 111_320.0
    grados_lon = grados_lat / max(math.cos(math.radians(lat)), 1e-6)
    ny = max(3, int(2 * grados_lat / paso) + 1)
    nx = max(3, int(2 * grados_lon / paso) + 1)
    return MallaDem(
        lat_sur=lat - grados_lat,
        lon_oeste=lon - grados_lon,
        paso_deg=paso,
        nx=nx,
        ny=ny,
        alturas_msnm=[cota] * (nx * ny),
        huecos=nx * ny,
        teselas=[],
        provisional=True,
    )


def cache_disponible() -> list[str]:
    carpeta = Path(carpeta_cache("nasadem"))
    return sorted(p.stem for p in carpeta.glob("*.hgt"))


async def probar_credencial() -> tuple[bool, str]:
    """Verifica que el token permita descargar. Devuelve (ok, mensaje)."""
    token = token_earthdata()
    if not token:
        return False, "Sin EARTHDATA_TOKEN configurado"
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}) as cliente:
        try:
            # Solo los primeros bytes de un mosaico que existe: alcanza para saber si
            # la credencial pasa, y no depende del catálogo.
            r = await cliente.get(
                url_descarga("s32w065"),
                headers={"Authorization": f"Bearer {token}", "Range": "bytes=0-1023"},
                follow_redirects=True,
                timeout=30,
            )
            if r.status_code in (401, 403):
                return False, f"Earthdata rechazó el token (HTTP {r.status_code}); puede estar vencido"
            r.raise_for_status()
            return True, "Token válido"
        except httpx.HTTPError as e:
            return False, f"{type(e).__name__}: {e}"
