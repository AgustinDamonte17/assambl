"""R01 · Reglas de la capa Terreno (MVP_01 §3.1 y §2).

Parámetros con valor por defecto y rango; los umbrales son de partida y se
ajustan por proyecto. Ninguna regla codifica normativa municipal.
"""

from __future__ import annotations

import math

from ..geometria import malla as gmalla
from ..geometria import poligono
from ..modelo.estados import Estado
from . import Verificacion

VERSION = "0.2"
ORIGEN = "MVP_01 §2 (dominio) y §3.1 (reglas de terreno)"

PARAMETROS = {
    "pendiente_max_pct": 5.0,       # dominio MVP_01: pendiente uniforme ≤ 5 %
    "area_lote_min_m2": 150.0,      # aviso: por debajo, difícil implantar 40 m² + retiros
    "lado_min_m": 1.0,              # lados menores se consideran error de carga
    "posts_min_por_lado": 2.0,      # por debajo, el DEM no resuelve la pendiente interna
}


def analizar_lote(vertices: list[tuple[float, float]], malla: gmalla.MallaLocal | None = None,
                  margen_m: float | None = None, provisional: bool = False,
                  parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    verificaciones: list[Verificacion] = []
    n = len(vertices)

    simple = n >= 3 and poligono.es_simple(vertices)
    verificaciones.append(Verificacion(
        id="R01.01", version=VERSION, origen=ORIGEN,
        descripcion="El lote es un polígono cerrado sin autointersecciones",
        estado=Estado.COMPROBADO_POR_REGLAS if simple else Estado.PENDIENTE_DATOS,
        detalle="" if simple else ("Faltan vértices (mínimo 3)" if n < 3 else "Los lados se cruzan"),
    ))

    area = poligono.area(vertices) if n >= 3 else 0.0
    perimetro = poligono.perimetro(vertices) if n >= 2 else 0.0
    lados = poligono.lados(vertices) if n >= 2 else []
    centro = poligono.centroide(vertices) if n >= 3 else (0.0, 0.0)

    if simple:
        cortos = [i + 1 for i, l in enumerate(lados) if l["longitud_m"] < p["lado_min_m"]]
        verificaciones.append(Verificacion(
            id="R01.02", version=VERSION, origen=ORIGEN,
            descripcion=f"Ningún lado menor a {p['lado_min_m']:.1f} m",
            estado=Estado.COMPROBADO_POR_REGLAS if not cortos else Estado.PENDIENTE_REVISION,
            detalle="" if not cortos else f"Lados {cortos} demasiado cortos; probable error de carga",
            parametros={"lado_min_m": p["lado_min_m"]},
        ))
        verificaciones.append(Verificacion(
            id="R01.03", version=VERSION, origen=ORIGEN,
            descripcion=f"Superficie del lote ≥ {p['area_lote_min_m2']:.0f} m²",
            estado=Estado.COMPROBADO_POR_REGLAS if area >= p["area_lote_min_m2"] else Estado.PENDIENTE_REVISION,
            detalle="" if area >= p["area_lote_min_m2"] else f"Superficie {area:.1f} m²: verificar que admita la casa y los retiros",
            parametros={"area_lote_min_m2": p["area_lote_min_m2"]},
        ))
        if margen_m:
            fuera = [i + 1 for i, (x, y) in enumerate(vertices) if max(abs(x), abs(y)) > margen_m]
            verificaciones.append(Verificacion(
                id="R01.04", version=VERSION, origen=ORIGEN,
                descripcion="El lote queda dentro del entorno modelado",
                estado=Estado.COMPROBADO_POR_REGLAS if not fuera else Estado.PENDIENTE_DATOS,
                detalle="" if not fuera else f"Vértices {fuera} fuera del margen de {margen_m:.0f} m; ampliar el margen o mover el origen",
            ))

    pendiente = None
    if simple and malla is not None and not provisional:
        pct, azimut = gmalla.pendiente_media(malla, vertices)
        paso = malla.paso_medio_m
        pendiente = {"porcentaje": round(pct, 2), "direccion_deg": round(azimut, 1), "paso_dem_m": round(paso, 1)}
        ok = pct <= p["pendiente_max_pct"]
        verificaciones.append(Verificacion(
            id="R01.05", version=VERSION, origen=ORIGEN,
            descripcion=f"Pendiente uniforme ≤ {p['pendiente_max_pct']:.0f} % (dominio del MVP_01)",
            estado=Estado.COMPROBADO_POR_REGLAS if ok else Estado.PENDIENTE_REVISION,
            detalle=(f"Pendiente {pct:.1f} % hacia {azimut:.0f}° según un DEM con posts cada {paso:.0f} m. "
                     "Es una estimación regional, no una mensura: confirmar con relevamiento topográfico"
                     + ("" if ok else ". Excede el dominio del MVP_01: requiere revisión")),
            parametros={"pendiente_max_pct": p["pendiente_max_pct"]},
        ))

        # El lote puede ser más chico que la celda del DEM: en ese caso la pendiente
        # que se informa es la de la ladera, no la del lote.
        lado_equivalente = math.sqrt(area) if area > 0 else 0.0
        resuelve = lado_equivalente >= p["posts_min_por_lado"] * paso
        verificaciones.append(Verificacion(
            id="R01.06", version=VERSION, origen=ORIGEN,
            descripcion="El relieve disponible resuelve el interior del lote",
            estado=Estado.COMPROBADO_POR_REGLAS if resuelve else Estado.PENDIENTE_DATOS,
            detalle="" if resuelve else (
                f"El lote mide unos {lado_equivalente:.0f} m de lado y los posts del DEM están cada {paso:.0f} m. "
                "La pendiente informada es la de la ladera, no la interna del lote. "
                "Para fundaciones hace falta una mensura."
            ),
            parametros={"posts_min_por_lado": p["posts_min_por_lado"]},
        ))
    elif simple:
        verificaciones.append(Verificacion(
            id="R01.05", version=VERSION, origen=ORIGEN,
            descripcion="Pendiente del lote",
            estado=Estado.PENDIENTE_DATOS,
            detalle=("Escena plana provisional: no hay relieve" if provisional
                     else "Sin relieve: generar la escena para estimarla"),
        ))

    if not simple:
        estado = Estado.PENDIENTE_DATOS
    elif any(v.estado in (Estado.PENDIENTE_REVISION, Estado.PENDIENTE_CALCULO) for v in verificaciones):
        estado = Estado.PENDIENTE_REVISION
    elif any(v.estado == Estado.PENDIENTE_DATOS for v in verificaciones):
        estado = Estado.PENDIENTE_DATOS
    else:
        estado = Estado.COMPROBADO_POR_REGLAS

    return {
        "estado": estado.value,
        "area_m2": round(area, 2),
        "perimetro_m": round(perimetro, 2),
        "centroide": [round(centro[0], 2), round(centro[1], 2)],
        "lados": [{"longitud_m": round(l["longitud_m"], 3), "rumbo_deg": round(l["rumbo_deg"], 2)} for l in lados],
        "pendiente": pendiente,
        "verificaciones": [v.como_dict() for v in verificaciones],
    }
