"""Capa 03 · Casa: de ambientes rectangulares a una planta con muros y aberturas.

La inteligencia artificial nunca escribe muros. Entiende lo que el usuario quiere
(el programa) o lo que muestra un bosquejo (ambientes aproximados), y a partir de
ahí la geometría la arma este módulo con reglas deterministas:

1. `alternativas(programa)` reparte los ambientes del programa en dos o tres
   partidos de planta (compacta, lineal, espejada) como rectángulos de ejes.
2. `normalizar_rectangulos()` limpia rectángulos leídos de una imagen: alinea
   bordes casi coincidentes y los lleva a la grilla de 5 cm.
3. `planta_desde_rectangulos()` convierte los rectángulos en muros exteriores,
   tabiques, aberturas por defecto del catálogo y ambientes con contorno
   interior, en el formato de `casos/angus_ranch.assambl.json`.

Convenciones (las de Angus Ranch): metros, X al este, Y al norte, ejes de muro
sobre los bordes de los rectángulos, contorno de ambiente en la cara interior.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from ..geometria import poligono
from ..modelo.casa import AREA_TIPICA_M2, ESQUEMA_CASA, Programa, Rectangulo
from ..modelo.estados import Estado

GRILLA_M = 0.05
PASILLO_M = 1.1

# Sistemas por defecto, tomados de Angus Ranch (MVP_01 §3.3).
SISTEMAS: dict[str, dict] = {
    "exterior": {
        "descripcion": "Muro exterior woodframe 45 × 140 con OSB, WRB, cámara ventilada y siding",
        "espesor_arquitectonico_m": 0.2,
        "capas": [
            {"capa": "terminacion_interior", "material": "revoque_calido", "espesor_mm": 12.5},
            {"capa": "entramado", "seccion_mm": [45, 140], "modulo_mm": 600, "material": "madera_estructura"},
            {"capa": "aislante", "material": "lana_mineral", "espesor_mm": 140},
            {"capa": "osb", "material": "osb", "espesor_mm": 12, "placa_mm": [1200, 2400], "junta_mm": 3.2},
            {"capa": "wrb", "material": "wrb", "solape_mm": 150, "retorno_esquina_mm": 300},
            {"capa": "camara_ventilada", "espesor_mm": 25, "liston_mm": [45, 25], "material": "madera_estructura"},
            {"capa": "siding", "material": "siding_oscuro", "espesor_mm": 20, "paso_mm": 180},
        ],
    },
    "interior_portante": {
        "descripcion": "Tabique portante 45 × 140, revoque en ambas caras",
        "espesor_arquitectonico_m": 0.2,
        "capas": [{"capa": "entramado", "seccion_mm": [45, 140], "modulo_mm": 600, "material": "madera_estructura"}],
        "terminacion": "revoque_calido",
    },
    "tabique": {
        "descripcion": "Tabique no portante 45 × 90, revoque en ambas caras",
        "espesor_arquitectonico_m": 0.15,
        "capas": [{"capa": "entramado", "seccion_mm": [45, 90], "modulo_mm": 600, "material": "madera_estructura"}],
        "terminacion": "revoque_calido",
    },
}

# Ancho mínimo razonable por uso (m). Por debajo el ambiente no se amuebla.
ANCHO_MIN_M: dict[str, float] = {
    "social": 3.6, "cocina": 2.2, "dormitorio": 2.7, "bano": 1.6, "lavadero": 1.5,
    "oficina": 2.4, "vestidor": 1.4, "deposito": 1.2, "circulacion": 0.9, "otro": 2.0,
}

# Qué ambientes no llevan muro entre sí: el pasillo desemboca en el estar.
_ABIERTOS = {frozenset({"social", "circulacion"})}

LADOS = ("norte", "sur", "este", "oeste")


# ---------------------------------------------------------------- catálogo

@lru_cache(maxsize=1)
def catalogo() -> dict:
    ruta = Path(__file__).resolve().parents[1] / "catalogo" / "ar.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def item_catalogo(codigo: str) -> dict:
    for it in catalogo()["familias"]["aberturas"]["items"]:
        if it["codigo"] == codigo:
            return it
    raise KeyError(codigo)


# ---------------------------------------------------------------- utilidades

def _g(v: float) -> float:
    """Redondea a la grilla de 5 cm y evita el -0.0."""
    r = round(round(v / GRILLA_M) * GRILLA_M, 3)
    return 0.0 if r == 0 else r


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return t or "ambiente"


def _nombre_muro(texto: str) -> str:
    return "_".join(p.capitalize() for p in texto.split("_"))


# ---------------------------------------------------------------- normalización

def normalizar_rectangulos(rects: list[Rectangulo], tolerancia_m: float = 0.3) -> tuple[list[Rectangulo], list[str]]:
    """Alinea bordes que difieren en menos de `tolerancia_m`, redondea a la grilla
    y lleva la planta al origen. Pensado para lo que devuelve la lectura de un
    bosquejo, donde dos ambientes vecinos rara vez comparten el borde exacto."""
    advertencias: list[str] = []
    utiles = []
    for r in rects:
        x0, x1 = sorted((r.x0, r.x1))
        y0, y1 = sorted((r.y0, r.y1))
        if x1 - x0 < 0.5 or y1 - y0 < 0.5:
            advertencias.append(f"«{r.nombre}» es demasiado chico para ser un ambiente y se descartó.")
            continue
        utiles.append(r.model_copy(update={"x0": x0, "x1": x1, "y0": y0, "y1": y1}))
    if not utiles:
        return [], advertencias

    def agrupar(valores: list[float]) -> dict[float, float]:
        orden = sorted(set(valores))
        mapa: dict[float, float] = {}
        grupo = [orden[0]]
        for v in orden[1:]:
            if v - grupo[0] <= tolerancia_m:
                grupo.append(v)
            else:
                m = sum(grupo) / len(grupo)
                mapa.update({g: m for g in grupo})
                grupo = [v]
        m = sum(grupo) / len(grupo)
        mapa.update({g: m for g in grupo})
        return mapa

    mx = agrupar([v for r in utiles for v in (r.x0, r.x1)])
    my = agrupar([v for r in utiles for v in (r.y0, r.y1)])
    ox = min(mx.values())
    oy = min(my.values())
    salida, ids = [], set()
    for r in utiles:
        base = slug(r.id or r.nombre)
        rid, n = base, 2
        while rid in ids:
            rid, n = f"{base}_{n}", n + 1
        ids.add(rid)
        salida.append(r.model_copy(update={
            "id": rid,
            "x0": _g(mx[r.x0] - ox), "x1": _g(mx[r.x1] - ox),
            "y0": _g(my[r.y0] - oy), "y1": _g(my[r.y1] - oy),
        }))
    return salida, advertencias


# ---------------------------------------------------------------- planta

class _Grilla:
    """Celdas entre las coordenadas únicas de los rectángulos, cada una con el
    ambiente que la ocupa. Es la forma más simple y robusta de encontrar bordes
    compartidos y exteriores en una planta ortogonal."""

    def __init__(self, rects: list[Rectangulo]):
        self.rects = {r.id: r for r in rects}
        self.xs = sorted({v for r in rects for v in (r.x0, r.x1)})
        self.ys = sorted({v for r in rects for v in (r.y0, r.y1)})
        self.celda: dict[tuple[int, int], str] = {}
        self.superpuestos: set[frozenset[str]] = set()
        for i in range(len(self.xs) - 1):
            cx = (self.xs[i] + self.xs[i + 1]) / 2
            for j in range(len(self.ys) - 1):
                cy = (self.ys[j] + self.ys[j + 1]) / 2
                dentro = [r.id for r in rects if r.x0 < cx < r.x1 and r.y0 < cy < r.y1]
                if dentro:
                    self.celda[(i, j)] = dentro[0]
                    for otro in dentro[1:]:
                        self.superpuestos.add(frozenset({dentro[0], otro}))

    def en(self, i: int, j: int) -> str | None:
        return self.celda.get((i, j))

    def segmentos(self):
        """Bordes atómicos: (orientación, coordenada fija, desde, hasta, a, b) con
        `a` a la izquierda/abajo y `b` a la derecha/arriba (None = exterior)."""
        for i, x in enumerate(self.xs):
            for j in range(len(self.ys) - 1):
                a, b = self.en(i - 1, j), self.en(i, j)
                if a != b:
                    yield ("v", x, self.ys[j], self.ys[j + 1], a, b)
        for j, y in enumerate(self.ys):
            for i in range(len(self.xs) - 1):
                a, b = self.en(i, j - 1), self.en(i, j)
                if a != b:
                    yield ("h", y, self.xs[i], self.xs[i + 1], a, b)


def _grupo(nombre: str) -> str:
    """Un ambiente en L llega partido en «Estar (a)» y «Estar (b)»: entre ellos no va muro."""
    return re.sub(r"\s*\([a-z]\)$", "", nombre.strip().lower())


def _usos(rects: dict[str, Rectangulo]) -> dict[str, str]:
    return {k: r.uso for k, r in rects.items()}


def planta_desde_rectangulos(
    rects: list[Rectangulo],
    estado: Estado = Estado.PROPUESTO,
    lat: float | None = None,
    nombre: str = "Casa",
    origen: dict | None = None,
) -> tuple[dict, list[str]]:
    """Devuelve (casa, advertencias). `estado` es el que reciben todas las piezas
    generadas: `propuesto` para lo que armó el generador, `pendiente_revision`
    para lo que se interpretó de una imagen y alguien debe mirar."""
    advertencias: list[str] = []
    if not rects:
        raise ValueError("No hay ambientes para armar la planta")
    grilla = _Grilla(rects)
    for par in grilla.superpuestos:
        a, b = sorted(par)
        advertencias.append(f"«{grilla.rects[a].nombre}» y «{grilla.rects[b].nombre}» se superponen; se tomó el primero.")
    usos = _usos(grilla.rects)
    sur_asoleado = lat is not None and lat > 0  # hemisferio norte: el sol viene del sur

    # 1. Bordes atómicos agrupados por línea y clave, en orden a lo largo de la línea.
    lineas: dict[tuple, list[tuple[float, float, str | None, str | None]]] = {}
    for ori, fijo, t0, t1, a, b in grilla.segmentos():
        if a is None or b is None:
            lado = {("v", True): "oeste", ("v", False): "este", ("h", True): "sur", ("h", False): "norte"}[(ori, a is None)]
            clave = ("ext", lado)
        else:
            if frozenset({usos[a], usos[b]}) in _ABIERTOS or _grupo(grilla.rects[a].nombre) == _grupo(grilla.rects[b].nombre):
                continue
            clave = ("int", tuple(sorted((a, b))))
        lineas.setdefault((ori, fijo, clave), []).append((t0, t1, a, b))

    # 2. Tramos contiguos de la misma clave forman un muro.
    muros: list[dict] = []
    tramos_ext: dict[str, list[tuple[str, float, float]]] = {}  # muro -> [(ambiente, t0, t1)]
    usados: set[str] = set()
    par_de: dict[str, tuple[str, str]] = {}  # tabique -> ambientes que separa

    def nuevo_id(base: str) -> str:
        mid, n = base, 2
        while mid in usados:
            mid, n = f"{base}_{n}", n + 1
        usados.add(mid)
        return mid

    for (ori, fijo, clave), segs in sorted(lineas.items(), key=lambda kv: (kv[0][2][0] != "ext", kv[0][0], kv[0][1])):
        segs.sort()
        grupos: list[list] = []
        for s in segs:
            if grupos and abs(grupos[-1][-1][1] - s[0]) < 1e-6:
                grupos[-1].append(s)
            else:
                grupos.append([s])
        for g in grupos:
            t0, t1 = g[0][0], g[-1][1]
            if clave[0] == "ext":
                lado = clave[1]
                mid = nuevo_id(lado.capitalize())
                sistema = "exterior"
            else:
                a, b = clave[1]
                mid = nuevo_id(f"{_nombre_muro(a)}_{_nombre_muro(b)}")
                sistema = "tabique"
                par_de[mid] = (a, b)
            desde = (fijo, t0) if ori == "v" else (t0, fijo)
            hasta = (fijo, t1) if ori == "v" else (t1, fijo)
            muro = {
                "id": mid,
                "sistema": sistema,
                "eje": {"desde_m": [_g(desde[0]), _g(desde[1])], "hasta_m": [_g(hasta[0]), _g(hasta[1])]},
                "altura": {"tipo": "hasta_cubierta", "cubierta": "principal"} if sistema == "exterior" else {"tipo": "tabique"},
                "aberturas": [],
                "estado": estado.value,
            }
            if clave[0] == "ext":
                muro["lado_exterior"] = clave[1]
                tramos_ext[mid] = [((s[2] or s[3]), s[0] - t0, s[1] - t0) for s in g]
            muros.append(muro)

    por_id = {m["id"]: m for m in muros}

    # 3. Aberturas por defecto.
    def colocar(muro: dict, codigo: str, centro: float | None = None, desde: float | None = None,
                hoja: dict | None = None) -> bool:
        it = item_catalogo(codigo)
        largo = _largo(muro)
        ancho = it["ancho_m"]
        pos = desde if desde is not None else (centro - ancho / 2 if centro is not None else (largo - ancho) / 2)
        pos = _g(min(max(pos, 0.1), largo - ancho - 0.1))
        if pos < 0.1 - 1e-6 or pos + ancho > largo - 0.1 + 1e-6:
            return False
        for o in muro["aberturas"]:
            if pos < o["posicion_m"] + o["ancho_m"] + 0.2 and o["posicion_m"] < pos + ancho + 0.2:
                return False
        ab = {
            "id": "",
            "tipo": it["tipo"],
            "posicion_m": pos,
            "ancho_m": ancho,
            "antepecho_m": it["antepecho_m"],
            "dintel_m": round(it["antepecho_m"] + it["alto_m"], 3),
            "catalogo": codigo,
            "estado": estado.value,
        }
        if it["tipo"] == "puerta":
            ab["hoja"] = hoja or {"bisagra": "inicio", "apertura_deg": 70}
        muro["aberturas"].append(ab)
        return True

    # 3a. Puertas interiores: cada ambiente cerrado se abre hacia el pasillo, el
    # estar o, en última instancia, hacia el ambiente que lo contiene (baño en suite).
    preferencia = {"circulacion": 0, "social": 1, "cocina": 2, "dormitorio": 3, "vestidor": 4}
    for rid, r in grilla.rects.items():
        if r.uso in ("social", "circulacion"):
            continue
        candidatos = []
        for m in muros:
            par = par_de.get(m["id"])
            if not par or rid not in par:
                continue
            otro = par[1] if par[0] == rid else par[0]
            if usos[otro] == "bano":
                continue
            candidatos.append((preferencia.get(usos[otro], 5), -_largo(m), m["id"], m))
        if not candidatos:
            advertencias.append(f"«{r.nombre}» no linda con ningún ambiente de paso: no se le pudo poner puerta.")
            continue
        candidatos.sort(key=lambda c: (c[0], c[1]))
        codigo = {"bano": "puerta_070", "vestidor": "paso_080", "deposito": "puerta_070", "cocina": "paso_080"}.get(r.uso, "puerta_080")
        for _, _, _, m in candidatos:
            if colocar(m, codigo, desde=0.15) or colocar(m, codigo):
                break
        else:
            advertencias.append(f"«{r.nombre}»: el muro de acceso es demasiado corto para una puerta.")

    # 3b. Ventanas y acceso sobre los muros exteriores de cada ambiente.
    orden_lados = ["sur", "este", "oeste", "norte"] if sur_asoleado else ["norte", "este", "oeste", "sur"]
    ventanas = {
        "social": ["corrediza_200_205", "ventana_200_110", "ventana_150_110"],
        "dormitorio": ["ventana_150_110", "ventana_100_110"],
        "oficina": ["ventana_150_110", "ventana_100_110"],
        "cocina": ["ventana_100_110"],
        "lavadero": ["ventana_100_110", "ventiluz_060_040"],
        "bano": ["ventiluz_060_040"],
        "otro": ["ventana_100_110"],
    }

    def spans(rid: str) -> list[tuple[int, float, dict, float, float]]:
        res = []
        for mid, tr in tramos_ext.items():
            m = por_id[mid]
            for amb, t0, t1 in tr:
                if amb == rid:
                    res.append((orden_lados.index(m["lado_exterior"]), -(t1 - t0), m, t0, t1))
        # Tramos contiguos del mismo ambiente sobre el mismo muro se unen.
        res.sort(key=lambda s: (s[2]["id"], s[3]))
        unidos: list[list] = []
        for s in res:
            if unidos and unidos[-1][2] is s[2] and abs(unidos[-1][4] - s[3]) < 1e-6:
                unidos[-1][4] = s[4]
                unidos[-1][1] = -(unidos[-1][4] - unidos[-1][3])
            else:
                unidos.append(list(s))
        return sorted((tuple(u) for u in unidos), key=lambda s: (s[0], s[1]))  # type: ignore[misc]

    acceso_puesto = False
    for rid, r in grilla.rects.items():
        opciones = ventanas.get(r.uso)
        disponibles = spans(rid)
        if r.uso == "social" and not acceso_puesto and disponibles:
            # El acceso va del lado opuesto al sol cuando se puede: la fachada asoleada queda para el estar.
            por_acceso = sorted(disponibles, key=lambda s: (-s[0], s[1]))
            for _, _, m, t0, t1 in por_acceso:
                # La hoja abre hacia adentro: a la izquierda del eje en los muros sur y este.
                hacia_adentro = 80 if m["lado_exterior"] in ("sur", "este") else -80
                if t1 - t0 >= 1.5 and colocar(m, "puerta_090", desde=t0 + 0.3, hoja={"bisagra": "inicio", "apertura_deg": hacia_adentro}):
                    acceso_puesto = True
                    break
        if not opciones or not disponibles:
            continue
        puesta = False
        for _, _, m, t0, t1 in disponibles:
            for codigo in opciones:
                if item_catalogo(codigo)["ancho_m"] + 0.4 <= t1 - t0 and colocar(m, codigo, centro=(t0 + t1) / 2):
                    puesta = True
                    break
            if puesta:
                break
        if not puesta and r.uso in ("dormitorio", "social", "oficina"):
            advertencias.append(f"«{r.nombre}» no tiene muro exterior con lugar para una ventana.")
    if not acceso_puesto:
        advertencias.append("No se encontró dónde poner la puerta de acceso; agregala desde el editor.")

    for m in muros:
        m["aberturas"].sort(key=lambda o: o["posicion_m"])
        for i, o in enumerate(m["aberturas"]):
            o["id"] = f"{m['id']}/O{i}"

    # 4. Ambientes con contorno interior (cara del muro) y huella exterior.
    ambientes = []
    for rid, r in grilla.rects.items():
        contorno = _contorno_interior(r, muros)
        amb = {
            "id": rid,
            "nombre": r.nombre,
            "uso": r.uso,
            "contorno_m": contorno,
            "estado": estado.value,
        }
        ambientes.append(amb)

    huella = _huella(grilla)
    casa = {
        "esquema": ESQUEMA_CASA,
        "nombre": nombre,
        "origen": origen or {"fuente": "assambl/capas/casa.py", "nota": "Planta generada a partir de ambientes rectangulares."},
        "unidades": "m",
        "ejes": {"x": "este", "y": "norte", "z": "arriba", "origen": "esquina suroeste de la planta, sobre el piso terminado"},
        "implantacion": {"origen_en_lote_m": [0.0, 0.0], "giro_deg": 0.0, "cota_piso_sobre_terreno_m": 0.2},
        "huella_m": huella,
        "sistemas": json.loads(json.dumps(SISTEMAS)),
        "parametros": {"altura_tabiques_m": 2.6},
        "muros": muros,
        "ambientes": ambientes,
    }
    return casa, advertencias


def _largo(muro: dict) -> float:
    (x0, y0), (x1, y1) = muro["eje"]["desde_m"], muro["eje"]["hasta_m"]
    return math.hypot(x1 - x0, y1 - y0)


def _espesor(sistema: str) -> float:
    return SISTEMAS.get(sistema, SISTEMAS["tabique"])["espesor_arquitectonico_m"]


def _contorno_interior(r: Rectangulo, muros: list[dict]) -> list[list[float]]:
    """Retira cada lado del rectángulo medio espesor del muro que tiene encima."""

    def retiro(ori: str, fijo: float, a: float, b: float) -> float:
        e = 0.0
        for m in muros:
            (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
            if ori == "h" and abs(y0 - fijo) < 1e-6 and abs(y1 - fijo) < 1e-6:
                lo, hi = sorted((x0, x1))
            elif ori == "v" and abs(x0 - fijo) < 1e-6 and abs(x1 - fijo) < 1e-6:
                lo, hi = sorted((y0, y1))
            else:
                continue
            if min(hi, b) - max(lo, a) > 1e-6:
                e = max(e, _espesor(m["sistema"]) / 2)
        return e

    x0 = r.x0 + retiro("v", r.x0, r.y0, r.y1)
    x1 = r.x1 - retiro("v", r.x1, r.y0, r.y1)
    y0 = r.y0 + retiro("h", r.y0, r.x0, r.x1)
    y1 = r.y1 - retiro("h", r.y1, r.x0, r.x1)
    return [[round(x0, 3), round(y0, 3)], [round(x1, 3), round(y0, 3)], [round(x1, 3), round(y1, 3)], [round(x0, 3), round(y1, 3)]]


def _huella(grilla: _Grilla) -> list[list[float]]:
    """Contorno exterior de la planta: se recorre el borde de las celdas ocupadas
    dejando el interior a la izquierda y se desplaza medio espesor de muro exterior."""
    siguiente: dict[tuple[float, float], tuple[float, float]] = {}
    for ori, fijo, t0, t1, a, b in grilla.segmentos():
        if a is not None and b is not None:
            continue
        if ori == "v":
            p, q = ((fijo, t1), (fijo, t0)) if a is None else ((fijo, t0), (fijo, t1))
        else:
            p, q = ((t0, fijo), (t1, fijo)) if a is None else ((t1, fijo), (t0, fijo))
        siguiente[p] = q
    lazos: list[list[tuple[float, float]]] = []
    pendientes = dict(siguiente)
    while pendientes:
        inicio, q = next(iter(pendientes.items()))
        lazo = [inicio]
        del pendientes[inicio]
        while q != inicio and q in pendientes:
            lazo.append(q)
            q = pendientes.pop(q)
        lazos.append(lazo)
    lazo = max(lazos, key=lambda l: abs(poligono.area_con_signo(l)))
    # Quita vértices colineales.
    limpio = []
    n = len(lazo)
    for i in range(n):
        a, b, c = lazo[i - 1], lazo[i], lazo[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            limpio.append(b)
    d = _espesor("exterior") / 2
    salida = []
    n = len(limpio)
    for i in range(n):
        a, b, c = limpio[i - 1], limpio[i], limpio[(i + 1) % n]
        n1 = _normal_derecha(a, b)
        n2 = _normal_derecha(b, c)
        salida.append([_g(b[0] + d * (n1[0] + n2[0])), _g(b[1] + d * (n1[1] + n2[1]))])
    # Empieza en el vértice suroeste, como Angus Ranch.
    k = min(range(len(salida)), key=lambda i: (salida[i][1] + salida[i][0], salida[i][0]))
    return salida[k:] + salida[:k]


def _normal_derecha(a, b) -> tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1.0
    return (dy / l, -dx / l)


# ---------------------------------------------------------------- alternativas

def _area(amb) -> float:
    return float(amb.area_m2 or AREA_TIPICA_M2.get(amb.uso, 8.0))


def _preparar(programa: Programa):
    ambs = [a for a in programa.ambientes if a.uso != "circulacion"]
    sociales = [a for a in ambs if a.uso == "social"]
    cocinas = [a for a in ambs if a.uso == "cocina"]
    area_social = sum(_area(a) for a in sociales) or AREA_TIPICA_M2["social"]
    nombre_social = sociales[0].nombre if sociales else "Estar y comedor"
    id_social = sociales[0].id if sociales else "estar"
    if cocinas and programa.cocina_integrada is not False and programa.cocina_integrada is not None:
        area_social += sum(_area(a) for a in cocinas)
        cocinas = []
        if "cocina" not in nombre_social.lower():
            nombre_social = f"{nombre_social} y cocina"
    resto = [a for a in ambs if a.uso not in ("social", "cocina")]
    return (id_social, nombre_social, area_social), cocinas, resto


def _anchos(lista, profundidad: float) -> list[float]:
    return [max(ANCHO_MIN_M.get(a.uso, 2.0), _area(a) / profundidad) for a in lista]


def _estirar(anchos: list[float], total: float) -> list[float]:
    s = sum(anchos)
    if s <= 0 or total <= s:
        return anchos
    return [w * total / s for w in anchos]


def _fila(lista, anchos, x: float, y0: float, y1: float) -> list[Rectangulo]:
    rects = []
    for a, w in zip(lista, anchos):
        rects.append(Rectangulo(id=slug(a.id), nombre=a.nombre, uso=a.uso, x0=_g(x), y0=y0, x1=_g(x + w), y1=y1))
        x += w
    if rects:  # el último cierra exacto, sin arrastrar redondeos
        rects[-1] = rects[-1].model_copy(update={"x1": _g(x)})
    return rects


def _compacta(programa: Programa) -> list[Rectangulo]:
    (sid, snombre, sarea), cocinas, resto = _preparar(programa)
    dn, ds = 3.6, 2.4
    prof = dn + PASILLO_M + ds
    norte = [a for a in resto if a.uso in ("dormitorio", "oficina")]
    sur = [a for a in resto if a.uso not in ("dormitorio", "oficina")]
    # Orden: lo público cerca del estar, el dormitorio principal al fondo.
    norte.sort(key=lambda a: (a.uso != "oficina", a.principal))
    sur.sort(key=lambda a: ({"lavadero": 0, "deposito": 1, "bano": 2, "vestidor": 3}.get(a.uso, 4), a.principal))
    # Si la franja norte queda mucho más larga, un dormitorio secundario cruza al sur.
    while True:
        wn, ws = sum(_anchos(norte, dn)), sum(_anchos(sur, ds))
        movibles = [a for a in norte if a.uso == "dormitorio" and not a.principal]
        if wn - ws <= 3.0 or len(movibles) < 2:
            break
        mover = movibles[-1]
        norte.remove(mover)
        sur.append(mover)
    if any(a.uso == "dormitorio" for a in sur):
        ds = 3.0  # un dormitorio en la franja sur necesita más profundidad
        prof = dn + PASILLO_M + ds
    wn, ws = _anchos(norte, dn), _anchos(sur, ds)
    ancho_priv = max(sum(wn), sum(ws), 2.0)
    wn, ws = _estirar(wn, ancho_priv), _estirar(ws, ancho_priv)

    ancho_social = max(ANCHO_MIN_M["social"], sarea / prof)
    rects: list[Rectangulo] = []
    if cocinas:
        c = cocinas[0]
        rects.append(Rectangulo(id=slug(c.id), nombre=c.nombre, uso="cocina", x0=0, y0=0, x1=_g(ancho_social), y1=ds))
        rects.append(Rectangulo(id=slug(sid), nombre=snombre, uso="social", x0=0, y0=ds, x1=_g(ancho_social), y1=_g(prof)))
    else:
        rects.append(Rectangulo(id=slug(sid), nombre=snombre, uso="social", x0=0, y0=0, x1=_g(ancho_social), y1=_g(prof)))
    x = _g(ancho_social)
    rects += _fila(sur, ws, x, 0.0, ds)
    if resto:
        rects.append(Rectangulo(id="pasillo", nombre="Pasillo", uso="circulacion", x0=x, y0=ds, x1=_g(x + ancho_priv), y1=_g(ds + PASILLO_M)))
    rects += _fila(norte, wn, x, _g(ds + PASILLO_M), _g(prof))
    return _cerrar_filas(rects)


def _lineal(programa: Programa) -> list[Rectangulo]:
    (sid, snombre, sarea), cocinas, resto = _preparar(programa)
    dn = 3.8
    prof = dn + PASILLO_M
    fila = list(cocinas) + sorted(resto, key=lambda a: (
        {"lavadero": 0, "oficina": 1, "dormitorio": 2, "bano": 3, "vestidor": 4}.get(a.uso, 5), a.principal))
    # Baño y vestidor del principal quedan junto a él, al final de la tira.
    ancho_social = max(ANCHO_MIN_M["social"], sarea / prof)
    rects = [Rectangulo(id=slug(sid), nombre=snombre, uso="social", x0=0, y0=0, x1=_g(ancho_social), y1=_g(prof))]
    x = _g(ancho_social)
    anchos = _anchos(fila, dn)
    rects += _fila(fila, anchos, x, PASILLO_M, _g(prof))
    if fila:
        rects.append(Rectangulo(id="pasillo", nombre="Pasillo", uso="circulacion", x0=x, y0=0, x1=rects[-1].x1, y1=PASILLO_M))
    return _cerrar_filas(rects)


def _cerrar_filas(rects: list[Rectangulo]) -> list[Rectangulo]:
    """Iguala el borde este de las filas para que la planta cierre en un rectángulo."""
    fin = max(r.x1 for r in rects)
    for i, r in enumerate(rects):
        es_ultimo = not any(o.x0 >= r.x1 - 1e-6 and o.y0 < r.y1 and r.y0 < o.y1 for o in rects if o is not r)
        if es_ultimo and r.x1 < fin:
            rects[i] = r.model_copy(update={"x1": fin})
    return rects


def _espejar_x(rects: list[Rectangulo]) -> list[Rectangulo]:
    fin = max(r.x1 for r in rects)
    return [r.model_copy(update={"x0": _g(fin - r.x1), "x1": _g(fin - r.x0)}) for r in rects]


def _espejar_y(rects: list[Rectangulo]) -> list[Rectangulo]:
    fin = max(r.y1 for r in rects)
    return [r.model_copy(update={"y0": _g(fin - r.y1), "y1": _g(fin - r.y0)}) for r in rects]


def alternativas(programa: Programa, lat: float | None = None, estado: Estado = Estado.PROPUESTO) -> list[dict]:
    """Dos o tres partidos de planta para el mismo programa. Todos respetan el
    dominio del MVP_01 (una planta, ortogonal) y ponen el estar y los dormitorios
    hacia el sol: el norte en el hemisferio sur."""
    sol = "sur" if lat is not None and lat > 0 else "norte"
    partidos = [
        ("compacta", "Compacta en dos franjas",
         f"Estar a un lado y un pasillo corto que reparte. Dormitorios hacia el {sol}; baños y lavadero del lado opuesto. "
         "Menos perímetro de muro exterior: más económica de construir y de calefaccionar.",
         _compacta(programa)),
        ("lineal", "Lineal, todo al sol",
         f"Una tira de ambientes con el pasillo del lado frío. Todos los ambientes miran al {sol}. "
         "Más fachada y más muro exterior, a cambio de luz en cada ambiente.",
         _lineal(programa)),
        ("compacta_espejada", "Compacta, estar al este",
         "Igual que la compacta, con el estar del lado del sol de la mañana y los dormitorios hacia el oeste.",
         _espejar_x(_compacta(programa))),
    ]
    salida = []
    for pid, nombre, descripcion, rects in partidos:
        if sol == "sur":
            rects = _espejar_y(rects)
        casa, adv = planta_desde_rectangulos(rects, estado=estado, lat=lat,
                                             origen={"fuente": "assambl/capas/casa.py", "partido": pid,
                                                     "nota": "Alternativa generada a partir del programa."})
        huella = casa["huella_m"]
        xs = [p[0] for p in huella]
        ys = [p[1] for p in huella]
        salida.append({
            "id": pid,
            "nombre": nombre,
            "descripcion": descripcion,
            "rectangulos": [r.model_dump() for r in rects],
            "casa": casa,
            "advertencias": adv,
            "resumen": {
                "superficie_cubierta_m2": round(poligono.area([tuple(p) for p in huella]), 1),
                "ancho_m": round(max(xs) - min(xs), 2),
                "profundidad_m": round(max(ys) - min(ys), 2),
                "muro_exterior_m": round(sum(_largo(m) for m in casa["muros"] if m["sistema"] == "exterior"), 1),
                "ambientes": len(casa["ambientes"]),
            },
        })
    return salida
