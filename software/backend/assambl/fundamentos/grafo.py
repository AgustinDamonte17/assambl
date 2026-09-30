"""Grafo de la planta: qué ambiente linda con cuál y cómo se pasa de uno a otro.

Se arma solo con la casa (muros, aberturas y contornos de ambientes), así sirve
igual para una planta generada, una leída de una imagen, una dibujada a mano o
Angus Ranch. Dos ambientes son vecinos si tienen lados paralelos enfrentados a
menos de un espesor de muro; la relación es:

- `abierto`: no hay muro entre ellos (estar y comedor, pasillo y estar);
- `puerta`: hay muro y una puerta, paso o corrediza en el tramo compartido;
- `muro`: solo muro.

Con eso se responde lo que piden los fundamentos: por dónde se entra, cuántos
ambientes hay que atravesar para llegar a un dormitorio, qué baño alcanza una
visita sin pasar por un dormitorio, qué dormitorio comparte muro con el estar.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from ..geometria import poligono

TOL_ENFRENTADOS_M = 0.36   # separación máxima entre caras de ambientes vecinos (muro de 20 cm + holgura)
TOL_LINEA_M = 0.12         # distancia del eje del muro a la línea media entre las caras
SOLAPE_MIN_M = 0.3         # tramo compartido mínimo para considerarlos vecinos
PASO = ("puerta", "paso", "ventana_corrediza")


@dataclass
class Vecindad:
    a: str
    b: str
    tipo: str               # abierto | puerta | muro
    largo_m: float           # largo compartido
    muros: set[str] = field(default_factory=set)


@dataclass
class Grafo:
    ambientes: dict[str, dict]
    vecinos: dict[tuple[str, str], Vecindad]
    exterior: dict[str, list[dict]]        # ambiente -> [{muro, lado, abertura}] sobre muros exteriores
    accesos: list[str]                      # ambientes a los que da una puerta exterior
    areas: dict[str, float]
    muros_por_id: dict[str, dict]

    def uso(self, aid: str) -> str:
        return self.ambientes[aid].get("uso", "otro")

    def nombre(self, aid: str) -> str:
        return self.ambientes[aid].get("nombre", aid)

    def relacion(self, a: str, b: str) -> Vecindad | None:
        return self.vecinos.get((a, b)) or self.vecinos.get((b, a))

    def conectados(self, a: str) -> list[str]:
        """Ambientes a los que se pasa desde `a` (abierto o por puerta)."""
        res = []
        for (x, y), v in self.vecinos.items():
            if v.tipo in ("abierto", "puerta") and a in (x, y):
                res.append(y if x == a else x)
        return res

    def lindantes(self, a: str) -> list[Vecindad]:
        return [v for (x, y), v in self.vecinos.items() if a in (x, y)]

    def camino(self, desde: str, hasta: str, evitar: set[str] | None = None) -> list[str] | None:
        """Camino más corto por puertas y pasos, sin atravesar `evitar` (salvo los extremos)."""
        evitar = evitar or set()
        previo: dict[str, str | None] = {desde: None}
        cola = deque([desde])
        while cola:
            n = cola.popleft()
            if n == hasta:
                break
            for m in self.conectados(n):
                if m in previo or (m in evitar and m != hasta):
                    continue
                previo[m] = n
                cola.append(m)
        if hasta not in previo:
            return None
        res, n = [], hasta
        while n is not None:
            res.append(n)
            n = previo[n]
        return res[::-1]


def _lados(contorno: list) -> list[tuple[str, float, float, float, tuple[float, float]]]:
    """Lados ortogonales: (orientación, coordenada fija, desde, hasta, normal hacia afuera)."""
    pts = [tuple(p) for p in contorno]
    horario = poligono.area_con_signo(pts) < 0
    res = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        l = math.hypot(dx, dy)
        if l < 1e-6:
            continue
        # Normal exterior: a la derecha en sentido antihorario.
        nx, ny = (dy / l, -dx / l)
        if horario:
            nx, ny = -nx, -ny
        if abs(dy) < 1e-6:
            res.append(("h", y0, min(x0, x1), max(x0, x1), (nx, ny)))
        elif abs(dx) < 1e-6:
            res.append(("v", x0, min(y0, y1), max(y0, y1), (nx, ny)))
    return res


def _muros_en(muros: list[dict], ori: str, fijo: float, a: float, b: float) -> list[tuple[dict, float, float]]:
    """Muros sobre la línea, con el tramo (en coordenada a lo largo) que se solapa con [a, b]."""
    res = []
    for m in muros:
        (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
        if ori == "h" and abs(y0 - y1) < 1e-6 and abs(y0 - fijo) <= TOL_LINEA_M:
            lo, hi = sorted((x0, x1))
        elif ori == "v" and abs(x0 - x1) < 1e-6 and abs(x0 - fijo) <= TOL_LINEA_M:
            lo, hi = sorted((y0, y1))
        else:
            continue
        s0, s1 = max(lo, a), min(hi, b)
        if s1 - s0 > 1e-6:
            res.append((m, s0, s1))
    return res


def _hay_paso(m: dict, s0: float, s1: float) -> dict | None:
    """Abertura de paso dentro del tramo [s0, s1] (coordenadas absolutas a lo largo del eje)."""
    (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
    horizontal = abs(y0 - y1) < 1e-6
    inicio = x0 if horizontal else y0
    sentido = 1 if (x1 >= x0 if horizontal else y1 >= y0) else -1
    for o in m.get("aberturas") or []:
        if o.get("tipo") not in PASO:
            continue
        a = inicio + sentido * o["posicion_m"]
        b = inicio + sentido * (o["posicion_m"] + o["ancho_m"])
        a, b = sorted((a, b))
        if min(b, s1) - max(a, s0) > 0.3:
            return o
    return None


def construir(casa: dict) -> Grafo:
    muros = casa.get("muros") or []
    ambientes = {a["id"]: a for a in casa.get("ambientes") or [] if a.get("contorno_m") and len(a["contorno_m"]) >= 3}
    lados = {aid: _lados(a["contorno_m"]) for aid, a in ambientes.items()}
    areas = {aid: poligono.area([tuple(p) for p in a["contorno_m"]]) for aid, a in ambientes.items()}
    vecinos: dict[tuple[str, str], Vecindad] = {}
    ids = sorted(ambientes)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            for ori, fa, a0, a1, na in lados[a]:
                for orib, fb, b0, b1, nb in lados[b]:
                    if ori != orib:
                        continue
                    # Enfrentados: normales opuestas y separación corta hacia afuera de `a`.
                    if na[0] * nb[0] + na[1] * nb[1] > -0.5:
                        continue
                    sep = (fb - fa) * (na[1] if ori == "h" else na[0])
                    if not (-0.02 <= sep <= TOL_ENFRENTADOS_M):
                        continue
                    s0, s1 = max(a0, b0), min(a1, b1)
                    if s1 - s0 < SOLAPE_MIN_M:
                        continue
                    medio = (fa + fb) / 2
                    en_linea = _muros_en(muros, ori, medio, s0, s1)
                    cubierto = sum(t1 - t0 for _, t0, t1 in en_linea)
                    if cubierto < 0.5 * (s1 - s0):
                        tipo = "abierto"
                    else:
                        tipo = "puerta" if any(_hay_paso(m, t0, t1) for m, t0, t1 in en_linea) else "muro"
                    clave = (a, b)
                    previo = vecinos.get(clave)
                    rango = {"abierto": 2, "puerta": 1, "muro": 0}
                    if previo is None:
                        vecinos[clave] = Vecindad(a, b, tipo, s1 - s0, {m["id"] for m, _, _ in en_linea})
                    else:
                        previo.largo_m += s1 - s0
                        previo.muros |= {m["id"] for m, _, _ in en_linea}
                        if rango[tipo] > rango[previo.tipo]:
                            previo.tipo = tipo

    # Muros exteriores: cada ambiente con los tramos de fachada que le tocan.
    exterior: dict[str, list[dict]] = {}
    accesos: list[str] = []
    for aid in ids:
        for ori, fa, a0, a1, na in lados[aid]:
            for m, t0, t1 in _muros_en([m for m in muros if m.get("sistema") == "exterior"], ori,
                                       fa + (na[1] if ori == "h" else na[0]) * 0.1, a0, a1):
                lado = m.get("lado_exterior") or _lado_por_normal(na)
                o = _hay_paso(m, t0, t1)
                exterior.setdefault(aid, []).append({"muro": m["id"], "lado": lado, "largo_m": t1 - t0, "tramo": (t0, t1)})
                if o and o.get("tipo") == "puerta" and aid not in accesos:
                    accesos.append(aid)
    # Un muro «exterior» que separa dos ambientes (la casa y el garage) no es fachada.
    compartidos = {(v.a, mid) for v in vecinos.values() for mid in v.muros} | {(v.b, mid) for v in vecinos.values() for mid in v.muros}
    exterior = {aid: [t for t in ts if (aid, t["muro"]) not in compartidos] for aid, ts in exterior.items()}
    return Grafo(ambientes, vecinos, exterior, accesos, areas, {m["id"]: m for m in muros})


def _lado_por_normal(n: tuple[float, float]) -> str:
    if abs(n[1]) >= abs(n[0]):
        return "norte" if n[1] > 0 else "sur"
    return "este" if n[0] > 0 else "oeste"
