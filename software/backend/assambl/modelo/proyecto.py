"""Esquema de casa.assambl.json (MVP_01 §4.2). Fuente de verdad del proyecto.

Solo se modela lo que la capa 01 necesita hoy. Las capas siguientes agregan
sus secciones sin romper las anteriores: el campo `esquema` lleva la versión.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .estados import Estado

ESQUEMA_ACTUAL = "assambl/proyecto@0.1"


class Ubicacion(BaseModel):
    lat: float
    lon: float
    direccion: str | None = None
    fuente: str = "manual"
    fecha: str | None = None


class SistemaLocal(BaseModel):
    origen_lat: float
    origen_lon: float
    norte: str = "+Y"
    unidades: str = "m"
    proyeccion: str = "equirrectangular local"
    cota_origen_msnm: float | None = None


class Lado(BaseModel):
    longitud_m: float = Field(gt=0)
    rumbo_deg: float = Field(description="Azimut desde el norte, horario, en grados")


class Lote(BaseModel):
    """Poligonal cerrada. Se define por el primer vértice y los lados; el último
    lado cierra el polígono y se deriva. `vertices` es la forma resuelta."""

    origen: tuple[float, float] = (0.0, 0.0)
    lados: list[Lado] = []
    vertices: list[tuple[float, float]] = []
    area_m2: float | None = None
    perimetro_m: float | None = None
    fuente: str = "manual"


class Retiros(BaseModel):
    frente_m: float = 3.0
    fondo_m: float = 3.0
    laterales_m: float = 0.0


class Pendiente(BaseModel):
    porcentaje: float
    direccion_deg: float = Field(description="Azimut hacia donde baja el terreno")
    fuente: str = "dem"


class Terreno(BaseModel):
    estado: Estado = Estado.PENDIENTE_DATOS
    ubicacion: Ubicacion | None = None
    radio_contexto_m: float = 500.0
    sistema_local: SistemaLocal | None = None
    contexto_ref: str | None = Field(default=None, description="Clave de caché del contexto")
    lote: Lote = Lote()
    retiros: Retiros = Retiros()
    pendiente: Pendiente | None = None


class Proyecto(BaseModel):
    esquema: str = ESQUEMA_ACTUAL
    id: str
    nombre: str
    mercado: str = "AR"
    creado: str
    modificado: str
    terreno: Terreno = Terreno()
