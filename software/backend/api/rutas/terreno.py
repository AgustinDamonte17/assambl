"""Rutas de la capa 01 — Terreno.

La geometría se arma una sola vez en el backend y se sirve como .glb por capa.
Las rutas son finas: validan la entrada y delegan en el paquete `assambl`.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from assambl.capas import terreno as capa
from assambl.clima import sol as csol
from assambl.fuentes import nasadem
from assambl.generadores import blender
from assambl.modelo.operaciones import EscenaDisponible
from assambl.modelo.sitio import Relieve
from assambl.reglas import r01_terreno

router = APIRouter()

# La escena se guarda en memoria entre pedidos para no rehacer la malla cuando el
# visor pide el .glb o el script de Blender. Es caché regenerable, no estado.
_escenas: dict[str, capa.EscenaTerreno] = {}
_MAX_ESCENAS = 8


class PedidoEscena(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    margen_m: float = Field(default=capa.MARGEN_POR_DEFECTO_M, ge=capa.MARGEN_MIN_M, le=capa.MARGEN_MAX_M)
    vertices: list[tuple[float, float]] = []


class RespuestaEscena(BaseModel):
    ref: str
    relieve: Relieve
    fuentes: list
    advertencias: list[str]
    area_m2: float
    pendiente_pct: float
    pendiente_azimut_deg: float
    posts: list[int]
    paso_m: list[float]
    extension_m: list[float]
    reglas: dict
    bytes_glb: int


def _guardar(escena: capa.EscenaTerreno, pedido: PedidoEscena) -> str:
    semilla = f"{pedido.lat:.6f}_{pedido.lon:.6f}_{pedido.margen_m:.0f}_{pedido.vertices}"
    ref = hashlib.sha1(semilla.encode()).hexdigest()[:12]
    _escenas[ref] = escena
    while len(_escenas) > _MAX_ESCENAS:
        _escenas.pop(next(iter(_escenas)))
    return ref


def escena_disponible(ref: str) -> EscenaDisponible | None:
    """La escena en caché, en la forma que la leen las operaciones."""
    e = _escenas.get(ref)
    if e is None:
        return None
    return EscenaDisponible(ref=ref, lat=e.lat, lon=e.lon, margen_m=e.margen_m, malla=e.malla,
                            provisional=e.relieve.provisional, cota_origen_msnm=e.relieve.cota_origen_msnm)


def _escena(ref: str) -> capa.EscenaTerreno:
    e = _escenas.get(ref)
    if e is None:
        raise HTTPException(404, "Escena no encontrada; volvé a generarla")
    return e


@router.post("/escena", response_model=RespuestaEscena)
async def generar_escena(pedido: PedidoEscena) -> RespuestaEscena:
    escena = await capa.generar(pedido.lat, pedido.lon, pedido.margen_m, pedido.vertices)
    ref = _guardar(escena, pedido)
    ancho, alto = escena.malla.extension_m()
    return RespuestaEscena(
        ref=ref,
        relieve=escena.relieve,
        fuentes=[f.model_dump() for f in escena.fuentes],
        advertencias=escena.advertencias,
        area_m2=escena.area_m2,
        pendiente_pct=escena.pendiente_pct,
        pendiente_azimut_deg=escena.pendiente_azimut_deg,
        posts=[escena.malla.nx, escena.malla.ny],
        paso_m=[round(escena.malla.dx, 2), round(escena.malla.dy, 2)],
        extension_m=[round(ancho, 1), round(alto, 1)],
        reglas=r01_terreno.analizar_lote(
            pedido.vertices, escena.malla, pedido.margen_m, escena.relieve.provisional
        ),
        bytes_glb=len(escena.glb),
    )


@router.get("/escena/{ref}.glb")
def descargar_glb(ref: str) -> Response:
    return Response(
        _escena(ref).glb,
        media_type="model/gltf-binary",
        headers={"Cache-Control": "public, max-age=3600", "Content-Disposition": f'inline; filename="{ref}.glb"'},
    )


@router.get("/escena/{ref}.py")
def descargar_script_blender(ref: str, fecha: str | None = None, hora: float = 12.0,
                             huso_h: float | None = None) -> Response:
    """Script de Blender que reconstruye la escena. Es la salida de la fase de terreno."""
    escena = _escena(ref)
    posicion = _posicion_sol(escena.lat, escena.lon, fecha, hora, huso_h)
    texto = blender.generar(escena, escena.lat, escena.lon, escena.margen_m, posicion)
    return Response(
        texto,
        media_type="text/x-python; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="assambl_terreno_{ref}.py"'},
    )


def _posicion_sol(lat: float, lon: float, fecha: str | None, hora: float, huso_h: float | None):
    dia = date.fromisoformat(fecha) if fecha else date.today()
    huso = csol.huso_por_longitud(lon) if huso_h is None else huso_h
    momento = datetime(dia.year, dia.month, dia.day, tzinfo=timezone(timedelta(hours=huso))) + timedelta(hours=hora)
    return csol.posicion(lat, lon, momento.astimezone(timezone.utc), huso)


@router.get("/sol")
def trayectoria_solar(lat: float, lon: float, fecha: str | None = None, huso_h: float | None = None,
                      paso_min: int = 5) -> dict:
    """Recorrido del sol del día, calculado localmente. El visor interpola entre
    muestras: el algoritmo está implementado una sola vez, acá."""
    dia = date.fromisoformat(fecha) if fecha else date.today()
    if 1440 % max(paso_min, 1):
        raise HTTPException(400, "El paso debe ser un divisor entero de 1440 minutos")
    t = csol.trayectoria(lat, lon, dia, huso_h, paso_min)
    return {
        **t.model_dump(),
        "fechas_clave": csol.fechas_clave(dia.year, hemisferio_sur=lat < 0),
        "procedencia": {
            "fuente": "cálculo local",
            "algoritmo": csol.ALGORITMO,
            "naturaleza": "calculo_local",
            "resolucion": "exacta para el punto; ±0,01° en declinación",
            "advertencia": "Es la posición astronómica del sol, distinta de la radiación histórica de NASA POWER "
                           "y de la sombra que calcula el modelo 3D.",
        },
    }


@router.get("/credencial")
async def estado_credencial() -> dict:
    ok, mensaje = await nasadem.probar_credencial()
    return {"earthdata": ok, "mensaje": mensaje, "mosaicos_en_cache": nasadem.cache_disponible()}


class PedidoAnalisis(BaseModel):
    vertices: list[tuple[float, float]]
    escena_ref: str | None = None
    margen_m: float | None = None
    parametros: dict | None = None


@router.post("/lote/analizar")
def analizar_lote(pedido: PedidoAnalisis) -> dict:
    escena = _escenas.get(pedido.escena_ref) if pedido.escena_ref else None
    return r01_terreno.analizar_lote(
        pedido.vertices,
        escena.malla if escena else None,
        pedido.margen_m,
        escena.relieve.provisional if escena else False,
        pedido.parametros,
    )
