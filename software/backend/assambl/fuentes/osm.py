"""Calles, construcciones y árboles mapeados de OpenStreetMap, vía Overpass.

OSM da geometría con nombre y tipo (esto es una calle residencial, esto una casa de
dos plantas) que la imagen sola no da. La cobertura es muy buena en ciudades y
pobre en zonas rurales: donde no hay nada mapeado, el modelo del sitio queda con la
imagen y los árboles detectados en ella.

Datos © colaboradores de OpenStreetMap, licencia ODbL.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import httpx

from ..config import carpeta_cache, variable
from ..geometria.coordenadas import SistemaLocal
from . import USER_AGENT

NOMBRE = "OpenStreetMap (Overpass)"
LICENCIA = "© colaboradores de OpenStreetMap, ODbL"
URL_POR_DEFECTO = "https://overpass-api.de/api/interpreter"

# Ancho por tipo de vía cuando OSM no lo informa. Son valores típicos, no medidos.
ANCHO_VIA_M = {
    "motorway": 14.0, "trunk": 12.0, "primary": 10.0, "secondary": 9.0, "tertiary": 8.0,
    "residential": 7.0, "unclassified": 6.0, "service": 4.0, "living_street": 5.0,
    "track": 3.5, "path": 1.5, "footway": 1.5, "cycleway": 2.0, "pedestrian": 5.0,
}
SIN_PAVIMENTO = {"unpaved", "dirt", "earth", "ground", "gravel", "grass", "sand", "compacted", "fine_gravel"}
ALTURA_PLANTA_M = 3.0
ALTURA_POR_DEFECTO_M = 4.5


@dataclass
class Via:
    puntos: list[tuple[float, float]]
    tipo: str
    ancho_m: float
    pavimentada: bool
    nombre: str | None
    ancho_supuesto: bool


@dataclass
class Construccion:
    contorno: list[tuple[float, float]]
    altura_m: float
    tipo: str
    altura_supuesta: bool


@dataclass
class DatosOsm:
    vias: list[Via]
    construcciones: list[Construccion]
    arboles: list[tuple[float, float]]
    estado: str  # ok, sin_datos, error
    detalle: str = ""
    sintetico: bool = False


def consulta(sur: float, oeste: float, norte: float, este: float) -> str:
    caja = f"({sur:.6f},{oeste:.6f},{norte:.6f},{este:.6f})"
    return (f'[out:json][timeout:40];(way["building"]{caja};way["highway"]{caja};'
            f'node["natural"="tree"]{caja};);out geom;')


def interpretar(datos: dict, sistema: SistemaLocal) -> DatosOsm:
    vias: list[Via] = []
    construcciones: list[Construccion] = []
    arboles: list[tuple[float, float]] = []
    for e in datos.get("elements", []):
        etiquetas = e.get("tags", {})
        if e.get("type") == "node" and etiquetas.get("natural") == "tree":
            arboles.append(sistema.a_local(e["lat"], e["lon"]))
            continue
        geom = e.get("geometry") or []
        puntos = [sistema.a_local(p["lat"], p["lon"]) for p in geom if p]
        if len(puntos) < 2:
            continue
        if "building" in etiquetas and len(puntos) >= 4:
            altura, supuesta = _altura(etiquetas)
            if puntos[0] == puntos[-1]:
                puntos = puntos[:-1]
            construcciones.append(Construccion(puntos, altura, etiquetas["building"], supuesta))
        elif "highway" in etiquetas:
            tipo = etiquetas["highway"]
            ancho = _numero(etiquetas.get("width"))
            vias.append(Via(
                puntos=puntos, tipo=tipo, ancho_m=ancho or ANCHO_VIA_M.get(tipo, 5.0),
                pavimentada=etiquetas.get("surface", "") not in SIN_PAVIMENTO and tipo != "track",
                nombre=etiquetas.get("name"), ancho_supuesto=ancho is None,
            ))
    estado = "ok" if (vias or construcciones or arboles) else "sin_datos"
    return DatosOsm(vias, construcciones, arboles, estado)


def _numero(texto: str | None) -> float | None:
    if not texto:
        return None
    try:
        return float(texto.replace(",", ".").split()[0])
    except ValueError:
        return None


def _altura(etiquetas: dict) -> tuple[float, bool]:
    altura = _numero(etiquetas.get("height"))
    if altura:
        return altura, False
    plantas = _numero(etiquetas.get("building:levels"))
    if plantas:
        return plantas * ALTURA_PLANTA_M + 1.0, True
    return ALTURA_POR_DEFECTO_M, True


async def descargar(sistema: SistemaLocal, margen_m: float) -> DatosOsm:
    """Todo lo mapeado en el cuadrado de ±margen alrededor del origen."""
    sur, oeste = sistema.a_geografica(-margen_m, -margen_m)
    norte, este = sistema.a_geografica(margen_m, margen_m)

    if variable("ASSAMBL_IMAGEN_SINTETICA") in ("1", "true", "si"):
        from . import imagen_sintetica

        salida = interpretar(imagen_sintetica.overpass(sur, oeste, norte, este), sistema)
        salida.sintetico = True
        return salida

    q = consulta(sur, oeste, norte, este)
    ruta = carpeta_cache("osm") / f"{hashlib.sha1(q.encode()).hexdigest()[:16]}.json"
    try:
        if ruta.exists():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        else:
            url = variable("ASSAMBL_OVERPASS_URL", URL_POR_DEFECTO)
            async with httpx.AsyncClient(timeout=60, headers={"User-Agent": USER_AGENT}) as c:
                r = await c.post(url, data={"data": q})
                r.raise_for_status()
                datos = r.json()
            ruta.write_text(json.dumps(datos), encoding="utf-8")
    except (httpx.HTTPError, ValueError, OSError) as e:
        return DatosOsm([], [], [], "error", str(e) or type(e).__name__)
    return interpretar(datos, sistema)
