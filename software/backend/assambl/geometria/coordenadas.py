"""Conversión entre lat/lon, coordenadas locales en metros y teselas web-mercator."""

from __future__ import annotations

import math

RADIO_TIERRA_M = 6_371_008.8


class SistemaLocal:
    """Equirrectangular local centrada en (lat0, lon0). +X este, +Y norte."""

    def __init__(self, lat0: float, lon0: float) -> None:
        self.lat0 = lat0
        self.lon0 = lon0
        self._k = RADIO_TIERRA_M * math.pi / 180.0
        self._cos = math.cos(math.radians(lat0))

    @property
    def metros_por_grado_lat(self) -> float:
        return self._k

    @property
    def metros_por_grado_lon(self) -> float:
        return self._cos * self._k

    def a_local(self, lat: float, lon: float) -> tuple[float, float]:
        return ((lon - self.lon0) * self._cos * self._k, (lat - self.lat0) * self._k)

    def a_geografica(self, x: float, y: float) -> tuple[float, float]:
        return (self.lat0 + y / self._k, self.lon0 + x / (self._cos * self._k))


def metros_por_pixel(lat: float, zoom: int) -> float:
    return 156543.03392 * math.cos(math.radians(lat)) / (2**zoom)


def lonlat_a_pixel(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    """Píxel global (x, y) en web-mercator con teselas de 256 px."""
    n = 256 * (2**zoom)
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return x, y


def pixel_a_lonlat(px: float, py: float, zoom: int) -> tuple[float, float]:
    n = 256 * (2**zoom)
    lon = px / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * py / n))))
    return lon, lat


def zoom_para_paso(lat: float, paso_m: float, maximo: int = 14, minimo: int = 8) -> int:
    """Menor zoom cuyo píxel es ≤ paso_m (más resolución que la malla pedida)."""
    for z in range(minimo, maximo + 1):
        if metros_por_pixel(lat, z) <= paso_m:
            return z
    return maximo
