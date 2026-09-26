"""Capa 01 — Terreno.

Arma la escena 3D del lote y su entorno a partir de NASADEM, y la emite como un
.glb por capa. Es la salida de la fase de terreno: el resto del proyecto se apoya
sobre esta geometría y sobre las coordenadas que la definen.

Toda la geometría se construye acá, una sola vez, en Python. El visor web, Blender
y el HTML autocontenido consumen el mismo archivo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from ..fuentes import nasadem
from ..generadores import glb
from ..geometria import malla as gmalla
from ..geometria import poligono
from ..geometria.coordenadas import SistemaLocal
from ..modelo.estados import EstadoFuente
from ..modelo.proyecto import MARGEN_MAX_M, MARGEN_MIN_M, MARGEN_POR_DEFECTO_M
from ..modelo.sitio import Fuente, MallaDem, Relieve

PASO_CONTORNO_M = 2.0
# Separaciones sobre la superficie del terreno. No son decorativas: con escenas de
# más de 1 km el búfer de profundidad no distingue diferencias de pocos centímetros
# y el lote parpadearía contra el relieve.
SEPARACION_SUPERFICIE_M = 0.25
SEPARACION_LINEA_M = 0.45

COLOR_TERRENO = (0.55, 0.53, 0.48, 1.0)
COLOR_TERRENO_PROVISIONAL = (0.42, 0.42, 0.44, 1.0)
COLOR_LOTE = (1.0, 0.31, 0.12, 0.28)
COLOR_CONTORNO = (1.0, 0.31, 0.12, 1.0)
COLOR_NORTE = (0.07, 0.07, 0.07, 1.0)


@dataclass
class EscenaTerreno:
    lat: float
    lon: float
    margen_m: float
    relieve: Relieve
    fuentes: list[Fuente]
    advertencias: list[str]
    malla: gmalla.MallaLocal
    lote_3d: list[list[float]]
    area_m2: float
    pendiente_pct: float
    pendiente_azimut_deg: float
    glb: bytes


def validar_margen(margen_m: float) -> float:
    return float(min(max(margen_m, MARGEN_MIN_M), MARGEN_MAX_M))


async def obtener_relieve(lat: float, lon: float, margen_m: float) -> tuple[MallaDem, list[Fuente], list[str]]:
    """Descarga el recorte de NASADEM que cubre el entorno pedido.

    Si no hay cobertura, falta la credencial o falla la descarga, devuelve una
    malla plana marcada como provisional en lugar de interrumpir el trabajo.
    """
    fecha = datetime.now(timezone.utc).date().isoformat()
    grados_lat = margen_m / 111_320.0
    grados_lon = grados_lat / max(math.cos(math.radians(lat)), 1e-6)
    try:
        dem = await nasadem.descargar_recorte(lat - grados_lat, lat + grados_lat, lon - grados_lon, lon + grados_lon)
    except Exception as e:
        motivo = str(e) or type(e).__name__
        return (
            nasadem.malla_provisional(lat, lon, margen_m),
            [
                Fuente(
                    nombre=nasadem.NOMBRE,
                    url=f"https://doi.org/{nasadem.DOI}",
                    licencia=nasadem.LICENCIA,
                    fecha=fecha,
                    estado=EstadoFuente.PENDIENTE_DATOS,
                    resolucion="sin dato",
                    naturaleza="provisional",
                    detalle=motivo,
                )
            ],
            [f"Escena plana provisional: no se pudo obtener el relieve de NASADEM ({motivo}). No representa el terreno."],
        )

    advertencias = []
    if dem.huecos:
        advertencias.append(
            f"{dem.huecos} posts de NASADEM sin dato en el recorte; se rellenaron con la mediana del entorno."
        )
    return (
        dem,
        [
            Fuente(
                nombre=nasadem.NOMBRE,
                url=f"https://doi.org/{nasadem.DOI}",
                licencia=nasadem.LICENCIA,
                fecha=fecha,
                estado=EstadoFuente.OK if not dem.huecos else EstadoFuente.PARCIAL,
                resolucion=nasadem.RESOLUCION,
                naturaleza="medicion_satelital",
                detalle=f"mosaicos {', '.join(dem.teselas)}; {dem.nx}×{dem.ny} posts",
            )
        ],
        advertencias,
    )


def _nodo_terreno(malla: gmalla.MallaLocal, provisional: bool, extras: dict) -> glb.Nodo:
    vertices, normales = glb.normales_planas(malla.vertices, glb.rejilla_indices(malla.nx, malla.ny))
    material = glb.Material(
        nombre="terreno_provisional" if provisional else "terreno_nasadem",
        color=COLOR_TERRENO_PROVISIONAL if provisional else COLOR_TERRENO,
        rugosidad=1.0,
        doble_cara=False,
    )
    return glb.Nodo(
        nombre="01_terreno",
        primitivas=[glb.Primitiva(posiciones=vertices.astype(np.float32), normales=normales.astype(np.float32),
                                  material=material)],
        extras=extras,
    )


def _nodo_lote(malla: gmalla.MallaLocal, vertices_lote: list[tuple[float, float]], extras: dict) -> tuple[glb.Nodo, np.ndarray]:
    """Superficie y contorno del lote, apoyados sobre la malla existente.

    Apoyar no es inventar relieve: cada punto se ubica en la cara del terreno que
    ya existe. La forma del lote la define el usuario y es exacta.
    """
    triangulos = poligono.triangular(vertices_lote)
    base = gmalla.apoyar(malla, vertices_lote, SEPARACION_SUPERFICIE_M)
    primitivas: list[glb.Primitiva] = []
    if triangulos:
        indices = np.array(triangulos, dtype=np.uint32)
        caras, normales = glb.normales_planas(base.astype(np.float64), indices)
        primitivas.append(
            glb.Primitiva(
                posiciones=caras.astype(np.float32),
                normales=normales.astype(np.float32),
                material=glb.Material("lote_superficie", color=COLOR_LOTE, doble_cara=True),
            )
        )

    denso = poligono.densificar(vertices_lote, PASO_CONTORNO_M, cerrado=True)
    contorno = gmalla.apoyar(malla, denso, SEPARACION_LINEA_M)
    primitivas.append(
        glb.Primitiva(
            posiciones=np.vstack([contorno, contorno[:1]]),
            modo=glb.TIRA_DE_LINEAS,
            material=glb.Material("lote_contorno", color=COLOR_CONTORNO, sin_iluminacion=True),
        )
    )
    return glb.Nodo(nombre="01_lote", primitivas=primitivas, extras=extras), base


def _nodo_referencias(malla: gmalla.MallaLocal, margen_m: float) -> glb.Nodo:
    """Norte y origen del sistema local, para que la escena se lea sin interfaz."""
    material = glb.Material("referencias", color=COLOR_NORTE, sin_iluminacion=True)
    z = malla.altura_en(0.0, 0.0) + SEPARACION_LINEA_M
    largo = margen_m * 0.9
    punta = largo * 0.06
    flecha = np.array(
        [[0, 0, z], [0, largo, z], [-punta, largo - punta * 1.8, z], [0, largo, z], [punta, largo - punta * 1.8, z]],
        dtype=np.float32,
    )
    eje_x = np.array([[-largo * 0.08, 0, z], [largo * 0.08, 0, z]], dtype=np.float32)
    eje_z = np.array([[0, 0, z], [0, 0, z + largo * 0.08]], dtype=np.float32)
    return glb.Nodo(
        nombre="01_referencias",
        primitivas=[
            glb.Primitiva(posiciones=flecha, modo=glb.TIRA_DE_LINEAS, material=material),
            glb.Primitiva(posiciones=eje_x, modo=glb.LINEAS, material=material),
            glb.Primitiva(posiciones=eje_z, modo=glb.LINEAS, material=material),
        ],
        extras={"fuente": "cálculo local", "descripcion": "flecha al norte y origen del sistema local"},
    )


def componer(
    lat: float,
    lon: float,
    margen_m: float,
    dem: MallaDem,
    vertices_lote: list[tuple[float, float]],
    fuentes: list[Fuente],
    advertencias: list[str],
) -> EscenaTerreno:
    """Arma la escena completa y la serializa como .glb."""
    margen_m = validar_margen(margen_m)
    sistema = SistemaLocal(lat, lon)
    malla, cota = gmalla.desde_dem(dem, sistema)
    malla = gmalla.recortar(malla, margen_m)
    provisional = dem.provisional

    advertencias = list(advertencias)
    area = poligono.area(vertices_lote) if len(vertices_lote) >= 3 else 0.0
    if not provisional and area > 0:
        lado_equivalente = math.sqrt(area)
        if lado_equivalente < 2 * malla.paso_medio_m:
            advertencias.append(
                f"El lote mide unos {lado_equivalente:.0f} m de lado y los posts de NASADEM están cada "
                f"{malla.paso_medio_m:.0f} m: el relieve no resuelve la pendiente interna del lote. "
                "Para fundaciones hace falta una mensura."
            )

    pendiente, azimut = (
        gmalla.pendiente_media(malla, vertices_lote) if len(vertices_lote) >= 3 and not provisional else (0.0, 0.0)
    )

    resolucion = "plana provisional" if provisional else nasadem.RESOLUCION
    extras_terreno = {
        "capa": "01_terreno",
        "fuente": "escena provisional sin datos" if provisional else nasadem.NOMBRE,
        "resolucion": resolucion,
        "naturaleza": "provisional" if provisional else "medicion_satelital",
        "cota_origen_msnm": round(cota, 2),
        "paso_x_m": round(malla.dx, 2),
        "paso_y_m": round(malla.dy, 2),
        "advertencia": "Modelo de elevación de resolución aproximada 30 m. No es una mensura.",
    }
    nodos = [_nodo_terreno(malla, provisional, extras_terreno)]

    lote_3d: list[list[float]] = []
    if len(vertices_lote) >= 3:
        nodo_lote, base = _nodo_lote(
            malla,
            vertices_lote,
            {
                "capa": "01_lote",
                "fuente": "definido por el usuario",
                "resolucion": "exacta; la altura surge de apoyarlo sobre la malla de 30 m",
                "naturaleza": "calculo_local",
                "area_m2": round(area, 2),
            },
        )
        nodos.append(nodo_lote)
        lote_3d = [[round(float(v), 3) for v in p] for p in base]

    nodos.append(_nodo_referencias(malla, margen_m))

    ancho, alto = malla.extension_m()
    datos = glb.construir(
        nodos,
        extras_escena={
            "proyecto": {"lat": lat, "lon": lon, "margen_m": margen_m},
            "cota_origen_msnm": round(cota, 2),
            "extension_m": [round(ancho, 1), round(alto, 1)],
            "advertencias": advertencias,
        },
        generador="Assambl capa 01 terreno",
    )

    z = malla.vertices[:, 2]
    return EscenaTerreno(
        lat=lat,
        lon=lon,
        margen_m=margen_m,
        relieve=Relieve(
            dem=dem,
            cota_origen_msnm=round(cota, 2),
            paso_x_m=round(malla.dx, 3),
            paso_y_m=round(malla.dy, 3),
            z_min_m=round(float(z.min()), 2),
            z_max_m=round(float(z.max()), 2),
            provisional=provisional,
        ),
        fuentes=fuentes,
        advertencias=advertencias,
        malla=malla,
        lote_3d=lote_3d,
        area_m2=round(area, 2),
        pendiente_pct=round(pendiente, 2),
        pendiente_azimut_deg=round(azimut, 1),
        glb=datos,
    )


async def generar(lat: float, lon: float, margen_m: float, vertices_lote: list[tuple[float, float]]) -> EscenaTerreno:
    margen_m = validar_margen(margen_m)
    dem, fuentes, advertencias = await obtener_relieve(lat, lon, margen_m)
    return componer(lat, lon, margen_m, dem, vertices_lote, fuentes, advertencias)
