"""Malla de relieve en coordenadas locales.

Los vértices son los posts de NASADEM, uno a uno: no se interpola ni se densifica
el relieve. Lo único que se interpola es la consulta de altura sobre la superficie
ya triangulada, que devuelve el punto exacto de la cara donde cae la consulta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..modelo.sitio import MallaDem
from .coordenadas import SistemaLocal


@dataclass
class MallaLocal:
    """Rejilla regular en metros. El vértice (j, i) está en el índice j*nx + i,
    con j creciendo hacia el norte e i hacia el este."""

    vertices: np.ndarray  # (ny*nx, 3) en metros locales
    nx: int
    ny: int
    x0: float
    y0: float
    dx: float
    dy: float

    @property
    def paso_medio_m(self) -> float:
        return (self.dx + self.dy) / 2

    @property
    def z(self) -> np.ndarray:
        return self.vertices[:, 2].reshape(self.ny, self.nx)

    def altura_en(self, x: float, y: float) -> float:
        """Altura de la superficie triangulada en (x, y), en metros locales.

        Usa la misma diagonal suroeste–noreste que generadores.glb.rejilla_indices,
        así que el resultado cae exactamente sobre la cara que se ve en la escena.
        """
        z = self.z
        fi = (x - self.x0) / self.dx
        fj = (y - self.y0) / self.dy
        i = min(max(int(math.floor(fi)), 0), self.nx - 2)
        j = min(max(int(math.floor(fj)), 0), self.ny - 2)
        u = min(max(fi - i, 0.0), 1.0)
        v = min(max(fj - j, 0.0), 1.0)
        z_so, z_se, z_no, z_ne = z[j, i], z[j, i + 1], z[j + 1, i], z[j + 1, i + 1]
        if v <= u:
            return float(z_so + u * (z_se - z_so) + v * (z_ne - z_se))
        return float(z_so + v * (z_no - z_so) + u * (z_ne - z_no))

    def dentro(self, x: float, y: float) -> bool:
        return (
            self.x0 <= x <= self.x0 + (self.nx - 1) * self.dx
            and self.y0 <= y <= self.y0 + (self.ny - 1) * self.dy
        )

    def extension_m(self) -> tuple[float, float]:
        return (self.nx - 1) * self.dx, (self.ny - 1) * self.dy


def desde_dem(dem: MallaDem, sistema: SistemaLocal, cota_origen: float | None = None) -> tuple[MallaLocal, float]:
    """Proyecta los posts del DEM al sistema local. Devuelve la malla y la cota de
    referencia (msnm) que quedó en z = 0."""
    alturas = np.asarray(dem.alturas_msnm, dtype=np.float64).reshape(dem.ny, dem.nx)

    lat = dem.lat_sur + np.arange(dem.ny) * dem.paso_deg
    lon = dem.lon_oeste + np.arange(dem.nx) * dem.paso_deg
    x = (lon - sistema.lon0) * sistema.metros_por_grado_lon
    y = (lat - sistema.lat0) * sistema.metros_por_grado_lat

    malla_x, malla_y = np.meshgrid(x, y)
    dx = float(x[1] - x[0]) if dem.nx > 1 else 0.0
    dy = float(y[1] - y[0]) if dem.ny > 1 else 0.0

    provisoria = MallaLocal(
        vertices=np.column_stack([malla_x.ravel(), malla_y.ravel(), alturas.ravel()]),
        nx=dem.nx,
        ny=dem.ny,
        x0=float(x[0]),
        y0=float(y[0]),
        dx=dx,
        dy=dy,
    )
    if cota_origen is None:
        # La cota del origen sale de la superficie ya triangulada: fija el nivel de
        # referencia, no agrega detalle al relieve.
        cota_origen = provisoria.altura_en(0.0, 0.0) if provisoria.dentro(0.0, 0.0) else float(alturas.mean())

    provisoria.vertices[:, 2] -= cota_origen
    return provisoria, float(cota_origen)


def apoyar(malla: MallaLocal, puntos: list[tuple[float, float]], separacion_m: float = 0.0) -> np.ndarray:
    """Lleva puntos planos a la superficie de la malla, con una separación opcional
    para que las líneas no queden escondidas dentro de las caras."""
    return np.array(
        [[x, y, malla.altura_en(x, y) + separacion_m] for x, y in puntos],
        dtype=np.float32,
    )


def malla_plana(sistema: SistemaLocal, margen_m: float, paso_m: float = 30.0) -> MallaLocal:
    """Rejilla horizontal en z = 0, para la escena provisional cuando no hay DEM."""
    n = max(2, int(round(2 * margen_m / paso_m)) + 1)
    coord = np.linspace(-margen_m, margen_m, n)
    mx, my = np.meshgrid(coord, coord)
    paso = float(coord[1] - coord[0])
    return MallaLocal(
        vertices=np.column_stack([mx.ravel(), my.ravel(), np.zeros(n * n)]),
        nx=n,
        ny=n,
        x0=-margen_m,
        y0=-margen_m,
        dx=paso,
        dy=paso,
    )


def recortar(malla: MallaLocal, margen_m: float) -> MallaLocal:
    """Recorta la malla al cuadrado de ±margen alrededor del origen, conservando
    los posts completos que lo cubren."""
    i0 = max(0, int(math.floor((-margen_m - malla.x0) / malla.dx)))
    i1 = min(malla.nx - 1, int(math.ceil((margen_m - malla.x0) / malla.dx)))
    j0 = max(0, int(math.floor((-margen_m - malla.y0) / malla.dy)))
    j1 = min(malla.ny - 1, int(math.ceil((margen_m - malla.y0) / malla.dy)))
    if i1 - i0 < 1 or j1 - j0 < 1:
        return malla
    bloque = malla.vertices.reshape(malla.ny, malla.nx, 3)[j0 : j1 + 1, i0 : i1 + 1]
    return MallaLocal(
        vertices=bloque.reshape(-1, 3).copy(),
        nx=i1 - i0 + 1,
        ny=j1 - j0 + 1,
        x0=malla.x0 + i0 * malla.dx,
        y0=malla.y0 + j0 * malla.dy,
        dx=malla.dx,
        dy=malla.dy,
    )


def pendiente_media(malla: MallaLocal, puntos: list[tuple[float, float]]) -> tuple[float, float]:
    """Ajusta un plano por mínimos cuadrados a la superficie bajo un polígono.
    Devuelve (pendiente en %, azimut de máxima pendiente en grados desde el norte)."""
    if len(puntos) < 3:
        return 0.0, 0.0
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    muestras = []
    paso = max(malla.paso_medio_m / 4, 1.0)
    x = min(xs)
    while x <= max(xs):
        y = min(ys)
        while y <= max(ys):
            muestras.append((x, y, malla.altura_en(x, y)))
            y += paso
        x += paso
    if len(muestras) < 3:
        muestras = [(px, py, malla.altura_en(px, py)) for px, py in puntos]

    a = np.array([[p[0], p[1], 1.0] for p in muestras])
    b = np.array([p[2] for p in muestras])
    (cx, cy, _), *_ = np.linalg.lstsq(a, b, rcond=None)
    pendiente = math.hypot(cx, cy)
    azimut = math.degrees(math.atan2(-cx, -cy)) % 360.0  # hacia donde baja
    return pendiente * 100.0, azimut
