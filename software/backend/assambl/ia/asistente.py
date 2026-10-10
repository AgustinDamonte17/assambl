"""Lectura de bosquejos y planos con IA (capa 03).

`interpretar_imagen()` lee un bosquejo o un plano y devuelve ambientes como
rectángulos aproximados, con la escala que usó y sus dudas. La IA no dibuja
muros: eso lo hace `capas/casa.py` con reglas. Lo que devuelve el modelo se
valida con pydantic; si no valida, se le devuelve el error una vez para que lo
corrija.

El recorrido guiado de Lumo no pasa por acá: es fijo y vive en `ia/lumo.py`.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from ..modelo.casa import USOS, Pregunta, Rectangulo
from .proveedores import ErrorIA, Imagen, Mensaje, Proveedor, extraer_json

DOMINIO = (
    "Assambl diseña casas de una planta en woodframe (entramado de madera) sobre platea de hormigón, "
    "de 40 a 200 m² cubiertos, con planta ortogonal (muros a 90°) y hasta tres volúmenes adosados. "
    "Dos plantas, subsuelos, curvas o muros inclinados quedan fuera por ahora."
)

USUARIO = (
    "Quien te escribe no es arquitecto ni sabe usar programas de dibujo: es alguien entusiasmado con "
    "construir su casa. Hablá en español rioplatense, con frases cortas y sin jerga; si usás un término "
    "técnico, explicalo en pocas palabras. Nunca lo hagas sentir que respondió mal."
)

async def _pedir_validado(proveedor: Proveedor, sistema: str, mensajes: list[Mensaje], modelo: type[BaseModel],
                          imagenes: list[Imagen] | None = None, esfuerzo: str = "bajo") -> BaseModel:
    texto = await proveedor.completar_json(sistema, mensajes, imagenes, esfuerzo)
    try:
        return modelo.model_validate(extraer_json(texto))
    except (ValidationError, json.JSONDecodeError) as e:
        correccion = mensajes + [
            Mensaje("asistente", texto[:4000]),
            Mensaje("usuario", f"Esa respuesta no cumple el formato pedido ({str(e)[:600]}). "
                               "Devolvé solo el objeto JSON corregido."),
        ]
        texto = await proveedor.completar_json(sistema, correccion, None, esfuerzo)
        try:
            return modelo.model_validate(extraer_json(texto))
        except (ValidationError, json.JSONDecodeError) as e2:
            raise ErrorIA(f"La IA devolvió una respuesta que no se pudo interpretar: {str(e2)[:300]}") from e2


# ---------------------------------------------------------------- imágenes

class Escala(BaseModel):
    fuente: str = Field(description="cotas | referencia_usuario | estimada")
    detalle: str = ""


class Recuadro(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class Interpretacion(BaseModel):
    resumen: str = ""
    ambientes: list[Rectangulo]
    escala: Escala = Escala(fuente="estimada")
    confianza: float = Field(default=0.5, ge=0, le=1)
    recuadro_imagen: Recuadro | None = Field(default=None, description="Parte de la imagen que ocupa la planta, 0..1")
    advertencias: list[str] = []
    preguntas: list[Pregunta] = []


SISTEMA_IMAGEN = "\n\n".join([
    "Sos el lector de planos de Assambl. Recibís un bosquejo a mano, una foto o un plano de una casa de una "
    "planta y lo convertís en ambientes rectangulares con medidas en metros.",
    DOMINIO,
    """Reglas:
- Cada ambiente es un rectángulo de EJES de muro: x0,y0 esquina inferior izquierda, x1,y1 superior derecha. Ambientes vecinos comparten exactamente el borde.
- Eje X hacia la derecha de la imagen, eje Y hacia ARRIBA de la imagen. El origen es la esquina inferior izquierda de la planta.
- Si un ambiente tiene forma de L, partilo en dos rectángulos con el mismo nombre seguido de «(a)» y «(b)».
- Escala: usá las cotas escritas si las hay (fuente "cotas"). Si no, usá la medida de referencia que da el usuario ("referencia_usuario"). Si tampoco, estimá con tamaños típicos: puerta 0,80 m, cama doble 1,40 × 1,90 m, dormitorio 3 × 3,5 m ("estimada") y decilo.
- Los pasillos y circulaciones son ambientes de uso "circulacion".
- Usos válidos: """ + ", ".join(USOS) + """.
- No inventes ambientes que no se ven. Si algo es ilegible o ambiguo, ponelo en "advertencias" o hacé una pregunta con opciones.
- "recuadro_imagen": la porción de la imagen que ocupa la planta, en fracciones de 0 a 1 medidas desde la esquina SUPERIOR izquierda de la imagen.""",
    """Respondé SOLO con un objeto JSON:
{
  "resumen": "qué entendiste, en una oración para el usuario",
  "ambientes": [{"id": "estar", "nombre": "Estar", "uso": "social", "x0": 0, "y0": 0, "x1": 5.2, "y1": 7.1}],
  "escala": {"fuente": "cotas", "detalle": "cota de 12,40 m en el frente"},
  "confianza": 0.7,
  "recuadro_imagen": {"x0": 0.08, "y0": 0.1, "x1": 0.92, "y1": 0.85},
  "advertencias": ["..."],
  "preguntas": [{"texto": "...", "opciones": [{"id": "a", "etiqueta": "...", "detalle": "..."}], "multiple": false, "importante": true}]
}""",
    USUARIO,
])


def _demostracion(ancho_total_m: float | None) -> Interpretacion:
    """Lectura fija para el proveedor simulado: permite probar el recorrido sin IA."""
    f = (ancho_total_m / 12.0) if ancho_total_m else 1.0
    base = [
        ("estar", "Estar-comedor", "social", 0, 0, 5.2, 7.0),
        ("cocina", "Cocina", "cocina", 5.2, 4.3, 8.0, 7.0),
        ("pasillo", "Pasillo", "circulacion", 5.2, 3.2, 12.0, 4.3),
        ("bano", "Baño", "bano", 5.2, 0, 7.3, 3.2),
        ("dorm_1", "Dormitorio 1", "dormitorio", 7.3, 0, 12.0, 3.2),
        ("dorm_2", "Dormitorio 2", "dormitorio", 8.0, 4.3, 12.0, 7.0),
    ]
    return Interpretacion(
        resumen="Modo demostración: no hay proveedor de IA configurado, así que esta planta NO sale de tu imagen.",
        ambientes=[Rectangulo(id=i, nombre=n, uso=u, x0=a * f, y0=b * f, x1=c * f, y1=d * f) for i, n, u, a, b, c, d in base],
        escala=Escala(fuente="referencia_usuario" if ancho_total_m else "estimada", detalle="planta de ejemplo"),
        confianza=0.0,
        advertencias=["Configurá OPENAI_API_KEY (u otro proveedor) en el .env para interpretar imágenes de verdad."],
    )


async def interpretar_imagen(proveedor: Proveedor, imagen: Imagen, notas: str = "",
                             ancho_total_m: float | None = None) -> Interpretacion:
    if proveedor.simulado:
        return _demostracion(ancho_total_m)
    if not proveedor.vision:
        raise ErrorIA(f"El modelo {proveedor.modelo} no acepta imágenes; elegí uno con visión en IA_MODELO.")
    pedido = "Interpretá esta planta."
    if ancho_total_m:
        pedido += f" Referencia del usuario: el frente (ancho total de la planta) mide {ancho_total_m} m."
    if notas.strip():
        pedido += f" Notas del usuario: {notas.strip()}"
    r = await _pedir_validado(proveedor, SISTEMA_IMAGEN, [Mensaje("usuario", pedido)], Interpretacion,
                              imagenes=[imagen], esfuerzo="medio")
    assert isinstance(r, Interpretacion)
    return r
