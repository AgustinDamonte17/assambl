"""Polígonos planos: área, perímetro, lados, centroide, validez y poligonal por lados."""

from __future__ import annotations

import math

Punto = tuple[float, float]


def area_con_signo(puntos: list[Punto]) -> float:
    if len(puntos) < 3:
        return 0.0
    s = 0.0
    for (x1, y1), (x2, y2) in zip(puntos, puntos[1:] + puntos[:1]):
        s += x1 * y2 - x2 * y1
    return s / 2.0


def area(puntos: list[Punto]) -> float:
    return abs(area_con_signo(puntos))


def perimetro(puntos: list[Punto]) -> float:
    return sum(math.dist(a, b) for a, b in zip(puntos, puntos[1:] + puntos[:1]))


def centroide(puntos: list[Punto]) -> Punto:
    a = area_con_signo(puntos)
    if abs(a) < 1e-12:
        n = len(puntos) or 1
        return (sum(p[0] for p in puntos) / n, sum(p[1] for p in puntos) / n)
    cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(puntos, puntos[1:] + puntos[:1]):
        cruz = x1 * y2 - x2 * y1
        cx += (x1 + x2) * cruz
        cy += (y1 + y2) * cruz
    return (cx / (6 * a), cy / (6 * a))


def rumbo_deg(a: Punto, b: Punto) -> float:
    """Azimut de a→b desde el norte (+Y), horario, en [0, 360)."""
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360.0


def lados(puntos: list[Punto]) -> list[dict]:
    return [
        {"longitud_m": math.dist(a, b), "rumbo_deg": rumbo_deg(a, b)}
        for a, b in zip(puntos, puntos[1:] + puntos[:1])
    ]


def desde_lados(origen: Punto, lados_: list[dict]) -> list[Punto]:
    """Vértices a partir del origen y los lados (longitud, rumbo). El último lado
    de la lista se ignora si cierra: la poligonal siempre se cierra al origen."""
    puntos = [origen]
    for lado in lados_[:-1] if len(lados_) >= 3 else lados_:
        x, y = puntos[-1]
        r = math.radians(lado["rumbo_deg"])
        puntos.append((x + lado["longitud_m"] * math.sin(r), y + lado["longitud_m"] * math.cos(r)))
    return puntos


def _se_cruzan(p1: Punto, p2: Punto, p3: Punto, p4: Punto) -> bool:
    def orient(a: Punto, b: Punto, c: Punto) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and all(abs(d) > 1e-9 for d in (d1, d2, d3, d4))


def es_simple(puntos: list[Punto]) -> bool:
    """Sin autointersecciones entre lados no adyacentes."""
    n = len(puntos)
    if n < 3:
        return False
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) in (1, n - 1):
                continue
            if _se_cruzan(puntos[i], puntos[(i + 1) % n], puntos[j], puntos[(j + 1) % n]):
                return False
    return True


def contiene(puntos: list[Punto], x: float, y: float) -> bool:
    dentro = False
    for (ax, ay), (bx, by) in zip(puntos, puntos[1:] + puntos[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            dentro = not dentro
    return dentro


def caja(puntos: list[Punto]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    return min(xs), min(ys), max(xs), max(ys)


def _en_triangulo(p: Punto, a: Punto, b: Punto, c: Punto) -> bool:
    def signo(u: Punto, v: Punto, w: Punto) -> float:
        return (u[0] - w[0]) * (v[1] - w[1]) - (v[0] - w[0]) * (u[1] - w[1])

    d1, d2, d3 = signo(p, a, b), signo(p, b, c), signo(p, c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def triangular(puntos: list[Punto]) -> list[tuple[int, int, int]]:
    """Triangula un polígono simple por recorte de orejas.

    Sirve para lotes en L o en forma de bandera, donde un abanico desde el
    centroide produciría triángulos fuera del lote. Devuelve índices sobre la
    lista original, con los triángulos en sentido antihorario.
    """
    n = len(puntos)
    if n < 3:
        return []
    indices = list(range(n))
    if area_con_signo(puntos) < 0:
        indices.reverse()

    triangulos: list[tuple[int, int, int]] = []
    intentos = 0
    while len(indices) > 3 and intentos < 2 * len(indices) ** 2:
        intentos += 1
        recorto = False
        for k in range(len(indices)):
            ia, ib, ic = indices[k - 1], indices[k], indices[(k + 1) % len(indices)]
            a, b, c = puntos[ia], puntos[ib], puntos[ic]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-12:
                continue  # vértice cóncavo o colineal
            if any(_en_triangulo(puntos[i], a, b, c) for i in indices if i not in (ia, ib, ic)):
                continue
            triangulos.append((ia, ib, ic))
            indices.pop(k)
            recorto = True
            break
        if not recorto:
            break
    if len(indices) == 3:
        triangulos.append((indices[0], indices[1], indices[2]))
    return triangulos


def densificar(puntos: list[Punto], paso_m: float, cerrado: bool = True) -> list[Punto]:
    """Agrega vértices intermedios cada paso_m sobre cada lado.

    Se usa para apoyar el contorno del lote sobre la malla: sin puntos intermedios
    una línea recta entre dos esquinas atravesaría el relieve.
    """
    if len(puntos) < 2 or paso_m <= 0:
        return list(puntos)
    pares = list(zip(puntos, puntos[1:] + puntos[:1])) if cerrado else list(zip(puntos, puntos[1:]))
    salida: list[Punto] = []
    for a, b in pares:
        salida.append(a)
        largo = math.dist(a, b)
        for t in range(1, int(largo / paso_m)):
            f = t * paso_m / largo
            salida.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    if not cerrado:
        salida.append(puntos[-1])
    return salida
