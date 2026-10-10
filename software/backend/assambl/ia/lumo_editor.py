"""Lumo en el editor: de un pedido en palabras a acciones sobre la planta.

El usuario escribe «quiero ampliar este ambiente» o «cambiá la entrada de lugar».
Un modelo de lenguaje lo traduce a **acciones de una lista cerrada**; no escribe
muros ni coordenadas. Las acciones las ejecuta el editor con las mismas
operaciones que usa la interfaz (`frontend/src/pasos/casa/acciones.ts`), las
muestra aplicadas y el usuario confirma o vuelve atrás.

Si al pedido le falta un dato que cambia el resultado, Lumo no adivina:
devuelve una pregunta con opciones y ninguna acción.

El contexto (ambientes, muros, selección) lo arma el editor y llega ya resumido.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..modelo.casa import Lado, Pregunta, Uso
from .asistente import USUARIO, _pedir_validado
from .proveedores import Mensaje, Proveedor

TIPOS = ("ampliar", "mover_muro", "quitar_muro", "integrar", "renombrar", "quitar_ambiente",
         "agregar_abertura", "quitar_abertura", "cambiar_abertura", "mover_entrada")


class Accion(BaseModel):
    """Una operación del editor. Cada tipo usa algunos campos; el resto queda vacío."""

    model_config = ConfigDict(extra="ignore")

    tipo: Literal[TIPOS]  # type: ignore[valid-type]
    ambiente: str | None = None
    destino: str | None = None
    lado: Lado | None = None
    metros: float | None = Field(default=None, ge=-10, le=10)
    muro: str | None = None
    abertura: str | None = None
    catalogo: str | None = None
    clase: Literal["ventana", "puerta", "puerta_ventana"] | None = None
    nombre: str | None = Field(default=None, max_length=60)
    uso: Uso | None = None


class TurnoEditor(BaseModel):
    mensaje: str
    pregunta: Pregunta | None = None
    acciones: list[Accion] = Field(default=[], max_length=8)


class MensajeEditor(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str = Field(max_length=2000)


SISTEMA = "\n\n".join([
    "Sos Lumo, el asistente de Assambl dentro del editor de planta de una casa de una sola planta, con muros a 90°. "
    "El usuario te pide cambios con sus palabras. Vos no dibujás: elegís acciones de una lista y el editor las "
    "ejecuta, las muestra aplicadas y le pide al usuario que confirme o vuelva atrás.",
    USUARIO,
    """Cómo decidir:
- Si el pedido es claro, devolvé las acciones y contá en una o dos oraciones qué hacés y qué efecto tiene («Corro el muro norte del dormitorio 1 m hacia afuera: la casa crece de ese lado»).
- Si falta un dato que cambia el resultado (hacia qué lado ampliar, a qué lado llevar la entrada, con qué ambiente integrar), NO adivines: devolvé "pregunta" con 2 a 4 opciones concretas tomadas del contexto y "acciones": []. Cada opción tiene que poder responderse sola, por ejemplo «Hacia el norte · la casa crece hacia el frente».
- Cuánto ampliar: si no lo dice, usá 1 metro y decilo.
- «Este ambiente», «esto», «acá» se refieren a la selección del contexto. Si no hay selección y no nombra el ambiente, preguntá cuál.
- Ampliar un ambiente corre un muro entero: si ese muro lo comparte con otros ambientes, también cambian. Avisalo. Hacia un lado donde hay un vecino, el vecino se achica.
- Usá solo ids que estén en el contexto. No inventes ambientes, muros ni códigos de catálogo.
- Si el pedido no se puede hacer con estas acciones (dibujar un ambiente nuevo, cambiar la forma de la casa), decilo con amabilidad y sugerí la herramienta del editor que sirve: Muro, Puerta / ventana o Ambiente.
- Nunca describas coordenadas.
- "mensaje": dos oraciones como mucho. Si hacés una pregunta, no la repitas en "mensaje": ahí va solo una línea de contexto, o nada.""",
    """Acciones disponibles:
- {"tipo": "ampliar", "ambiente": id, "lado": "norte|sur|este|oeste", "metros": n}  Corre el muro de ese lado del ambiente. Con metros negativos lo achica.
- {"tipo": "mover_muro", "muro": id, "metros": n}  Corre un muro en perpendicular: positivo hacia el norte o el este.
- {"tipo": "quitar_muro", "muro": id}
- {"tipo": "integrar", "ambiente": id, "destino": id}  Quita el muro entre dos ambientes vecinos y los une en uno, que conserva el nombre y el uso de "destino". Es lo que hace falta para «cocina abierta» o «integrar al living».
- {"tipo": "renombrar", "ambiente": id, "nombre": texto, "uso": uso}  "uso" es opcional.
- {"tipo": "quitar_ambiente", "ambiente": id}  Le quita el nombre al espacio; los muros quedan.
- {"tipo": "agregar_abertura", "ambiente": id, "clase": "ventana|puerta|puerta_ventana", "lado": lado, "destino": id}  "lado" y "destino" son opcionales: una ventana va a un muro exterior; una puerta, hacia el ambiente "destino".
- {"tipo": "quitar_abertura", "abertura": id}
- {"tipo": "cambiar_abertura", "abertura": id, "catalogo": codigo}  La reemplaza por otro ítem del catálogo, en el mismo lugar.
- {"tipo": "mover_entrada", "lado": lado, "ambiente": id}  Saca la puerta de entrada y la pone en el muro exterior de ese lado. "ambiente" es opcional: por defecto, el estar.""",
    """Respondé SOLO con un objeto JSON:
{
  "mensaje": "texto breve para el usuario",
  "pregunta": null | {"texto": "una sola pregunta", "opciones": [{"id": "corto", "etiqueta": "texto del botón", "detalle": "qué cambia"}]},
  "acciones": []
}""",
])

SIN_IA = ("Para pedirme cambios con tus palabras hace falta configurar una clave de IA en el .env. Mientras tanto puedo "
          "resolver los problemas de la lista «Para resolver» con el botón Resolver, y vos podés usar las herramientas "
          "del editor.")


async def pedir_cambios(proveedor: Proveedor, texto: str, contexto: dict,
                        historial: list[MensajeEditor] | None = None) -> TurnoEditor:
    if proveedor.simulado:
        return TurnoEditor(mensaje=SIN_IA)
    mensajes = [Mensaje(m.rol, m.texto) for m in (historial or [])[-8:]]
    mensajes.append(Mensaje("usuario", f"{texto}\n\n[Contexto de la planta (JSON): {json.dumps(contexto, ensure_ascii=False)}]"))
    r = await _pedir_validado(proveedor, SISTEMA, mensajes, TurnoEditor)
    assert isinstance(r, TurnoEditor)
    return r
