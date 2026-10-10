"""Capa 03 · Casa: de ambientes rectangulares a una planta con muros y aberturas.

Nadie más escribe muros: ni Lumo ni la IA que lee bosquejos. Los dos entregan
ambientes como rectángulos, y a partir de ahí la geometría la arma este módulo
con reglas deterministas:

1. `capas/planta_base.py` decide dónde va cada ambiente (la planta base que
   propone Lumo) y lo expresa como rectángulos de ejes.
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
from ..modelo.casa import ESQUEMA_CASA, Rectangulo
from ..modelo.estados import Estado

GRILLA_M = 0.05

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


def _grupo_de(r: Rectangulo) -> str:
    """Ambiente al que pertenece el rectángulo. Un ambiente que no es rectangular
    llega partido en varios rectángulos con el mismo `grupo` (o, desde una imagen,
    como «Estar (a)» y «Estar (b)»): entre ellos no va muro y forman un solo contorno."""
    if r.grupo:
        return r.grupo
    m = re.match(r"^(.*\S)\s*\([a-z]\)$", r.nombre.strip(), re.I)
    return slug(m.group(1)) if m else r.id


def _nombre_de_grupo(r: Rectangulo) -> str:
    return re.sub(r"\s*\([a-z]\)$", "", r.nombre.strip(), flags=re.I)


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
    grupo_de = {r.id: _grupo_de(r) for r in rects}
    grupos: dict[str, list[Rectangulo]] = {}
    for r in rects:
        grupos.setdefault(grupo_de[r.id], []).append(r)
    usos = {gid: rs[0].uso for gid, rs in grupos.items()}
    sur_asoleado = lat is not None and lat > 0  # hemisferio norte: el sol viene del sur

    # 1. Bordes atómicos agrupados por línea y clave, en orden a lo largo de la línea.
    lineas: dict[tuple, list[tuple[float, float, str | None, str | None]]] = {}
    for ori, fijo, t0, t1, a, b in grilla.segmentos():
        if a is None or b is None:
            lado = {("v", True): "oeste", ("v", False): "este", ("h", True): "sur", ("h", False): "norte"}[(ori, a is None)]
            clave = ("ext", lado)
        else:
            ga, gb = grupo_de[a], grupo_de[b]
            if ga == gb or frozenset({usos[ga], usos[gb]}) in _ABIERTOS:
                continue
            clave = ("int", tuple(sorted((ga, gb))))
        lineas.setdefault((ori, fijo, clave), []).append((t0, t1, a, b))

    # 2. Tramos contiguos de la misma clave forman un muro.
    muros: list[dict] = []
    tramos_ext: dict[str, list[tuple[str, float, float]]] = {}  # muro -> [(rectángulo, t0, t1)]
    inicio_de: dict[str, float] = {}  # muro -> coordenada donde empieza su eje
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
        tramos: list[list] = []
        for s in segs:
            if tramos and abs(tramos[-1][-1][1] - s[0]) < 1e-6:
                tramos[-1].append(s)
            else:
                tramos.append([s])
        for g in tramos:
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
            inicio_de[mid] = t0
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

    def lado_del_muro(m: dict, rs: list[Rectangulo]) -> str | None:
        """De qué lado del ambiente queda el muro."""
        (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
        for r in rs:
            if abs(x0 - x1) < 1e-6 and min(y1, r.y1) - max(y0, r.y0) > 1e-6:
                if abs(r.x1 - x0) < 1e-6:
                    return "este"
                if abs(r.x0 - x0) < 1e-6:
                    return "oeste"
            if abs(y0 - y1) < 1e-6 and min(x1, r.x1) - max(x0, r.x0) > 1e-6:
                if abs(r.y1 - y0) < 1e-6:
                    return "norte"
                if abs(r.y0 - y0) < 1e-6:
                    return "sur"
        return None

    # 3a. Puertas interiores: cada ambiente cerrado se abre hacia el pasillo, el
    # estar o, en última instancia, hacia el ambiente que lo contiene (baño en suite).
    # Un rectángulo puede pedir su puerta (`puerta`); si no se puede cumplir, se elige igual.
    preferencia = {"circulacion": 0, "social": 1, "cocina": 2, "dormitorio": 3, "vestidor": 4}
    for gid, rs in grupos.items():
        uso = usos[gid]
        if uso in ("social", "circulacion"):
            continue
        nombre_amb = _nombre_de_grupo(rs[0])
        candidatos = []
        for m in muros:
            par = par_de.get(m["id"])
            if not par or gid not in par:
                continue
            otro = par[1] if par[0] == gid else par[0]
            if usos[otro] == "bano":
                continue
            candidatos.append((preferencia.get(usos[otro], 5), -_largo(m), m["id"], m, otro))
        if not candidatos:
            advertencias.append(f"«{nombre_amb}» no linda con ningún ambiente de paso: no se le pudo poner puerta.")
            continue
        deseo = next((r.puerta for r in rs if r.puerta), None)
        if deseo:
            pedidos = [c for c in candidatos
                       if (not deseo.hacia or c[4] == deseo.hacia) and (not deseo.lado or lado_del_muro(c[3], rs) == deseo.lado)]
            candidatos = pedidos or candidatos
        candidatos.sort(key=lambda c: (c[0], c[1]))
        codigo = {"bano": "puerta_070", "vestidor": "paso_080", "deposito": "puerta_070", "cocina": "paso_080"}.get(uso, "puerta_080")
        ancho = item_catalogo(codigo)["ancho_m"]
        for _, _, _, m, _ in candidatos:
            margen = deseo.margen_m if deseo else 0.15
            en_extremo = _largo(m) - ancho - margen if deseo and deseo.extremo == "fin" else margen
            if colocar(m, codigo, desde=en_extremo) or colocar(m, codigo):
                break
        else:
            advertencias.append(f"«{nombre_amb}»: el muro de acceso es demasiado corto para una puerta.")

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

    def spans(ids: set[str]) -> list[tuple[int, float, dict, float, float]]:
        """Tramos de muro exterior de un ambiente: (orden del lado, -largo, muro, t0, t1)."""
        res = []
        for mid, tr in tramos_ext.items():
            m = por_id[mid]
            for amb, t0, t1 in tr:
                if amb in ids:
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

    def hoja_hacia_adentro(m: dict) -> dict:
        # A la izquierda del eje en los muros sur y este.
        return {"bisagra": "inicio", "apertura_deg": 80 if m["lado_exterior"] in ("sur", "este") else -80}

    # La entrada, donde la pide la planta; si nadie la pide, en el estar.
    acceso_puesto = False
    pide_acceso = [r for r in rects if r.acceso]
    for r in pide_acceso:
        for _, _, m, t0, t1 in spans({r.id}):
            if m["lado_exterior"] != r.acceso.lado or acceso_puesto:
                continue
            centro = r.acceso.centro_m - inicio_de[m["id"]] if r.acceso.centro_m is not None else (t0 + t1) / 2
            acceso_puesto = colocar(m, "puerta_090", centro=centro, hoja=hoja_hacia_adentro(m))

    def entra(codigo: str, tramo: float) -> bool:
        return item_catalogo(codigo)["ancho_m"] + 0.4 <= tramo

    for gid, rs in grupos.items():
        uso = usos[gid]
        opciones = ventanas.get(uso)
        disponibles = spans({r.id for r in rs})
        if uso == "social" and not acceso_puesto and not pide_acceso and disponibles:
            # El acceso va del lado opuesto al sol cuando se puede: la fachada asoleada queda para el estar.
            for _, _, m, t0, t1 in sorted(disponibles, key=lambda s: (-s[0], s[1])):
                if t1 - t0 >= 1.5 and colocar(m, "puerta_090", desde=t0 + 0.3, hoja=hoja_hacia_adentro(m)):
                    acceso_puesto = True
                    break
        if not opciones or not disponibles:
            continue
        puesta = False
        if uso == "social":
            # Hacia el sol, puertas-ventana (dos si el frente es largo); en las otras fachadas,
            # una ventana por tramo donde entra: el estar ventila cruzado.
            for orden, _, m, t0, t1 in disponibles:
                tramo = t1 - t0
                if orden == 0:
                    centros = [(t0 + t1) / 2] if tramo < 6.0 else [t0 + tramo * 0.27, t0 + tramo * 0.73]
                    for c in centros:
                        for codigo in opciones:
                            if entra(codigo, tramo / len(centros)) and colocar(m, codigo, centro=c):
                                puesta = True
                                break
                else:
                    for codigo in ("ventana_150_110", "ventana_100_110"):
                        if entra(codigo, tramo) and colocar(m, codigo, centro=(t0 + t1) / 2):
                            puesta = True
                            break
        else:
            for _, _, m, t0, t1 in disponibles:
                for codigo in opciones:
                    if entra(codigo, t1 - t0) and colocar(m, codigo, centro=(t0 + t1) / 2):
                        puesta = True
                        break
                if puesta:
                    break
        if not puesta and uso in ("dormitorio", "social", "oficina"):
            advertencias.append(f"«{_nombre_de_grupo(rs[0])}» no tiene muro exterior con lugar para una ventana.")
    if not acceso_puesto:
        advertencias.append("No se encontró dónde poner la puerta de acceso; agregala desde el editor.")

    for m in muros:
        m["aberturas"].sort(key=lambda o: o["posicion_m"])
        for i, o in enumerate(m["aberturas"]):
            o["id"] = f"{m['id']}/O{i}"

    # 4. Ambientes con contorno interior (cara del muro) y huella exterior.
    ambientes = []
    for gid, rs in grupos.items():
        ids = {r.id for r in rs}
        contorno = _contorno_interior(rs[0], muros) if len(rs) == 1 else _contorno_de_grupo(grilla, ids, muros)
        ambientes.append({
            "id": gid,
            "nombre": _nombre_de_grupo(rs[0]),
            "uso": usos[gid],
            "contorno_m": contorno,
            "estado": estado.value,
        })

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


def _retiro(muros: list[dict], ori: str, fijo: float, a: float, b: float) -> float:
    """Medio espesor del muro más grueso que corre sobre el borde (ori, fijo) entre a y b."""
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


def _contorno_interior(r: Rectangulo, muros: list[dict]) -> list[list[float]]:
    """Retira cada lado del rectángulo medio espesor del muro que tiene encima."""
    x0 = r.x0 + _retiro(muros, "v", r.x0, r.y0, r.y1)
    x1 = r.x1 - _retiro(muros, "v", r.x1, r.y0, r.y1)
    y0 = r.y0 + _retiro(muros, "h", r.y0, r.x0, r.x1)
    y1 = r.y1 - _retiro(muros, "h", r.y1, r.x0, r.x1)
    return [[round(x0, 3), round(y0, 3)], [round(x1, 3), round(y0, 3)], [round(x1, 3), round(y1, 3)], [round(x0, 3), round(y1, 3)]]


def _lazo(grilla: _Grilla, dentro) -> list[tuple[float, float]]:
    """Borde de las celdas que cumplen `dentro`, recorrido con el interior a la
    izquierda y sin vértices colineales."""
    siguiente: dict[tuple[float, float], tuple[float, float]] = {}
    for ori, fijo, t0, t1, a, b in grilla.segmentos():
        da, db = a is not None and dentro(a), b is not None and dentro(b)
        if da == db:
            continue
        if ori == "v":
            p, q = ((fijo, t1), (fijo, t0)) if not da else ((fijo, t0), (fijo, t1))
        else:
            p, q = ((t0, fijo), (t1, fijo)) if not da else ((t1, fijo), (t0, fijo))
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
    limpio = []
    n = len(lazo)
    for i in range(n):
        a, b, c = lazo[i - 1], lazo[i], lazo[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            limpio.append(b)
    return limpio


def _desde_suroeste(puntos: list[list[float]]) -> list[list[float]]:
    """Empieza en el vértice suroeste, como Angus Ranch."""
    k = min(range(len(puntos)), key=lambda i: (puntos[i][1] + puntos[i][0], puntos[i][0]))
    return puntos[k:] + puntos[:k]


def _contorno_de_grupo(grilla: _Grilla, ids: set[str], muros: list[dict]) -> list[list[float]]:
    """Contorno interior de un ambiente formado por varios rectángulos: su borde,
    con cada lado retirado medio espesor del muro que tiene encima."""
    lazo = _lazo(grilla, lambda c: c in ids)

    def retiro(a, b) -> float:
        if abs(a[0] - b[0]) < 1e-9:
            return _retiro(muros, "v", a[0], *sorted((a[1], b[1])))
        return _retiro(muros, "h", a[1], *sorted((a[0], b[0])))

    salida = []
    n = len(lazo)
    for i in range(n):
        a, b, c = lazo[i - 1], lazo[i], lazo[(i + 1) % n]
        n1, n2 = _normal_derecha(a, b), _normal_derecha(b, c)
        d1, d2 = retiro(a, b), retiro(b, c)
        salida.append([round(b[0] - d1 * n1[0] - d2 * n2[0], 3), round(b[1] - d1 * n1[1] - d2 * n2[1], 3)])
    return _desde_suroeste(salida)


def _huella(grilla: _Grilla) -> list[list[float]]:
    """Contorno exterior de la planta: el borde de las celdas ocupadas, desplazado
    medio espesor de muro exterior hacia afuera."""
    lazo = _lazo(grilla, lambda c: True)
    d = _espesor("exterior") / 2
    salida = []
    n = len(lazo)
    for i in range(n):
        a, b, c = lazo[i - 1], lazo[i], lazo[(i + 1) % n]
        n1 = _normal_derecha(a, b)
        n2 = _normal_derecha(b, c)
        salida.append([_g(b[0] + d * (n1[0] + n2[0])), _g(b[1] + d * (n1[1] + n2[1]))])
    return _desde_suroeste(salida)


def _normal_derecha(a, b) -> tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1.0
    return (dy / l, -dx / l)
