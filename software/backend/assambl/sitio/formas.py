"""Geometría de los objetos del sitio en coordenadas locales (metros, Z arriba).

Cada función devuelve (posiciones, índices) o, para el suelo, también las
coordenadas de textura. Las formas son deliberadamente simples: el sitio es una
aproximación y no debe aparentar más detalle del que tiene el dato.
"""

from __future__ import annotations

import math

import numpy as np

from ..geometria import poligono

Malla = tuple[np.ndarray, np.ndarray]


def unir(mallas: list[Malla]) -> Malla | None:
    mallas = [m for m in mallas if len(m[1])]
    if not mallas:
        return None
    posiciones, indices, base = [], [], 0
    for p, i in mallas:
        posiciones.append(p)
        indices.append(i + base)
        base += len(p)
    return np.vstack(posiciones).astype(np.float32), np.concatenate(indices).astype(np.uint32)


def rectangulo(xmin: float, xmax: float, ymin: float, ymax: float, z: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rectángulo horizontal con coordenadas de textura de una imagen norte arriba."""
    p = np.array([[xmin, ymin, z], [xmax, ymin, z], [xmax, ymax, z], [xmin, ymax, z]], dtype=np.float32)
    uv = np.array([[0, 1], [1, 1], [1, 0], [0, 0]], dtype=np.float32)
    return p, np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32), uv


def cinta(puntos: list[tuple[float, float]], ancho: float, z: float, cerrada: bool = False) -> Malla:
    """Franja horizontal de `ancho` metros centrada en la polilínea."""
    pts = list(puntos) + ([puntos[0]] if cerrada else [])
    posiciones, indices = [], []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        largo = math.hypot(x2 - x1, y2 - y1)
        if largo < 1e-6:
            continue
        nx, ny = -(y2 - y1) / largo * ancho / 2, (x2 - x1) / largo * ancho / 2
        base = len(posiciones)
        posiciones += [(x1 + nx, y1 + ny, z), (x1 - nx, y1 - ny, z), (x2 - nx, y2 - ny, z), (x2 + nx, y2 + ny, z)]
        indices += [base, base + 1, base + 2, base, base + 2, base + 3]
    return np.array(posiciones, dtype=np.float32).reshape(-1, 3), np.array(indices, dtype=np.uint32)


def extrusion(contorno: list[tuple[float, float]], altura: float, z0: float = 0.0) -> Malla:
    """Prisma de techo plano: muros y cubierta, sin base."""
    pts = list(contorno)
    if poligono.area_con_signo(pts) < 0:
        pts.reverse()
    n = len(pts)
    posiciones = [(x, y, z0) for x, y in pts] + [(x, y, z0 + altura) for x, y in pts]
    indices = []
    for i in range(n):
        j = (i + 1) % n
        indices += [i, j, n + j, i, n + j, n + i]
    for a, b, c in poligono.triangular(pts):
        indices += [n + a, n + b, n + c]
    return np.array(posiciones, dtype=np.float32), np.array(indices, dtype=np.uint32)


def _elipsoide(cx: float, cy: float, cz: float, rx: float, rz: float, lados: int, anillos: int) -> Malla:
    posiciones = [(cx, cy, cz + rz)]
    for j in range(1, anillos):
        fi = math.pi * j / anillos
        for k in range(lados):
            t = 2 * math.pi * k / lados
            posiciones.append((cx + rx * math.sin(fi) * math.cos(t), cy + rx * math.sin(fi) * math.sin(t),
                               cz + rz * math.cos(fi)))
    posiciones.append((cx, cy, cz - rz))
    fondo = len(posiciones) - 1
    indices = []
    for k in range(lados):
        indices += [0, 1 + k, 1 + (k + 1) % lados]
    for j in range(anillos - 2):
        a, b = 1 + j * lados, 1 + (j + 1) * lados
        for k in range(lados):
            k2 = (k + 1) % lados
            indices += [a + k, b + k, b + k2, a + k, b + k2, a + k2]
    a = 1 + (anillos - 2) * lados
    for k in range(lados):
        indices += [fondo, a + (k + 1) % lados, a + k]
    return np.array(posiciones, dtype=np.float32), np.array(indices, dtype=np.uint32)


def _cilindro(cx: float, cy: float, z0: float, z1: float, r: float, lados: int) -> Malla:
    posiciones = []
    for z in (z0, z1):
        for k in range(lados):
            t = 2 * math.pi * k / lados
            posiciones.append((cx + r * math.cos(t), cy + r * math.sin(t), z))
    indices = []
    for k in range(lados):
        k2 = (k + 1) % lados
        indices += [k, k2, lados + k2, k, lados + k2, lados + k]
    return np.array(posiciones, dtype=np.float32), np.array(indices, dtype=np.uint32)


def arbol(x: float, y: float, radio: float, altura: float, detalle: bool) -> tuple[Malla, Malla]:
    """Tronco y copa. La copa es un elipsoide del radio medido y la altura supuesta."""
    alto_copa = min(max(altura * 0.55, radio * 0.9), altura - 0.8)
    centro = altura - alto_copa / 2
    tronco = _cilindro(x, y, 0.0, centro, max(0.08, radio * 0.08), 7 if detalle else 4)
    copa = _elipsoide(x, y, centro, radio, alto_copa / 2, 10 if detalle else 6, 6 if detalle else 3)
    return tronco, copa
