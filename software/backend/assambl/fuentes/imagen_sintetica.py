"""Mundo SINTÉTICO para desarrollar y probar sin red (ASSAMBL_IMAGEN_SINTETICA=1).

No son datos reales. Dibuja un campo con un camino de tierra norte-sur, una calle
este-oeste, casas sobre el camino y árboles con su sombra, de forma coherente en
todos los zooms. También devuelve ese mundo como respuesta de Overpass, para probar
calles y construcciones. La fuente de cada capa lo declara.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

NOMBRE = "Mundo sintético de prueba (no es una imagen real)"
LAT_REF, LON_REF = -31.42, -64.19
_K = 6_371_008.8 * math.pi / 180.0
_COS = math.cos(math.radians(LAT_REF))

CAMINO_X = (38.0, 44.0)  # tierra, norte-sur
CALLE_Y = (-126.0, -118.0)  # pavimento, este-oeste
CASAS_X = (52.0, 64.0)
CASAS_PASO_Y = 30.0
CELDA_ARBOL = 9.0


def _a_metros(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (lon - LON_REF) * _COS * _K, (lat - LAT_REF) * _K


def _a_latlon(x: float, y: float) -> tuple[float, float]:
    return LAT_REF + y / _K, LON_REF + x / (_COS * _K)


def _azar(i: np.ndarray, j: np.ndarray, k: float) -> np.ndarray:
    return np.modf(np.abs(np.sin(i * 12.9898 + j * 78.233 + k * 37.719) * 43758.5453))[0]


def arboles_en(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Distancia normalizada al árbol más cercano (<1 dentro de la copa) y a su sombra."""
    ci, cj = np.floor(x / CELDA_ARBOL), np.floor(y / CELDA_ARBOL)
    copa = np.full(x.shape, 9.0)
    sombra = np.full(x.shape, 9.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            i, j = ci + di, cj + dj
            cx = (i + 0.2 + 0.6 * _azar(i, j, 1)) * CELDA_ARBOL
            cy = (j + 0.2 + 0.6 * _azar(i, j, 2)) * CELDA_ARBOL
            r = 1.6 + 3.2 * _azar(i, j, 3)
            hay = (_azar(i, j, 4) < 0.22) & ~((cx > CAMINO_X[0] - 3) & (cx < CASAS_X[1] + 4)) & \
                  ~((cy > CALLE_Y[0] - 4) & (cy < CALLE_Y[1] + 4))
            d = np.hypot(x - cx, y - cy) / r
            ds = np.hypot(x - cx - 0.35 * r, y - cy + 0.6 * r) / r
            copa = np.where(hay, np.minimum(copa, d), copa)
            sombra = np.where(hay, np.minimum(sombra, ds), sombra)
    return copa, sombra


def arboles_en_rectangulo(xmin: float, xmax: float, ymin: float, ymax: float) -> list[tuple[float, float, float]]:
    """Árboles del mundo sintético (x, y, radio) en metros de referencia; para pruebas."""
    salida = []
    for i in range(math.floor(xmin / CELDA_ARBOL) - 1, math.ceil(xmax / CELDA_ARBOL) + 1):
        for j in range(math.floor(ymin / CELDA_ARBOL) - 1, math.ceil(ymax / CELDA_ARBOL) + 1):
            a = lambda k: float(_azar(np.float64(i), np.float64(j), k))
            cx = (i + 0.2 + 0.6 * a(1)) * CELDA_ARBOL
            cy = (j + 0.2 + 0.6 * a(2)) * CELDA_ARBOL
            if a(4) >= 0.22 or (CAMINO_X[0] - 3 < cx < CASAS_X[1] + 4) or (CALLE_Y[0] - 4 < cy < CALLE_Y[1] + 4):
                continue
            if xmin <= cx <= xmax and ymin <= cy <= ymax:
                salida.append((cx, cy, 1.6 + 3.2 * a(3)))
    return salida


def tesela(z: int, tx: int, ty: int) -> Image.Image:
    px = tx * 256 + np.arange(256) + 0.5
    py = ty * 256 + np.arange(256) + 0.5
    n = 256 * 2**z
    lon = px / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * py / n))))
    x, y = _a_metros(lat[:, None], lon[None, :])
    x, y = np.broadcast_to(x, (256, 256)), np.broadcast_to(y, (256, 256))

    # Pasto con manchas.
    ruido = 0.5 + 0.25 * np.sin(x / 23 + y / 41) + 0.15 * np.cos(x / 9 - y / 13) + 0.1 * np.sin(y / 5.3)
    rgb = np.stack([118 + 30 * ruido, 128 + 22 * ruido, 72 + 10 * ruido], axis=-1)

    camino = (x > CAMINO_X[0]) & (x < CAMINO_X[1])
    rgb[camino] = (168, 138, 104)
    calle = (y > CALLE_Y[0]) & (y < CALLE_Y[1])
    rgb[calle] = (112, 112, 110)

    fila = np.floor(y / CASAS_PASO_Y)
    ly = y - fila * CASAS_PASO_Y
    casa = (x > CASAS_X[0]) & (x < CASAS_X[1]) & (ly > 6) & (ly < 18) & ~calle
    sombra_casa = (x > CASAS_X[0] + 1) & (x < CASAS_X[1] + 1) & (ly > 4) & (ly < 6) & ~calle
    rgb[sombra_casa] *= 0.55
    tono = np.where(_azar(fila, fila, 7)[..., None] < 0.5, np.array([176, 92, 70]), np.array([190, 190, 186]))
    rgb = np.where(casa[..., None], tono, rgb)

    copa, sombra = arboles_en(x, y)
    en_sombra = (sombra < 1) & (copa >= 1) & ~casa
    rgb[en_sombra] *= 0.5
    en_copa = copa < 1
    luz = (0.75 + 0.25 * (1 - copa))[..., None]
    rgb = np.where(en_copa[..., None], np.array([48, 78, 38]) * luz, rgb)

    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def overpass(sur: float, oeste: float, norte: float, este: float) -> dict:
    """El mundo sintético como respuesta de Overpass (`out geom`)."""
    x0, y0 = _a_metros(np.float64(sur), np.float64(oeste))
    x1, y1 = _a_metros(np.float64(norte), np.float64(este))
    elementos: list[dict] = []

    def via(etiquetas: dict, puntos: list[tuple[float, float]]) -> None:
        geom = [dict(zip(("lat", "lon"), _a_latlon(px, py))) for px, py in puntos]
        elementos.append({"type": "way", "id": len(elementos) + 1, "tags": etiquetas, "geometry": geom})

    cx = sum(CAMINO_X) / 2
    if x0 <= cx <= x1:
        via({"highway": "track", "surface": "dirt", "width": "6"}, [(cx, y0), (cx, y1)])
    cy = sum(CALLE_Y) / 2
    if y0 <= cy <= y1:
        via({"highway": "residential", "surface": "asphalt"}, [(x0, cy), (x1, cy)])
    if CASAS_X[1] >= x0 and CASAS_X[0] <= x1:
        for fila in range(math.floor(y0 / CASAS_PASO_Y), math.ceil(y1 / CASAS_PASO_Y)):
            a, b = fila * CASAS_PASO_Y + 6, fila * CASAS_PASO_Y + 18
            if b < y0 or a > y1 or (a < CALLE_Y[1] and b > CALLE_Y[0]):
                continue
            etiquetas = {"building": "house"}
            if fila % 3 == 0:
                etiquetas["building:levels"] = "2"
            via(etiquetas, [(CASAS_X[0], a), (CASAS_X[1], a), (CASAS_X[1], b), (CASAS_X[0], b), (CASAS_X[0], a)])
    return {"elements": elementos}

