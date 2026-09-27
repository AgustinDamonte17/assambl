"""Copas de árboles detectadas en la ortofoto, sin IA.

Método: una copa vista desde arriba es una mancha más verde y más oscura que el
suelo que la rodea. Se marca la vegetación oscura con el índice de exceso de verde
(ExG sobre colores cromáticos) y el brillo, se limpia la máscara y cada copa es un
máximo de la distancia al borde: su posición es el centro de la mancha y su radio,
la distancia al borde. Dos copas que se tocan dejan un cuello en esa distancia y se
separan solas.

La sombra de un árbol es oscura pero no verde, así que no se confunde con otra
copa; un pasto muy verde es verde pero claro. Es una aproximación: no distingue
especies, no ve árboles bajo otros y la altura no se puede medir desde arriba, así
que se supone a partir del diámetro de copa y se declara como supuesto.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from ..fuentes.imagen_satelital import Ortofoto


@dataclass
class Arbol:
    x: float
    y: float
    radio_m: float
    altura_m: float
    fuente: str
    altura_supuesta: bool = True

    def como_dict(self) -> dict:
        return {"x": round(self.x, 2), "y": round(self.y, 2), "radio_m": round(self.radio_m, 2),
                "altura_m": round(self.altura_m, 1), "fuente": self.fuente,
                "altura_supuesta": self.altura_supuesta}


FUENTE = "detección en imagen satelital"


def altura_supuesta(radio_m: float) -> float:
    """Relación típica copa-altura de árboles aislados de llanura; solo para dibujar."""
    return float(np.clip(1.6 * radio_m + 2.0, 3.0, 16.0))


def mascara_copas(rgb: np.ndarray) -> np.ndarray:
    f = rgb.astype(np.float32) / 255.0
    suma = f.sum(axis=2) + 1e-6
    r, g, b = f[..., 0] / suma, f[..., 1] / suma, f[..., 2] / suma
    exg = 2 * g - r - b
    brillo = f.mean(axis=2)
    # Umbrales relativos a la propia imagen: el pasto de un lote seco y el de uno
    # regado no tienen el mismo verde.
    umbral_verde = max(0.08, float(np.percentile(exg, 50)) + 0.06)
    umbral_brillo = float(np.percentile(brillo, 50))
    return (exg > umbral_verde) & (brillo < umbral_brillo) & (brillo > 0.04)


def detectar(orto: Ortofoto, radio_min_m: float = 0.9, radio_max_m: float = 12.0,
             max_arboles: int = 2000, fuente: str = FUENTE) -> list[Arbol]:
    m = orto.m_px
    mascara = mascara_copas(orto.rgb)
    # Limpieza: quita ramitas y píxeles sueltos, y cierra huecos dentro de la copa.
    radio_px = max(1, int(round(0.6 / m)))
    estructura = _disco(radio_px)
    mascara = ndimage.binary_opening(mascara, structure=estructura)
    mascara = ndimage.binary_fill_holes(mascara)

    distancia = ndimage.distance_transform_edt(mascara) * m
    ventana = max(3, int(2 * radio_min_m / m) | 1)
    maximos = (distancia == ndimage.maximum_filter(distancia, size=ventana)) & (distancia >= radio_min_m)
    filas, cols = np.nonzero(maximos)
    valores = distancia[filas, cols]
    orden = np.argsort(-valores)

    aceptados: list[tuple[float, float, float]] = []
    for k in orden:
        r = min(float(valores[k]) + 0.5 * m, radio_max_m)
        x, y = orto.a_local(cols[k] + 0.5, filas[k] + 0.5)
        x, y = float(x), float(y)
        if any((x - ax) ** 2 + (y - ay) ** 2 < (0.9 * max(r, ar)) ** 2 for ax, ay, ar in aceptados):
            continue
        aceptados.append((x, y, r))
        if len(aceptados) >= max_arboles:
            break
    return [Arbol(x, y, r, altura_supuesta(r), fuente) for x, y, r in aceptados]


def _disco(radio: int) -> np.ndarray:
    y, x = np.mgrid[-radio:radio + 1, -radio:radio + 1]
    return x * x + y * y <= radio * radio
