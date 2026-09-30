"""Esquema de la capa 03 · Casa: programa de necesidades y planta (assambl/casa@0.1).

La planta sigue el formato de `casos/angus_ranch.assambl.json`: muros por eje con
sus aberturas, ambientes con contorno interior y sistemas constructivos. Los
modelos son permisivos (`extra="allow"`) porque la casa lleva secciones de otras
capas (cubiertas, instalaciones, mobiliario) que este paso no toca y debe
conservar intactas.

El **programa** es lo que el usuario quiere («tres dormitorios, 120 m², estar al
norte»). Lo construye la conversación con el asistente o el formulario, y de él
salen las alternativas de planta. No es geometría: es la lista de ambientes con
superficies objetivo y las decisiones tomadas.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .estados import Estado

ESQUEMA_CASA = "assambl/casa@0.1"

Uso = Literal[
    "social", "cocina", "dormitorio", "bano", "lavadero", "oficina",
    "vestidor", "deposito", "circulacion", "otro",
]
USOS: tuple[str, ...] = Uso.__args__  # type: ignore[attr-defined]

# Superficie orientativa por uso (m²) cuando el usuario no la dice. Son valores
# de partida para una vivienda de una planta, no mínimos normativos.
AREA_TIPICA_M2: dict[str, float] = {
    "social": 30.0, "cocina": 9.0, "dormitorio": 11.0, "bano": 4.5, "lavadero": 4.0,
    "oficina": 8.0, "vestidor": 4.0, "deposito": 3.0, "circulacion": 6.0, "otro": 8.0,
}


class _Abierto(BaseModel):
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------- programa

class AmbientePrograma(_Abierto):
    id: str
    nombre: str
    uso: Uso = "otro"
    area_m2: float | None = Field(default=None, gt=0, le=200)
    principal: bool = Field(default=False, description="Dormitorio principal, en suite, etc.")
    notas: str = ""


class Programa(_Abierto):
    superficie_objetivo_m2: float | None = Field(default=None, gt=0, le=400)
    ambientes: list[AmbientePrograma] = []
    cocina_integrada: bool | None = Field(default=None, description="Cocina dentro del estar-comedor")
    galeria: bool | None = None
    prioridades: list[str] = []
    notas: list[str] = []


# ---------------------------------------------------------------- conversación

class Opcion(BaseModel):
    id: str
    etiqueta: str
    detalle: str = ""


class Pregunta(BaseModel):
    texto: str
    opciones: list[Opcion] = []
    multiple: bool = False
    importante: bool = Field(default=True, description="Decisión que cambia la forma de la casa")


class MensajeChat(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str


class RespuestaAsistente(BaseModel):
    mensaje: str
    pregunta: Pregunta | None = None
    programa: Programa
    listo: bool = Field(default=False, description="El programa alcanza para proponer plantas")


# ---------------------------------------------------------------- planta

class Eje(BaseModel):
    desde_m: tuple[float, float]
    hasta_m: tuple[float, float]


class Abertura(_Abierto):
    id: str
    tipo: Literal["puerta", "ventana", "ventana_corrediza", "paso"] = "ventana"
    posicion_m: float = Field(description="Distancia desde el inicio del eje al borde de la abertura")
    ancho_m: float = Field(gt=0)
    antepecho_m: float = 0.0
    dintel_m: float = 2.05
    catalogo: str | None = None
    estado: Estado | None = None


class Muro(_Abierto):
    id: str
    sistema: str = "tabique"
    eje: Eje
    aberturas: list[Abertura] = []
    estado: Estado | None = None


class Ambiente(_Abierto):
    id: str
    nombre: str
    uso: Uso = "otro"
    contorno_m: list[tuple[float, float]] | None = None
    estado: Estado | None = None


class Rectangulo(BaseModel):
    """Ambiente como rectángulo de ejes de muro. Es la forma en que el generador
    de alternativas y la lectura de imágenes describen una planta ortogonal."""

    id: str
    nombre: str
    uso: Uso = "otro"
    x0: float
    y0: float
    x1: float
    y1: float
