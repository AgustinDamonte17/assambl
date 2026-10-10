"""RI · Reglas del interior: muebles, artefactos y galería.

Se aplican sobre la planta amoblada, junto con las R03. Igual que aquellas, nombran
las piezas a las que se refieren para que la interfaz pinte el mueble que tiene el
problema. Los espacios de uso salen del catálogo (`frente_libre_m`): 70 cm delante del
inodoro, 60 cm delante de los demás artefactos, 90 cm en los pasillos.
"""

from __future__ import annotations

from ..capas import interior as ci
from ..geometria import poligono
from ..modelo.casa import USOS_EXTERIORES
from ..modelo.estados import Estado
from . import Verificacion

VERSION = "0.1"
ORIGEN = "Catálogo de mobiliario (espacios de uso) y reglas de interior de Assambl"

PARAMETROS = {
    "paso_pasillo_min_m": 0.9,
    "galeria_fondo_min_m": 1.8,
    "superposicion_max_m2": 0.01,
}


def _v(id_: str, descripcion: str, estado: Estado, detalle: str = "", piezas: list[str] | None = None) -> dict:
    d = Verificacion(id=id_, version=VERSION, origen=ORIGEN, descripcion=descripcion, estado=estado,
                     detalle=detalle).como_dict()
    d["piezas"] = piezas or []
    return d


def _nombre(p: dict) -> str:
    it = ci.item(p.get("tipo", ""))
    return it["nombre"] if it else str(p.get("tipo", p["id"])).replace("_", " ")


def _se_toleran(a: dict, b: dict) -> bool:
    """Pares que se superponen a propósito: alfombra bajo el estar, sillas bajo la mesa,
    piezas colgadas sobre la mesada, televisor sobre su mueble."""
    fa, fb = ci.forma(a), ci.forma(b)
    if fa in ci.SOBRE_OTRAS or fb in ci.SOBRE_OTRAS:
        return True
    if (fa in ci.ACOMPANAN_MESA and fb in ci.MESAS) or (fb in ci.ACOMPANAN_MESA and fa in ci.MESAS):
        return True
    ia, ib = ci.item(a.get("tipo", "")) or {}, ci.item(b.get("tipo", "")) or {}
    return bool(ia.get("elevacion_m") or ib.get("elevacion_m"))


def verificar(casa: dict, parametros: dict | None = None) -> list[dict]:
    p = {**PARAMETROS, **(parametros or {})}
    vs: list[dict] = []
    ambientes = {a["id"]: a for a in casa.get("ambientes") or []}
    salas = {aid: s for aid, a in ambientes.items() if (s := ci.sala(casa, a))}
    todas = ci.piezas(casa)

    for pieza in todas:
        nombre = _nombre(pieza)
        r = ci.huella(pieza)
        s = salas.get(pieza.get("ambiente") or "")
        if s is None:
            s = next((x for x in salas.values() if ci.dentro(r, x.poly)), None)
        # RI.01 · Dentro de un ambiente.
        if s is None or not ci.dentro(r, s.poly):
            vs.append(_v("RI.01", "Cada pieza queda dentro de su ambiente", Estado.PENDIENTE_REVISION,
                         f"{nombre} ({pieza['id']}) atraviesa un muro o queda fuera del ambiente.", [pieza["id"]]))
            continue
        it = ci.item(pieza.get("tipo", ""))
        # RI.05 · Ambiente adecuado (sanitarios en baños, muebles de galería afuera).
        if it:
            mal = (it.get("usos") and s.uso not in it["usos"]) or \
                  (s.exterior and not it.get("exterior")) or (not s.exterior and not it.get("interior", True))
            if mal:
                vs.append(_v("RI.05", "Cada pieza va en un ambiente adecuado", Estado.PENDIENTE_REVISION,
                             f"{nombre} no va en «{s.nombre}».", [pieza["id"]]))
        # RI.03 · Espacio de uso libre delante.
        # Las piezas exentas (mesas, sillones) reservan su espacio al ubicarse, no hacia un frente.
        z = ci.zona_frente(pieza) if it and it.get("apoyo") != "libre" else None
        if z:
            tapado = [o for o in todas if o["id"] != pieza["id"] and not _se_toleran(pieza, o)
                      and ci.forma(o) not in ci.EN_ZONA_DE_USO and not (ci.item(o.get("tipo", "")) or {}).get("elevacion_m")
                      and ci.cruce(z, ci.huella(o)) > p["superposicion_max_m2"]]
            fuera = not ci.dentro(z, s.poly)
            if tapado or fuera:
                que = f"lo tapa {_nombre(tapado[0]).lower()}" if tapado else "choca con un muro"
                vs.append(_v("RI.03", "Cada pieza tiene su espacio de uso libre", Estado.PENDIENTE_REVISION,
                             f"Delante de {nombre.lower()} hacen falta {it['frente_libre_m'] * 100:.0f} cm y {que}.",
                             [pieza["id"]] + [o["id"] for o in tapado[:1]]))
        # RI.04 · Ninguna pieza bloquea una puerta.
        if not (it and it.get("elevacion_m")) and ci.forma(pieza) not in ci.SOBRE_OTRAS:
            for otra in salas.values():
                if any(ci.cruce(r, zp) > 0.02 for zp in otra.zonas_puerta):
                    vs.append(_v("RI.04", "Las puertas y pasos quedan libres", Estado.PENDIENTE_REVISION,
                                 f"{nombre} está en el barrido de una puerta o en un paso de «{otra.nombre}».", [pieza["id"]]))
                    break

    # RI.02 · Piezas que se pisan.
    for i, a in enumerate(todas):
        ra = ci.huella(a)
        for b in todas[i + 1:]:
            if _se_toleran(a, b):
                continue
            if ci.cruce(ra, ci.huella(b)) > p["superposicion_max_m2"]:
                vs.append(_v("RI.02", "Las piezas no se superponen", Estado.PENDIENTE_REVISION,
                             f"{_nombre(a)} y {_nombre(b).lower()} se pisan.", [a["id"], b["id"]]))

    # RI.06 · Paso libre en pasillos.
    for s in salas.values():
        if s.uso != "circulacion":
            continue
        dentro_ = [x for x in todas if x.get("ambiente") == s.id and not _se_toleran(x, x)]
        if not dentro_:
            continue
        x0, y0, x1, y1 = s.caja
        horizontal = (x1 - x0) >= (y1 - y0)
        ancho = (y1 - y0) if horizontal else (x1 - x0)
        ocupa = max((ci.huella(x)[3] - ci.huella(x)[1]) if horizontal else (ci.huella(x)[2] - ci.huella(x)[0]) for x in dentro_)
        if ancho - ocupa < p["paso_pasillo_min_m"]:
            vs.append(_v("RI.06", f"Los pasillos dejan {p['paso_pasillo_min_m'] * 100:.0f} cm de paso",
                         Estado.PENDIENTE_REVISION, f"En «{s.nombre}» quedan {max(0, ancho - ocupa) * 100:.0f} cm.",
                         [x["id"] for x in dentro_]))

    # RI.07 · Galería usable y pegada a la casa.
    huella_casa = [tuple(v) for v in casa.get("huella_m") or []]
    for s in salas.values():
        if s.uso not in USOS_EXTERIORES:
            continue
        fondo = s.lado_min
        ok = fondo >= p["galeria_fondo_min_m"]
        vs.append(_v("RI.07", f"La galería tiene al menos {p['galeria_fondo_min_m']:.1f} m de fondo",
                     Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_REVISION,
                     "" if ok else f"«{s.nombre}» tiene {fondo:.2f} m: alcanza para pasar, no para una mesa.", [s.id]))
        if len(huella_casa) >= 3:
            x0, y0, x1, y1 = s.caja
            junto = any(poligono.contiene(huella_casa, x, y) for x, y in
                        (((x0 + x1) / 2, y0 - 0.1), ((x0 + x1) / 2, y1 + 0.1), (x0 - 0.1, (y0 + y1) / 2), (x1 + 0.1, (y0 + y1) / 2)))
            if not junto:
                vs.append(_v("RI.07", "La galería está junto a la casa", Estado.PENDIENTE_REVISION,
                             f"«{s.nombre}» no toca ningún muro exterior.", [s.id]))
    return vs
