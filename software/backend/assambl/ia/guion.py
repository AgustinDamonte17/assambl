"""Asistente sin IA: guion fijo y lectura por palabras clave.

Cumple el mismo contrato que el asistente con IA (`RespuestaAsistente`), así la
interfaz, las pruebas y quien no tenga clave usan el mismo recorrido. También
aporta `completar_programa()`, que el asistente con IA usa para normalizar lo
que devuelve el modelo: ids únicos y superficies que cierran con el objetivo.
"""

from __future__ import annotations

import re
import unicodedata

from ..capas.casa import slug
from ..modelo.casa import AREA_TIPICA_M2, AmbientePrograma, Opcion, Pregunta, Programa, RespuestaAsistente

# Fracción de la superficie cubierta que ocupan los ambientes; el resto son
# muros y circulación que agrega el generador.
FRACCION_UTIL = 0.82

_NUMEROS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t)


def _cuenta(texto: str, patron: str) -> int | None:
    m = re.search(rf"(\d+|{'|'.join(_NUMEROS)})\s+(?:\w+\s+)?(?:{patron})", texto)
    if not m:
        return None
    v = m.group(1)
    return int(v) if v.isdigit() else _NUMEROS[v]


# ---------------------------------------------------------------- programa

def programa_desde_conteos(dormitorios: int, banos: int, superficie: float | None, cocina_integrada: bool = True,
                           extras: list[str] | None = None, galeria: bool | None = None, garage: bool | None = None,
                           zona: str | None = None, entrada: str | None = None) -> Programa:
    extras = extras or []
    ambs = [AmbientePrograma(id="estar", nombre="Estar y comedor" + (" con cocina" if cocina_integrada else ""), uso="social")]
    if not cocina_integrada:
        ambs.append(AmbientePrograma(id="cocina", nombre="Cocina", uso="cocina"))
    for i in range(dormitorios):
        principal = i == 0 and dormitorios > 1
        nombre = "Dormitorio principal" if principal else ("Dormitorio" if dormitorios == 1 else f"Dormitorio {i + 1}")
        ambs.append(AmbientePrograma(id="dorm_principal" if principal else f"dorm_{i + 1}", nombre=nombre,
                                     uso="dormitorio", principal=principal,
                                     area_m2=14.0 if principal else None))
    for i in range(banos):
        ambs.append(AmbientePrograma(id="bano" if i == 0 else f"bano_{i + 1}", nombre="Baño" if i == 0 else f"Baño {i + 1}", uso="bano"))
    nombres = {"oficina": "Oficina", "lavadero": "Lavadero", "vestidor": "Vestidor", "deposito": "Depósito"}
    for e in extras:
        if e in nombres:
            ambs.append(AmbientePrograma(id=e, nombre=nombres[e], uso=e))  # type: ignore[arg-type]
    return completar_programa(Programa(superficie_objetivo_m2=superficie, ambientes=ambs,
                                       cocina_integrada=cocina_integrada, galeria=galeria, garage=garage,
                                       dormitorios=zona, entrada=entrada))


def completar_programa(p: Programa) -> Programa:
    """Ids únicos, usos válidos y superficies que suman la superficie objetivo."""
    vistos: set[str] = set()
    ambs = []
    for a in p.ambientes:
        base = slug(a.id or a.nombre)
        aid, n = base, 2
        while aid in vistos:
            aid, n = f"{base}_{n}", n + 1
        vistos.add(aid)
        ambs.append(a.model_copy(update={"id": aid}))
    faltan = [a for a in ambs if a.area_m2 is None]
    if p.superficie_objetivo_m2 and ambs:
        objetivo = p.superficie_objetivo_m2 * FRACCION_UTIL
        fijas = sum(a.area_m2 or 0 for a in ambs)
        tipicas = sum(AREA_TIPICA_M2.get(a.uso, 8.0) for a in faltan)
        libre = objetivo - fijas
        escala = min(max(libre / tipicas, 0.75), 1.6) if tipicas and libre > 0 else 1.0
        ambs = [a if a.area_m2 is not None else a.model_copy(update={"area_m2": round(AREA_TIPICA_M2.get(a.uso, 8.0) * escala, 1)})
                for a in ambs]
    else:
        ambs = [a if a.area_m2 is not None else a.model_copy(update={"area_m2": AREA_TIPICA_M2.get(a.uso, 8.0)}) for a in ambs]
    return p.model_copy(update={"ambientes": ambs})


def superficie_sugerida(dormitorios: int) -> tuple[int, int, int]:
    """(compacta, media, amplia) en m² para una casa de una planta."""
    base = {1: 50, 2: 70, 3: 95, 4: 125}.get(dormitorios, 95 + 28 * (dormitorios - 3))
    return base, round(base * 1.2 / 5) * 5, round(base * 1.45 / 5) * 5


# ---------------------------------------------------------------- guion

def _estado(p: Programa) -> dict:
    return dict(getattr(p, "guion", None) or {})


def _con_guion(p: Programa, g: dict) -> Programa:
    d = p.model_dump()
    d["guion"] = g
    return Programa.model_validate(d)


def _pregunta(clave: str, g: dict) -> Pregunta:
    if clave == "dormitorios":
        return Pregunta(texto="¿Cuántos dormitorios necesitás?", opciones=[
            Opcion(id="1", etiqueta="1 dormitorio", detalle="Para una o dos personas"),
            Opcion(id="2", etiqueta="2 dormitorios", detalle="Pareja con un hijo o un cuarto de huéspedes"),
            Opcion(id="3", etiqueta="3 dormitorios", detalle="Familia"),
            Opcion(id="4", etiqueta="4 dormitorios", detalle="Familia grande"),
        ])
    if clave == "superficie":
        c, m, a = superficie_sugerida(int(g.get("dormitorios", 2)))
        return Pregunta(texto="¿Qué tamaño imaginás? Cuanto más grande, más material y más obra.", opciones=[
            Opcion(id=str(c), etiqueta=f"Compacta · {c} m²", detalle="Lo justo, más económica"),
            Opcion(id=str(m), etiqueta=f"Media · {m} m²", detalle="Ambientes cómodos"),
            Opcion(id=str(a), etiqueta=f"Amplia · {a} m²", detalle="Espacios generosos"),
        ])
    if clave == "banos":
        return Pregunta(texto="¿Cuántos baños?", opciones=[
            Opcion(id="1", etiqueta="Uno", detalle="Más simple: una sola zona de cañerías"),
            Opcion(id="2", etiqueta="Dos", detalle="Uno puede quedar en suite con el dormitorio principal"),
        ])
    if clave == "cocina":
        return Pregunta(texto="¿La cocina integrada al estar o separada?", opciones=[
            Opcion(id="integrada", etiqueta="Integrada", detalle="Un solo ambiente social, más luz y menos muros"),
            Opcion(id="separada", etiqueta="Separada", detalle="Olores y ruidos aparte"),
        ])
    # Las tres que siguen salen de los fundamentos (docs/fundamentos_diseno.md):
    # no tienen respuesta correcta, cada opción gana algo y resigna otra cosa.
    if clave == "zona":
        return Pregunta(texto="¿Cómo querés los dormitorios?", opciones=[
            Opcion(id="juntos", etiqueta="Todos juntos", detalle="Una zona de noche silenciosa; los chicos cerca de los padres"),
            Opcion(id="divididos", etiqueta="El principal aparte", detalle="Más privacidad entre padres e hijos o con huéspedes"),
            Opcion(id="igual", etiqueta="Me da igual", detalle="Te muestro de las dos"),
        ])
    if clave == "entrada":
        return Pregunta(texto="¿Cómo te imaginás la llegada a la casa?", opciones=[
            Opcion(id="recibidor", etiqueta="Con recibidor", detalle="Un lugar para dejar abrigos antes de entrar al estar"),
            Opcion(id="directa", etiqueta="Directo al estar", detalle="Menos pasillo, más metros para vivir"),
            Opcion(id="igual", etiqueta="Me da igual"),
        ])
    if clave == "garage":
        return Pregunta(texto="¿Querés garage cubierto pegado a la casa?", opciones=[
            Opcion(id="si", etiqueta="Sí", detalle="Suma unos 36 m²; bien ubicado protege a la casa de la calle"),
            Opcion(id="no", etiqueta="No", detalle="Un auto al aire libre o un techito aparte"),
        ])
    return Pregunta(texto="¿Querés sumar algo más? Podés elegir varios.", multiple=True, importante=False, opciones=[
        Opcion(id="lavadero", etiqueta="Lavadero"),
        Opcion(id="oficina", etiqueta="Oficina / estudio"),
        Opcion(id="vestidor", etiqueta="Vestidor"),
        Opcion(id="galeria", etiqueta="Galería", detalle="Se resuelve con el techo, no suma ambientes"),
        Opcion(id="nada", etiqueta="Nada más"),
    ])


_ORDEN = ["dormitorios", "superficie", "banos", "cocina", "zona", "entrada", "garage", "extras"]


def _orden(g: dict) -> list[str]:
    # Con un dormitorio no hay nada que agrupar ni dividir.
    return [k for k in _ORDEN if not (k == "zona" and int(g.get("dormitorios", 2)) < 2)]


def _aplicar_respuesta(clave: str, texto: str, opciones: list[str], g: dict) -> bool:
    """Guarda la respuesta a la pregunta `clave`. Devuelve False si no se entendió."""
    t = _plano(texto)
    if clave in ("dormitorios", "banos"):
        v = opciones[0] if opciones else (re.search(r"\d+", t) or [None])[0]
        if v is None and len(t) <= 25:  # «dos», «uno solo»; no el «una» de una frase larga
            v = next((str(n) for w, n in _NUMEROS.items() if re.search(rf"\b{w}\b", t)), None)
        if v is None or not str(v).isdigit():
            return False
        g[clave] = max(0 if clave == "banos" else 1, min(int(v), 6))
        return True
    if clave == "superficie":
        v = opciones[0] if opciones else (re.search(r"\d+", t) or [None])[0]
        if v is None:
            return False
        g[clave] = float(v)
        return True
    if clave == "cocina":
        if opciones:
            g[clave] = opciones[0] != "separada"
        elif "separ" in t or "aparte" in t:
            g[clave] = False
        elif "integr" in t or "abierta" in t:
            g[clave] = True
        else:
            return False
        return True
    if clave in ("zona", "entrada", "garage"):
        v = opciones[0] if opciones else None
        if v is None:
            claves = {"zona": {"juntos": ("junt", "cerca"), "divididos": ("divid", "separ", "aparte", "lejos")},
                      "entrada": {"recibidor": ("recibidor", "hall", "entrada"), "directa": ("direct", "sin")},
                      "garage": {"no": ("no",), "si": ("si", "quiero", "dale")}}[clave]
            v = next((k for k, ws in claves.items() if any(re.search(rf"\b{w}", t) for w in ws)), None)
            if v is None and ("igual" in t or "indistinto" in t):
                v = "igual"
        if v is None:
            return False
        g[clave] = None if v == "igual" else (v == "si") if clave == "garage" else v
        return True
    sel = opciones or [k for k in ("lavadero", "oficina", "vestidor", "galeria") if k[:5] in t]
    g[clave] = [s for s in sel if s != "nada"]
    return True


def _desde_texto_libre(texto: str, g: dict) -> None:
    t = _plano(texto)
    m = re.search(r"(\d{2,3})\s*(?:m2|m²|mts|metros)", t)
    if m:
        g["superficie"] = float(m.group(1))
    d = _cuenta(t, r"dormitorios?|habitacion(?:es)?|cuartos?|piezas?")
    if d:
        g["dormitorios"] = d
    elif re.search(r"\b(?:un|una) (?:dormitorio|habitacion|cuarto)", t):
        g["dormitorios"] = 1
    b = _cuenta(t, r"banos?")
    if b:
        g["banos"] = b
    if "cocina separada" in t or "cocina aparte" in t or "cocina cerrada" in t:
        g["cocina"] = False
    elif "cocina integrada" in t or "cocina abierta" in t or "cocina comedor" in t:
        g["cocina"] = True
    if re.search(r"\bgarage|\bcochera", t):
        g["garage"] = not re.search(r"sin (?:garage|cochera)", t)
    if re.search(r"dormitorios? (?:separad|dividid)|principal (?:aparte|separad|lejos)", t):
        g["zona"] = "divididos"
    elif re.search(r"dormitorios? (?:junt|cerca)", t):
        g["zona"] = "juntos"
    if "recibidor" in t or "hall de entrada" in t:
        g["entrada"] = "recibidor"
    extras = set(g.get("extras") or [])
    for clave, palabras in {"oficina": ("oficina", "escritorio", "estudio"), "lavadero": ("lavadero",),
                            "vestidor": ("vestidor",), "galeria": ("galeria", "quincho", "porche")}.items():
        if any(w in t for w in palabras):
            extras.add(clave)
    if extras:
        g["extras"] = sorted(extras)


def _programa_de_guion(g: dict) -> Programa:
    extras = list(g.get("extras") or [])
    return programa_desde_conteos(
        dormitorios=int(g.get("dormitorios", 2)),
        banos=int(g.get("banos", 1)),
        superficie=g.get("superficie"),
        cocina_integrada=g.get("cocina", True),
        extras=[e for e in extras if e != "galeria"],
        galeria="galeria" in extras if "extras" in g else None,
        garage=g.get("garage"),
        zona=g.get("zona"),
        entrada=g.get("entrada"),
    )


def responder(modo: str, historial: list, programa: Programa | None, opciones: list[str]) -> RespuestaAsistente:
    g = _estado(programa) if programa else {}
    ultima = next((m.texto for m in reversed(historial) if m.rol == "usuario"), "")
    pendiente = g.get("pendiente")
    entendido = True
    if ultima and not opciones:
        _desde_texto_libre(ultima, g)
    if pendiente and ultima and (opciones or pendiente not in g):
        entendido = _aplicar_respuesta(pendiente, ultima, opciones, g)

    # Lo imprescindible para proponer: dormitorios. El resto tiene valores por defecto
    # y en modo libre no se pregunta si el usuario no lo mencionó.
    imprescindibles = ["dormitorios"] if modo == "libre" else _orden(g)
    if modo == "libre" and "superficie" not in g and "dormitorios" in g:
        imprescindibles = ["dormitorios", "superficie"]
    falta = next((k for k in imprescindibles if k not in g), None)
    g["pendiente"] = falta
    p = _con_guion(_programa_de_guion(g), g)

    if falta:
        pregunta = _pregunta(falta, g)
        if not entendido:
            mensaje = "No te entendí bien. Elegí una opción o escribilo con un número."
        elif not historial or not ultima:
            mensaje = ("¡Hola! Soy Monti. Te hago unas pocas preguntas y te muestro plantas posibles para tu casa. "
                       "Siempre vas a poder cambiar todo después.") if modo == "orientador" else \
                      "Contame cómo imaginás tu casa: cuántos dormitorios, qué tamaño, qué no puede faltar."
        else:
            mensaje = _eco(g)
        return RespuestaAsistente(mensaje=mensaje, pregunta=pregunta, programa=p, listo=False)
    return RespuestaAsistente(
        mensaje=f"{_eco(g)} Con eso ya puedo proponerte algunas plantas. Elegí la que más te guste y la ajustamos en el editor.",
        programa=p, listo=True)


def _eco(g: dict) -> str:
    partes = []
    if "dormitorios" in g:
        d = g["dormitorios"]
        partes.append(f"{d} dormitorio{'s' if d != 1 else ''}")
    if "banos" in g:
        partes.append(f"{g['banos']} baño{'s' if g['banos'] != 1 else ''}")
    if "superficie" in g:
        partes.append(f"unos {g['superficie']:.0f} m²")
    if "cocina" in g:
        partes.append("cocina integrada" if g["cocina"] else "cocina separada")
    if g.get("zona"):
        partes.append("dormitorios juntos" if g["zona"] == "juntos" else "el principal aparte")
    if g.get("entrada"):
        partes.append("con recibidor" if g["entrada"] == "recibidor" else "entrada directa al estar")
    if g.get("garage") is not None:
        partes.append("con garage" if g["garage"] else "sin garage")
    extras = [e for e in g.get("extras") or []]
    if extras:
        partes.append(", ".join(extras))
    return f"Anoto: {', '.join(partes)}." if partes else "Perfecto."
