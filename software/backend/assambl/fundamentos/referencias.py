"""Plantas de referencia convertidas en alternativas para un programa.

Las diez plantas de `docs/interior_fundamentals/` están transcriptas en
`plantas_referencia.json` como rectángulos. Para ofrecerlas a un usuario:

1. se eligen las que tienen los dormitorios pedidos (o uno más, que pasa a ser
   oficina o cuarto de huéspedes);
2. se ajustan: se quita el garage o la galería si no se pidieron y se escala la
   planta hacia la superficie objetivo, sin achicar más de 7 % ni agrandar más de 12 % para no deformar
   pasillos y dormitorios;
3. se renombran los ambientes con los nombres del programa;
4. se prueban los ocho giros y espejados y se queda la orientación que mejor
   pone el estar y los dormitorios al sol;
5. se evalúan con los fundamentos y se ordenan por parecido al programa y por
   puntaje.

Cada alternativa dice de qué planta sale y qué se le cambió: son puntos de
partida para editar, no respuestas cerradas.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from ..modelo.casa import Programa, Rectangulo
from ..modelo.estados import Estado
from . import evaluar

RUTA = Path(__file__).with_name("plantas_referencia.json")
ESCALA_MIN, ESCALA_MAX = 0.93, 1.12

RASGOS = {
    "sin_pasillo": "Sin pasillo: los ambientes se recorren a través del estar",
    "hall_central": "Hall central que reparte a todos los ambientes",
    "social_integrado": "Estar, comedor y cocina integrados",
    "social_en_extremo": "Zona social en un extremo, lejos de los dormitorios",
    "nucleo_humedo_agrupado": "Baños, cocina y lavadero agrupados",
    "lavadero_en_cocina": "Lavadero junto a la cocina",
    "lavadero_con_salida": "Lavadero con salida al exterior",
    "acceso_por_cocina": "Se entra por la cocina",
    "toilette_separado": "Toilette para visitas",
    "vestidor_principal": "Vestidor en el dormitorio principal",
    "suite_principal": "Dormitorio principal en suite",
    "suite_aislada": "Suite aislada del resto",
    "dormitorios_agrupados": "Dormitorios agrupados",
    "dormitorios_divididos": "Planta dividida: el principal lejos de los demás",
    "dormitorios_en_fila": "Dormitorios en fila sobre una fachada",
    "galeria_integrada": "Galería integrada a la planta",
    "entrada_con_recibidor": "Recibidor de entrada",
    "entrada_en_angulo": "Entrada en el ángulo entre dos alas",
    "garage_como_colchon": "Garage como colchón entre la calle y la casa",
    "pasillo_central": "Pasillo central con dormitorios a ambos lados",
    "forma_l": "Planta en L que arma un patio",
    "estar_pabellon": "Estar como pabellón con tres fachadas",
    "dos_alas": "Dos alas: social y privada",
    "oficina": "Oficina como bisagra entre alas",
    "deposito": "Depósito o despensa",
}


@lru_cache(maxsize=1)
def cargar() -> dict:
    return json.loads(RUTA.read_text(encoding="utf-8"))


def rectangulos(planta: dict) -> list[Rectangulo]:
    return [Rectangulo(id=a[0], nombre=a[1], uso=a[2], x0=a[3], y0=a[4], x1=a[5], y1=a[6], **a[7])
            for a in planta["ambientes"]]


def resumen_referencias() -> list[dict]:
    """Las plantas de referencia para mostrar como galería (sin la geometría)."""
    return [{k: p[k] for k in ("id", "nombre", "archivo", "superficie_m2", "dormitorios", "banos", "garage", "forma",
                               "rasgos", "lectura")} | {"rasgos_texto": [RASGOS.get(r, r) for r in p["rasgos"]]}
            for p in cargar()["plantas"]]


# ---------------------------------------------------------------- geometría

def _g(v: float) -> float:
    return round(round(v / 0.05) * 0.05, 2)


def _transformar(rects: list[Rectangulo], giro: int, espejo: bool, escala: float = 1.0) -> list[Rectangulo]:
    """Gira de a 90° (antihorario), espeja en x y escala; la planta queda con su esquina en (0, 0)."""
    def punto(x: float, y: float) -> tuple[float, float]:
        if espejo:
            x = -x
        for _ in range(giro % 4):
            x, y = -y, x
        return x * escala, y * escala

    salida = []
    for r in rects:
        (ax, ay), (bx, by) = punto(r.x0, r.y0), punto(r.x1, r.y1)
        salida.append(r.model_copy(update={"x0": min(ax, bx), "y0": min(ay, by), "x1": max(ax, bx), "y1": max(ay, by)}))
    dx = min(r.x0 for r in salida)
    dy = min(r.y0 for r in salida)
    return [r.model_copy(update={"x0": _g(r.x0 - dx), "y0": _g(r.y0 - dy), "x1": _g(r.x1 - dx), "y1": _g(r.y1 - dy)})
            for r in salida]


def _area(rs: list[Rectangulo]) -> float:
    return sum((r.x1 - r.x0) * (r.y1 - r.y0) for r in rs)


def _entidades(rects: list[Rectangulo], uso: str) -> list[list[Rectangulo]]:
    grupos: dict[str, list[Rectangulo]] = {}
    for r in rects:
        grupos.setdefault(r.grupo or r.id, []).append(r)
    return [rs for rs in grupos.values() if max(rs, key=lambda q: (q.x1 - q.x0) * (q.y1 - q.y0)).uso == uso]


# ---------------------------------------------------------------- adaptación

def _pedido(programa: Programa) -> dict:
    usos = [a.uso for a in programa.ambientes]
    return {
        "dormitorios": [a for a in programa.ambientes if a.uso == "dormitorio"],
        "banos": usos.count("bano"),
        "oficinas": [a for a in programa.ambientes if a.uso == "oficina"],
        "garage": programa.garage if programa.garage is not None else ("garage" in usos or None),
        "galeria": programa.galeria if programa.galeria is not None else ("galeria" in usos or None),
    }


def adaptar(planta: dict, programa: Programa) -> tuple[list[Rectangulo], list[str], float] | None:
    """(rectángulos, cambios hechos, parecido 0–1) o None si la planta no sirve para el programa."""
    pedido = _pedido(programa)
    n_dorm = len(pedido["dormitorios"])
    rects = rectangulos(planta)
    cambios: list[str] = []
    parecido = 1.0

    dorms = sorted(_entidades(rects, "dormitorio"), key=lambda rs: (not rs[0].id.startswith("dorm_principal"), -_area(rs)))
    sobran = len(dorms) - n_dorm
    admite = 1 + (1 if pedido["oficinas"] and not _entidades(rects, "oficina") else 0)
    if n_dorm == 0 or sobran < 0 or sobran > admite:
        return None

    # Dormitorios: el principal del programa al principal de la planta, los demás por tamaño.
    del_programa = sorted(pedido["dormitorios"], key=lambda a: (not a.principal, -(a.area_m2 or 0)))
    renombre: dict[int, tuple[str, str]] = {}
    for rs, amb in zip(dorms, del_programa):
        for r in rs:
            renombre[id(r)] = (amb.nombre, "dormitorio")
    oficinas = list(pedido["oficinas"])
    for rs in sorted(dorms[n_dorm:], key=_area):
        if oficinas:
            nombre = oficinas.pop(0).nombre
            cambios.append(f"Un dormitorio de la planta original ({_area(rs):.0f} m²) pasa a ser «{nombre}».")
            parecido -= 0.05
        else:
            nombre = "Oficina o cuarto de huéspedes"
            cambios.append(f"La planta original tiene un dormitorio más: queda como «{nombre}» ({_area(rs):.0f} m²).")
            parecido -= 0.2
        for r in rs:
            renombre[id(r)] = (nombre, "oficina")
    for amb in oficinas:
        if not _entidades(rects, "oficina"):
            cambios.append(f"No tiene lugar para «{amb.nombre}»: habría que sumarlo en el editor o usar un rincón del estar.")
            parecido -= 0.12
    rects = [r.model_copy(update={"nombre": renombre[id(r)][0], "uso": renombre[id(r)][1]}) if id(r) in renombre else r
             for r in rects]

    # Garage y galería.
    tiene_garage = any(r.uso == "garage" for r in rects)
    if tiene_garage and pedido["garage"] is not True:
        rects = [r for r in rects if r.uso != "garage"]
        cambios.append("Se quitó el garage de la planta original; el lado donde estaba queda como fachada."
                       if pedido["garage"] is False else
                       "Se quitó el garage (no lo pediste): si lo querés, está en la planta original.")
        parecido -= 0.1 if pedido["garage"] is False else 0.15
    elif not tiene_garage and pedido["garage"]:
        cambios.append("No tiene garage: se puede sumar pegado a la cocina o al lavadero, como colchón hacia la calle.")
        parecido -= 0.45
    tiene_galeria = any(r.uso == "galeria" for r in rects)
    if tiene_galeria and pedido["galeria"] is False:
        rects = [r for r in rects if r.uso != "galeria"]
        cambios.append("Se quitó la galería.")
    elif not tiene_galeria and pedido["galeria"]:
        cambios.append("No tiene galería: se suma sobre la fachada del estar en el editor.")
        parecido -= 0.05

    # Baños.
    banos_ref = len(_entidades(rects, "bano"))
    if pedido["banos"] and banos_ref != pedido["banos"]:
        cambios.append(f"Tiene {banos_ref} baño{'s' if banos_ref != 1 else ''} completo{'s' if banos_ref != 1 else ''} "
                       f"y pediste {pedido['banos']}.")
        parecido -= 0.08 * abs(banos_ref - pedido["banos"])

    # Preferencias.
    rasgos = set(planta["rasgos"])
    if programa.dormitorios == "divididos":
        parecido += 0.12 if rasgos & {"dormitorios_divididos", "suite_aislada", "dos_alas"} else -0.12
    elif programa.dormitorios == "juntos":
        parecido += -0.12 if rasgos & {"dormitorios_divididos", "suite_aislada", "dos_alas"} else 0.05
    if programa.entrada == "recibidor":
        parecido += 0.1 if rasgos & {"entrada_con_recibidor", "hall_central", "entrada_en_angulo"} else -0.1
    elif programa.entrada == "directa":
        parecido += 0.1 if rasgos & {"sin_pasillo", "acceso_por_cocina"} else -0.05

    # Superficie.
    objetivo = programa.superficie_objetivo_m2
    if objetivo:
        cubierta = sum((r.x1 - r.x0) * (r.y1 - r.y0) for r in rects if r.uso not in ("garage", "galeria")) / 0.9
        relacion = objetivo / cubierta
        escala = min(ESCALA_MAX, max(ESCALA_MIN, math.sqrt(relacion)))
        if abs(escala - 1) > 0.015:
            rects = _transformar(rects, 0, False, escala)
            cambios.append(f"Escalada {'+' if escala > 1 else '−'}{abs(escala - 1) * 100:.0f} % en cada lado "
                           f"para acercarse a los {objetivo:.0f} m² que buscás.")
        fuera = relacion / escala ** 2
        if fuera < 0.85 or fuera > 1.18:
            parecido -= min(0.35, abs(math.log(fuera)))
    return rects, cambios, max(0.0, min(1.0, parecido))


def orientar(rects: list[Rectangulo], lat: float | None, estado: Estado,
             origen: dict) -> tuple[list[Rectangulo], dict, list[str], dict, str | None]:
    """Prueba los ocho giros y espejados; devuelve el que mejor evalúa (sobre todo por sol)."""
    from ..capas.casa import planta_desde_rectangulos

    mejor = None
    for espejo in (False, True):
        for giro in range(4):
            rs = _transformar(rects, giro, espejo)
            casa, adv = planta_desde_rectangulos(rs, estado=estado, lat=lat, origen=origen)
            ev = evaluar.evaluar(casa, lat)
            luz = next(c["puntaje"] for c in ev["criterios"] if c["id"] == "luz") or 0
            clave = (round(ev["puntaje"] or 0, 3) + 0.5 * luz, -giro, not espejo)
            if mejor is None or clave > mejor[0]:
                mejor = (clave, rs, casa, adv, ev, giro, espejo)
    _, rs, casa, adv, ev, giro, espejo = mejor
    sol = "sur" if lat is not None and lat > 0 else "norte"
    if giro or espejo:
        nota = (f"{'Girada' if giro else ''}{' y ' if giro and espejo else ''}{'espejada' if espejo else ''}"
                f" respecto del dibujo original para poner el estar y los dormitorios al {sol}.").capitalize()
    else:
        nota = None
    return rs, casa, adv, ev, nota


def alternativas(programa: Programa, lat: float | None = None, estado: Estado = Estado.PROPUESTO,
                 cantidad: int = 3) -> list[dict]:
    """Las plantas de referencia que mejor se adaptan al programa, ya adaptadas y evaluadas."""
    candidatas = []
    for planta in cargar()["plantas"]:
        res = adaptar(planta, programa)
        if res:
            candidatas.append((planta, *res))
    # Primero las más parecidas; se orientan y evalúan solo las que pueden entrar.
    candidatas.sort(key=lambda c: -c[3])
    salida = []
    for planta, rects, cambios, parecido in candidatas[: cantidad + 3]:
        origen = {"fuente": "assambl/fundamentos/plantas_referencia.json", "referencia": planta["id"],
                  "archivo": planta["archivo"], "nota": f"Adaptada de «{planta['nombre']}»."}
        rects, casa, adv, ev, nota = orientar(rects, lat, estado, origen)
        salida.append({
            "id": planta["id"],
            "nombre": planta["nombre"],
            "descripcion": planta["lectura"],
            "rectangulos": [r.model_dump() for r in rects],
            "casa": casa,
            "advertencias": adv,
            "origen": {"tipo": "referencia", "id": planta["id"], "archivo": planta["archivo"],
                       "superficie_m2": planta["superficie_m2"],
                       "rasgos": [RASGOS.get(r, r) for r in planta["rasgos"]]},
            "adaptacion": cambios + ([nota] if nota else []),
            "parecido": round(parecido, 2),
            "evaluacion": ev,
            "_orden": 0.55 * parecido + 0.45 * (ev["puntaje"] or 0) - 0.05 * len(adv),
        })
    salida.sort(key=lambda a: -a["_orden"])
    for a in salida:
        a.pop("_orden")
    return salida[:cantidad]
