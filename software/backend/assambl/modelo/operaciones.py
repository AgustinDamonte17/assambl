"""Operaciones del dominio (MVP_01 §4.4). Único camino para modificar un proyecto.

La interfaz y el asistente llaman las mismas operaciones con los mismos
parámetros validados; ninguno escribe el proyecto directamente. Cada operación
aplicada devuelve el proyecto nuevo y un registro para el historial: qué se
pidió, quién lo pidió, qué campos cambiaron y cómo quedó el estado de la capa.

`aplicar` es una función pura: no guarda nada, no sale a la red y no modifica el
proyecto que recibe. Lo que necesita del mundo exterior (hoy, la malla de una
escena ya generada) le llega por un `Contexto`. La persistencia del proyecto y
del historial es de otra capa (docs/decisiones/0001_almacenamiento.md).
"""

from __future__ import annotations

import inspect
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Any, ClassVar, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ..geometria import malla as gmalla
from ..geometria import poligono
from ..reglas import r01_terreno
from .estados import Estado
from .proyecto import (
    ESQUEMA_ACTUAL,
    MARGEN_MAX_M,
    MARGEN_MIN_M,
    Lado,
    Pendiente,
    Proyecto,
    Retiros,
    SistemaLocal,
    Ubicacion,
)

Autor = Literal["usuario", "asistente", "sistema"]
Coordenada = Annotated[float, Field(allow_inf_nan=False)]

MAX_VERTICES_LOTE = 200
RETIRO_MAX_M = 50.0


class OperacionInvalida(ValueError):
    """La operación no se puede aplicar a este proyecto. El mensaje es para el usuario."""


# ---------------------------------------------------------------------------
# Catálogo de operaciones. El docstring de cada clase es su descripción pública:
# la ve el usuario en la documentación de la API y la verá el asistente como
# descripción de la herramienta, así que tiene que ser corta y precisa.
# ---------------------------------------------------------------------------


class _Operacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Las que el asistente no debe ofrecer: vinculan resultados de cálculo, no
    # expresan una intención del usuario.
    para_asistente: ClassVar[bool] = True
    capa: ClassVar[str] = "01"


class RenombrarProyecto(_Operacion):
    """Cambia el nombre del proyecto."""

    tipo: Literal["renombrar_proyecto"] = "renombrar_proyecto"
    nombre: str = Field(min_length=1, max_length=120)
    capa: ClassVar[str] = "proyecto"


class DefinirUbicacion(_Operacion):
    """Fija el origen del proyecto (0, 0) en latitud y longitud. Si el origen se mueve
    y ya hay un lote dibujado, el lote queda desactualizado: sus vértices están en
    metros respecto del origen anterior."""

    tipo: Literal["definir_ubicacion"] = "definir_ubicacion"
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    direccion: str | None = Field(default=None, max_length=300)
    fuente: str = Field(default="manual", max_length=40, description="mapa, coordenadas, nominatim o manual")


class DefinirMargen(_Operacion):
    """Define cuántos metros de relieve se modelan alrededor del origen."""

    tipo: Literal["definir_margen"] = "definir_margen"
    margen_m: float = Field(ge=MARGEN_MIN_M, le=MARGEN_MAX_M)


class DefinirLote(_Operacion):
    """Reemplaza la poligonal del lote. Vértices en metros, +X este, +Y norte, respecto
    del origen; el último vértice cierra con el primero. Con menos de tres vértices
    el lote queda sin definir."""

    tipo: Literal["definir_lote"] = "definir_lote"
    vertices: list[tuple[Coordenada, Coordenada]] = Field(max_length=MAX_VERTICES_LOTE)


class DefinirRetiros(_Operacion):
    """Define los retiros de frente, fondo y laterales, en metros."""

    tipo: Literal["definir_retiros"] = "definir_retiros"
    frente_m: float = Field(ge=0, le=RETIRO_MAX_M)
    fondo_m: float = Field(ge=0, le=RETIRO_MAX_M)
    laterales_m: float = Field(ge=0, le=RETIRO_MAX_M)


class VincularEscena(_Operacion):
    """Asocia al proyecto una escena de relieve ya generada, identificada por su
    referencia. La cota del origen y la pendiente salen de la escena, no de la
    operación."""

    tipo: Literal["vincular_escena"] = "vincular_escena"
    ref: str = Field(pattern=r"^[0-9a-f]{12}$")
    para_asistente: ClassVar[bool] = False


TIPOS = (RenombrarProyecto, DefinirUbicacion, DefinirMargen, DefinirLote, DefinirRetiros, VincularEscena)

Operacion = Annotated[
    RenombrarProyecto | DefinirUbicacion | DefinirMargen | DefinirLote | DefinirRetiros | VincularEscena,
    Field(discriminator="tipo"),
]
ADAPTADOR = TypeAdapter(Operacion)


def catalogo() -> list[dict]:
    """Descripción de cada operación con el esquema JSON de sus parámetros.

    Es el contrato que comparten la interfaz y el asistente: de acá saldrán las
    definiciones de herramientas del asistente, sin escribirlas dos veces.
    """
    salida = []
    for clase in TIPOS:
        esquema = clase.model_json_schema()
        esquema["properties"].pop("tipo", None)
        esquema.pop("title", None)
        esquema.pop("description", None)
        salida.append({
            "tipo": clase.model_fields["tipo"].default,
            "capa": clase.capa,
            "descripcion": inspect.cleandoc(clase.__doc__ or ""),
            "para_asistente": clase.para_asistente,
            "parametros": esquema,
        })
    return salida


# ---------------------------------------------------------------------------
# Contexto: lo que una operación necesita leer y no está en el proyecto.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EscenaDisponible:
    """Lo que una operación necesita de una escena generada."""

    ref: str
    lat: float
    lon: float
    margen_m: float
    malla: gmalla.MallaLocal
    provisional: bool
    cota_origen_msnm: float | None


class Contexto(Protocol):
    def escena(self, ref: str) -> EscenaDisponible | None: ...


class SinContexto:
    def escena(self, ref: str) -> EscenaDisponible | None:
        return None


# ---------------------------------------------------------------------------
# Registro para el historial
# ---------------------------------------------------------------------------


class RegistroOperacion(BaseModel):
    id: str
    proyecto_id: str
    operacion: dict
    autor: Autor
    fecha: str
    cambios: list[str] = Field(description="Campos modificados, por ejemplo terreno.lote.vertices")
    estado_antes: Estado
    estado_despues: Estado
    avisos: list[str] = []


class Resultado(BaseModel):
    proyecto: Proyecto
    registro: RegistroOperacion
    analisis_lote: dict | None = Field(default=None, description="Resultado de R01 si la operación lo recalculó")


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------


def ahora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def aplicar(proyecto: Proyecto, operacion: Operacion, autor: Autor = "usuario",
            contexto: Contexto | None = None, ahora: str | None = None) -> Resultado:
    """Aplica una operación y devuelve el proyecto nuevo con su registro.

    Lanza `OperacionInvalida` si la operación no tiene sentido sobre este proyecto
    (los parámetros fuera de rango ya los rechaza la validación del esquema).
    """
    if proyecto.esquema != ESQUEMA_ACTUAL:
        raise OperacionInvalida(f"Esquema no compatible: {proyecto.esquema} (se esperaba {ESQUEMA_ACTUAL})")
    contexto = contexto or SinContexto()
    ahora = ahora or ahora_iso()
    p = proyecto.model_copy(deep=True)
    t = p.terreno
    avisos: list[str] = []
    analisis: dict | None = None

    match operacion:
        case RenombrarProyecto(nombre=nombre):
            p.nombre = nombre.strip() or p.nombre

        case DefinirUbicacion():
            cambio_origen = (t.ubicacion is None or t.ubicacion.lat != operacion.lat
                             or t.ubicacion.lon != operacion.lon)
            cota = None if cambio_origen or t.sistema_local is None else t.sistema_local.cota_origen_msnm
            t.ubicacion = Ubicacion(lat=operacion.lat, lon=operacion.lon, direccion=operacion.direccion,
                                    fuente=operacion.fuente, fecha=ahora)
            t.sistema_local = SistemaLocal(origen_lat=operacion.lat, origen_lon=operacion.lon,
                                           cota_origen_msnm=cota)
            if cambio_origen:
                t.pendiente = None
                if t.lote.vertices:
                    t.estado = Estado.DESACTUALIZADO
                    avisos.append("El origen se movió: el lote conserva sus medidas pero quedó desactualizado. "
                                  "Revisalo y confirmalo.")

        case DefinirMargen(margen_m=margen):
            t.margen_m = margen
            analisis = _evaluar_terreno(p, contexto)

        case DefinirLote(vertices=vertices):
            v = [(float(x), float(y)) for x, y in vertices]
            t.lote.vertices = v
            t.lote.origen = v[0] if v else (0.0, 0.0)
            t.lote.lados = [Lado(longitud_m=round(l["longitud_m"], 3), rumbo_deg=round(l["rumbo_deg"], 2))
                            for l in poligono.lados(v)] if len(v) >= 2 else []
            t.lote.area_m2 = round(poligono.area(v), 2) if len(v) >= 3 else None
            t.lote.perimetro_m = round(poligono.perimetro(v), 2) if len(v) >= 2 else None
            # Redefinir el lote es lo que saca al terreno de «desactualizado».
            analisis = _evaluar_terreno(p, contexto, forzar=True)

        case DefinirRetiros():
            t.retiros = Retiros(frente_m=operacion.frente_m, fondo_m=operacion.fondo_m,
                                laterales_m=operacion.laterales_m)

        case VincularEscena(ref=ref):
            escena = contexto.escena(ref)
            if escena is None:
                raise OperacionInvalida("Escena no encontrada; volvé a generarla")
            if not _escena_corresponde(p, escena):
                raise OperacionInvalida("La escena corresponde a otro origen o a otro margen; volvé a generarla")
            t.escena_ref = ref
            if t.sistema_local is not None:
                t.sistema_local.cota_origen_msnm = escena.cota_origen_msnm
            analisis = _evaluar_terreno(p, contexto)

        case _:
            raise OperacionInvalida(f"Operación desconocida: {operacion!r}")

    cambios = _diferencias(proyecto.model_dump(mode="json"), p.model_dump(mode="json"))
    if cambios:
        p.modificado = ahora
    registro = RegistroOperacion(
        id=uuid.uuid4().hex,
        proyecto_id=p.id,
        operacion=operacion.model_dump(mode="json"),
        autor=autor,
        fecha=ahora,
        cambios=cambios,
        estado_antes=proyecto.terreno.estado,
        estado_despues=t.estado,
        avisos=avisos,
    )
    return Resultado(proyecto=p, registro=registro, analisis_lote=analisis)


def _escena_corresponde(p: Proyecto, escena: EscenaDisponible) -> bool:
    u = p.terreno.ubicacion
    return (u is not None and math.isclose(u.lat, escena.lat, abs_tol=1e-7)
            and math.isclose(u.lon, escena.lon, abs_tol=1e-7)
            and math.isclose(p.terreno.margen_m, escena.margen_m, abs_tol=0.5))


def _evaluar_terreno(p: Proyecto, contexto: Contexto, forzar: bool = False) -> dict | None:
    """Vuelve a correr R01 sobre el lote y actualiza estado y pendiente.

    Un terreno desactualizado sigue así hasta que el lote se redefine (`forzar`):
    que las reglas pasen no alcanza para confirmar un lote que se corrió de lugar.
    """
    t = p.terreno
    if t.estado == Estado.DESACTUALIZADO and not forzar:
        return None
    if t.ubicacion is None:
        t.estado = Estado.PENDIENTE_DATOS
        t.pendiente = None
        return None

    escena = contexto.escena(t.escena_ref) if t.escena_ref else None
    if escena is not None and not _escena_corresponde(p, escena):
        escena = None
    analisis = r01_terreno.analizar_lote(
        t.lote.vertices,
        escena.malla if escena else None,
        t.margen_m,
        escena.provisional if escena else False,
    )
    t.estado = Estado(analisis["estado"])
    t.pendiente = Pendiente(**analisis["pendiente"]) if analisis["pendiente"] else None
    return analisis


def _diferencias(antes: Any, despues: Any, ruta: str = "", profundidad: int = 3) -> list[str]:
    """Rutas de los campos que cambiaron, hasta `profundidad` niveles. Las listas se
    comparan enteras. `modificado` no cuenta como cambio."""
    if ruta == "modificado":
        return []
    if isinstance(antes, dict) and isinstance(despues, dict) and profundidad > 0:
        salida: list[str] = []
        for clave in sorted(set(antes) | set(despues)):
            sub = f"{ruta}.{clave}" if ruta else clave
            salida += _diferencias(antes.get(clave), despues.get(clave), sub, profundidad - 1)
        return salida
    return [] if antes == despues else [ruta]
