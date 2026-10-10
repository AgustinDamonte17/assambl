"""La planta base: una casa ordenada para empezar a editar.

Assambl no reparte ambientes al azar ni ofrece varias plantas para elegir: arma
una sola, con un orden que se puede explicar. Ese orden sale de leer cómo está
resuelta Angus Ranch (`casos/angus_ranch.assambl.json`) y quedarse con lo que la
hace funcionar:

1. Una barra alargada de este a oeste, con el frente largo hacia el sol.
2. Estar, comedor y cocina en el centro, de fachada a fachada. No hay pasillos:
   el centro reparte hacia los dos extremos.
3. La suite principal (dormitorio, vestidor y baño) en un extremo. Enfrente, otro
   ambiente; entre los dos, un rincón del estar al que dan sus puertas.
4. En el otro extremo, la entrada: un hall chico entre dos ambientes.
5. Baño y lavadero en un anexo del lado frío, pegados a la cocina: una sola zona
   de cañerías, y la fachada del sol queda libre para vivir.

Las decisiones del usuario (dormitorios, cocina, tamaño) no cambian el esquema:
cambian las medidas y qué ambiente ocupa cada lugar. La salida son rectángulos
de ejes; los muros y las aberturas los pone `capas/casa.py`.

Todo se arma con el sol al norte y, si la casa está en el hemisferio norte, se
espeja de norte a sur al final.
"""

from __future__ import annotations

from ..geometria import poligono
from ..modelo.casa import AccesoDeseado, Decisiones, PuertaDeseada, Rectangulo
from ..modelo.estados import Estado
from .casa import _g, _largo, planta_desde_rectangulos

POR_DEFECTO = Decisiones(dormitorios=3, cocina="abierta", tamano="comoda")

# Por tamaño: profundidad del dormitorio principal, profundidad de la franja de
# enfrente y ancho del centro social. «Amplia» con tres dormitorios es Angus Ranch.
MEDIDAS: dict[str, tuple[float, float, float]] = {
    "compacta": (4.0, 3.0, 7.0),
    "comoda": (4.3, 3.3, 8.0),
    "amplia": (4.5, 3.5, 9.2),
}

ANCHO_PRINCIPAL_M = 4.0
ANCHO_SUITE_M = 2.0          # columna de vestidor y baño en suite
PROF_VESTIDOR_M = 1.2
ANCHO_ENFRENTE_M = 2.9       # dormitorio 2 (o escritorio) frente al principal
ANCHO_ALA_ENTRADA_M = 3.1
HALL_M = (1.3, 3.1)          # tramo del ala de entrada que ocupa el hall, desde el fondo
PROF_ANEXO_M = 2.4
ANCHO_BANO_M = 2.6
ANCHO_LAVADERO_M = 2.0
# Cocina cerrada: deja un paso hacia las puertas de los dormitorios y avanza sobre el centro.
PASO_M = 1.1
FRANJA_CON_COCINA_M = 3.6
COCINA_SOBRE_EL_CENTRO_M = 1.6
# Sin ala de entrada (uno o dos dormitorios) el centro puede ser más angosto.
CENTRO_SIN_ALA_M = -1.0


def completar(d: Decisiones | None) -> Decisiones:
    """Lo que el usuario todavía no decidió toma el valor más común."""
    dados = d.model_dump(exclude_none=True) if d else {}
    return POR_DEFECTO.model_copy(update=dados)


def rectangulos(dormitorios: int, cocina_abierta: bool, tamano: str, sol_al_sur: bool = False) -> list[Rectangulo]:
    prof_principal, franja, centro = MEDIDAS[tamano]
    if not cocina_abierta:
        franja = max(franja, FRANJA_CON_COCINA_M)
    con_ala = dormitorios >= 3
    if not con_ala:
        centro += CENTRO_SIN_ALA_M
    fondo = franja + prof_principal                       # profundidad de la barra
    x_suite = ANCHO_PRINCIPAL_M
    x_centro = x_suite + ANCHO_SUITE_M                    # donde termina el ala de la suite
    x_ala = x_centro + centro                             # donde termina el centro
    x_fin = x_ala + ANCHO_ALA_ENTRADA_M
    hall_0, hall_1 = HALL_M

    def r(id_: str, nombre: str, uso: str, x0: float, y0: float, x1: float, y1: float, **extra) -> Rectangulo:
        return Rectangulo(id=id_, nombre=nombre, uso=uso, x0=_g(x0), y0=_g(y0), x1=_g(x1), y1=_g(y1), **extra)

    al_estar = PuertaDeseada(hacia="estar")
    del_principal = PuertaDeseada(hacia="dorm_principal")
    entrada = AccesoDeseado(lado="este", centro_m=(hall_0 + hall_1) / 2)
    nombre_estar = "Estar, comedor y cocina" if cocina_abierta else "Estar y comedor"
    rects: list[Rectangulo] = []

    # Centro social y rincón frente a la suite.
    acceso_directo = None if con_ala else entrada
    if cocina_abierta:
        rects.append(r("estar_centro", nombre_estar, "social", x_centro, 0, x_ala, fondo, grupo="estar", acceso=acceso_directo))
        rects.append(r("estar_rincon", nombre_estar, "social", ANCHO_ENFRENTE_M, 0, x_centro, franja, grupo="estar"))
    else:
        # Si el anexo empieza cerca, la cocina termina donde empieza: sus muros quedan en línea.
        x_cocina = min(x_centro + COCINA_SOBRE_EL_CENTRO_M, x_ala - ANCHO_LAVADERO_M - ANCHO_BANO_M)
        y_cocina = franja - PASO_M
        rects.append(r("estar_centro", nombre_estar, "social", x_cocina, 0, x_ala, fondo, grupo="estar", acceso=acceso_directo))
        rects.append(r("estar_frente", nombre_estar, "social", x_centro, y_cocina, x_cocina, fondo, grupo="estar"))
        rects.append(r("estar_rincon", nombre_estar, "social", ANCHO_ENFRENTE_M, y_cocina, x_centro, franja, grupo="estar"))
        rects.append(r("cocina", "Cocina", "cocina", ANCHO_ENFRENTE_M, 0, x_cocina, y_cocina,
                       puerta=PuertaDeseada(hacia="estar", lado="este")))

    # Ala de la suite.
    rects.append(r("dorm_principal", "Dormitorio principal", "dormitorio", 0, franja, x_suite, fondo, puerta=al_estar))
    rects.append(r("vestidor", "Vestidor", "vestidor", x_suite, franja, x_centro, franja + PROF_VESTIDOR_M, puerta=del_principal))
    rects.append(r("bano_suite", "Baño en suite", "bano", x_suite, franja + PROF_VESTIDOR_M, x_centro, fondo, puerta=del_principal))
    enfrente = ("escritorio", "Escritorio", "oficina") if dormitorios == 1 else ("dorm_2", "Dormitorio 2", "dormitorio")
    # Su puerta se aparta de la esquina para no chocar con la del principal.
    rects.append(r(*enfrente, 0, 0, ANCHO_ENFRENTE_M, franja,
                   puerta=PuertaDeseada(hacia="estar", lado="este", extremo="fin", margen_m=1.0)))

    # Anexo de servicio, contra el final del centro.
    x_lavadero = x_ala - ANCHO_LAVADERO_M
    rects.append(r("bano", "Baño", "bano", x_lavadero - ANCHO_BANO_M, -PROF_ANEXO_M, x_lavadero, 0, puerta=al_estar))
    rects.append(r("lavadero", "Lavadero", "lavadero", x_lavadero, -PROF_ANEXO_M, x_ala, 0, puerta=al_estar))

    # Ala de entrada.
    if con_ala:
        rects.append(r("acceso", nombre_estar, "social", x_ala, hall_0, x_fin, hall_1, grupo="estar", acceso=AccesoDeseado(lado="este")))
        rects.append(r("dorm_3", "Dormitorio 3", "dormitorio", x_ala, -PROF_ANEXO_M, x_fin, hall_0,
                       puerta=PuertaDeseada(hacia="estar", lado="norte")))
        arriba = ("dorm_4", "Dormitorio 4", "dormitorio") if dormitorios >= 4 else ("escritorio", "Escritorio", "oficina")
        rects.append(r(*arriba, x_ala, hall_1, x_fin, fondo, puerta=PuertaDeseada(hacia="estar", lado="sur")))

    rects = _desplazar_y(rects, PROF_ANEXO_M)             # el origen queda en la esquina suroeste del conjunto
    return _espejar_norte_sur(rects) if sol_al_sur else rects


def _desplazar_y(rects: list[Rectangulo], dy: float) -> list[Rectangulo]:
    salida = []
    for q in rects:
        cambios: dict = {"y0": _g(q.y0 + dy), "y1": _g(q.y1 + dy)}
        if q.acceso and q.acceso.centro_m is not None and q.acceso.lado in ("este", "oeste"):
            cambios["acceso"] = q.acceso.model_copy(update={"centro_m": q.acceso.centro_m + dy})
        salida.append(q.model_copy(update=cambios))
    return salida


def _espejar_norte_sur(rects: list[Rectangulo]) -> list[Rectangulo]:
    """La misma casa con el frente al sur: para el hemisferio norte."""
    alto = max(q.y1 for q in rects)
    opuesto = {"norte": "sur", "sur": "norte"}
    salida = []
    for q in rects:
        cambios: dict = {"y0": _g(alto - q.y1), "y1": _g(alto - q.y0)}
        if q.puerta:
            p = {"lado": opuesto.get(q.puerta.lado, q.puerta.lado)}
            if q.puerta.lado in ("este", "oeste"):  # el eje de ese muro corre de sur a norte
                p["extremo"] = "inicio" if q.puerta.extremo == "fin" else "fin"
            cambios["puerta"] = q.puerta.model_copy(update=p)
        if q.acceso and q.acceso.centro_m is not None and q.acceso.lado in ("este", "oeste"):
            cambios["acceso"] = q.acceso.model_copy(update={"centro_m": alto - q.acceso.centro_m})
        salida.append(q.model_copy(update=cambios))
    return salida


def razones(d: Decisiones, sol: str) -> list[dict]:
    """Por qué la casa quedó ordenada así, en palabras de Lumo."""
    frio = "sur" if sol == "norte" else "norte"
    entrada = ("Se entra por un costado, a un hall chico entre dos ambientes: nadie cae de golpe en el medio del estar."
               if d.dormitorios >= 3 else
               "Se entra por un costado del estar, cerca de la cocina y lejos de los dormitorios.")
    cocina = ("La cocina queda contra la pared del fondo del estar." if d.cocina == "abierta" else
              "La cocina tiene su propio ambiente, alargado, con un paso hacia el comedor.")
    return [
        {"titulo": "El estar en el centro",
         "texto": f"Ocupa la casa de lado a lado y mira al {sol}, que es de donde viene el sol. Reparte hacia los "
                  "dos extremos, así que no hace falta ningún pasillo."},
        {"titulo": "Los dormitorios en los extremos",
         "texto": "El principal va en suite, con su vestidor y su baño. Los demás quedan lejos del ruido del estar; "
                  "sus puertas dan a un rincón, no a la mesa del comedor."},
        {"titulo": "Baño y lavadero juntos, del lado frío",
         "texto": f"Van en un anexo al {frio}, pegados a la cocina: una sola zona de cañerías, y el frente del sol "
                  f"queda libre para vivir. {cocina}"},
        {"titulo": "La entrada", "texto": entrada},
    ]


def planta_base(decisiones: Decisiones | None, lat: float | None = None, estado: Estado = Estado.PROPUESTO) -> dict:
    d = completar(decisiones)
    sol_al_sur = lat is not None and lat > 0
    rects = rectangulos(d.dormitorios, d.cocina == "abierta", d.tamano, sol_al_sur)
    casa, advertencias = planta_desde_rectangulos(
        rects, estado=estado, lat=lat,
        origen={"fuente": "assambl/capas/planta_base.py", "decisiones": d.model_dump(),
                "nota": "Planta base propuesta por Lumo: un punto de partida ordenado para editar."})
    huella = casa["huella_m"]
    xs = [p[0] for p in huella]
    ys = [p[1] for p in huella]
    return {
        "decisiones": d.model_dump(),
        "rectangulos": [q.model_dump() for q in rects],
        "casa": casa,
        "advertencias": advertencias,
        "razones": razones(d, "sur" if sol_al_sur else "norte"),
        "resumen": {
            "superficie_cubierta_m2": round(poligono.area([tuple(p) for p in huella]), 1),
            "ancho_m": round(max(xs) - min(xs), 2),
            "profundidad_m": round(max(ys) - min(ys), 2),
            "muro_exterior_m": round(sum(_largo(m) for m in casa["muros"] if m["sistema"] == "exterior"), 1),
            "ambientes": len(casa["ambientes"]),
        },
    }


def superficie_m2(d: Decisiones) -> float:
    """Superficie cubierta de la planta base para esas decisiones (redondeada al metro)."""
    return round(planta_base(d)["resumen"]["superficie_cubierta_m2"])
