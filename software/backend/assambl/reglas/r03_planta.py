"""R03 · Reglas de la planta (capa 03, MVP_01 §2 y §3.3).

Revisan la planta tal como la dibuja el usuario —muros por eje, aberturas y
ambientes— antes de que exista el entramado. Cada verificación nombra las piezas
a las que se aplica, y el estado de cada pieza es el peor de los que recibe.
Así la interfaz puede pintar el muro, la ventana o el ambiente que tiene el
problema, no solo listarlo.

Además de las piezas se mira la casa entera (R03.11 en adelante): que tenga un
baño al que se llegue sin pasar por un dormitorio, dónde dormir, dónde cocinar y
por dónde entrar. Eso es **grave**: la interfaz lo avisa antes que todo lo demás.
En el otro extremo están las **sugerencias**, como un espacio que quedó sin uso:
no son errores, son algo para mirar.

Los umbrales son de partida y se ajustan por proyecto (MVP_01 §3.3: «deben
ratificarse con el especialista»). Ninguno codifica normativa municipal.
"""

from __future__ import annotations

import math

from ..geometria import poligono
from ..modelo.estados import Estado
from . import Verificacion

VERSION = "0.1"
ORIGEN = "MVP_01 §2 (dominio) y §3.3 (aberturas y headers)"

PARAMETROS = {
    "superficie_min_m2": 40.0,
    "superficie_max_m2": 200.0,
    "holgura_vano_m": 0.015,        # por lado: rough opening = nominal + 2 × holgura
    "header_2x6_hasta_m": 1.20,
    "header_2x8_hasta_m": 1.80,
    "header_2x10_hasta_m": 2.40,
    "margen_extremo_m": 0.10,       # abertura a menos de esto del extremo del eje: no entra el king
    "separacion_aberturas_m": 0.10,
    "dormitorio_min_m2": 7.5,
    "dormitorio_lado_min_m": 2.4,
    "bano_min_m2": 2.4,
    "tolerancia_orto_deg": 0.5,
    "altura_puerta_min_m": 2.0,
    "ambientes_para_mirar_la_casa": 3,  # con menos, la planta recién empieza: no se le pide baño todavía
    "espacio_libre_min_m2": 3.0,
    "espacio_libre_lado_min_m": 0.45,   # más angosto que esto es el espesor de un muro, no un espacio
}

# Orden de gravedad para combinar estados sobre una misma pieza.
_GRAVEDAD = {
    Estado.COMPROBADO_POR_REGLAS: 0,
    Estado.PROPUESTO: 1,
    Estado.PENDIENTE_REVISION: 2,
    Estado.PENDIENTE_DATOS: 3,
    Estado.PENDIENTE_CALCULO: 4,
}

HABITABLES = ("dormitorio", "social", "oficina")


def _largo(m: dict) -> float:
    (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
    return math.hypot(x1 - x0, y1 - y0)


def _v(id_: str, descripcion: str, estado: Estado, detalle: str = "", piezas: list[str] | None = None,
       parametros: dict | None = None) -> dict:
    d = Verificacion(id=id_, version=VERSION, origen=ORIGEN, descripcion=descripcion, estado=estado,
                     detalle=detalle, parametros=parametros or {}).como_dict()
    d["piezas"] = piezas or []
    return d


def _header(luz: float, p: dict) -> str | None:
    if luz <= p["header_2x6_hasta_m"]:
        return "2 × 6"
    if luz <= p["header_2x8_hasta_m"]:
        return "2 × 8"
    if luz <= p["header_2x10_hasta_m"]:
        return "2 × 10"
    return None


def _toca(ambiente: list, muro: dict, tolerancia: float = 0.16) -> float:
    """Largo del muro que corre junto a un lado del contorno del ambiente."""
    (x0, y0), (x1, y1) = muro["eje"]["desde_m"], muro["eje"]["hasta_m"]
    total = 0.0
    n = len(ambiente)
    for i in range(n):
        (ax, ay), (bx, by) = ambiente[i], ambiente[(i + 1) % n]
        if abs(y0 - y1) < 1e-6 and abs(ay - by) < 1e-6 and abs(ay - y0) <= tolerancia:
            lo, hi = sorted((x0, x1))
            a, b = sorted((ax, bx))
            total += max(0.0, min(hi, b) - max(lo, a))
        elif abs(x0 - x1) < 1e-6 and abs(ax - bx) < 1e-6 and abs(ax - x0) <= tolerancia:
            lo, hi = sorted((y0, y1))
            a, b = sorted((ay, by))
            total += max(0.0, min(hi, b) - max(lo, a))
    return total


def _vecinos_por_muro(amb: dict, muro: dict, ambientes: list[dict]) -> list[dict]:
    """Ambientes que están del otro lado de un muro que toca a `amb`."""
    return [o for o in ambientes
            if o["id"] != amb["id"] and o.get("contorno_m") and _toca(o["contorno_m"], muro) > 0.3]


def _es_en_suite(bano: dict, muros: list[dict], ambientes: list[dict]) -> bool:
    """Un baño es en suite si todas sus puertas dan a un dormitorio o a su vestidor.
    Si no tiene puertas, o no se sabe a dónde dan, no se lo cuenta como en suite."""
    destinos: list[str] = []
    for m in muros:
        if _toca(bano["contorno_m"], m) <= 0.3:
            continue
        if not any(o.get("tipo") in ("puerta", "paso") for o in m.get("aberturas") or []):
            continue
        otros = _vecinos_por_muro(bano, m, ambientes)
        if not otros:
            return False
        destinos += [o.get("uso") for o in otros]
    return bool(destinos) and all(u in ("dormitorio", "vestidor") for u in destinos)


def _espacios_libres(casa: dict, p: dict) -> list[dict]:
    """Zonas dentro de la huella que no pertenecen a ningún ambiente. Se buscan
    sobre la grilla que forman las coordenadas de la huella y de los contornos."""
    huella = [tuple(v) for v in casa.get("huella_m") or []]
    contornos = [[tuple(v) for v in a["contorno_m"]] for a in casa.get("ambientes") or []
                 if a.get("contorno_m") and len(a["contorno_m"]) >= 3]
    if len(huella) < 3 or not contornos:
        return []
    xs = sorted({round(v[0], 3) for c in contornos + [huella] for v in c})
    ys = sorted({round(v[1], 3) for c in contornos + [huella] for v in c})
    libres: set[tuple[int, int]] = set()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if min(xs[i + 1] - xs[i], ys[j + 1] - ys[j]) < p["espacio_libre_lado_min_m"]:
                continue
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if poligono.contiene(huella, cx, cy) and not any(poligono.contiene(c, cx, cy) for c in contornos):
                libres.add((i, j))
    zonas = []
    while libres:
        pila, zona = [libres.pop()], []
        while pila:
            i, j = pila.pop()
            zona.append((i, j))
            for v in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if v in libres:
                    libres.remove(v)
                    pila.append(v)
        area = sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i, j in zona)
        if area >= p["espacio_libre_min_m2"]:
            x0, x1 = min(xs[i] for i, _ in zona), max(xs[i + 1] for i, _ in zona)
            y0, y1 = min(ys[j] for _, j in zona), max(ys[j + 1] for _, j in zona)
            zonas.append({"area_m2": round(area, 1), "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                          "rectangular": abs(area - (x1 - x0) * (y1 - y0)) < 0.05})
    return sorted(zonas, key=lambda z: -z["area_m2"])


def _mirar_la_casa(casa: dict, p: dict) -> list[dict]:
    """R03.11–R03.15: lo que se ve mirando la casa entera y no pieza por pieza."""
    muros: list[dict] = casa.get("muros") or []
    ambientes: list[dict] = casa.get("ambientes") or []
    vs: list[dict] = []
    if len(ambientes) < p["ambientes_para_mirar_la_casa"]:
        return vs

    def grave(id_: str, descripcion: str, ok: bool, detalle: str, piezas: list[str] | None = None) -> None:
        v = _v(id_, descripcion, Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_DATOS, "" if ok else detalle,
               [] if ok else piezas)
        v["gravedad"] = "grave"
        vs.append(v)

    banos = [a for a in ambientes if a.get("uso") == "bano"]
    con_contorno = [b for b in banos if b.get("contorno_m")]
    generales = [b for b in banos if not b.get("contorno_m") or not _es_en_suite(b, muros, ambientes)]
    if not banos:
        detalle = "La casa no tiene ningún baño."
    elif len(banos) == 1:
        detalle = (f"El único baño («{banos[0].get('nombre', banos[0]['id'])}») es en suite: para usarlo hay que pasar "
                   "por un dormitorio. Falta un baño para el resto de la casa y las visitas.")
    else:
        detalle = "Todos los baños son en suite: para usarlos hay que pasar por un dormitorio."
    grave("R03.11", "La casa tiene un baño al que se llega sin pasar por un dormitorio", bool(generales), detalle,
          [b["id"] for b in con_contorno])

    usos = [a.get("uso") for a in ambientes]
    grave("R03.12", "La casa tiene al menos un dormitorio", "dormitorio" in usos, "La casa no tiene ningún dormitorio.")
    sociales = [a for a in ambientes if a.get("uso") == "social"]
    con_cocina = "cocina" in usos or any("cocina" in (a.get("nombre") or "").lower() for a in sociales)
    grave("R03.13", "La casa tiene dónde estar y dónde cocinar", bool(sociales) and con_cocina,
          "La casa no tiene estar." if not sociales else
          "La casa no tiene cocina. Si está integrada al estar, nombralo «Estar y cocina».",
          [a["id"] for a in sociales])
    entrada = any(o.get("tipo") == "puerta" for m in muros if m.get("sistema") == "exterior" for o in m.get("aberturas") or [])
    grave("R03.14", "Se puede entrar a la casa", entrada, "Ningún muro exterior tiene una puerta: no hay por dónde entrar.")

    for z in _espacios_libres(casa, p):
        v = _v("R03.15", "No quedan espacios sin uso dentro de la casa", Estado.PROPUESTO,
               f"Hay unos {z['area_m2']:.0f} m² dentro de la casa que no son de ningún ambiente "
               f"({z['x1'] - z['x0']:.1f} × {z['y1'] - z['y0']:.1f} m). Se pueden sumar a un ambiente vecino o "
               "darles un uso propio.", parametros=z)
        v["gravedad"] = "sugerencia"
        vs.append(v)
    return vs


def analizar_planta(casa: dict, parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    muros: list[dict] = casa.get("muros") or []
    ambientes: list[dict] = casa.get("ambientes") or []
    vs: list[dict] = []

    if not muros:
        vs.append(_v("R03.00", "La planta tiene muros", Estado.PENDIENTE_DATOS, "Todavía no hay muros."))

    # R03.01 · Planta ortogonal (dominio MVP_01).
    oblicuos = []
    for m in muros:
        (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0)) % 90
        if min(ang, 90 - ang) > p["tolerancia_orto_deg"]:
            oblicuos.append(m["id"])
    vs.append(_v("R03.01", "Muros a 90° (planta ortogonal del MVP_01)",
                 Estado.PENDIENTE_REVISION if oblicuos else Estado.COMPROBADO_POR_REGLAS,
                 f"Muros fuera de escuadra: {', '.join(oblicuos)}" if oblicuos else "", oblicuos))

    # R03.02 · Superficie cubierta en el dominio.
    huella = casa.get("huella_m") or []
    if len(huella) >= 3:
        sup = poligono.area([tuple(v) for v in huella])
        ok = p["superficie_min_m2"] <= sup <= p["superficie_max_m2"]
        vs.append(_v("R03.02", f"Superficie cubierta entre {p['superficie_min_m2']:.0f} y {p['superficie_max_m2']:.0f} m²",
                     Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_REVISION,
                     "" if ok else f"{sup:.1f} m² queda fuera del dominio del MVP_01; requiere revisión estructural.",
                     parametros={"superficie_m2": round(sup, 1)}))

    # R03.03 · Muros sin largo o duplicados.
    cortos = [m["id"] for m in muros if _largo(m) < 0.3]
    if cortos:
        vs.append(_v("R03.03", "Ningún muro menor a 30 cm", Estado.PENDIENTE_REVISION,
                     f"Probable error de dibujo: {', '.join(cortos)}", cortos))

    # R03.04 · Aberturas dentro del muro y sin superponerse.
    # R03.05 · Header según la luz del vano en bruto.
    for m in muros:
        largo = _largo(m)
        abs_ = sorted(m.get("aberturas") or [], key=lambda o: o.get("posicion_m", 0))
        for o in abs_:
            ini, fin = o["posicion_m"], o["posicion_m"] + o["ancho_m"]
            dentro = ini >= p["margen_extremo_m"] - 1e-6 and fin <= largo - p["margen_extremo_m"] + 1e-6
            vs.append(_v("R03.04", "La abertura entra en su muro con lugar para el montante king",
                         Estado.COMPROBADO_POR_REGLAS if dentro else Estado.PENDIENTE_REVISION,
                         "" if dentro else f"{o['id']} se sale del muro {m['id']} ({largo:.2f} m) o queda pegada al extremo.",
                         [o["id"]]))
            if o.get("tipo") == "paso" and m.get("sistema") == "tabique":
                continue
            luz = o["ancho_m"] + 2 * p["holgura_vano_m"]
            h = _header(luz, p)
            vs.append(_v("R03.05", "Header dimensionado por tabla según la luz",
                         Estado.COMPROBADO_POR_REGLAS if h else Estado.PENDIENTE_CALCULO,
                         f"Luz {luz:.2f} m → header {h}." if h else
                         f"Luz {luz:.2f} m supera los {p['header_2x10_hasta_m']:.2f} m de la tabla: el header necesita cálculo (LVL o viga compuesta).",
                         [o["id"]], {"luz_m": round(luz, 3)}))
            if o.get("tipo") in ("puerta", "paso") and o.get("dintel_m", 2.05) < p["altura_puerta_min_m"]:
                vs.append(_v("R03.06", f"Puertas de al menos {p['altura_puerta_min_m']:.2f} m de alto",
                             Estado.PENDIENTE_REVISION, f"{o['id']}: dintel a {o['dintel_m']:.2f} m.", [o["id"]]))
        for a, b in zip(abs_, abs_[1:]):
            if a["posicion_m"] + a["ancho_m"] + p["separacion_aberturas_m"] > b["posicion_m"] + 1e-6:
                vs.append(_v("R03.04", "Las aberturas de un muro no se superponen", Estado.PENDIENTE_REVISION,
                             f"{a['id']} y {b['id']} se pisan o no dejan lugar para los montantes.", [a["id"], b["id"]]))

    # R03.07–R03.10 · Ambientes.
    for amb in ambientes:
        cont = amb.get("contorno_m")
        if not cont or len(cont) < 3:
            vs.append(_v("R03.07", "El ambiente tiene contorno", Estado.PENDIENTE_DATOS,
                         f"«{amb.get('nombre', amb['id'])}» no tiene contorno dibujado.", [amb["id"]]))
            continue
        area = poligono.area([tuple(v) for v in cont])
        xs, ys = [v[0] for v in cont], [v[1] for v in cont]
        lado_min = min(max(xs) - min(xs), max(ys) - min(ys))
        uso = amb.get("uso")
        if uso == "dormitorio":
            ok = area >= p["dormitorio_min_m2"] and lado_min >= p["dormitorio_lado_min_m"]
            vs.append(_v("R03.08", f"Dormitorio de al menos {p['dormitorio_min_m2']} m² y {p['dormitorio_lado_min_m']} m de lado",
                         Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_REVISION,
                         "" if ok else f"«{amb['nombre']}»: {area:.1f} m², lado menor {lado_min:.2f} m.", [amb["id"]]))
        elif uso == "bano":
            ok = area >= p["bano_min_m2"]
            vs.append(_v("R03.08", f"Baño de al menos {p['bano_min_m2']} m²",
                         Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_REVISION,
                         "" if ok else f"«{amb['nombre']}»: {area:.1f} m².", [amb["id"]]))

        vecinos = [m for m in muros if _toca(cont, m) > 0.3]
        if uso in HABITABLES:
            con_ventana = any(o.get("tipo") in ("ventana", "ventana_corrediza")
                              for m in vecinos if m.get("sistema") == "exterior" for o in m.get("aberturas") or [])
            vs.append(_v("R03.09", "Los ambientes habitables tienen ventana al exterior",
                         Estado.COMPROBADO_POR_REGLAS if con_ventana else Estado.PENDIENTE_DATOS,
                         "" if con_ventana else f"«{amb['nombre']}» no tiene ventana en un muro exterior.", [amb["id"]]))
        if uso not in ("social", "circulacion"):
            con_puerta = any(o.get("tipo") in ("puerta", "paso", "ventana_corrediza")
                             for m in vecinos for o in m.get("aberturas") or [])
            # Un ambiente que no está cerrado por muros en todo su perímetro se abre a otro.
            cubierto = sum(_toca(cont, m) for m in vecinos)
            abierto = cubierto < 0.85 * poligono.perimetro([tuple(v) for v in cont])
            vs.append(_v("R03.10", "Cada ambiente tiene por dónde entrar",
                         Estado.COMPROBADO_POR_REGLAS if con_puerta or abierto else Estado.PENDIENTE_DATOS,
                         "" if con_puerta or abierto else f"«{amb['nombre']}» no tiene puerta ni paso.", [amb["id"]]))

    vs += _mirar_la_casa(casa, p)

    # Estado por pieza: el peor de los que recibe; sin verificaciones, propuesto.
    por_pieza: dict[str, str] = {}
    for v in vs:
        e = Estado(v["estado"])
        for pid in v["piezas"]:
            actual = por_pieza.get(pid)
            if actual is None or _GRAVEDAD[e] > _GRAVEDAD[Estado(actual)]:
                por_pieza[pid] = e.value
    # Lo que ninguna regla objetó y tiene su geometría completa queda comprobado.
    for amb in ambientes:
        if amb["id"] not in por_pieza and amb.get("contorno_m"):
            por_pieza[amb["id"]] = Estado.COMPROBADO_POR_REGLAS.value
    for m in muros:
        if m["id"] not in por_pieza:
            por_pieza[m["id"]] = Estado.COMPROBADO_POR_REGLAS.value if not oblicuos or m["id"] not in oblicuos else Estado.PENDIENTE_REVISION.value

    peor = max((Estado(v["estado"]) for v in vs), key=lambda e: _GRAVEDAD[e], default=Estado.PENDIENTE_DATOS)
    resumen: dict[str, int] = {}
    for v in vs:
        if v["estado"] != Estado.COMPROBADO_POR_REGLAS.value:
            resumen[v["estado"]] = resumen.get(v["estado"], 0) + 1
    return {"estado": peor.value, "verificaciones": vs, "por_pieza": por_pieza, "resumen": resumen,
            "version": VERSION}
