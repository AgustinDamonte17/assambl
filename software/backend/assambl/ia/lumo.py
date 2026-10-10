"""Lumo: el recorrido guiado que lleva a la planta base.

Son tres decisiones, siempre las mismas y en el mismo orden, cada una con sus
opciones y lo que cambia al elegirla. No usa un modelo de lenguaje: las preguntas
son fijas, y lo que el usuario escribe en vez de tocar una opción se lee por
palabras clave. Así el recorrido es inmediato, igual para todos y no depende de
tener una clave de IA.

La planta la arma `capas/planta_base.py`; acá solo se conversa.
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel

from ..capas import planta_base
from ..modelo.casa import Decisiones, Opcion, Pregunta

ORDEN = ("dormitorios", "cocina", "tamano")

_NUMEROS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4}


class RespuestaLumo(BaseModel):
    mensaje: str
    pregunta: Pregunta | None = None
    decisiones: Decisiones
    listo: bool = False


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t)


def pendiente(d: Decisiones) -> str | None:
    """La primera decisión que falta tomar."""
    return next((k for k in ORDEN if getattr(d, k) is None), None)


def pregunta(clave: str, d: Decisiones) -> Pregunta:
    if clave == "dormitorios":
        return Pregunta(texto="¿Cuántos dormitorios necesitás?", opciones=[
            Opcion(id="1", etiqueta="1 dormitorio", detalle="En suite, más un escritorio que también recibe visitas"),
            Opcion(id="2", etiqueta="2 dormitorios", detalle="El principal en suite y otro enfrente"),
            Opcion(id="3", etiqueta="3 dormitorios", detalle="Suma un ala junto a la entrada, con un escritorio"),
            Opcion(id="4", etiqueta="4 dormitorios", detalle="Dos en cada extremo de la casa"),
        ])
    if clave == "cocina":
        return Pregunta(texto="¿La cocina abierta al estar o cerrada?", opciones=[
            Opcion(id="abierta", etiqueta="Abierta", detalle="Un solo ambiente con el estar: más luz y menos muros"),
            Opcion(id="cerrada", etiqueta="Cerrada", detalle="Olores y ruidos aparte; la casa crece un poco"),
        ])
    base = planta_base.completar(d)
    etiquetas = {"compacta": ("Compacta", "Lo justo: menos material y menos obra"),
                 "comoda": ("Cómoda", "Ambientes holgados"),
                 "amplia": ("Amplia", "Espacios generosos")}
    opciones = []
    for tamano, (nombre, detalle) in etiquetas.items():
        m2 = planta_base.superficie_m2(base.model_copy(update={"tamano": tamano}))
        opciones.append(Opcion(id=tamano, etiqueta=f"{nombre} · {m2:.0f} m²", detalle=detalle))
    return Pregunta(texto="¿Qué tamaño imaginás? Cuanto más grande, más material y más obra.", opciones=opciones)


def interpretar(clave: str, texto: str) -> int | str | None:
    """Lee una respuesta escrita a la pregunta `clave`. None si no se entiende."""
    t = _plano(texto)
    if clave == "dormitorios":
        m = re.search(r"\d+", t)
        n = int(m.group()) if m else next((v for w, v in _NUMEROS.items() if re.search(rf"\b{w}\b", t)), None)
        return n if n is not None and 1 <= n <= 4 else None
    if clave == "cocina":
        if re.search(r"cerrad|separad|aparte|independiente", t):
            return "cerrada"
        if re.search(r"abiert|integrad|isla|barra", t):
            return "abierta"
        return None
    if re.search(r"compact|chic|pequen|justo|minim", t):
        return "compacta"
    if re.search(r"ampli|grande|generos|espacios", t):
        return "amplia"
    if re.search(r"comod|medi|normal|intermedi", t):
        return "comoda"
    return None


def _eco(clave: str, d: Decisiones) -> str:
    """Qué hizo Lumo con la última decisión."""
    if clave == "dormitorios":
        return {
            1: "Un dormitorio: va en suite en un extremo de la casa, con su vestidor y su baño. Enfrente te dejo un "
               "escritorio, que también sirve para recibir visitas.",
            2: "Dos dormitorios: el principal en suite y el otro enfrente, los dos en el mismo extremo, lejos del "
               "ruido del estar.",
            3: "Tres dormitorios: el principal en suite y otro en un extremo; el tercero del otro lado de la casa, "
               "junto a la entrada, con un escritorio.",
            4: "Cuatro dormitorios: dos en cada extremo de la casa, con el estar en el medio.",
        }[d.dormitorios or 3]
    if clave == "cocina":
        return ("Cocina abierta: queda contra la pared del fondo del estar, con el baño y el lavadero a un paso."
                if d.cocina == "abierta" else
                "Cocina cerrada: tiene su propio ambiente, alargado, con un paso hacia el comedor.")
    return {"compacta": "Tamaño compacto: lo justo en cada ambiente.",
            "comoda": "Tamaño cómodo: ambientes holgados sin que la casa se dispare.",
            "amplia": "Tamaño amplio: espacios generosos."}.get(d.tamano or "", "")


def mensaje_listo(resumen: dict) -> str:
    return (f"¡Listo! Esta es tu casa: {resumen['superficie_cubierta_m2']:.0f} m², "
            f"{resumen['ancho_m']:.1f} × {resumen['profundidad_m']:.1f} m. Podés cambiar cualquier decisión y ver cómo "
            "queda, o abrirla en el editor para mover muros y ventanas.")


def mensaje_cambio(clave: str, d: Decisiones, resumen: dict) -> str:
    """Cuando la casa ya estaba lista y se cambia una decisión desde los controles."""
    return (f"{_eco(clave, d)} Ahora mide {resumen['superficie_cubierta_m2']:.0f} m², "
            f"{resumen['ancho_m']:.1f} × {resumen['profundidad_m']:.1f} m.")


def responder(d: Decisiones, texto: str = "", cambio: str | None = None) -> RespuestaLumo:
    """Un turno. `texto` es lo que el usuario escribió en vez de tocar una opción;
    `cambio`, la decisión que tocó en los controles sin que fuera la que se estaba preguntando."""
    entendido = True
    respondida = None
    falta = pendiente(d)
    if texto.strip() and falta:
        valor = interpretar(falta, texto)
        if valor is None:
            entendido = False
        else:
            d = d.model_copy(update={falta: valor})
            respondida = falta
    elif cambio in ORDEN:
        respondida = cambio
    elif not texto.strip():
        tomadas = [k for k in ORDEN if getattr(d, k) is not None]
        respondida = tomadas[-1] if tomadas else None
    falta = pendiente(d)

    if not falta:
        return RespuestaLumo(mensaje="¡Listo! Esta es tu casa.", decisiones=d, listo=True)
    if not entendido:
        mensaje = "No te entendí bien. Elegí una de las opciones o escribilo más corto."
    elif respondida is None:
        mensaje = ("¡Hola! Soy Lumo. Con tres decisiones te armo una casa ordenada, lista para que la ajustes a tu "
                   "gusto. Empecemos por la que más la cambia.")
    else:
        mensaje = f"{_eco(respondida, d)} Mirá a la derecha cómo va quedando."
    return RespuestaLumo(mensaje=mensaje, pregunta=pregunta(falta, d), decisiones=d, listo=False)
