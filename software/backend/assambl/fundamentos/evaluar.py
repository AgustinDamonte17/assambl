"""Fundamentos de diseño de la planta y su evaluación.

No son reglas físicas como las de R03 (un header aguanta o no aguanta): son
criterios de buena práctica que ayudan a comparar alternativas y a explicarle al
usuario qué gana y qué resigna con cada una. Por eso no producen estados, sino
observaciones «a favor», «a considerar» o informativas, con un puntaje de 0 a 1
que solo sirve para ordenar y comparar.

Fuente principal: M. Mitton y C. Nystuen, *Residential Interior Design: A Guide
to Planning Spaces*, 3.ª ed., Wiley, 2016 (citado «RID» con capítulo y página),
que a su vez recoge a Alexander (*A Pattern Language*), Newman, Hall, Susanka y
el International Residential Code (IRC 2015). Los umbrales en metros son la
conversión de los del libro y deben leerse como orientativos.
"""

from __future__ import annotations

import math

from ..geometria import poligono
from . import grafo as g

FUENTE = "Mitton y Nystuen, Residential Interior Design, 3.ª ed. (Wiley, 2016)"

CRITERIOS = [
    {"id": "privacidad", "nombre": "Privacidad y zonas", "pregunta": "¿La casa separa lo social de lo íntimo?"},
    {"id": "recorridos", "nombre": "Recorridos", "pregunta": "¿Se circula poco, con comodidad y sin cruzar por el medio de los ambientes?"},
    {"id": "luz", "nombre": "Luz y sol", "pregunta": "¿Los ambientes donde se vive reciben luz y sol?"},
    {"id": "ambientes", "nombre": "Ambientes cómodos", "pregunta": "¿Cada ambiente tiene tamaño y forma para su uso?"},
    {"id": "instalaciones", "nombre": "Instalaciones agrupadas", "pregunta": "¿Baños, cocina y lavadero comparten cañerías?"},
    {"id": "economia", "nombre": "Economía de obra", "pregunta": "¿Cuánto muro y cuánta superficie cuesta lo que se obtiene?"},
]

FUNDAMENTOS = [
    {
        "id": "F01", "criterio": "privacidad", "titulo": "Gradiente de intimidad",
        "principio": "Los espacios se ordenan de lo público a lo privado: entrada, estar, circulación y, al final, dormitorios y baños. Un dormitorio no debería abrirse al medio del estar.",
        "por_que": "Si los ambientes no siguen el orden de su privacidad, las visitas de extraños, amigos o la propia familia resultan siempre un poco incómodas (Alexander). La casa ofrece una jerarquía clara de territorios, de lo público a lo privado (Lang).",
        "fuente": "RID cap. 1, pp. 2–4 (Alexander, Pattern 127; Lang; Newman)",
        "mide": "Qué ambiente da acceso a cada dormitorio: un pasillo o recibidor (a favor) o directamente el estar o la cocina.",
        "tension": "Sin pasillo se ahorra superficie (las plantas compactas de 60 y 101 m² lo hacen). Es válido en casas chicas o para una pareja; con chicos o visitas frecuentes se nota.",
    },
    {
        "id": "F02", "criterio": "privacidad", "titulo": "Dormitorios lejos del ruido",
        "principio": "La ubicación de los dormitorios se piensa en relación con la circulación de la familia y el ruido. Placares y baños entre el dormitorio y el estar funcionan como colchón.",
        "por_que": "El dormitorio es refugio: se usa para dormir, vestirse, la intimidad y recuperarse de una enfermedad.",
        "fuente": "RID cap. 5, p. 126",
        "mide": "Cuánto muro comparte cada dormitorio con el estar o la cocina, en proporción a su perímetro.",
        "tension": "Separar del todo alarga recorridos; un placar en el muro compartido suele alcanzar.",
    },
    {
        "id": "F03", "criterio": "privacidad", "titulo": "Entrada como transición",
        "principio": "Entre la calle y el interior hace falta un lugar de transición: un recibidor con placar, más ancho que profundo, cerca del estar y del toilette, y a resguardo del viento dominante.",
        "por_que": "Si la transición es demasiado brusca no hay sensación de llegada (Alexander, Pattern 112). La entrada es el colchón clave entre lo más público y lo más privado.",
        "fuente": "RID cap. 2, pp. 29–31",
        "mide": "A qué ambiente da la puerta de acceso: un recibidor (a favor), el estar o la cocina.",
        "tension": "Un recibidor ocupa 2,5 % a 5 % de la casa (RID fig. 2-6 a 2-10). En casas muy chicas se resuelve con un mueble o un cambio de piso.",
    },
    {
        "id": "F06", "criterio": "privacidad", "titulo": "Baño para las visitas",
        "principio": "Una visita tiene que poder llegar a un baño o toilette sin atravesar un dormitorio.",
        "por_que": "Es uno de los tres criterios de visitabilidad junto con la entrada sin escalones y las puertas anchas; el toilette cerca del acceso es la adyacencia típica del recibidor.",
        "fuente": "RID cap. 1, p. 7 y cap. 2, p. 31",
        "mide": "Si existe un recorrido desde la entrada hasta algún baño que no pase por un dormitorio o vestidor.",
        "tension": "Con un solo baño en suite, las visitas entran al dormitorio principal.",
    },
    {
        "id": "F04", "criterio": "recorridos", "titulo": "Circulación justa",
        "principio": "La superficie dedicada solo a circular es improductiva y conviene minimizarla. Un pasillo con puertas a ambos lados (doble carga) sirve el doble que uno con puertas de un solo lado.",
        "por_que": "La circulación simple es el doble de larga y lleva el doble de tiempo que la doble; solo se justifica cuando el recorrido es parte de la experiencia (vistas, galería).",
        "fuente": "RID cap. 2, p. 42 (fig. 2-18)",
        "mide": "Metros cuadrados de pasillos y recibidores sobre la superficie útil. Orientativo: hasta 10 % muy eficiente, más de 18 % es mucho.",
        "tension": "Menos circulación suele significar dormitorios que se abren al estar (F01).",
    },
    {
        "id": "F16", "criterio": "recorridos", "titulo": "Anchos para todos",
        "principio": "Pasillos de 0,90 m como mínimo (1,10–1,20 m para cruzarse cómodos) y puertas que dejen 0,80 m libres, que en la práctica son hojas de 0,90 m.",
        "por_que": "Con 0,90 m dos adultos no se cruzan de frente; una silla de ruedas necesita 0,80 m libres en las puertas y 1,50 m para girar. Diseñar así desde el principio no cuesta más (diseño universal).",
        "fuente": "RID cap. 2, pp. 38–40 y 46; cap. 1, pp. 6–7",
        "mide": "El ancho del pasillo más angosto y la hoja de puerta interior más angosta.",
        "tension": "Cada 10 cm de pasillo, multiplicados por su largo, son superficie que se construye.",
    },
    {
        "id": "F10", "criterio": "ambientes", "titulo": "Estar para reunirse",
        "principio": "El estar se organiza en grupos de conversación de unas seis personas, en un círculo de 3,7 a 4 m. Las puertas y los pasos no deben obligar a cruzar el grupo; cuantas más puertas, menos formas de amoblarlo.",
        "por_que": "Los grupos más grandes se parten en conversaciones menores; el tránsito de punta a punta de un ambiente rectangular es el que más limita el amoblamiento.",
        "fuente": "RID cap. 3, pp. 52 y 56–59 (fig. 3-1 y 3-9)",
        "mide": "El lado menor del estar (≥ 3,6 m) y cuántas puertas o pasos desembocan en él.",
        "tension": "Un estar integrado con cocina y comedor gana amplitud pero reúne más accesos.",
    },
    {
        "id": "F07", "criterio": "ambientes", "titulo": "Dormitorios con lugar para amoblar",
        "principio": "Un dormitorio casi cuadrado de 12 a 13,5 m² admite cama de dos plazas y cómoda en dos paredes; desde 14 m², en tres. El mínimo legal es 6,5 m² con 2,13 m de lado. El placard, cerca de la puerta.",
        "por_que": "La cama manda en el dormitorio: hacen falta 0,90 a 1,20 m de paso principal y 0,45 a 0,60 m para tender la cama.",
        "fuente": "RID cap. 5, pp. 126, 129 y 136 (IRC R304)",
        "mide": "Superficie, lado menor y proporción de cada dormitorio (principal ≥ 12 m² y 3 m de lado; los demás ≥ 9 m² y 2,7 m).",
        "tension": "Dormitorios más grandes suman superficie cubierta, que es lo que más cuesta.",
    },
    {
        "id": "F11", "criterio": "ambientes", "titulo": "Cocina conectada",
        "principio": "La cocina se abre al comedor y queda cerca de una entrada de servicio, el lavadero o el garage, para que las compras y la ropa no crucen el estar.",
        "por_que": "La cocina volvió a ser el centro social de la casa; el lavadero cerca de la cocina o de una entrada secundaria es una de las ubicaciones preferidas.",
        "fuente": "RID cap. 4, pp. 66–71; cap. 7, p. 188",
        "mide": "Si la cocina está abierta o comunicada con el comedor y si linda con el lavadero, el garage o tiene salida propia.",
        "tension": "La cocina integrada lleva olores y ruido al estar.",
    },
    {
        "id": "F08", "criterio": "luz", "titulo": "Luz natural suficiente",
        "principio": "Los ambientes habitables llevan ventanas por al menos el 8 % de su superficie y aberturas de ventilación por el 4 %.",
        "por_que": "Es el mínimo del IRC; los efectos de la luz natural sobre la salud y el ahorro de energía están bien documentados, así que conviene superarlo.",
        "fuente": "RID cap. 1, p. 17 y cap. 3, p. 62 (IRC R303)",
        "mide": "Superficie vidriada de cada dormitorio, estar, cocina y oficina sobre su superficie de piso.",
        "tension": "Más vidrio es más pérdida de calor en invierno si no está bien orientado.",
    },
    {
        "id": "F09", "criterio": "luz", "titulo": "Orientación al sol",
        "principio": "El estar y los dormitorios miran al sol (al norte en Argentina); baños, lavadero y circulaciones van del lado frío y hacen de colchón.",
        "por_que": "La ubicación de las ventanas respecto del sol define la ganancia y la pérdida de calor; la orientación es una decisión de sitio que se toma desde el primer diagrama.",
        "fuente": "RID cap. 9, p. 229; cap. 8, p. 205; práctica bioclimática para el hemisferio sur",
        "mide": "Qué ambientes habitables tienen ventana hacia el sol; el estar cuenta doble.",
        "tension": "La mejor vista o la calle pueden estar del otro lado.",
    },
    {
        "id": "F05", "criterio": "instalaciones", "titulo": "Núcleo húmedo",
        "principio": "Baños, cocina y lavadero juntos, compartiendo muros con cañerías. Mejor en muros interiores que en exteriores en climas fríos.",
        "por_que": "Mover o multiplicar cañerías es de lo que más encarece una obra; en Assambl, además, cada grupo húmedo son pases en la platea (capa 02) y perforaciones en la estructura (capa 13).",
        "fuente": "RID cap. 6, pp. 176–178; cap. 10, p. 241",
        "mide": "En cuántos grupos separados quedan los ambientes húmedos y qué tan lejos están entre sí.",
        "tension": "Un baño en suite casi siempre forma un segundo grupo.",
    },
    {
        "id": "F12", "criterio": "economia", "titulo": "Compacidad",
        "principio": "A igual superficie, una planta más compacta tiene menos muro exterior, menos esquinas y un techo más simple.",
        "por_que": "El entramado (pisos, muros, aberturas y techo) es el 45 % a 55 % del costo de una obra; el muro exterior es además por donde se pierde el calor.",
        "fuente": "RID cap. 10, p. 243; MVP_01 §3.3",
        "mide": "Índice de compacidad (perímetro / perímetro del cuadrado de igual área: 1,0 es un cuadrado) y cantidad de esquinas.",
        "tension": "Las plantas en L o con alas ganan luz, vistas y privacidad a cambio de muro.",
    },
    {
        "id": "F13", "criterio": "economia", "titulo": "Superficie que se aprovecha",
        "principio": "Lo programado (los ambientes) suele ser el 80 % a 85 % de la superficie bruta; el resto son muros y circulación.",
        "por_que": "Es la proporción con la que el libro dimensiona su proyecto de ejemplo; bien por debajo, se está pagando superficie que no se usa.",
        "fuente": "RID cap. 8, p. 203 (tabla 8-1)",
        "mide": "Suma de superficies de los ambientes sobre la superficie cubierta.",
        "tension": "Muros más gruesos (mejor aislación) bajan este número a propósito.",
    },
]

_POR_ID = {f["id"]: f for f in FUNDAMENTOS}
HABITABLES = ("dormitorio", "social", "oficina", "cocina")
HUMEDOS = ("bano", "toilette", "lavadero", "cocina")


def _obs(fid: str, puntaje: float | None, texto: str, piezas: list[str] | None = None) -> dict:
    nivel = "info" if puntaje is None else ("a_favor" if puntaje >= 0.75 else "a_considerar" if puntaje < 0.5 else "neutral")
    return {"fundamento": fid, "criterio": _POR_ID[fid]["criterio"], "titulo": _POR_ID[fid]["titulo"],
            "puntaje": None if puntaje is None else round(max(0.0, min(1.0, puntaje)), 2),
            "nivel": nivel, "texto": texto, "piezas": piezas or []}


def _bbox(contorno) -> tuple[float, float]:
    xs = [p[0] for p in contorno]
    ys = [p[1] for p in contorno]
    a, b = max(xs) - min(xs), max(ys) - min(ys)
    return min(a, b), max(a, b)


def _perimetro(contorno) -> float:
    return poligono.perimetro([tuple(p) for p in contorno])


def _tiene_cocina(gr: g.Grafo, aid: str) -> bool:
    return gr.uso(aid) == "cocina" or "cocina" in gr.nombre(aid).lower()


def _ventanas(gr: g.Grafo, aid: str) -> list[tuple[str, float]]:
    """(lado, superficie vidriada) de las ventanas sobre la fachada del ambiente."""
    res = []
    for t in gr.exterior.get(aid, []):
        m = gr.muros_por_id[t["muro"]]
        (x0, y0), (x1, y1) = m["eje"]["desde_m"], m["eje"]["hasta_m"]
        horizontal = abs(y0 - y1) < 1e-6
        inicio = x0 if horizontal else y0
        sentido = 1 if (x1 >= x0 if horizontal else y1 >= y0) else -1
        t0, t1 = t["tramo"]
        for o in m.get("aberturas") or []:
            if o.get("tipo") not in ("ventana", "ventana_corrediza"):
                continue
            a, b = sorted((inicio + sentido * o["posicion_m"], inicio + sentido * (o["posicion_m"] + o["ancho_m"])))
            solape = min(b, t1) - max(a, t0)
            if solape > 0.2:
                alto = max(0.3, float(o.get("dintel_m", 2.05)) - float(o.get("antepecho_m", 0)))
                res.append((t["lado"], solape * alto))
    return res


def evaluar(casa: dict, lat: float | None = None) -> dict:
    gr = g.construir(casa)
    obs: list[dict] = []
    amb = gr.ambientes
    usos = {a: gr.uso(a) for a in amb}
    dorms = [a for a in amb if usos[a] == "dormitorio"]
    sociales = sorted([a for a in amb if usos[a] == "social"], key=lambda a: -gr.areas[a])
    circ = [a for a in amb if usos[a] == "circulacion"]
    cubiertos = [a for a in amb if usos[a] not in ("garage", "galeria")]
    util = sum(gr.areas[a] for a in cubiertos) or 1.0
    sol = "sur" if lat is not None and lat > 0 else "norte"
    # Ambientes declarados sin contorno (p. ej. el estar de Angus Ranch, que es «lo que queda»):
    # sin ellos no se puede saber por dónde se circula, así que esos fundamentos se omiten.
    sin_contorno = [a.get("nombre") or a["id"] for a in casa.get("ambientes") or [] if a["id"] not in amb]
    completo = not sin_contorno
    if sin_contorno:
        obs.append({"fundamento": None, "criterio": None, "titulo": "Evaluación parcial", "puntaje": None, "nivel": "info",
                    "texto": f"{', '.join('«' + n + '»' for n in sin_contorno)} no tiene contorno dibujado: "
                             "se omiten los fundamentos de recorridos y privacidad que dependen de él.", "piezas": []})

    # F01 · Gradiente de intimidad
    if dorms and completo:
        buenos, al_estar = [], []
        for d in dorms:
            accesos = [n for n in gr.conectados(d) if usos[n] not in ("bano", "vestidor", "toilette")]
            if any(usos[n] == "circulacion" for n in accesos):
                buenos.append(d)
            elif any(usos[n] in ("social", "cocina") for n in accesos):
                al_estar.append(d)
        p = (len(buenos) + 0.4 * len(al_estar)) / len(dorms)
        if len(buenos) == len(dorms):
            t = "Todos los dormitorios se abren a un pasillo o recibidor, no al estar."
        elif al_estar:
            t = (f"{len(al_estar)} de {len(dorms)} dormitorios se abren directo al estar o la cocina: "
                 "se ahorra pasillo, a cambio de menos privacidad.")
        else:
            t = f"{len(buenos)} de {len(dorms)} dormitorios se abren a un pasillo; hay alguno al que se entra por otro ambiente."
        obs.append(_obs("F01", p, t, al_estar))

    # F02 · Dormitorios lejos del ruido
    if completo and dorms and sociales + [a for a in amb if usos[a] == "cocina"]:
        ruidosos = {a for a in amb if usos[a] in ("social", "cocina")}
        expuestos, proporciones = [], []
        for d in dorms:
            comp = sum(v.largo_m for v in gr.lindantes(d) if ({v.a, v.b} - {d}) & ruidosos)
            r = comp / max(_perimetro(amb[d]["contorno_m"]), 1)
            proporciones.append(r)
            if r > 0.15:
                expuestos.append(d)
        p = 1 - min(1.0, 2.5 * sum(proporciones) / len(proporciones))
        if not expuestos:
            t = "Ningún dormitorio comparte muro con el estar o la cocina."
        else:
            t = (f"{len(expuestos)} dormitorio{'s' if len(expuestos) > 1 else ''} comparte{'n' if len(expuestos) > 1 else ''} muro "
                 "con el estar o la cocina: un placar o un muro con aislación acústica en ese lado ayuda.")
        obs.append(_obs("F02", p, t, expuestos))
        # Informativo: dormitorios agrupados o divididos.
        if len(dorms) >= 2:
            privados = {a for a in amb if usos[a] in ("dormitorio", "bano", "toilette", "vestidor")}
            grupos = _componentes(gr, set(dorms), privados | set(circ), cualquier_vecindad=False)
            if len(grupos) > 1:
                obs.append(_obs("F02", None, "Planta dividida: el dormitorio principal queda separado de los demás. "
                                "Da privacidad entre padres e hijos o con huéspedes; con chicos chicos, algunos prefieren tenerlos cerca."))
            else:
                obs.append(_obs("F02", None, "Dormitorios agrupados en una misma zona: silencio para todos y recorridos cortos entre ellos."))

    # F03 · Entrada como transición
    if gr.accesos:
        principal = next((a for a in gr.accesos if usos[a] in ("circulacion", "social")), gr.accesos[0])
        u = usos[principal]
        if u == "circulacion":
            obs.append(_obs("F03", 1.0, f"Se entra a «{gr.nombre(principal)}», un lugar de transición antes del estar."))
        elif u == "social":
            obs.append(_obs("F03", 0.5, "Se entra directo al estar: no hay transición entre la calle y la casa. "
                            "Un recibidor chico o un mueble que arme la llegada lo resuelve.", [principal]))
        elif u == "cocina":
            obs.append(_obs("F03", 0.55, "La entrada principal es por la cocina: práctica para el uso diario, poco formal para las visitas.", [principal]))
        else:
            obs.append(_obs("F03", 0.2, f"La puerta de acceso da a «{gr.nombre(principal)}».", [principal]))
    elif completo:
        obs.append(_obs("F03", 0.1, "Todavía no hay puerta de acceso."))

    # F06 · Baño para las visitas
    banos = [a for a in amb if usos[a] in ("bano", "toilette")]
    if banos and gr.accesos and completo:
        evitar = {a for a in amb if usos[a] in ("dormitorio", "vestidor")}
        llega = [b for b in banos if gr.camino(gr.accesos[0], b, evitar)]
        if llega:
            obs.append(_obs("F06", 1.0, f"Una visita llega a «{gr.nombre(llega[0])}» sin pasar por un dormitorio."))
        else:
            obs.append(_obs("F06", 0.3, "Para llegar a un baño hay que atravesar un dormitorio: conviene un toilette o un baño con acceso desde la circulación.", banos))

    # F04 · Circulación justa
    if cubiertos and completo:
        area_circ = sum(gr.areas[a] for a in circ)
        r = area_circ / util
        p = 1.0 if r <= 0.10 else 1.0 - (r - 0.10) / 0.16 if r <= 0.26 else 0.0
        t = f"Pasillos y recibidores: {area_circ:.1f} m², {100 * r:.0f} % de la superficie útil."
        if r <= 0.04:
            t += " Casi no hay circulación: la casa se recorre a través de los ambientes."
        elif r > 0.18:
            t += " Es mucha superficie solo para circular."
        obs.append(_obs("F04", max(0.25, p), t, circ if r > 0.18 else []))

    # F16 · Anchos para todos
    angostos, puertas = [], []
    for m in casa.get("muros") or []:
        for o in m.get("aberturas") or []:
            if o.get("tipo") == "puerta" and m.get("sistema") != "exterior":
                puertas.append(o["ancho_m"])
                if o["ancho_m"] < 0.75:
                    angostos.append(o["id"])
    anchos_pasillo = [(a, _bbox(amb[a]["contorno_m"])[0]) for a in circ]
    partes, p = [], 1.0
    if anchos_pasillo:
        a_min, w = min(anchos_pasillo, key=lambda x: x[1])
        partes.append(f"el pasillo más angosto mide {w:.2f} m")
        p = min(p, 1.0 if w >= 1.05 else 0.75 if w >= 0.88 else 0.35)
    if puertas:
        partes.append(f"la puerta interior más angosta, {min(puertas):.2f} m")
        if min(puertas) < 0.75:
            p = min(p, 0.6)
    if partes:
        t = "Anchos: " + " y ".join(partes) + "."
        if p < 0.75:
            t += " Para una silla de ruedas o un andador hacen falta pasillos de 0,90–1,20 m y puertas de 0,90 m."
        obs.append(_obs("F16", p, t, angostos))

    # F10 · Estar para reunirse
    if sociales:
        s = sociales[0]
        lado, _ = _bbox(amb[s]["contorno_m"])
        accesos = [v for v in gr.lindantes(s) if v.tipo in ("puerta", "abierto")]
        p = min(1.0, lado / 3.6) * (1.0 if len(accesos) <= 4 else 0.8 if len(accesos) <= 6 else 0.6)
        t = f"«{gr.nombre(s)}»: {gr.areas[s]:.0f} m², lado menor {lado:.1f} m"
        t += ", con lugar para un grupo de conversación." if lado >= 3.5 else "; queda justo para un grupo de conversación de 3,7 m."
        if len(accesos) > 4:
            t += f" Desembocan {len(accesos)} puertas y pasos: conviene que el paso no cruce el sector de estar."
        obs.append(_obs("F10", p, t, [s] if p < 0.75 else []))

    # F07 · Dormitorios con lugar para amoblar
    if dorms:
        principal = max(dorms, key=lambda d: gr.areas[d])
        chicos, puntajes = [], []
        for d in dorms:
            corto, largo = _bbox(amb[d]["contorno_m"])
            area_obj, lado_obj = (12.0, 3.0) if d == principal else (9.0, 2.7)
            pd = min(1.0, gr.areas[d] / area_obj) * min(1.0, corto / lado_obj)
            if largo / max(corto, 0.1) > 1.7:
                pd *= 0.8
            puntajes.append(pd)
            if pd < 0.8:
                chicos.append(d)
        p = sum(puntajes) / len(puntajes)
        if not chicos:
            t = f"Los dormitorios tienen tamaño y proporción para amoblar (principal de {gr.areas[principal]:.1f} m²)."
        else:
            nombres = ", ".join(f"«{gr.nombre(d)}» ({gr.areas[d]:.1f} m²)" for d in chicos)
            t = f"Quedan justos para amoblar: {nombres}. Referencia: principal ≥ 12 m² y 3 m de lado; los demás ≥ 9 m²."
        obs.append(_obs("F07", p, t, chicos))

    # F11 · Cocina conectada
    cocinas = [a for a in amb if _tiene_cocina(gr, a)]
    if cocinas and completo:
        c = cocinas[0]
        integrada = usos[c] == "social" or any(v.tipo == "abierto" and usos[({v.a, v.b} - {c}).pop()] == "social" for v in gr.lindantes(c))
        con_comedor = integrada or any(usos[n] == "social" for n in gr.conectados(c))
        servicio = c in gr.accesos or any(usos[({v.a, v.b} - {c}).pop()] in ("lavadero", "garage") for v in gr.lindantes(c))
        p = (0.6 if con_comedor else 0.2) + (0.4 if servicio else 0.0)
        partes = ["abierta al comedor" if integrada else "comunicada con el comedor" if con_comedor else "sin conexión directa con el comedor"]
        partes.append("con el lavadero, el garage o una salida de servicio al lado" if servicio else
                      "lejos del lavadero y sin salida de servicio: las compras y la ropa cruzan la casa")
        obs.append(_obs("F11", p, "Cocina " + ", ".join(partes) + ".", [] if p >= 0.75 else [c]))

    # F08 · Luz natural suficiente
    habitables = [a for a in amb if usos[a] in HABITABLES and not (usos[a] == "social" and gr.areas[a] < 4)]
    if habitables:
        oscuros, puntajes = [], []
        for a in habitables:
            vid = sum(s for _, s in _ventanas(gr, a))
            r = vid / max(gr.areas[a], 1)
            puntajes.append(min(1.0, r / 0.10))
            if r < 0.08:
                oscuros.append(a)
        p = sum(puntajes) / len(puntajes)
        t = ("Todos los ambientes habitables superan el 8 % de su superficie en ventanas." if not oscuros else
             f"Por debajo del 8 % de ventanas: {', '.join('«' + gr.nombre(a) + '»' for a in oscuros)}.")
        obs.append(_obs("F08", p, t, oscuros))

    # F09 · Orientación al sol
    vivir = [a for a in amb if usos[a] in ("social", "dormitorio", "oficina")]
    if vivir:
        total = peso_ok = 0.0
        sin_sol = []
        for a in vivir:
            peso = 2.0 if usos[a] == "social" else 1.0
            lados = {lado for lado, _ in _ventanas(gr, a)}
            val = 1.0 if sol in lados else 0.5 if lados & {"este", "oeste"} else 0.0
            total += peso
            peso_ok += peso * val
            if val < 1:
                sin_sol.append(a)
        p = peso_ok / total
        con_sol = len([a for a in vivir if a not in sin_sol and usos[a] != "social"])
        n_dorm = len([a for a in vivir if usos[a] != "social"])
        t = f"{con_sol} de {n_dorm} dormitorios u oficinas tienen ventana al {sol}"
        if sociales:
            t += (", y el estar también." if sociales[0] not in sin_sol else
                  f"; el estar no: conviene abrirlo al {sol}.")
        else:
            t += "."
        if lat is None:
            t += " (Se supuso hemisferio sur: cargá la ubicación en Terreno para afinarlo.)"
        obs.append(_obs("F09", p, t, sin_sol))

    # F05 · Núcleo húmedo
    humedos = {a for a in amb if usos[a] in HUMEDOS or _tiene_cocina(gr, a)}
    if len(humedos) >= 2:
        grupos = _componentes(gr, humedos, humedos, cualquier_vecindad=True)
        cent = {a: poligono.centroide([tuple(p) for p in amb[a]["contorno_m"]]) for a in humedos}
        dist = 0.0
        for i, ga in enumerate(grupos):
            for gb in grupos[i + 1:]:
                dist = max(dist, min(math.dist(cent[x], cent[y]) for x in ga for y in gb))
        k = len(grupos)
        p = 1.0 if k == 1 else (0.75 if dist < 5 else 0.55) if k == 2 else 0.35
        if k == 1:
            t = "Baños, cocina y lavadero forman un solo núcleo húmedo: cañerías cortas y pocos pases en la platea."
        else:
            t = (f"Los ambientes con agua quedan en {k} grupos separados (hasta {dist:.0f} m entre ellos): "
                 "más cañería y más pases en la platea.")
        obs.append(_obs("F05", p, t, [] if k == 1 else sorted(humedos)))

    # F12 · Compacidad
    huella = casa.get("huella_m") or []
    if len(huella) >= 3:
        pts = [tuple(p) for p in huella]
        area_h = poligono.area(pts)
        per = poligono.perimetro(pts)
        indice = per / (4 * math.sqrt(area_h)) if area_h else 0
        esquinas = len(pts)
        p = 1.0 if indice <= 1.08 else max(0.25, 1.0 - (indice - 1.08) / 0.34)
        if esquinas > 8:
            p *= 0.9
        muro_ext = sum(math.dist(m["eje"]["desde_m"], m["eje"]["hasta_m"]) for m in casa.get("muros") or [] if m.get("sistema") == "exterior")
        t = (f"Índice de compacidad {indice:.2f} (1,00 es un cuadrado) y {esquinas} esquinas; "
             f"{muro_ext / max(area_h, 1):.2f} m de muro exterior por m² cubierto.")
        obs.append(_obs("F12", p, t))

        # F13 · Superficie que se aprovecha
        r = util / area_h if area_h else 0
        p = 1.0 if r >= 0.80 else max(0.3, 1.0 - (0.80 - r) / 0.15)
        if completo:
            obs.append(_obs("F13", p, f"Los ambientes ocupan el {100 * r:.0f} % de la superficie cubierta (referencia: 80–85 %)."))

    # Puntaje por criterio: promedio de sus observaciones con puntaje.
    criterios = []
    for c in CRITERIOS:
        ps = [o["puntaje"] for o in obs if o["criterio"] == c["id"] and o["puntaje"] is not None]
        criterios.append({**c, "puntaje": round(sum(ps) / len(ps), 2) if ps else None})
    validos = [c["puntaje"] for c in criterios if c["puntaje"] is not None]
    return {
        "criterios": criterios,
        "observaciones": obs,
        "puntaje": round(sum(validos) / len(validos), 2) if validos else None,
        "fuente": FUENTE,
    }


def _componentes(gr: g.Grafo, nodos: set[str], permitidos: set[str], cualquier_vecindad: bool) -> list[set[str]]:
    """Grupos de `nodos` conectados a través de ambientes `permitidos`."""
    visto: set[str] = set()
    grupos = []
    for n in nodos:
        if n in visto:
            continue
        grupo, pila = set(), [n]
        while pila:
            x = pila.pop()
            if x in visto:
                continue
            visto.add(x)
            if x in nodos:
                grupo.add(x)
            vecinos = ([({v.a, v.b} - {x}).pop() for v in gr.lindantes(x)] if cualquier_vecindad else gr.conectados(x))
            pila.extend(y for y in vecinos if y in permitidos and y not in visto)
        grupos.append(grupo)
    return grupos
