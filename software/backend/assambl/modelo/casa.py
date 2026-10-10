"""Esquema de la capa 03 · Casa: decisiones del usuario y planta (assambl/casa@0.1).

La planta sigue el formato de `casos/angus_ranch.assambl.json`: muros por eje con
sus aberturas, ambientes con contorno interior y sistemas constructivos. Los
modelos son permisivos (`extra="allow"`) porque la casa lleva secciones de otras
capas (cubiertas, instalaciones, mobiliario) que este paso no toca y debe
conservar intactas.

Las **decisiones** son lo poco que el usuario elige con Lumo (cuántos dormitorios,
cocina abierta o cerrada, tamaño). No son geometría: de ellas sale la planta base.
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

class _Abierto(BaseModel):
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------- conversación

class Decisiones(BaseModel):
    """Lo que el usuario decide con Lumo. Lo que falta se completa con el valor más común."""

    dormitorios: int | None = Field(default=None, ge=1, le=4)
    cocina: Literal["abierta", "cerrada"] | None = None
    tamano: Literal["compacta", "comoda", "amplia"] | None = None


class Opcion(BaseModel):
    id: str
    etiqueta: str
    detalle: str = ""


class Pregunta(BaseModel):
    texto: str
    opciones: list[Opcion] = []
    multiple: bool = False
    importante: bool = Field(default=True, description="Decisión que cambia la forma de la casa")


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


Lado = Literal["norte", "sur", "este", "oeste"]


class PuertaDeseada(BaseModel):
    """Dónde va la puerta de un ambiente cuando el generador no debe elegirlo solo."""

    hacia: str | None = Field(default=None, description="Id del ambiente al que abre")
    lado: Lado | None = Field(default=None, description="Lado del rectángulo donde va")
    extremo: Literal["inicio", "fin"] = Field(default="inicio", description="Extremo del muro, en el sentido de su eje")
    margen_m: float = Field(default=0.15, ge=0.1, description="Distancia de la puerta a ese extremo")


class AccesoDeseado(BaseModel):
    """Puerta de entrada a la casa sobre un lado exterior del rectángulo."""

    lado: Lado
    centro_m: float | None = Field(default=None, description="Coordenada del centro de la puerta a lo largo del lado")


class Rectangulo(BaseModel):
    """Ambiente como rectángulo de ejes de muro. Es la forma en que el generador
    de la planta base y la lectura de imágenes describen una planta ortogonal."""

    id: str
    nombre: str
    uso: Uso = "otro"
    x0: float
    y0: float
    x1: float
    y1: float
    grupo: str | None = Field(default=None, description="Rectángulos del mismo grupo forman un solo ambiente, sin muro entre ellos")
    puerta: PuertaDeseada | None = None
    acceso: AccesoDeseado | None = None
