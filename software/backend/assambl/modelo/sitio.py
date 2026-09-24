"""Datos del sitio: relieve NASADEM y clima NASA POWER.

Es caché regenerable (MVP_01 §4.2): se identifica por (lat, lon, margen) y puede
volver a descargarse. Coordenadas locales en metros: +X este, +Y norte, +Z arriba,
origen en la ubicación del proyecto.

Cada bloque registra su procedencia para que la interfaz nunca presente una
estimación regional como si fuera una medición del terreno.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .estados import EstadoFuente


class Fuente(BaseModel):
    nombre: str
    url: str
    licencia: str
    fecha: str
    estado: EstadoFuente
    resolucion: str = Field(description="Resolución espacial informada por la fuente, en texto")
    naturaleza: str = Field(description="'medicion_satelital' | 'reanalisis_regional' | 'calculo_local' | 'provisional'")
    detalle: str = ""


class MallaDem(BaseModel):
    """Posts nativos de NASADEM (1 arcosegundo). No se interpola ni se suaviza:
    cada vértice es un post tal como lo publica la fuente."""

    lat_sur: float = Field(description="Latitud del primer post (fila 0)")
    lon_oeste: float = Field(description="Longitud del primer post (columna 0)")
    paso_deg: float
    nx: int
    ny: int
    alturas_msnm: list[float] = Field(description="ny × nx, fila 0 = sur, columna 0 = oeste")
    huecos: int = Field(default=0, description="Posts sin dato en el recorte")
    teselas: list[str] = []
    provisional: bool = False

    @property
    def cantidad(self) -> int:
        return self.nx * self.ny


class Relieve(BaseModel):
    dem: MallaDem | None
    cota_origen_msnm: float | None
    paso_x_m: float = Field(default=0.0, description="Separación este-oeste entre posts, en metros")
    paso_y_m: float = Field(default=0.0, description="Separación norte-sur entre posts, en metros")
    z_min_m: float = 0.0
    z_max_m: float = 0.0
    provisional: bool = False


class ResumenMes(BaseModel):
    mes: int
    t_media_c: float | None = None
    t_max_c: float | None = Field(default=None, description="Máxima del período de climatología, no una media de máximas")
    t_min_c: float | None = Field(default=None, description="Mínima del período de climatología")
    t_max_abs_c: float | None = Field(default=None, description="Máxima de las series horarias recientes")
    t_min_abs_c: float | None = Field(default=None, description="Mínima de las series horarias recientes")
    radiacion_kwh_m2_dia: float | None = None
    viento_medio_ms: float | None = None
    viento_dir_predominante_deg: float | None = Field(
        default=None, description="Centro del sector de 22,5° más frecuente en las series horarias"
    )
    perfil_horario_c: list[float] = Field(default_factory=list, description="24 medias horarias, hora solar local")


class SectorViento(BaseModel):
    desde_deg: float
    hasta_deg: float
    centro_deg: float
    frecuencia_pct: float
    por_velocidad_pct: list[float]
    velocidad_media_ms: float | None = None


class Clima(BaseModel):
    lat: float
    lon: float
    elevacion_power_m: float | None = None
    periodo_climatologia: str = ""
    periodo_horario: str = ""
    anios_horarios: int = 0
    horas: int = 0
    meses: list[ResumenMes] = []
    rosa: list[SectorViento] = []
    bins_velocidad_ms: list[float] = []
    calma_pct: float = 0.0
    grados_dia_calefaccion: float | None = None
    grados_dia_refrigeracion: float | None = None
    base_grados_dia_c: float = 18.0
    altura_medicion_viento_m: float = 10.0
    # Separados porque las unidades difieren entre consultas: la radiación viene en
    # kW-hr/m^2/day en la climatología y en Wh/m^2 en las series horarias.
    parametros_climatologia: dict[str, dict[str, str]] = {}
    parametros_horarios: dict[str, dict[str, str]] = {}


class Sitio(BaseModel):
    esquema: str = "assambl/sitio@0.2"
    lat: float
    lon: float
    margen_m: float
    relieve: Relieve | None = None
    clima: Clima | None = None
    fuentes: list[Fuente] = []
    advertencias: list[str] = []
    generado: str = ""
