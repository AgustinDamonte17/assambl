"""Modelo 3D del sitio: el lote y su entorno reconstruidos a partir de la imagen
satelital, con el terreno supuesto plano (docs/decisiones/0005_modelo_del_sitio.md).

Dos niveles de definición:

- **Entorno** (±margen): ortofoto de baja definición como suelo, calles y
  construcciones de OpenStreetMap, y árboles detectados en la imagen, en forma
  simple.
- **Lote y su borde**: ortofoto de alta definición y árboles con posición y copa
  medidas en la imagen (o interpretados por IA, si está configurada), cada uno con
  identificador para poder usarlos en el diseño.

La geometría se arma una sola vez, acá, y se publica como .glb con las imágenes
embebidas. Suelo en Z = 0; todo lo demás apoya sobre él.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from ..fuentes import imagen_satelital, osm
from ..fuentes.imagen_satelital import Ortofoto
from ..generadores import glb
from ..geometria import poligono
from ..geometria.coordenadas import SistemaLocal
from ..modelo.estados import EstadoFuente
from ..modelo.proyecto import MARGEN_MAX_M, MARGEN_MIN_M
from ..modelo.sitio import Fuente
from . import formas, interpretacion_ia, vegetacion
from .vegetacion import Arbol

VERSION = "sitio@1"
M_PX_ENTORNO_MIN = 0.6
M_PX_LOTE = 0.3
BORDE_LOTE_MIN_M = 15.0
MAX_ARBOLES_ENTORNO = 1500
DISTANCIA_ARBOL_OSM_M = 3.0

Z_SUELO_LOTE = 0.03
Z_CALLES = 0.05
Z_CONTORNO_LOTE = 0.10

COLOR_SUELO_SIN_IMAGEN = (0.55, 0.54, 0.47, 1.0)
COLOR_CONTORNO = (1.0, 0.31, 0.12, 1.0)
COLOR_CALLE = (0.42, 0.42, 0.41, 1.0)
COLOR_CAMINO = (0.62, 0.50, 0.37, 1.0)
COLOR_CONSTRUCCION = (0.86, 0.84, 0.80, 1.0)
COLOR_TRONCO = (0.30, 0.22, 0.15, 1.0)
VERDES = [(0.20, 0.33, 0.16, 1.0), (0.26, 0.38, 0.19, 1.0), (0.17, 0.29, 0.20, 1.0)]


@dataclass
class ModeloSitio:
    lat: float
    lon: float
    margen_m: float
    vertices: list[tuple[float, float]]
    fuentes: list[Fuente]
    advertencias: list[str]
    resumen: dict
    arboles_lote: list[dict]
    glb: bytes = field(repr=False)


def rectangulo_lote(vertices: list[tuple[float, float]], margen_m: float) -> tuple[float, float, float, float] | None:
    """Recorte de alta definición: el lote y un borde para ver lo que lo rodea."""
    if len(vertices) < 3:
        return None
    xmin, ymin, xmax, ymax = poligono.caja(vertices)
    borde = max(BORDE_LOTE_MIN_M, 0.25 * math.hypot(xmax - xmin, ymax - ymin))
    return (max(xmin - borde, -margen_m), min(xmax + borde, margen_m),
            max(ymin - borde, -margen_m), min(ymax + borde, margen_m))


def _dentro(r: tuple[float, float, float, float] | None, x: float, y: float) -> bool:
    return r is not None and r[0] <= x <= r[1] and r[2] <= y <= r[3]


async def generar(lat: float, lon: float, margen_m: float, vertices: list[tuple[float, float]]) -> ModeloSitio:
    margen_m = float(min(max(margen_m, MARGEN_MIN_M), MARGEN_MAX_M))
    sistema = SistemaLocal(lat, lon)
    rect = rectangulo_lote(vertices, margen_m)

    m_px_entorno = max(M_PX_ENTORNO_MIN, 2 * margen_m / imagen_satelital.MAX_PX)
    tareas = [
        imagen_satelital.ortofoto(sistema, -margen_m, margen_m, -margen_m, margen_m, m_px_entorno),
        osm.descargar(sistema, margen_m),
    ]
    if rect:
        tareas.append(imagen_satelital.ortofoto(sistema, *rect, M_PX_LOTE))
    resultados = await asyncio.gather(*tareas)
    entorno: Ortofoto = resultados[0]
    datos_osm: osm.DatosOsm = resultados[1]
    lote_img: Ortofoto | None = resultados[2] if rect else None

    ia = None
    if lote_img is not None and lote_img.cobertura > 0:
        ia = await interpretacion_ia.interpretar(lote_img, vertices)
    ia_fallo = ia is None and lote_img is not None and interpretacion_ia.disponible()
    return componer(lat, lon, margen_m, vertices, entorno, lote_img, datos_osm, ia, ia_fallo)


def componer(lat: float, lon: float, margen_m: float, vertices: list[tuple[float, float]], entorno: Ortofoto,
             lote_img: Ortofoto | None, datos_osm: osm.DatosOsm,
             ia: interpretacion_ia.ResultadoIA | None, ia_fallo: bool = False) -> ModeloSitio:
    rect = (lote_img.xmin, lote_img.xmax, lote_img.ymin, lote_img.ymax) if lote_img else None
    advertencias: list[str] = [
        "El terreno se modela plano: no se relevó la pendiente. Para fundaciones hace falta un relevamiento topográfico."
    ]
    fecha = datetime.now(timezone.utc).date().isoformat()

    # Construcciones: OSM, más las que vea la IA en el lote si OSM no las tiene.
    construcciones = [(c.contorno, c.altura_m, c.tipo, "OpenStreetMap", c.altura_supuesta)
                      for c in datos_osm.construcciones]
    if ia:
        for c in ia.construcciones:
            cx, cy = poligono.centroide(c.contorno)
            if not any(poligono.contiene(o[0], cx, cy) for o in construcciones):
                construcciones.append((c.contorno, c.altura_m, c.tipo, interpretacion_ia.FUENTE, True))

    def sobre_construccion(x: float, y: float) -> bool:
        return any(poligono.contiene(c[0], x, y) for c in construcciones)

    # Árboles del recorte del lote: IA si está, si no detección por color.
    detalle: list[Arbol] = []
    if lote_img is not None and lote_img.cobertura > 0:
        detalle = ia.arboles if ia else vegetacion.detectar(lote_img)
    detalle = [a for a in detalle if not sobre_construccion(a.x, a.y)]

    # Árboles del entorno: baja definición, fuera del recorte del lote.
    lejanos: list[Arbol] = []
    if entorno.cobertura > 0:
        lejanos = [a for a in vegetacion.detectar(entorno, radio_min_m=1.5, max_arboles=MAX_ARBOLES_ENTORNO * 2)
                   if not _dentro(rect, a.x, a.y) and not sobre_construccion(a.x, a.y)]
        lejanos = lejanos[:MAX_ARBOLES_ENTORNO]
    for x, y in datos_osm.arboles:
        if _dentro(rect, x, y) or abs(x) > margen_m or abs(y) > margen_m:
            continue
        if all((a.x - x) ** 2 + (a.y - y) ** 2 > DISTANCIA_ARBOL_OSM_M ** 2 for a in lejanos):
            lejanos.append(Arbol(x, y, 3.0, 7.0, "OpenStreetMap"))

    arboles_lote = []
    for i, a in enumerate(detalle, 1):
        d = a.como_dict()
        d["id"] = f"A{i:02d}"
        d["dentro_del_lote"] = len(vertices) >= 3 and poligono.contiene(vertices, a.x, a.y)
        arboles_lote.append(d)

    nodos = _nodos(margen_m, vertices, entorno, lote_img, datos_osm, construcciones, detalle, lejanos, arboles_lote)

    # Procedencia de cada capa.
    fuentes = [_fuente_imagen(entorno, lote_img, fecha)]
    fuentes.append(Fuente(
        nombre=osm.NOMBRE if not datos_osm.sintetico else "OpenStreetMap sintético (no es real)",
        url="https://www.openstreetmap.org/copyright", licencia=osm.LICENCIA, fecha=fecha,
        estado={"ok": EstadoFuente.OK, "sin_datos": EstadoFuente.PARCIAL}.get(datos_osm.estado,
                                                                            EstadoFuente.PENDIENTE_DATOS),
        resolucion="geometría mapeada por voluntarios; alturas supuestas si no están cargadas",
        naturaleza="medicion_satelital" if datos_osm.estado == "ok" else "provisional",
        detalle=(f"{len(datos_osm.vias)} vías, {len(datos_osm.construcciones)} construcciones"
                 if datos_osm.estado != "error" else f"sin respuesta de Overpass: {datos_osm.detalle}"),
    ))
    fuentes.append(Fuente(
        nombre="Árboles del lote: " + (f"interpretación con IA ({ia.modelo})" if ia else "detección en la imagen"),
        url="", licencia="cálculo propio", fecha=fecha, estado=EstadoFuente.OK if lote_img else EstadoFuente.PENDIENTE_DATOS,
        resolucion=f"imagen de {lote_img.m_px:.2f} m por píxel" if lote_img else "sin lote",
        naturaleza="interpretacion_imagen",
        detalle="posición y copa medidas en la imagen; altura supuesta a partir de la copa"
        + ("" if ia else ". Sin IA configurada: detección por color"),
    ))

    if entorno.cobertura == 0:
        advertencias.append("No se pudo obtener imagen satelital: el suelo se muestra en un color neutro.")
    elif entorno.cobertura < 1:
        advertencias.append("Parte del entorno no tiene imagen satelital.")
    if lote_img is not None and lote_img.zoom_min_usado and lote_img.zoom_min_usado < lote_img.zoom:
        advertencias.append("La imagen del lote no está disponible en máxima definición en esta zona; se usó una "
                            "de menor definición ampliada.")
    if datos_osm.estado == "error":
        advertencias.append("No se pudo consultar OpenStreetMap: el entorno no tiene calles ni construcciones.")
    elif datos_osm.estado == "sin_datos":
        advertencias.append("OpenStreetMap no tiene calles ni construcciones mapeadas en esta zona.")
    if ia_fallo:
        advertencias.append("La interpretación con IA está configurada pero no respondió: los árboles del lote se "
                            "detectaron por color.")
    if entorno.sintetica:
        advertencias.append("IMAGEN SINTÉTICA DE PRUEBA: no representa el lugar.")

    resumen = {
        "arboles_lote": sum(1 for a in arboles_lote if a["dentro_del_lote"]),
        "arboles_borde": sum(1 for a in arboles_lote if not a["dentro_del_lote"]),
        "arboles_entorno": len(lejanos),
        "construcciones": len(construcciones),
        "vias": len(datos_osm.vias),
        "m_px_entorno": round(entorno.m_px, 2),
        "m_px_lote": round(lote_img.m_px, 2) if lote_img else None,
        "interpretacion": "ia" if ia else "imagen",
        "imagen_disponible": entorno.cobertura > 0,
        "sintetica": entorno.sintetica,
    }
    datos = glb.construir(nodos, extras_escena={
        "proyecto": {"lat": lat, "lon": lon, "margen_m": margen_m},
        "version": VERSION,
        "terreno": "plano supuesto, Z = 0",
        "advertencias": advertencias,
    }, generador="Assambl capa 01 sitio")
    return ModeloSitio(lat, lon, margen_m, list(vertices), fuentes, advertencias, resumen, arboles_lote, datos)


def _fuente_imagen(entorno: Ortofoto, lote_img: Ortofoto | None, fecha: str) -> Fuente:
    resolucion = f"entorno {entorno.m_px:.2f} m/píxel"
    if lote_img:
        resolucion += f"; lote {lote_img.m_px:.2f} m/píxel"
    return Fuente(
        nombre=entorno.fuente,
        url=imagen_satelital.URL.split("/tile/")[0],
        licencia=imagen_satelital.LICENCIA if not entorno.sintetica else "sintética",
        fecha=fecha,
        estado=EstadoFuente.OK if entorno.cobertura >= 1 else (
            EstadoFuente.PARCIAL if entorno.cobertura > 0 else EstadoFuente.PENDIENTE_DATOS),
        resolucion=resolucion,
        naturaleza="provisional" if entorno.sintetica or entorno.cobertura == 0 else "medicion_satelital",
        detalle=f"zoom {entorno.zoom} en el entorno" + (f", {lote_img.zoom} en el lote" if lote_img else "")
        + "; fecha de la toma desconocida",
    )


def _prim(malla: formas.Malla | None, material: glb.Material) -> glb.Primitiva | None:
    if malla is None:
        return None
    caras, normales = glb.normales_planas(malla[0].astype(np.float64), malla[1])
    return glb.Primitiva(posiciones=caras.astype(np.float32), normales=normales.astype(np.float32), material=material)


def _suelo(nombre: str, orto: Ortofoto | None, rect: tuple[float, float, float, float], z: float,
           extras: dict) -> glb.Nodo:
    p, i, uv = formas.rectangulo(*rect, z)
    material = glb.Material(nombre, color=(1, 1, 1, 1), rugosidad=1.0, doble_cara=False,
                            textura=orto.jpeg() if orto is not None and orto.cobertura > 0 else None)
    if material.textura is None:
        material.color = COLOR_SUELO_SIN_IMAGEN
    normales = np.tile(np.array([[0, 0, 1]], dtype=np.float32), (4, 1))
    return glb.Nodo(nombre, [glb.Primitiva(posiciones=p, indices=i, normales=normales, uv=uv if material.textura else None,
                                           material=material)], extras)


def _arboles(nombre: str, arboles: list[Arbol], detalle: bool, extras: dict) -> glb.Nodo | None:
    if not arboles:
        return None
    troncos, copas = [], [[] for _ in VERDES]
    for k, a in enumerate(arboles):
        t, c = formas.arbol(a.x, a.y, a.radio_m, a.altura_m, detalle)
        troncos.append(t)
        copas[k % len(VERDES)].append(c)
    primitivas = [_prim(formas.unir(troncos), glb.Material("tronco", color=COLOR_TRONCO, doble_cara=False))]
    for verde, grupo in zip(VERDES, copas):
        primitivas.append(_prim(formas.unir(grupo), glb.Material("copa", color=verde, doble_cara=False)))
    return glb.Nodo(nombre, [p for p in primitivas if p is not None], extras)


def _nodos(margen_m, vertices, entorno, lote_img, datos_osm, construcciones, detalle, lejanos, arboles_lote):
    nodos: list[glb.Nodo] = [
        _suelo("01_suelo", entorno, (entorno.xmin, entorno.xmax, entorno.ymin, entorno.ymax), 0.0,
               {"capa": "01_suelo", "fuente": entorno.fuente, "resolucion": f"{entorno.m_px:.2f} m/píxel",
                "advertencia": "Imagen satelital apoyada sobre un terreno supuesto plano."}),
    ]
    if lote_img is not None:
        nodos.append(_suelo("01_suelo_lote", lote_img, (lote_img.xmin, lote_img.xmax, lote_img.ymin, lote_img.ymax),
                            Z_SUELO_LOTE, {"capa": "01_suelo_lote", "fuente": lote_img.fuente,
                                           "resolucion": f"{lote_img.m_px:.2f} m/píxel"}))

    # Calles de OSM, recortadas al entorno.
    pavimento, tierra = [], []
    for v in datos_osm.vias:
        puntos = [(max(-margen_m, min(margen_m, x)), max(-margen_m, min(margen_m, y))) for x, y in v.puntos]
        (pavimento if v.pavimentada else tierra).append(formas.cinta(puntos, v.ancho_m, Z_CALLES))
    calles = [p for p in (_prim(formas.unir(pavimento), glb.Material("calle", color=COLOR_CALLE, doble_cara=False)),
                          _prim(formas.unir(tierra), glb.Material("camino", color=COLOR_CAMINO, doble_cara=False)))
              if p is not None]
    if calles:
        nodos.append(glb.Nodo("01_calles", calles, {"capa": "01_calles", "fuente": "OpenStreetMap",
                                                    "advertencia": "ancho típico por tipo de vía si OSM no lo informa"}))

    dentro = [c for c in construcciones if all(abs(x) <= margen_m and abs(y) <= margen_m for x, y in c[0])]
    edificios = _prim(formas.unir([formas.extrusion(c[0], c[1]) for c in dentro]),
                      glb.Material("construccion", color=COLOR_CONSTRUCCION, doble_cara=False))
    if edificios is not None:
        nodos.append(glb.Nodo("01_construcciones", [edificios], {
            "capa": "01_construcciones", "cantidad": len(dentro),
            "advertencia": "techo plano y altura supuesta cuando la fuente no la informa"}))

    lote_arboles = _arboles("01_arboles_lote", detalle, True, {
        "capa": "01_arboles_lote", "arboles": arboles_lote,
        "advertencia": "posición y copa medidas en la imagen; altura supuesta"})
    if lote_arboles:
        nodos.append(lote_arboles)
    entorno_arboles = _arboles("01_arboles_entorno", lejanos, False, {
        "capa": "01_arboles_entorno", "cantidad": len(lejanos),
        "advertencia": "baja definición: ubicación aproximada, forma genérica"})
    if entorno_arboles:
        nodos.append(entorno_arboles)

    if len(vertices) >= 3:
        contorno = _prim(formas.cinta(vertices, 0.35, Z_CONTORNO_LOTE, cerrada=True),
                         glb.Material("lote_contorno", color=COLOR_CONTORNO, sin_iluminacion=True))
        nodos.append(glb.Nodo("01_lote", [contorno], {
            "capa": "01_lote", "fuente": "definido por el usuario", "area_m2": round(poligono.area(vertices), 2)}))

    largo = margen_m * 0.9
    punta = largo * 0.06
    z = Z_CONTORNO_LOTE
    flecha = np.array([[0, 0, z], [0, largo, z], [-punta, largo - punta * 1.8, z], [0, largo, z],
                       [punta, largo - punta * 1.8, z]], dtype=np.float32)
    material = glb.Material("referencias", color=(0.09, 0.09, 0.08, 1.0), sin_iluminacion=True)
    nodos.append(glb.Nodo("01_referencias", [glb.Primitiva(posiciones=flecha, modo=glb.TIRA_DE_LINEAS,
                                                           material=material)],
                          {"descripcion": "flecha al norte desde el origen del sistema local"}))
    return nodos
