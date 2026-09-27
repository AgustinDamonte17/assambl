"""Rutas de la capa 01 — Terreno.

El modelo del sitio (lote y entorno reconstruidos desde la imagen satelital, con el
terreno supuesto plano) se arma una sola vez en el backend y se sirve como .glb.
Las rutas son finas: validan la entrada y delegan en el paquete `assambl`.

El relieve de NASADEM está en pausa (docs/decisiones/0005_modelo_del_sitio.md): su
código sigue en `assambl/fuentes/nasadem.py` y `assambl/capas/terreno.py`.
"""

from __future__ import annotations

import hashlib
from datetime import date

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from assambl.clima import sol as csol
from assambl.guia import terreno as guia
from assambl.modelo.operaciones import EscenaDisponible
from assambl.modelo.proyecto import MARGEN_MAX_M, MARGEN_MIN_M, MARGEN_POR_DEFECTO_M, Proyecto
from assambl.reglas import r01_terreno
from assambl.sitio import interpretacion_ia
from assambl.sitio import modelo as sitio

router = APIRouter()

# El modelo se guarda en memoria entre pedidos para que el visor pida el .glb sin
# rehacerlo. Es caché regenerable: las imágenes, OSM y la interpretación con IA
# quedan además en la caché de disco, así que rehacerlo después es rápido.
_escenas: dict[str, sitio.ModeloSitio] = {}
_MAX_ESCENAS = 8


class PedidoEscena(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    margen_m: float = Field(default=MARGEN_POR_DEFECTO_M, ge=MARGEN_MIN_M, le=MARGEN_MAX_M)
    vertices: list[tuple[float, float]] = []


class RespuestaEscena(BaseModel):
    ref: str
    entrada: PedidoEscena = Field(description="Ubicación, entorno y lote para los que se generó")
    fuentes: list
    advertencias: list[str]
    resumen: dict
    arboles_lote: list[dict]
    area_m2: float
    bytes_glb: int


def _referencia(pedido: PedidoEscena) -> str:
    # Si la IA se configura después, el mismo lote debe poder reinterpretarse.
    ia = "ia" if interpretacion_ia.disponible() else "sin-ia"
    semilla = f"{sitio.VERSION}_{ia}_{pedido.lat:.6f}_{pedido.lon:.6f}_{pedido.margen_m:.0f}_{pedido.vertices}"
    return hashlib.sha1(semilla.encode()).hexdigest()[:12]


def escena_disponible(ref: str) -> EscenaDisponible | None:
    """La escena en caché, en la forma que la leen las operaciones."""
    e = _escenas.get(ref)
    if e is None:
        return None
    return EscenaDisponible(ref=ref, lat=e.lat, lon=e.lon, margen_m=e.margen_m,
                            vertices=tuple((float(x), float(y)) for x, y in e.vertices))


class ContextoEscenas:
    def escena(self, ref: str) -> EscenaDisponible | None:
        return escena_disponible(ref)


def _escena(ref: str) -> sitio.ModeloSitio:
    e = _escenas.get(ref)
    if e is None:
        raise HTTPException(404, "Modelo del sitio no encontrado; volvé a generarlo")
    return e


def _respuesta(ref: str, e: sitio.ModeloSitio) -> RespuestaEscena:
    from assambl.geometria import poligono

    return RespuestaEscena(
        ref=ref,
        entrada=PedidoEscena(lat=e.lat, lon=e.lon, margen_m=e.margen_m, vertices=e.vertices),
        fuentes=[f.model_dump() for f in e.fuentes],
        advertencias=e.advertencias,
        resumen=e.resumen,
        arboles_lote=e.arboles_lote,
        area_m2=round(poligono.area(e.vertices), 2) if len(e.vertices) >= 3 else 0.0,
        bytes_glb=len(e.glb),
    )


@router.post("/escena", response_model=RespuestaEscena)
async def generar_escena(pedido: PedidoEscena) -> RespuestaEscena:
    """Reconstruye el lote y su entorno a partir de la imagen satelital."""
    ref = _referencia(pedido)
    e = _escenas.get(ref)
    if e is None:
        e = await sitio.generar(pedido.lat, pedido.lon, pedido.margen_m, pedido.vertices)
        _escenas[ref] = e
        while len(_escenas) > _MAX_ESCENAS:
            _escenas.pop(next(iter(_escenas)))
    return _respuesta(ref, e)


@router.get("/escena/{ref}.glb")
def descargar_glb(ref: str) -> Response:
    return Response(
        _escena(ref).glb,
        media_type="model/gltf-binary",
        headers={"Cache-Control": "public, max-age=3600", "Content-Disposition": f'inline; filename="{ref}.glb"'},
    )


@router.post("/requisitos")
def requisitos_para_avanzar(proyecto: Proyecto) -> dict:
    """Qué falta para confirmar el terreno y empezar a diseñar la casa."""
    return guia.requisitos(proyecto, ContextoEscenas())


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


class PedidoAnalisis(BaseModel):
    vertices: list[tuple[float, float]]
    escena_ref: str | None = None
    margen_m: float | None = None
    parametros: dict | None = None


@router.post("/lote/analizar")
def analizar_lote(pedido: PedidoAnalisis) -> dict:
    return r01_terreno.analizar_lote(pedido.vertices, None, pedido.margen_m, False, pedido.parametros)
