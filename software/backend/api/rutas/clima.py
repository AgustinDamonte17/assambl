"""Rutas de clima. Los datos vienen de NASA POWER y quedan en caché en disco.

Todo lo que sale de acá es una estimación regional derivada de un reanálisis.
La respuesta incluye la procedencia para que la interfaz pueda decirlo y no
presente, por ejemplo, la velocidad del viento como si fuera medida junto a una
ventana del proyecto.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from assambl.clima import resumen
from assambl.fuentes import power
from assambl.modelo.estados import EstadoFuente
from assambl.modelo.sitio import Clima, Fuente

router = APIRouter()


@router.get("/clima", response_model=dict)
async def clima(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    anios: int = Query(default=power.ANIOS_POR_DEFECTO, ge=1, le=10),
    forzar: bool = False,
) -> dict:
    try:
        crudo = await power.descargar(lat, lon, anios=anios, forzar=forzar)
    except Exception as e:
        raise HTTPException(502, f"NASA POWER no disponible: {e}") from e

    resultado: Clima = resumen.resumir(crudo, lat, lon)
    fuente = Fuente(
        nombre=power.NOMBRE,
        url="https://power.larc.nasa.gov/",
        licencia=power.LICENCIA,
        fecha=datetime.now(timezone.utc).date().isoformat(),
        estado=EstadoFuente.OK,
        resolucion=power.RESOLUCION,
        naturaleza="reanalisis_regional",
        detalle=f"climatología {resultado.periodo_climatologia}; horario {resultado.periodo_horario}",
    )
    return {
        "clima": resultado.model_dump(),
        "fuente": fuente.model_dump(),
        "advertencias": [
            "NASA POWER es un reanálisis global: sus celdas miden decenas de kilómetros. "
            "Sirve para orientar decisiones de diseño, no para describir el microclima del lote.",
            f"El viento está medido a {resultado.altura_medicion_viento_m:.0f} m sobre el terreno abierto de la celda. "
            "No es la velocidad que habrá junto a una ventana.",
            "La radiación es la histórica medida por satélite y es un dato distinto de la posición "
            "astronómica del sol y de la sombra que calcula el modelo 3D.",
        ],
    }
