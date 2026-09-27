"""Imagen satelital georreferenciada (ortofoto) a partir de mosaicos web-mercator.

Fuente por defecto: Esri World Imagery. La imagen se remuestrea a una rejilla en
coordenadas locales (+X este, +Y norte, norte arriba), de modo que un píxel de la
salida es un cuadrado de `m_px` metros del terreno y se puede apoyar tal cual sobre
el suelo del modelo 3D.

Donde Esri no tiene imagen a un zoom devuelve un mosaico gris con el texto «Map
data not yet available». Ese mosaico se reconoce y se reemplaza por el cuarto
correspondiente del mosaico de un zoom menor, ampliado: se pierde definición, no
se inventa contenido.

Para desarrollar sin red, ASSAMBL_IMAGEN_SINTETICA=1 reemplaza la descarga por un
mundo sintético (`imagen_sintetica.py`) marcado como tal en la fuente.
"""

from __future__ import annotations

import asyncio
import io
import math
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx
import numpy as np
from PIL import Image

from ..config import carpeta_cache, variable
from ..geometria.coordenadas import SistemaLocal, metros_por_pixel
from . import USER_AGENT

NOMBRE = "Esri World Imagery"
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
LICENCIA = "Esri, Maxar, Earthstar Geographics y colaboradores; uso sujeto a los términos de Esri"
ZOOM_MAX = 19
LADO = 256
MAX_PX = 2048
# Hasta cuántos zooms hacia abajo se busca imagen cuando falta en el pedido.
CAIDA_MAX = 3
CONCURRENCIA = 8
COLOR_SIN_IMAGEN = (150, 148, 132)

# Devuelve el mosaico (RGB) o None si no hay imagen a ese zoom.
ObtenerTesela = Callable[[int, int, int], Awaitable[Image.Image | None]]


@dataclass
class Ortofoto:
    """Imagen norte arriba sobre el rectángulo [xmin, xmax] × [ymin, ymax] en metros
    locales. La fila 0 es el borde norte."""

    rgb: np.ndarray  # (alto, ancho, 3) uint8
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    m_px: float
    zoom: int
    zoom_min_usado: int
    cobertura: float  # fracción de mosaicos con imagen, a cualquier zoom
    fuente: str
    sintetica: bool = False

    @property
    def ancho(self) -> int:
        return self.rgb.shape[1]

    @property
    def alto(self) -> int:
        return self.rgb.shape[0]

    def a_pixel(self, x: np.ndarray | float, y: np.ndarray | float):
        """Coordenadas locales → (columna, fila) en píxeles, con decimales."""
        return (np.asarray(x) - self.xmin) / self.m_px, (self.ymax - np.asarray(y)) / self.m_px

    def a_local(self, col: np.ndarray | float, fila: np.ndarray | float):
        return self.xmin + np.asarray(col) * self.m_px, self.ymax - np.asarray(fila) * self.m_px

    def jpeg(self, calidad: int = 85) -> bytes:
        salida = io.BytesIO()
        Image.fromarray(self.rgb).save(salida, format="JPEG", quality=calidad, optimize=True)
        return salida.getvalue()


def es_cartel_sin_imagen(img: Image.Image) -> bool:
    """El mosaico de relleno de Esri es gris claro casi uniforme con un texto. Una
    imagen real, incluso de agua o de campo arado, no tiene el 85 % de sus píxeles en
    el mismo gris."""
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    saturacion = a.max(axis=2) - a.min(axis=2)
    gris = a.mean(axis=2)
    moda = np.bincount(gris.astype(np.int64).ravel(), minlength=256).argmax()
    iguales = (np.abs(gris - moda) <= 4) & (saturacion <= 6)
    return bool(iguales.mean() > 0.85 and moda > 150)


def _zoom_para(lat: float, m_px: float) -> int:
    """Zoom cuyo píxel se acerca más al pedido, prefiriendo el de más definición
    cuando queda en el medio: pedir un zoom de más cuadruplica los mosaicos."""
    z = math.floor(math.log2(metros_por_pixel(lat, 0) / m_px) + 0.3)
    return max(1, min(z, ZOOM_MAX))


def _obtener_por_defecto() -> tuple[ObtenerTesela, str, bool, Callable[[], Awaitable[None]]]:
    if variable("ASSAMBL_IMAGEN_SINTETICA") in ("1", "true", "si"):
        from . import imagen_sintetica

        async def sintetica(z: int, x: int, y: int) -> Image.Image | None:
            return imagen_sintetica.tesela(z, x, y)

        async def nada() -> None:
            return None

        return sintetica, imagen_sintetica.NOMBRE, True, nada

    cliente = httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
    cache = carpeta_cache("imagen")

    async def descargar(z: int, x: int, y: int) -> Image.Image | None:
        ruta = cache / str(z) / str(x) / f"{y}.jpg"
        vacia = ruta.with_suffix(".vacia")
        if vacia.exists():
            return None
        if ruta.exists():
            return Image.open(ruta).convert("RGB")
        r = await cliente.get(URL.format(z=z, x=x, y=y))
        if r.status_code == 404:
            return None
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if es_cartel_sin_imagen(img):
            vacia.touch()
            return None
        ruta.write_bytes(r.content)
        return img

    return descargar, NOMBRE, False, cliente.aclose


async def _tesela_con_caida(obtener: ObtenerTesela, z: int, x: int, y: int) -> tuple[Image.Image | None, int]:
    """El mosaico pedido, o el cuarto que le corresponde de uno de menor zoom."""
    for k in range(0, CAIDA_MAX + 1):
        zz = z - k
        if zz < 1:
            break
        img = await obtener(zz, x >> k, y >> k)
        if img is None:
            continue
        if k == 0:
            return img, zz
        parte = LADO >> k
        ox, oy = (x - ((x >> k) << k)) * parte, (y - ((y >> k) << k)) * parte
        return img.crop((ox, oy, ox + parte, oy + parte)).resize((LADO, LADO), Image.BILINEAR), zz
    return None, 0


async def ortofoto(sistema: SistemaLocal, xmin: float, xmax: float, ymin: float, ymax: float,
                   m_px: float, zoom_max: int = ZOOM_MAX, obtener: ObtenerTesela | None = None,
                   nombre_fuente: str | None = None) -> Ortofoto:
    """Ortofoto del rectángulo pedido con píxeles de `m_px` metros o más grandes
    (nunca más de MAX_PX por lado)."""
    cerrar = None
    sintetica = False
    if obtener is None:
        obtener, nombre_fuente, sintetica, cerrar = _obtener_por_defecto()
    try:
        return await _ortofoto(sistema, xmin, xmax, ymin, ymax, m_px, zoom_max, obtener,
                               nombre_fuente or NOMBRE, sintetica)
    finally:
        if cerrar is not None:
            await cerrar()


async def _ortofoto(sistema: SistemaLocal, xmin: float, xmax: float, ymin: float, ymax: float, m_px: float,
                    zoom_max: int, obtener: ObtenerTesela, nombre_fuente: str, sintetica: bool) -> Ortofoto:
    ancho_m, alto_m = xmax - xmin, ymax - ymin
    m_px = max(m_px, ancho_m / MAX_PX, alto_m / MAX_PX)
    ancho, alto = max(1, math.ceil(ancho_m / m_px)), max(1, math.ceil(alto_m / m_px))
    xmax, ymin = xmin + ancho * m_px, ymax - alto * m_px
    z = min(_zoom_para(sistema.lat0, m_px), zoom_max)

    # Centro de cada píxel de salida → lat/lon → píxel global web-mercator.
    cols = xmin + (np.arange(ancho) + 0.5) * m_px
    filas = ymax - (np.arange(alto) + 0.5) * m_px
    lon = sistema.lon0 + cols / sistema.metros_por_grado_lon
    lat = sistema.lat0 + filas / sistema.metros_por_grado_lat
    n = LADO * 2**z
    gx = (lon + 180.0) / 360.0 * n
    lat_r = np.radians(lat)
    gy = (1.0 - np.log(np.tan(lat_r) + 1.0 / np.cos(lat_r)) / math.pi) / 2.0 * n

    tx0, tx1 = int(gx.min() // LADO), int(gx.max() // LADO)
    ty0, ty1 = int(gy.min() // LADO), int(gy.max() // LADO)
    mosaico = np.empty(((ty1 - ty0 + 1) * LADO, (tx1 - tx0 + 1) * LADO, 3), dtype=np.uint8)
    mosaico[:] = COLOR_SIN_IMAGEN

    semaforo = asyncio.Semaphore(CONCURRENCIA)

    async def una(tx: int, ty: int):
        async with semaforo:
            try:
                return tx, ty, *(await _tesela_con_caida(obtener, z, tx, ty))
            except (httpx.HTTPError, OSError):
                return tx, ty, None, 0

    resultados = await asyncio.gather(*(una(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)))
    con_imagen = 0
    zoom_min = z
    for tx, ty, img, zz in resultados:
        if img is None:
            continue
        con_imagen += 1
        zoom_min = min(zoom_min, zz)
        oy, ox = (ty - ty0) * LADO, (tx - tx0) * LADO
        mosaico[oy:oy + LADO, ox:ox + LADO] = np.asarray(img.convert("RGB").resize((LADO, LADO)))

    # Muestreo bilineal del mosaico en los centros de la salida.
    fx = np.clip(gx - tx0 * LADO - 0.5, 0, mosaico.shape[1] - 1.001)
    fy = np.clip(gy - ty0 * LADO - 0.5, 0, mosaico.shape[0] - 1.001)
    x0, y0 = fx.astype(int), fy.astype(int)
    u, v = (fx - x0)[None, :, None], (fy - y0)[:, None, None]
    m = mosaico.astype(np.float32)
    a = m[y0[:, None], x0[None, :]]
    b = m[y0[:, None], x0[None, :] + 1]
    c = m[y0[:, None] + 1, x0[None, :]]
    d = m[y0[:, None] + 1, x0[None, :] + 1]
    rgb = (a * (1 - u) * (1 - v) + b * u * (1 - v) + c * (1 - u) * v + d * u * v).round().astype(np.uint8)

    total = len(resultados)
    return Ortofoto(rgb=rgb, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, m_px=m_px, zoom=z,
                    zoom_min_usado=zoom_min if con_imagen else 0,
                    cobertura=con_imagen / total if total else 0.0, fuente=nombre_fuente, sintetica=sintetica)
