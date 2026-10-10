"""Interior de la casa: muebles, artefactos y galería.

Es la segunda mitad de la capa Casa. Con la planta resuelta, la vista 3D muestra la
casa levantada y amoblada para decidir antes de pasar a la estructura. Este módulo
pone las piezas con reglas, sin IA:

- `amoblar()` propone un amoblado completo por uso de ambiente (dormitorio: cama
  contra el muro sin ventana, mesas de luz a los costados y placard en otro muro; baño:
  ducha en la esquina lejos de la puerta, inodoro, bidet y vanitory; etc.).
- `colocar()` busca lugar para una pieza suelta en un ambiente.
- `agregar_galeria()` arma la galería sobre un muro exterior.

Convención de las piezas (la misma del catálogo `mobiliario`): `centro_m` es el centro
de la huella, `medidas_m` = [ancho, fondo, alto] en el sistema de la pieza y `giro_deg`
es antihorario, con la espalda al sur (−Y) y el frente al norte (+Y) en 0°. Las piezas
con agua o desagüe van en `casa.artefactos`; el resto en `casa.mobiliario`.

Todo trabaja con rectángulos alineados a los ejes: la planta es ortogonal (R03.01) y los
giros que propone el amoblado son múltiplos de 90°.
"""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

from ..geometria import poligono
from ..modelo.casa import USOS_EXTERIORES
from ..modelo.estados import Estado
from .casa import catalogo, slug

Rect = tuple[float, float, float, float]  # x0, y0, x1, y1

LISTAS = ("mobiliario", "artefactos")
PASO_M = 0.05
TOL = 0.02

# Piezas que pueden quedar encima o debajo de otra sin que sea un choque.
SOBRE_OTRAS = {"alfombra"}
ACOMPANAN_MESA = {"silla", "banqueta", "silla_escritorio", "silla_exterior"}
MESAS = {"mesa", "mesa_redonda", "isla", "escritorio", "mesa_baja"}
# Piezas que pueden estar dentro del espacio de uso de otra: la mesa ratona delante del sofá, las sillas.
EN_ZONA_DE_USO = SOBRE_OTRAS | ACOMPANAN_MESA | {"mesa_baja"}


# ---------------------------------------------------------------- catálogo

@lru_cache(maxsize=1)
def _catalogo_muebles() -> dict[str, dict]:
    return {i["codigo"]: i for i in catalogo()["familias"]["mobiliario"]["items"]}


def items_catalogo() -> list[dict]:
    return list(_catalogo_muebles().values())


def item(codigo: str) -> dict | None:
    return _catalogo_muebles().get(codigo)


def lista_de(codigo: str) -> str:
    it = item(codigo)
    return "artefactos" if it and it.get("familia") == "artefacto" else "mobiliario"


def piezas(casa: dict) -> list[dict]:
    return [p for nombre in LISTAS for p in (casa.get(nombre) or [])]


def forma(p: dict) -> str:
    it = item(p.get("tipo", ""))
    return it["forma"] if it else p.get("tipo", "caja")


def medidas(p: dict) -> tuple[float, float, float]:
    it = item(p.get("tipo", "")) or {}
    m = list(p.get("medidas_m") or it.get("medidas_m") or [0.6, 0.6, 0.9])
    if len(m) == 2:
        m.append((it.get("medidas_m") or [0, 0, 0.9])[2])
    return float(m[0]), float(m[1]), float(m[2])


def _giro90(g: float) -> int:
    return int(round((g or 0) / 90.0)) % 4 * 90


def huella(p: dict) -> Rect:
    """Rectángulo que ocupa la pieza en planta."""
    a, f, _ = medidas(p)
    g = math.radians(p.get("giro_deg") or 0)
    c, s = abs(math.cos(g)), abs(math.sin(g))
    w, d = a * c + f * s, a * s + f * c
    x, y = p["centro_m"]
    return (x - w / 2, y - d / 2, x + w / 2, y + d / 2)


def _frente(rect: Rect, giro: int, fondo: float) -> Rect | None:
    if fondo <= 0:
        return None
    x0, y0, x1, y1 = rect
    return {0: (x0, y1, x1, y1 + fondo), 180: (x0, y0 - fondo, x1, y0),
            90: (x0 - fondo, y0, x0, y1), 270: (x1, y0, x1 + fondo, y1)}[giro]


def zona_frente(p: dict) -> Rect | None:
    """Espacio de uso delante de la pieza (`frente_libre_m` del catálogo)."""
    it = item(p.get("tipo", ""))
    if not it:
        return None
    return _frente(huella(p), _giro90(p.get("giro_deg") or 0), it.get("frente_libre_m", 0))


# ---------------------------------------------------------------- rectángulos

def area(r: Rect) -> float:
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def cruce(a: Rect, b: Rect) -> float:
    return area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def _achicar(r: Rect, d: float) -> Rect:
    return (r[0] + d, r[1] + d, r[2] - d, r[3] - d)


def dentro(r: Rect, poly: list) -> bool:
    x0, y0, x1, y1 = _achicar(r, TOL)
    if x1 <= x0 or y1 <= y0:
        return True
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0 + x1) / 2, (y0 + y1) / 2)]
    if not all(poligono.contiene(poly, x, y) for x, y in pts):
        return False
    # Un vértice del ambiente adentro del rectángulo indica que lo atraviesa una esquina (planta en L).
    return not any(x0 < vx < x1 and y0 < vy < y1 for vx, vy in poly)


# ---------------------------------------------------------------- ambientes

@dataclass
class Lado:
    """Una arista del contorno del ambiente. `orient` dice de qué lado queda el muro respecto del
    ambiente (sur: el muro está abajo y el ambiente arriba). `a`–`b` es el tramo sobre el eje que corre."""
    clave: str
    orient: str
    fijo: float
    a: float
    b: float
    muro: bool           # hay un muro a lo largo (en una galería, solo del lado de la casa)
    ventanas: list[tuple[float, float, float]] = field(default_factory=list)  # desde, hasta, antepecho
    puertas: list[tuple[float, float]] = field(default_factory=list)
    tramos: list[tuple[float, float]] = field(default_factory=list)  # partes del lado con muro

    @property
    def horizontal(self) -> bool:
        return self.orient in ("sur", "norte")

    @property
    def largo(self) -> float:
        return self.b - self.a


@dataclass
class Sala:
    id: str
    nombre: str
    uso: str
    poly: list
    caja: Rect
    lados: dict[str, Lado]
    zonas_puerta: list[Rect]
    zonas_ventana: list[tuple[Rect, float]]

    @property
    def area(self) -> float:
        return poligono.area(self.poly)

    @property
    def lado_min(self) -> float:
        x0, y0, x1, y1 = self.caja
        return min(x1 - x0, y1 - y0)

    @property
    def exterior(self) -> bool:
        return self.uso in USOS_EXTERIORES


def _espesor(casa: dict, sistema: str) -> float:
    s = (casa.get("sistemas") or {}).get(sistema) or {}
    return s.get("espesor_arquitectonico_m") or {"exterior": 0.2, "interior_portante": 0.2}.get(sistema, 0.15)


def _segmento(muro: dict) -> tuple[bool, float, float, float]:
    """(horizontal, coordenada fija, desde, hasta) del eje."""
    (x0, y0), (x1, y1) = muro["eje"]["desde_m"], muro["eje"]["hasta_m"]
    if abs(y0 - y1) < 1e-6:
        return True, y0, min(x0, x1), max(x0, x1)
    return False, x0, min(y0, y1), max(y0, y1)


def _abertura_en_eje(muro: dict, o: dict) -> tuple[float, float]:
    (x0, y0), (x1, y1) = muro["eje"]["desde_m"], muro["eje"]["hasta_m"]
    horizontal = abs(y0 - y1) < 1e-6
    a, b = (x0, x1) if horizontal else (y0, y1)
    sentido = 1 if b >= a else -1
    p, q = a + sentido * o["posicion_m"], a + sentido * (o["posicion_m"] + o["ancho_m"])
    return min(p, q), max(p, q)


def _aristas(poly: list) -> list[tuple[str, float, float, float]]:
    """Aristas ortogonales del contorno como (orientación del muro, coordenada fija, desde, hasta)."""
    pts = list(poly)
    if poligono.area_con_signo(pts) < 0:
        pts.reverse()
    out = []
    for (px, py), (qx, qy) in zip(pts, pts[1:] + pts[:1]):
        if abs(py - qy) < 1e-6 and abs(px - qx) > 1e-6:
            out.append(("sur" if qx > px else "norte", py, min(px, qx), max(px, qx)))
        elif abs(px - qx) < 1e-6 and abs(py - qy) > 1e-6:
            out.append(("este" if qy > py else "oeste", px, min(py, qy), max(py, qy)))
    return out


def sala(casa: dict, amb: dict) -> Sala | None:
    cont = amb.get("contorno_m")
    if not cont or len(cont) < 3:
        return None
    poly = [tuple(v) for v in cont]
    exterior = amb.get("uso") in USOS_EXTERIORES
    lados: dict[str, Lado] = {}
    for orient, fijo, a, b in _aristas(poly):
        clave, n = orient, 1
        while clave in lados:
            n += 1
            clave = f"{orient}_{n}"
        lados[clave] = Lado(clave, orient, fijo, a, b, muro=not exterior)
    zonas_p: list[Rect] = []
    zonas_v: list[tuple[Rect, float]] = []
    for m in casa.get("muros") or []:
        horiz, c, lo, hi = _segmento(m)
        tol = _espesor(casa, m.get("sistema", "tabique")) / 2 + 0.08
        for lado in lados.values():
            if lado.horizontal != horiz or abs(c - lado.fijo) > tol or min(hi, lado.b) - max(lo, lado.a) < 0.2:
                continue
            lado.muro = True
            lado.tramos.append((max(lo, lado.a), min(hi, lado.b)))
            for o in m.get("aberturas") or []:
                d, h_ = _abertura_en_eje(m, o)
                if min(h_, lado.b) - max(d, lado.a) <= 0:
                    continue
                fondo = {"puerta": o["ancho_m"], "ventana_corrediza": 0.45}.get(o.get("tipo"), 0.6)
                if o.get("tipo") in ("puerta", "paso", "ventana_corrediza"):
                    lado.puertas.append((d, h_))
                    zonas_p.append(_zona_lado(lado, d, h_, fondo + 0.05))
                else:
                    lado.ventanas.append((d, h_, o.get("antepecho_m", 1.0)))
                    zonas_v.append((_zona_lado(lado, d, h_, 0.15), o.get("antepecho_m", 1.0)))
    if not exterior:
        # Un lado sin muro en parte de su largo es un paso abierto a otro ambiente: se deja libre.
        for lado in lados.values():
            for d, h_ in _huecos(lado.tramos, lado.a, lado.b):
                lado.puertas.append((d, h_))
                zonas_p.append(_zona_lado(lado, d, h_, 0.9))
    return Sala(amb["id"], amb.get("nombre", amb["id"]), amb.get("uso", "otro"), poly, poligono.caja(poly), lados,
                zonas_p, zonas_v)


def _huecos(tramos: list[tuple[float, float]], a: float, b: float, minimo: float = 0.45) -> list[tuple[float, float]]:
    huecos, pos = [], a
    for lo, hi in sorted(tramos):
        if lo - pos >= minimo:
            huecos.append((pos, lo))
        pos = max(pos, hi)
    if b - pos >= minimo:
        huecos.append((pos, b))
    return huecos


def _cubierto(s: "Sala", clave: str, r: Rect) -> bool:
    """El tramo del lado que ocupa la pieza tiene muro detrás en todo su largo."""
    lado = s.lados[clave]
    lo, hi = (r[0], r[2]) if lado.horizontal else (r[1], r[3])
    return not _huecos(lado.tramos, lo + TOL, hi - TOL, minimo=0.05)


def _zona_lado(lado: Lado, d: float, h: float, fondo: float) -> Rect:
    f = lado.fijo
    return {"sur": (d, f, h, f + fondo), "norte": (d, f - fondo, h, f),
            "oeste": (f, d, f + fondo, h), "este": (f - fondo, d, f, h)}[lado.orient]


GIRO_LADO = {"sur": 0, "norte": 180, "oeste": 270, "este": 90}


def _giro(s: Sala, clave: str) -> int:
    return GIRO_LADO[s.lados[clave].orient]


def _claves(s: Sala, filtro: list[str] | None = None) -> list[str]:
    """Lados del ambiente; el filtro acepta claves («sur_2») u orientaciones («sur»)."""
    return [k for k, l in s.lados.items() if filtro is None or k in filtro or l.orient in filtro]


def _rect_lado(s: Sala, clave: str, a: float, f: float, t: float) -> Rect:
    lado = s.lados[clave]
    base, fijo = lado.a + t, lado.fijo
    return {"sur": (base, fijo, base + a, fijo + f), "norte": (base, fijo - f, base + a, fijo),
            "oeste": (fijo, base, fijo + f, base + a), "este": (fijo - f, base, fijo, base + a)}[lado.orient]


def _largo_lado(s: Sala, clave: str) -> float:
    return s.lados[clave].largo


def _fondo(s: Sala, orient: str) -> float:
    """Profundidad del ambiente medida desde un muro con esa orientación."""
    x0, y0, x1, y1 = s.caja
    return (y1 - y0) if orient in ("sur", "norte") else (x1 - x0)


# ---------------------------------------------------------------- contexto de colocación

@dataclass
class Contexto:
    casa: dict
    ocupado: list[tuple[str, Rect, str]] = field(default_factory=list)   # id, huella, forma
    zonas: list[tuple[str, Rect]] = field(default_factory=list)           # frentes de uso
    ids: set[str] = field(default_factory=set)
    notas: list[str] = field(default_factory=list)

    @classmethod
    def desde(cls, casa: dict) -> "Contexto":
        ctx = cls(casa)
        for p in piezas(casa):
            ctx.registrar(p)
        return ctx

    def registrar(self, p: dict) -> None:
        self.ids.add(p["id"])
        it = item(p.get("tipo", "")) or {}
        if it.get("elevacion_m"):
            return
        self.ocupado.append((p["id"], huella(p), forma(p)))
        z = zona_frente(p)
        if z:
            self.zonas.append((p["id"], z))

    def nuevo_id(self, codigo: str) -> str:
        base = slug((item(codigo) or {}).get("nombre", codigo))
        i, nid = 1, base
        while nid in self.ids:
            i += 1
            nid = f"{base}_{i}"
        self.ids.add(nid)
        return nid


# Alto que cuenta frente a una ventana: el respaldo de la cama no tapa la ventana como un placard.
ALTO_ANTE_VENTANA = {"cama": 0.6, "cuna": 0.6, "ducha": 0.1, "banera": 0.6}


def _libre(ctx: Contexto, s: Sala, r: Rect, frente: Rect | None, alto: float, forma_: str,
           extra: list[Rect] = (), ignorar: set[str] = frozenset(), elevado: bool = False) -> bool:
    if not dentro(r, s.poly):
        return False
    sobre = forma_ in SOBRE_OTRAS
    acompana = forma_ in ACOMPANAN_MESA
    if not elevado and not sobre:
        for pid, o, fo in ctx.ocupado:
            if pid in ignorar or fo in SOBRE_OTRAS or (acompana and fo in MESAS):
                continue
            if cruce(r, o) > 1e-4:
                return False
        if forma_ not in EN_ZONA_DE_USO:
            for pid, z in ctx.zonas:
                if pid not in ignorar and cruce(r, z) > 1e-4:
                    return False
        for z in s.zonas_puerta:
            if cruce(r, z) > 1e-4:
                return False
    alto = ALTO_ANTE_VENTANA.get(forma_, alto)
    for z, antepecho in s.zonas_ventana:
        if (elevado or alto > antepecho - 0.02) and cruce(r, z) > 1e-4:
            return False
    for zona in [z for z in [frente, *extra] if z]:
        if not dentro(zona, s.poly):
            return False
        for pid, o, fo in ctx.ocupado:
            if pid not in ignorar and fo not in EN_ZONA_DE_USO and cruce(zona, o) > 1e-4:
                return False
        for z in s.zonas_puerta:
            if cruce(zona, z) > 0.05:
                return False
    return True


def _pieza(ctx: Contexto, s: Sala, codigo: str, r: Rect, giro: int, origen: str) -> dict:
    a, f, h = item(codigo)["medidas_m"]
    p = {"id": ctx.nuevo_id(codigo), "tipo": codigo, "ambiente": s.id,
         "centro_m": [round((r[0] + r[2]) / 2, 3), round((r[1] + r[3]) / 2, 3)],
         "medidas_m": [a, f, h], "giro_deg": giro, "origen": origen, "estado": Estado.PROPUESTO.value}
    ctx.casa.setdefault(lista_de(codigo), []).append(p)
    ctx.registrar(p)
    return p


Puntaje = Callable[[Rect, str, float], float]


def en_muro(ctx: Contexto, s: Sala, codigo: str, puntaje: Puntaje | None = None, lados: list[str] | None = None,
            lateral: float = 0.0, origen: str = "automatico", ignorar: set[str] = frozenset()) -> dict | None:
    """La pieza con la espalda contra un muro del ambiente. `puntaje(rect, lado, t)`: menor es mejor."""
    it = item(codigo)
    a, f, h = it["medidas_m"]
    elevado = bool(it.get("elevacion_m"))
    mejor: tuple[float, Rect, str] | None = None
    for lado in _claves(s, lados):
        if not s.lados[lado].muro:
            continue
        largo = _largo_lado(s, lado)
        n = int((largo - a) / PASO_M + 1e-6)
        for k in range(n + 1):
            t = k * PASO_M
            r = _rect_lado(s, lado, a, f, t)
            if not _cubierto(s, lado, r):
                continue
            g = _giro(s, lado)
            fr = _frente(r, g, it.get("frente_libre_m", 0))
            extra = _laterales(r, g, lateral) if lateral else []
            if not _libre(ctx, s, r, fr, h, it["forma"], extra, ignorar, elevado):
                continue
            centro = abs((t + a / 2) - largo / 2)
            v = puntaje(r, lado, t) if puntaje else centro
            if mejor is None or v < mejor[0] - 1e-9:
                mejor = (v, r, lado)
    if not mejor:
        return None
    return _pieza(ctx, s, codigo, mejor[1], _giro(s, mejor[2]), origen)


def _laterales(r: Rect, giro: int, d: float) -> list[Rect]:
    x0, y0, x1, y1 = r
    if giro in (0, 180):
        return [(x0 - d, y0, x0, y1), (x1, y0, x1 + d, y1)]
    return [(x0, y0 - d, x1, y0), (x0, y1, x1, y1 + d)]


def en_esquina(ctx: Contexto, s: Sala, codigo: str, puntaje: Callable[[Rect], float] | None = None,
               origen: str = "automatico") -> dict | None:
    it = item(codigo)
    a, f, h = it["medidas_m"]
    opciones: list[tuple[Rect, int]] = []
    for lado in _claves(s):
        g = _giro(s, lado)
        if not s.lados[lado].muro:
            continue
        largo = _largo_lado(s, lado)
        for t in (0.0, largo - a):
            r = _rect_lado(s, lado, a, f, t)
            if _cubierto(s, lado, r):
                opciones.append((r, g))
    mejor = None
    for r, g in opciones:
        if not _libre(ctx, s, r, _frente(r, g, it.get("frente_libre_m", 0)), h, it["forma"]):
            continue
        v = puntaje(r) if puntaje else 0.0
        if mejor is None or v < mejor[0]:
            mejor = (v, r, g)
    return _pieza(ctx, s, codigo, mejor[1], mejor[2], origen) if mejor else None


def libre(ctx: Contexto, s: Sala, codigo: str, objetivo: tuple[float, float] | None = None,
          giros: tuple[int, ...] = (0, 90), holgura: float | None = None, origen: str = "automatico",
          puntaje: Callable[[Rect], float] | None = None) -> dict | None:
    """Pieza exenta (mesa, isla, sillón): busca en una grilla el lugar libre más cercano al objetivo.
    `holgura` reserva espacio libre alrededor (para correr sillas, circular)."""
    it = item(codigo)
    a, f, h = it["medidas_m"]
    x0, y0, x1, y1 = s.caja
    ox, oy = objetivo or ((x0 + x1) / 2, (y0 + y1) / 2)
    hol = it.get("frente_libre_m", 0) if holgura is None else holgura
    mejor = None
    paso = 0.1
    for g in giros:
        w, d = (a, f) if g in (0, 180) else (f, a)
        nx, ny = int((x1 - x0 - w) / paso + 1e-6), int((y1 - y0 - d) / paso + 1e-6)
        for i in range(nx + 1):
            for j in range(ny + 1):
                r = (x0 + i * paso, y0 + j * paso, x0 + i * paso + w, y0 + j * paso + d)
                alrededor = [(r[0] - hol, r[1] - hol, r[2] + hol, r[3] + hol)] if hol else []
                if alrededor and not dentro(alrededor[0], s.poly):
                    continue
                if not _libre(ctx, s, r, None, h, it["forma"], alrededor):
                    continue
                cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
                v = puntaje(r) if puntaje else math.hypot(cx - ox, cy - oy)
                if mejor is None or v < mejor[0]:
                    mejor = (v, r, g)
    return _pieza(ctx, s, codigo, mejor[1], mejor[2], origen) if mejor else None


# ---------------------------------------------------------------- puntajes

def _con_ventana(s: Sala, lado: str) -> bool:
    return bool(s.lados[lado].ventanas)


def _dist_puertas(s: Sala, r: Rect) -> float:
    if not s.zonas_puerta:
        return 5.0
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    return min(math.hypot(cx - (z[0] + z[2]) / 2, cy - (z[1] + z[3]) / 2) for z in s.zonas_puerta)


def _dist_esquina(s: Sala, r: Rect) -> float:
    x0, y0, x1, y1 = s.caja
    return min(math.hypot(px - qx, py - qy) for px, py in ((r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3]))
               for qx, qy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)))


def _centro(r: Rect) -> tuple[float, float]:
    return (r[0] + r[2]) / 2, (r[1] + r[3]) / 2


def _opuesto(lado: str) -> str:
    return {"sur": "norte", "norte": "sur", "este": "oeste", "oeste": "este"}[lado]


def _lado_de(p: dict) -> str:
    return {v: k for k, v in GIRO_LADO.items()}[_giro90(p["giro_deg"])]


# ---------------------------------------------------------------- amoblado por uso

def _dormitorio(ctx: Contexto, s: Sala) -> None:
    """Prueba la cama contra cada muro (del mejor al peor) hasta que entre también el placard."""
    inicio = _foto(ctx)
    primera = None
    preferidos = sorted(_claves(s), key=lambda k: (4.0 if _con_ventana(s, k) else 0.0) - 0.2 * _largo_lado(s, k))
    for lado in preferidos:
        _volver(ctx, inicio)
        if _dormitorio_en(ctx, s, [lado]) == 2:
            return
        if primera is None or _dormitorio_puntos(ctx, s) > primera[1]:
            primera = (_foto(ctx), _dormitorio_puntos(ctx, s))
    _volver(ctx, inicio)
    if _dormitorio_en(ctx, s, None) < (primera[1] if primera else 0) and primera:
        _volver(ctx, primera[0])


def _dormitorio_puntos(ctx: Contexto, s: Sala) -> int:
    tipos = [p["tipo"] for p in piezas(ctx.casa) if p.get("ambiente") == s.id]
    return int(any(t.startswith("cama") for t in tipos)) + int(any(t.startswith("placard") for t in tipos))


def _dormitorio_en(ctx: Contexto, s: Sala, lados: list[str] | None) -> int:
    """Amobla con la cama en esos lados. Devuelve 2 si entraron cama y placard."""
    if s.area >= 13 and s.lado_min >= 3.2:
        camas = ["cama_queen", "cama_2", "cama_1"]
    elif s.area >= 9 and s.lado_min >= 2.6:
        camas = ["cama_2", "cama_1"]
    else:
        camas = ["cama_1"]
    cama = None
    for codigo in camas:
        a = item(codigo)["medidas_m"][0]
        lado_lib = 0.45 if a > 1.0 else 0.0

        def p_cama(r: Rect, lado: str, t: float, a=a) -> float:
            largo = _largo_lado(s, lado)
            return (4.0 if _con_ventana(s, lado) else 0.0) + abs(t + a / 2 - largo / 2) - 0.2 * largo

        cama = en_muro(ctx, s, codigo, p_cama, lados=lados, lateral=lado_lib)
        if cama:
            break
    if not cama:
        # Dormitorio angosto: una cama de 1 plaza contra el muro, sin paso de un lado.
        cama = en_muro(ctx, s, "cama_1", lambda r, l, t: _dist_esquina(s, r), lados=lados)
    if not cama:
        ctx.notas.append(f"«{s.nombre}»: no entra una cama con su espacio de uso.")
        return 0
    lado = _lado_de(cama)
    hr = huella(cama)
    for borde in (0, 1):
        def p_luz(r: Rect, _l: str, _t: float, borde=borde) -> float:
            if lado in ("sur", "norte"):
                return abs(r[2] - hr[0]) if borde == 0 else abs(r[0] - hr[2])
            return abs(r[3] - hr[1]) if borde == 0 else abs(r[1] - hr[3])

        luz = en_muro(ctx, s, "mesa_luz", p_luz, lados=[lado])
        if luz and p_luz(huella(luz), lado, 0) > 0.06:
            _quitar(ctx, luz["id"])
    for codigo in ("placard_180", "placard_120"):
        otros = [l for l in GIRO_LADO if l != lado]
        if en_muro(ctx, s, codigo, lambda r, l, t: _dist_esquina(s, r) + (0.5 if _con_ventana(s, l) else 0), lados=otros):
            return 2
    ctx.notas.append(f"«{s.nombre}»: no quedó lugar para un placard.")
    return 1


def _bano(ctx: Contexto, s: Sala) -> None:
    """Ducha en la esquina lejos de la puerta, inodoro, vanitory y, si queda lugar, bidet."""
    ducha = en_esquina(ctx, s, "ducha_90", lambda r: -_dist_puertas(s, r))
    if not ducha and s.area >= 4.5:
        ducha = en_esquina(ctx, s, "banera", lambda r: -_dist_puertas(s, r))
    if not ducha:
        ctx.notas.append(f"«{s.nombre}»: no entra una ducha de 90 × 90.")
    inodoro = en_muro(ctx, s, "inodoro", lambda r, l, t: -_dist_puertas(s, r) * 0.3 + (
        math.dist(_centro(r), _centro(huella(ducha))) * 0.5 if ducha else 0))
    if not inodoro:
        ctx.notas.append(f"«{s.nombre}»: no entra el inodoro con sus 70 cm delante.")
    if not en_muro(ctx, s, "vanitory_60", lambda r, l, t: _dist_puertas(s, r) * 0.4):
        ctx.notas.append(f"«{s.nombre}»: no entra el vanitory.")
    if inodoro and s.area >= 3.6:
        hi = huella(inodoro)
        bidet = en_muro(ctx, s, "bidet", lambda r, l, t: math.dist(_centro(r), _centro(hi)), lados=[_lado_de(inodoro)])
        if bidet and math.dist(_centro(huella(bidet)), _centro(hi)) > 1.2:
            _quitar(ctx, bidet["id"])


def _corrida_cocina(ctx: Contexto, s: Sala) -> bool:
    """Mesada corrida contra un muro: heladera, bajo mesadas, anafe y bacha, con alacenas encima."""
    nucleo = ["heladera", "bajo_mesada_60", "cocina_anafe", "bajo_mesada_60", "mesada_bacha"]
    for extra in (3, 2, 1, 0):
        orden = nucleo + ["bajo_mesada_60"] * extra
        for sin_heladera in (False, True):
            modulos = [m for m in orden if not (sin_heladera and m == "heladera")]
            largo = sum(item(m)["medidas_m"][0] for m in modulos)
            sitio = _lugar_corrida(ctx, s, largo)
            if not sitio:
                continue
            lado, t = sitio
            invertir = False
            if "heladera" in modulos and _choca_ventana(s, lado, t, item("heladera")["medidas_m"][0]):
                invertir = True
                modulos = modulos[::-1]
            pos = t
            puestos = []
            for m in modulos:
                a, f, h = item(m)["medidas_m"]
                r = _rect_lado(s, lado, a, f, pos)
                puestos.append(_pieza(ctx, s, m, r, _giro(s, lado), "automatico"))
                pos += a
            if "heladera" in modulos and invertir and _choca_ventana(s, lado, pos - item("heladera")["medidas_m"][0],
                                                                      item("heladera")["medidas_m"][0]):
                _quitar(ctx, puestos[-1]["id"])
                sin_heladera = True
            if sin_heladera:
                if not en_muro(ctx, s, "heladera", lambda r, l, tt: 0 if l == lado else 1):
                    ctx.notas.append(f"«{s.nombre}»: no entró la heladera.")
            # Alacenas sobre la mesada, donde no hay ventana.
            lo, hi = t, t + largo
            k = lo
            while k + 1.2 <= hi + 1e-6:
                r = _rect_lado(s, lado, 1.2, 0.35, k)
                if _cubierto(s, lado, r) and _libre(ctx, s, r, None, 2.2, "alacena", elevado=True):
                    _pieza(ctx, s, "alacena_120", r, _giro(s, lado), "automatico")
                    k += 1.2
                else:
                    k += 0.6
            return True
    ctx.notas.append(f"«{s.nombre}»: no hay un muro libre de al menos 1,8 m para la mesada.")
    return False


def _choca_ventana(s: Sala, lado: str, t: float, a: float) -> bool:
    base = s.lados[lado].a
    return any(min(h, base + t + a) - max(d, base + t) > 0 and ant < 1.85 for d, h, ant in s.lados[lado].ventanas)


def _lugar_corrida(ctx: Contexto, s: Sala, largo: float) -> tuple[str, float] | None:
    mejor = None
    for lado in _claves(s):
        if not s.lados[lado].muro:
            continue
        total = _largo_lado(s, lado)
        n = int((total - largo) / PASO_M + 1e-6)
        for k in range(n + 1):
            t = k * PASO_M
            r = _rect_lado(s, lado, largo, 0.6, t)
            if not _cubierto(s, lado, r):
                continue
            fr = _frente(r, _giro(s, lado), 1.0)
            if not _libre(ctx, s, r, fr, 0.9, "bajo_mesada"):
                continue
            v = min(t, total - largo - t)  # contra una esquina
            if mejor is None or v < mejor[0]:
                mejor = (v, lado, t)
    return (mejor[1], mejor[2]) if mejor else None


def _sillas(ctx: Contexto, s: Sala, mesa: dict, codigo: str = "silla") -> None:
    """Sillas alrededor de la mesa, mirando hacia ella."""
    n = (item(mesa["tipo"]) or {}).get("sillas", 4)
    x0, y0, x1, y1 = huella(mesa)
    w, d = x1 - x0, y1 - y0
    largo_x = w >= d
    por_lado = n // 2 if n <= 4 else (n - 2) // 2
    cabeceras = n > 4 or (n == 4 and abs(w - d) < 0.05)  # mesa cuadrada o redonda: una por lado
    if cabeceras and n == 4:
        por_lado = 1
    a, f, h = item(codigo)["medidas_m"]
    posiciones: list[tuple[float, float, int]] = []
    sale = 0.12  # la silla queda medio metida bajo la mesa
    if largo_x:
        for i in range(por_lado):
            cx = x0 + w * (i + 0.5) / por_lado
            posiciones += [(cx, y0 - f / 2 + sale, 0), (cx, y1 + f / 2 - sale, 180)]
        if cabeceras:
            cy = (y0 + y1) / 2
            posiciones += [(x0 - f / 2 + sale, cy, 270), (x1 + f / 2 - sale, cy, 90)]
    else:
        for i in range(por_lado):
            cy = y0 + d * (i + 0.5) / por_lado
            posiciones += [(x0 - f / 2 + sale, cy, 270), (x1 + f / 2 - sale, cy, 90)]
        if cabeceras:
            cx = (x0 + x1) / 2
            posiciones += [(cx, y0 - f / 2 + sale, 0), (cx, y1 + f / 2 - sale, 180)]
    for cx, cy, g in posiciones:
        r = (cx - a / 2, cy - f / 2, cx + a / 2, cy + f / 2) if g in (0, 180) else (cx - f / 2, cy - a / 2, cx + f / 2, cy + a / 2)
        if dentro(r, s.poly):
            _pieza(ctx, s, codigo, r, g, "automatico")


def _mesa_comedor(ctx: Contexto, s: Sala, lejos_de: tuple[float, float] | None, exterior: bool = False,
                  rincon: bool = False) -> dict | None:
    opciones = ["mesa_exterior"] if exterior else (["mesa_6", "mesa_4", "mesa_redonda"] if s.area >= 24 else ["mesa_4", "mesa_redonda"])
    for codigo in opciones:
        def p_mesa(r: Rect) -> float:
            if rincon:  # deja el resto del ambiente libre para el living
                return _dist_esquina(s, r)
            c = _centro(r)
            x0, y0, x1, y1 = s.caja
            v = math.dist(c, ((x0 + x1) / 2, (y0 + y1) / 2)) * 0.4
            if lejos_de:
                v -= math.dist(c, lejos_de)
            return v

        mesa = libre(ctx, s, codigo, holgura=0.6 if exterior else 0.75, puntaje=p_mesa)
        if mesa:
            _sillas(ctx, s, mesa, "silla_exterior" if exterior else "silla")
            return mesa
    # Ambiente justo: la mesa más chica con 60 cm para correr las sillas.
    if not exterior:
        for codigo in ("mesa_4", "mesa_redonda"):
            mesa = libre(ctx, s, codigo, holgura=0.6, puntaje=lambda r: _dist_esquina(s, r) if rincon else 0.0)
            if mesa:
                _sillas(ctx, s, mesa, "silla")
                return mesa
    return None


def _foto(ctx: Contexto) -> tuple:
    return ({n: list(ctx.casa.get(n) or []) for n in LISTAS}, list(ctx.ocupado), list(ctx.zonas), set(ctx.ids), list(ctx.notas))


def _volver(ctx: Contexto, foto: tuple) -> None:
    listas, ocupado, zonas, ids, notas = foto
    for n, l in listas.items():
        ctx.casa[n] = list(l)
    ctx.ocupado, ctx.zonas, ctx.ids, ctx.notas = list(ocupado), list(zonas), set(ids), list(notas)


def _claves_estar(ctx: Contexto, s: Sala) -> int:
    tipos = {p["tipo"] for p in piezas(ctx.casa) if p.get("ambiente") == s.id}
    return sum((any(t.startswith("sofa") for t in tipos), "mueble_tv" in tipos,
                any(t.startswith("mesa_") and t != "mesa_ratona" for t in tipos)))


def _estar(ctx: Contexto, s: Sala, con_cocina: bool) -> None:
    """Estar y comedor. Se prueban dos prioridades —primero el living, o primero el comedor arrinconado—
    y queda la que ubica más piezas clave (sofá, tele, mesa)."""
    if con_cocina:
        _corrida_cocina(ctx, s)
    inicio = _foto(ctx)
    _living(ctx, s)
    _mesa_comedor(ctx, s, _centro_living(ctx, s))
    if _claves_estar(ctx, s) == 3:
        en_esquina(ctx, s, "planta", lambda r: -_dist_puertas(s, r))
        return
    primera, puntos = _foto(ctx), _claves_estar(ctx, s)
    _volver(ctx, inicio)
    _mesa_comedor(ctx, s, None, rincon=True)
    _living(ctx, s)
    if _claves_estar(ctx, s) < puntos:
        _volver(ctx, primera)
    en_esquina(ctx, s, "planta", lambda r: -_dist_puertas(s, r))


def _centro_living(ctx: Contexto, s: Sala) -> tuple[float, float] | None:
    sofa = next((p for p in piezas(ctx.casa) if p.get("ambiente") == s.id and p["tipo"].startswith("sofa")), None)
    return _centro(huella(sofa)) if sofa else None


def _living(ctx: Contexto, s: Sala) -> None:
    sofa = None
    for codigo in ("sofa_3", "sofa_2"):
        def p_sofa(r: Rect, lado: str, t: float) -> float:
            opuesto = _fondo(s, s.lados[lado].orient)
            # Mejor con la tele a 2,2–3,5 m y lejos de la cocina.
            return abs(opuesto - 3.0) * 0.6 + abs(t + item(codigo)["medidas_m"][0] / 2 - _largo_lado(s, lado) / 2) * 0.3

        sofa = en_muro(ctx, s, codigo, p_sofa)
        if sofa:
            hs = huella(sofa)
            tv = en_muro(ctx, s, "mueble_tv", lambda r, l, t, hs=hs: _desalineo(r, hs, s.lados[l].orient),
                         lados=[_opuesto(_lado_de(sofa))])
            if tv and math.dist(_centro(hs), _centro(huella(tv))) <= 4.8:
                break
            if tv:
                _quitar(ctx, tv["id"])
            _quitar(ctx, sofa["id"])
            sofa = None
    if not sofa:
        sofa = _sofa_enfrentado(ctx, s)
    centro_estar = None
    if sofa:
        hs = huella(sofa)
        lado = _lado_de(sofa)
        cs = _centro(hs)
        tv = next((p for p in piezas(ctx.casa) if p["tipo"] == "mueble_tv" and p.get("ambiente") == s.id), None)
        if tv:
            ct = _centro(huella(tv))
            centro_estar = ((cs[0] + ct[0]) / 2, (cs[1] + ct[1]) / 2)
        objetivo = centro_estar
        if objetivo is None:
            fr = zona_frente(sofa)
            objetivo = _centro(fr) if fr else cs
        mesa = libre(ctx, s, "mesa_ratona", objetivo, giros=(0,) if lado in ("sur", "norte") else (90,), holgura=0.0)
        if mesa and math.dist(_centro(huella(mesa)), objetivo) > 1.2:
            _quitar(ctx, mesa["id"])
            mesa = None
        if mesa:
            c = _centro(huella(mesa))
            a, f, _ = item("alfombra")["medidas_m"]
            g = GIRO_LADO[lado]
            r = (c[0] - a / 2, c[1] - f / 2, c[0] + a / 2, c[1] + f / 2) if g in (0, 180) else (c[0] - f / 2, c[1] - a / 2, c[0] + f / 2, c[1] + a / 2)
            if dentro(r, s.poly):
                _pieza(ctx, s, "alfombra", r, g, "automatico")


def _desalineo(r: Rect, otra: Rect, lado: str) -> float:
    a, b = _centro(r), _centro(otra)
    return abs(a[0] - b[0]) if lado in ("sur", "norte") else abs(a[1] - b[1])


def _sofa_enfrentado(ctx: Contexto, s: Sala) -> dict | None:
    """Plan B del estar: la tele contra un muro y el sofá exento, enfrentado a 2,6 m.
    Es lo habitual cuando el estar comparte el ambiente con la cocina o el comedor."""
    for lado in sorted(_claves(s), key=lambda l: -_largo_lado(s, l)):
        tv = en_muro(ctx, s, "mueble_tv", lambda r, l, t: abs(t + 0.9 - _largo_lado(s, l) / 2), lados=[lado])
        if not tv:
            continue
        g = _giro90(tv["giro_deg"])
        fx, fy = -math.sin(math.radians(g)), math.cos(math.radians(g))
        x, y = tv["centro_m"]
        for codigo in ("sofa_3", "sofa_2"):
            f = item(codigo)["medidas_m"][1]
            objetivo = (x + fx * (2.6 + f / 2), y + fy * (2.6 + f / 2))
            sofa = libre(ctx, s, codigo, objetivo, giros=((g + 180) % 360,), holgura=0.0)
            if sofa and math.dist(_centro(huella(sofa)), objetivo) < 1.2:
                return sofa
            if sofa:
                _quitar(ctx, sofa["id"])
        _quitar(ctx, tv["id"])
    return None


def _cocina(ctx: Contexto, s: Sala) -> None:
    _corrida_cocina(ctx, s)
    if s.area >= 10 and s.lado_min >= 2.6:
        _mesa_comedor(ctx, s, None)


def _oficina(ctx: Contexto, s: Sala) -> None:
    esc = en_muro(ctx, s, "escritorio", lambda r, l, t: (0 if _con_ventana(s, l) else 1.5) + abs(
        t + 0.7 - _largo_lado(s, l) / 2) * 0.3)
    if esc:
        g = _giro90(esc["giro_deg"])
        x, y = esc["centro_m"]
        fx, fy = -math.sin(math.radians(g)), math.cos(math.radians(g))
        f = item("escritorio")["medidas_m"][1]
        c = (x + fx * (f / 2 + 0.1), y + fy * (f / 2 + 0.1))
        a = item("silla_escritorio")["medidas_m"][0]
        r = (c[0] - a / 2, c[1] - a / 2, c[0] + a / 2, c[1] + a / 2)
        if dentro(r, s.poly):
            _pieza(ctx, s, "silla_escritorio", r, (g + 180) % 360, "automatico")
        en_muro(ctx, s, "estanteria", lambda r, l, t: _dist_esquina(s, r), lados=[l for l in GIRO_LADO if l != _lado_de(esc)])
    if s.area >= 9:
        en_muro(ctx, s, "cama_1", lambda r, l, t: _dist_esquina(s, r))


def _lavadero(ctx: Contexto, s: Sala) -> None:
    pileta = en_muro(ctx, s, "pileta_lavadero", lambda r, l, t: _dist_esquina(s, r))
    if pileta:
        hp = huella(pileta)
        en_muro(ctx, s, "lavarropas", lambda r, l, t: math.dist(_centro(r), _centro(hp)))
    else:
        ctx.notas.append(f"«{s.nombre}»: no entra la pileta de lavar.")
    en_esquina(ctx, s, "termotanque", lambda r: -_dist_puertas(s, r))


def _vestidor(ctx: Contexto, s: Sala) -> None:
    for _ in range(2):
        if not (en_muro(ctx, s, "placard_180", lambda r, l, t: _dist_esquina(s, r))
                or en_muro(ctx, s, "placard_120", lambda r, l, t: _dist_esquina(s, r))):
            break


def _galeria(ctx: Contexto, s: Sala) -> None:
    _mesa_comedor(ctx, s, None, exterior=True)
    if any(l.muro for l in s.lados.values()):
        en_muro(ctx, s, "parrilla", lambda r, l, t: -min(t, _largo_lado(s, l) - t))
    en_esquina(ctx, s, "planta")


def _deposito(ctx: Contexto, s: Sala) -> None:
    en_muro(ctx, s, "estanteria", lambda r, l, t: _dist_esquina(s, r))


def _quitar(ctx: Contexto, pid: str) -> None:
    for nombre in LISTAS:
        lista = ctx.casa.get(nombre) or []
        ctx.casa[nombre] = [p for p in lista if p["id"] != pid]
    ctx.ocupado = [o for o in ctx.ocupado if o[0] != pid]
    ctx.zonas = [z for z in ctx.zonas if z[0] != pid]


def amoblar(casa: dict, ambientes: list[str] | None = None, reemplazar: bool = False) -> tuple[dict, list[str]]:
    """Propone muebles y artefactos para los ambientes. Sin `ambientes`, todos los que no tienen
    ninguna pieza (o todos, con `reemplazar`). Devuelve una copia de la casa y notas para el usuario."""
    casa = deepcopy(casa)
    for nombre in LISTAS:
        casa.setdefault(nombre, [])
    con_piezas = {p.get("ambiente") for p in piezas(casa)}
    objetivo = [a for a in casa.get("ambientes") or []
                if (ambientes is None or a["id"] in ambientes) and (reemplazar or a["id"] not in con_piezas)]
    if reemplazar:
        ids = {a["id"] for a in objetivo}
        for nombre in LISTAS:
            casa[nombre] = [p for p in casa[nombre] if p.get("ambiente") not in ids]
    ctx = Contexto.desde(casa)
    hay_cocina = any(a.get("uso") == "cocina" for a in casa.get("ambientes") or [])
    # Primero los ambientes chicos y especializados: el estar se adapta a lo que queda.
    orden = {"bano": 0, "cocina": 1, "lavadero": 2, "dormitorio": 3, "vestidor": 4, "oficina": 5, "social": 6,
             "deposito": 7, "galeria": 8}
    for amb in sorted(objetivo, key=lambda a: orden.get(a.get("uso"), 9)):
        s = sala(casa, amb)
        if not s:
            ctx.notas.append(f"«{amb.get('nombre', amb['id'])}» no tiene contorno: no se puede amoblar.")
            continue
        uso = s.uso
        if uso == "dormitorio":
            _dormitorio(ctx, s)
        elif uso == "bano":
            _bano(ctx, s)
        elif uso == "cocina":
            _cocina(ctx, s)
        elif uso == "social":
            _estar(ctx, s, con_cocina=not hay_cocina)
        elif uso == "oficina":
            _oficina(ctx, s)
        elif uso == "lavadero":
            _lavadero(ctx, s)
        elif uso == "vestidor":
            _vestidor(ctx, s)
        elif uso == "galeria":
            _galeria(ctx, s)
        elif uso == "deposito":
            _deposito(ctx, s)
    return casa, ctx.notas


def colocar(casa: dict, codigo: str, ambiente: str, origen: str = "usuario") -> tuple[dict, dict | None, str]:
    """Agrega una pieza del catálogo a un ambiente donde entre. Devuelve (casa, pieza o None, motivo)."""
    it = item(codigo)
    if not it:
        return casa, None, f"«{codigo}» no está en el catálogo."
    amb = next((a for a in casa.get("ambientes") or [] if a["id"] == ambiente), None)
    if not amb:
        return casa, None, f"No existe el ambiente «{ambiente}»."
    casa = deepcopy(casa)
    s = sala(casa, amb)
    if not s:
        return casa, None, f"«{amb['nombre']}» no tiene contorno."
    if s.exterior and not it.get("exterior"):
        return casa, None, f"{it['nombre']} es para adentro; la galería es exterior."
    if not s.exterior and not it.get("interior", True):
        return casa, None, f"{it['nombre']} es para la galería."
    if it.get("usos") and s.uso not in it["usos"]:
        return casa, None, f"{it['nombre']} no va en «{s.nombre}» ({s.uso})."
    ctx = Contexto.desde(casa)
    if it["apoyo"] == "muro":
        p = en_muro(ctx, s, codigo, origen=origen)
    elif it["apoyo"] == "esquina":
        p = en_esquina(ctx, s, codigo, origen=origen) or en_muro(ctx, s, codigo, origen=origen)
    else:
        p = libre(ctx, s, codigo, origen=origen)
    if not p:
        return casa, None, f"No queda lugar para {it['nombre'].lower()} en «{s.nombre}» con su espacio de uso."
    return casa, p, ""


# ---------------------------------------------------------------- galería

def _lado_exterior(casa: dict, muro: dict) -> str | None:
    """Hacia dónde mira un muro exterior: norte, sur, este u oeste."""
    huella_ = [tuple(v) for v in casa.get("huella_m") or []]
    if len(huella_) < 3:
        return None
    horiz, c, lo, hi = _segmento(muro)
    mitad = (lo + hi) / 2
    d = _espesor(casa, muro.get("sistema", "exterior")) / 2 + 0.05
    if horiz:
        if not poligono.contiene(huella_, mitad, c + d):
            return "norte"
        if not poligono.contiene(huella_, mitad, c - d):
            return "sur"
    else:
        if not poligono.contiene(huella_, c + d, mitad):
            return "este"
        if not poligono.contiene(huella_, c - d, mitad):
            return "oeste"
    return None


def lado_soleado(lat: float | None) -> str:
    """La galería al sol de invierno: al norte en el hemisferio sur."""
    return "sur" if lat is not None and lat > 0 else "norte"


def agregar_galeria(casa: dict, lado: str | None = None, fondo_m: float = 3.0, largo_m: float | None = None,
                    lat: float | None = None) -> tuple[dict, str | None, list[str]]:
    """Galería rectangular adosada a un muro exterior, del lado pedido (o del soleado).
    Prefiere el muro del estar y, si no tiene salida, propone una puerta-ventana corrediza."""
    casa = deepcopy(casa)
    lado = lado or lado_soleado(lat)
    notas: list[str] = []
    muros = [m for m in casa.get("muros") or [] if m.get("sistema") == "exterior" and _lado_exterior(casa, m) == lado]
    if not muros:
        return casa, None, [f"No hay un muro exterior mirando al {lado}."]
    social = [a for a in casa.get("ambientes") or [] if a.get("uso") == "social" and a.get("contorno_m")]

    def junto_estar(m: dict) -> float:
        horiz, c, lo, hi = _segmento(m)
        total = 0.0
        for a in social:
            x0, y0, x1, y1 = poligono.caja([tuple(v) for v in a["contorno_m"]])
            total += max(0.0, min(hi, x1 if horiz else y1) - max(lo, x0 if horiz else y0))
        return total

    muro = max(muros, key=lambda m: (junto_estar(m), _segmento(m)[3] - _segmento(m)[2]))
    horiz, c, lo, hi = _segmento(muro)
    cara = c + (_espesor(casa, "exterior") / 2) * (1 if lado in ("norte", "este") else -1)
    largo = min(largo_m or 6.0, hi - lo)
    # Centrada sobre el estar si lo toca; si no, sobre el muro.
    centro = (lo + hi) / 2
    if social and junto_estar(muro) > 0:
        a = social[0]
        x0, y0, x1, y1 = poligono.caja([tuple(v) for v in a["contorno_m"]])
        a0, a1 = (x0, x1) if horiz else (y0, y1)
        centro = (max(lo, a0) + min(hi, a1)) / 2
    d = max(lo, min(hi - largo, centro - largo / 2))
    signo = 1 if lado in ("norte", "este") else -1
    f0, f1 = sorted((cara, cara + signo * fondo_m))
    rect = (d, f0, d + largo, f1) if horiz else (f0, d, f1, d + largo)
    contorno = [[round(rect[0], 3), round(rect[1], 3)], [round(rect[2], 3), round(rect[1], 3)],
                [round(rect[2], 3), round(rect[3], 3)], [round(rect[0], 3), round(rect[3], 3)]]
    ambientes = casa.setdefault("ambientes", [])
    existente = next((a for a in ambientes if a.get("uso") == "galeria"), None)
    if existente:
        existente["contorno_m"] = contorno
        existente["estado"] = Estado.PROPUESTO.value
        gid = existente["id"]
        for nombre in LISTAS:
            casa[nombre] = [p for p in casa.get(nombre) or [] if p.get("ambiente") != gid]
    else:
        gid = "galeria"
        ambientes.append({"id": gid, "nombre": "Galería", "uso": "galeria", "contorno_m": contorno,
                          "solado": "madera_exterior", "estado": Estado.PROPUESTO.value})
    # Salida a la galería: una corrediza en el tramo compartido si no hay puerta.
    tramo = (max(lo, d), min(hi, d + largo))
    salidas = [o for o in muro.get("aberturas") or [] if o.get("tipo") in ("puerta", "ventana_corrediza", "paso")
               and min(tramo[1], _abertura_en_eje(muro, o)[1]) - max(tramo[0], _abertura_en_eje(muro, o)[0]) > 0]
    if not salidas:
        if _poner_corrediza(casa, muro, tramo):
            notas.append("Sumé una puerta-ventana corrediza para salir a la galería.")
        else:
            notas.append("La galería no tiene salida directa: agregá una puerta en ese muro.")
    return casa, gid, notas


def _poner_corrediza(casa: dict, muro: dict, tramo: tuple[float, float]) -> bool:
    it = next(i for i in catalogo()["familias"]["aberturas"]["items"] if i["codigo"] == "corrediza_200_205")
    (x0, y0), (x1, y1) = muro["eje"]["desde_m"], muro["eje"]["hasta_m"]
    horiz = abs(y0 - y1) < 1e-6
    a, b = (x0, x1) if horiz else (y0, y1)
    sentido = 1 if b >= a else -1
    largo = abs(b - a)
    ocupados = sorted((o["posicion_m"], o["posicion_m"] + o["ancho_m"]) for o in muro.get("aberturas") or [])
    ancho = it["ancho_m"]
    centro_tramo = (tramo[0] + tramo[1]) / 2
    candidatos = []
    k = 0.15
    while k + ancho <= largo - 0.15 + 1e-6:
        mundo = sorted((a + sentido * k, a + sentido * (k + ancho)))
        if mundo[0] >= tramo[0] - 1e-6 and mundo[1] <= tramo[1] + 1e-6 and all(
                k + ancho + 0.1 <= p or k >= q + 0.1 for p, q in ocupados):
            candidatos.append((abs((mundo[0] + mundo[1]) / 2 - centro_tramo), k))
        k += 0.05
    if not candidatos:
        return False
    k = min(candidatos)[1]
    ids = {o["id"] for m in casa.get("muros") or [] for o in m.get("aberturas") or []}
    oid, n = f"{muro['id']}_salida_galeria", 1
    while oid in ids:
        n += 1
        oid = f"{muro['id']}_salida_galeria_{n}"
    muro.setdefault("aberturas", []).append({
        "id": oid, "tipo": it["tipo"], "posicion_m": round(k, 3), "ancho_m": ancho, "antepecho_m": it["antepecho_m"],
        "dintel_m": round(it["antepecho_m"] + it["alto_m"], 3), "catalogo": it["codigo"], "estado": Estado.PROPUESTO.value})
    muro["aberturas"].sort(key=lambda o: o["posicion_m"])
    return True


# ---------------------------------------------------------------- descripción para el asistente

def describir(casa: dict) -> dict:
    """Resumen compacto de la planta y su interior para el asistente: ambientes con medidas,
    muros que los limitan (con su vecino) y piezas por ambiente."""
    ambs = []
    for a in casa.get("ambientes") or []:
        s = sala(casa, a)
        d = {"id": a["id"], "nombre": a.get("nombre"), "uso": a.get("uso")}
        if s:
            x0, y0, x1, y1 = s.caja
            d.update({"ancho_m": round(x1 - x0, 2), "fondo_m": round(y1 - y0, 2), "area_m2": round(s.area, 1),
                      "muros": _muros_de(casa, a, s)})
        d["piezas"] = [{"id": p["id"], "tipo": p.get("tipo")} for p in piezas(casa) if p.get("ambiente") == a["id"]]
        ambs.append(d)
    return {"ambientes": ambs}


def _muros_de(casa: dict, amb: dict, s: Sala) -> list[dict]:
    """Para cada lado del ambiente, el muro que lo limita y qué hay del otro lado."""
    out = []
    for lado in s.lados.values():
        for m in casa.get("muros") or []:
            horiz, c, lo, hi = _segmento(m)
            tol = _espesor(casa, m.get("sistema", "tabique")) / 2 + 0.08
            if horiz != lado.horizontal or abs(c - lado.fijo) > tol or min(hi, lado.b) - max(lo, lado.a) < 0.3:
                continue
            vecino = "exterior"
            d = _espesor(casa, m.get("sistema", "tabique")) + 0.15
            sx, sy = {"sur": (0, -d), "norte": (0, d), "oeste": (-d, 0), "este": (d, 0)}[lado.orient]
            mx, my = ((lado.a + lado.b) / 2, lado.fijo) if lado.horizontal else (lado.fijo, (lado.a + lado.b) / 2)
            for otro in casa.get("ambientes") or []:
                if otro["id"] != amb["id"] and otro.get("contorno_m") and \
                        poligono.contiene([tuple(v) for v in otro["contorno_m"]], mx + sx, my + sy):
                    vecino = otro["id"]
                    break
            # delta positivo mueve el muro hacia +X o +Y: agranda el ambiente si el muro está al norte o al este.
            out.append({"lado": lado.orient, "muro": m["id"], "sistema": m.get("sistema"), "vecino": vecino,
                        "agrandar_signo": 1 if lado.orient in ("norte", "este") else -1})
            break
    return out
