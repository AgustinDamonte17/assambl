"""Esquema de casa.assambl.json (MVP_01 §4.2). Fuente de verdad del proyecto.

Solo se modela lo que la capa 01 necesita hoy. Las capas siguientes agregan
sus secciones sin romper las anteriores: el campo `esquema` lleva la versión.
El espejo TypeScript es frontend/src/modelo/proyecto.ts y deben coincidir: el
backend valida con este esquema cada proyecto que recibe una operación.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .estados import Estado

ESQUEMA_ACTUAL = "assambl/proyecto@0.2"

MARGEN_MIN_M = 100.0
MARGEN_MAX_M = 1000.0
MARGEN_POR_DEFECTO_M = 500.0


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
    paso_dem_m: float | None = None


class Terreno(BaseModel):
    estado: Estado = Estado.PENDIENTE_DATOS
    ubicacion: Ubicacion | None = None
    margen_m: float = Field(default=MARGEN_POR_DEFECTO_M, ge=MARGEN_MIN_M, le=MARGEN_MAX_M)
    sistema_local: SistemaLocal | None = None
    escena_ref: str | None = Field(default=None, description="Clave de caché de la escena generada")
    lote: Lote = Lote()
    retiros: Retiros = Retiros()
    pendiente: Pendiente | None = None
    # Preferencias de estudio del asoleamiento: no son decisiones de diseño y no
    # pasan por operaciones (docs/decisiones/0002_operaciones_e_historial.md).
    fecha_sol: str | None = None
    hora_sol: float = 12.0
    huso_h: float | None = None

    @field_validator("margen_m", mode="before")
    @classmethod
    def _margen_en_rango(cls, v: float) -> float:
        """Proyectos guardados con el límite anterior (2000 m) se abren recortados."""
        return min(max(float(v), MARGEN_MIN_M), MARGEN_MAX_M)


class Proyecto(BaseModel):
    esquema: str = ESQUEMA_ACTUAL
    id: str
    nombre: str
    mercado: str = "AR"
    creado: str
    modificado: str
    terreno: Terreno = Terreno()
