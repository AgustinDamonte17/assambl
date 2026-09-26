"""Curvas de nivel de la malla del relieve, para dibujar el lote sobre el terreno.

Se calculan sobre los posts tal como vienen (marching squares sobre la rejilla),
sin suavizar ni interpolar entre posts: la curva tiene la resolución del dato y
no aparenta más precisión de la que hay.
"""

from __future__ import annotations

import numpy as np

from .malla import MallaLocal

EQUIDISTANCIAS_M = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0)
MAX_CURVAS = 25
# Cada cuántas curvas hay una maestra (más marcada y con cota).
CADA_MAESTRA = 5

Segmento = tuple[tuple[float, float], tuple[float, float]]


def equidistancia(desnivel_m: float) -> float | None:
    """La menor equidistancia estándar que deja a lo sumo MAX_CURVAS curvas.
    None si el relieve es plano a efectos prácticos."""
    if desnivel_m < EQUIDISTANCIAS_M[0] / 2:
        return None
    for e in EQUIDISTANCIAS_M:
        if desnivel_m / e <= MAX_CURVAS:
            return e
    return EQUIDISTANCIAS_M[-1]


def curvas(malla: MallaLocal, cota_origen_msnm: float | None = None,
           equidistancia_m: float | None = None) -> dict:
    """Curvas de nivel en coordenadas locales. Las cotas se informan en m s.n.m. si
    se conoce la cota del origen, y relativas al origen si no."""
    z = malla.z
    base = cota_origen_msnm or 0.0
    z_min, z_max = float(z.min()), float(z.max())
    e = equidistancia_m or equidistancia(z_max - z_min)
    salida = {
        "equidistancia_m": e,
        "cota_min": round(z_min + base, 2),
        "cota_max": round(z_max + base, 2),
        "absolutas": cota_origen_msnm is not None,
        "curvas": [],
    }
    if e is None:
        return salida

    # Niveles en cotas absolutas redondas (múltiplos de la equidistancia).
    primero = np.ceil((z_min + base) / e) * e
    for cota in np.arange(primero, z_max + base, e):
        nivel = float(cota) - base
        segmentos = _segmentos(malla, z, nivel)
        if segmentos:
            indice = int(round(cota / e))
            salida["curvas"].append({
                "cota": round(float(cota), 2),
                "maestra": indice % CADA_MAESTRA == 0,
                "segmentos": [[[round(x, 2), round(y, 2)] for x, y in s] for s in segmentos],
            })
    return salida


def _segmentos(m: MallaLocal, z: np.ndarray, nivel: float) -> list[Segmento]:
    # Un corrimiento mínimo evita que un post exactamente en el nivel genere
    # segmentos degenerados.
    zz = z - (nivel + 1e-9)
    arriba = zz > 0
    # Celdas donde el nivel cruza: no todas las esquinas del mismo lado.
    n_arriba = arriba[:-1, :-1].astype(int) + arriba[:-1, 1:] + arriba[1:, :-1] + arriba[1:, 1:]
    salida: list[Segmento] = []
    for j, i in zip(*np.nonzero((n_arriba > 0) & (n_arriba < 4))):
        # Esquinas en orden: suroeste, sureste, noreste, noroeste.
        esquinas = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        valores = [zz[b, a] for a, b in esquinas]
        puntos = []
        for k in range(4):
            a, b = valores[k], valores[(k + 1) % 4]
            if (a > 0) != (b > 0):
                t = a / (a - b)
                (ia, ja), (ib, jb) = esquinas[k], esquinas[(k + 1) % 4]
                puntos.append((m.x0 + (ia + t * (ib - ia)) * m.dx, m.y0 + (ja + t * (jb - ja)) * m.dy))
        if len(puntos) == 2:
            salida.append((puntos[0], puntos[1]))
        elif len(puntos) == 4:
            # Silla: se decide con el valor medio de la celda. Si el centro está del
            # lado del suroeste, quedan aisladas las esquinas sureste (lados 0-1) y
            # noroeste (lados 2-3); si no, la suroeste (3-0) y la noreste (1-2).
            centro = sum(valores) / 4
            if (centro > 0) == (valores[0] > 0):
                salida += [(puntos[0], puntos[1]), (puntos[2], puntos[3])]
            else:
                salida += [(puntos[3], puntos[0]), (puntos[1], puntos[2])]
    return salida
