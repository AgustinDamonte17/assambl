"""Genera el script .py que reconstruye la escena de terreno dentro de Blender.

Sale del mismo generador que el .glb, con los mismos números, para que no existan
dos implementaciones de la geometría. El .glb sirve para ver la malla ya resuelta;
este script sirve cuando se quiere la versión editable y paramétrica.

El relieve se escribe como la rejilla que realmente es: origen, paso y una lista
plana de alturas. No se interpola para "mejorarlo".
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..capas.terreno import EscenaTerreno
from ..clima.sol import PosicionSolar

PLANTILLA = '''"""Assambl — capa 01 terreno.

Generado por Assambl el {generado}.
Proyecto en lat {lat}, lon {lon}; margen de {margen:.0f} m alrededor del origen.

Sistema de coordenadas: +X este, +Y norte, +Z arriba, 1 unidad = 1 metro.
El origen (0, 0, 0) es el punto del proyecto, a {cota} msnm.

Relieve: {fuente_relieve}
Resolución: {resolucion}
{aviso}

Uso:  blender --python este_archivo.py
      o pegarlo en el editor de texto de Blender y ejecutarlo.
"""

import math

import bpy

# ---------------------------------------------------------------- parámetros
LATITUD = {lat}
LONGITUD = {lon}
MARGEN_M = {margen}
COTA_ORIGEN_MSNM = {cota}
PROVISIONAL = {provisional}

# Rejilla del relieve: el vértice (j, i) está en x0 + i·dx, y0 + j·dy.
NX, NY = {nx}, {ny}
X0, Y0 = {x0!r}, {y0!r}
DX, DY = {dx!r}, {dy!r}
ALTURAS = {alturas}

# Contorno del lote, ya apoyado sobre la malla del relieve.
LOTE = {lote}

# Posición del sol calculada localmente con el algoritmo del NOAA Solar Calculator.
SOL = {sol}


# ------------------------------------------------------------------ utilidades
def limpiar(nombre_coleccion="Assambl"):
    """Borra una ejecución anterior sin tocar el resto del archivo."""
    vieja = bpy.data.collections.get(nombre_coleccion)
    if vieja:
        for objeto in list(vieja.objects):
            bpy.data.objects.remove(objeto, do_unlink=True)
        bpy.data.collections.remove(vieja)
    coleccion = bpy.data.collections.new(nombre_coleccion)
    bpy.context.scene.collection.children.link(coleccion)
    return coleccion


def configurar_escena():
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.unit_settings.length_unit = "METERS"
    escena.unit_settings.scale_length = 1.0
    # El nombre del motor cambió en Blender 4.2; se prueba el nuevo y se cae al viejo.
    for motor in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            escena.render.engine = motor
            break
        except TypeError:
            continue


def material(nombre, color, rugosidad=1.0):
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    principal = mat.node_tree.nodes.get("Principled BSDF")
    if principal:
        principal.inputs["Base Color"].default_value = color
        if "Roughness" in principal.inputs:
            principal.inputs["Roughness"].default_value = rugosidad
    if color[3] < 1.0:
        mat.blend_method = "BLEND"
    return mat


# -------------------------------------------------------------------- relieve
def construir_relieve(coleccion):
    vertices = [
        (X0 + i * DX, Y0 + j * DY, ALTURAS[j * NX + i])
        for j in range(NY)
        for i in range(NX)
    ]
    caras = [
        (j * NX + i, j * NX + i + 1, (j + 1) * NX + i + 1, (j + 1) * NX + i)
        for j in range(NY - 1)
        for i in range(NX - 1)
    ]
    malla = bpy.data.meshes.new("01_terreno")
    malla.from_pydata(vertices, [], caras)
    malla.update()
    # Sombreado plano a propósito: las facetas son la resolución real del dato.
    for poligono in malla.polygons:
        poligono.use_smooth = False

    objeto = bpy.data.objects.new("01_terreno", malla)
    objeto.data.materials.append(
        material("terreno_provisional" if PROVISIONAL else "terreno_nasadem",
                 (0.42, 0.42, 0.44, 1.0) if PROVISIONAL else (0.55, 0.53, 0.48, 1.0))
    )
    coleccion.objects.link(objeto)
    return objeto


# ----------------------------------------------------------------------- lote
def construir_lote(coleccion):
    if len(LOTE) < 3:
        return None
    malla = bpy.data.meshes.new("01_lote")
    malla.from_pydata(LOTE, [(i, (i + 1) % len(LOTE)) for i in range(len(LOTE))], [list(range(len(LOTE)))])
    malla.update()
    objeto = bpy.data.objects.new("01_lote", malla)
    objeto.data.materials.append(material("lote", (1.0, 0.31, 0.12, 0.35)))
    objeto.show_wire = True
    coleccion.objects.link(objeto)
    return objeto


# ------------------------------------------------------------------------ sol
def construir_sol(coleccion):
    """Orienta un sol de Blender según el azimut y la elevación calculados.

    Un sol apunta por su eje −Z. Con el orden de Euler XYZ, girar (90° − elevación)
    en X y (180° − azimut) en Z deja el eje +Z del objeto apuntando al sol.
    """
    datos = bpy.data.lights.new("01_sol", type="SUN")
    datos.angle = math.radians(0.53)  # diámetro aparente del disco solar
    datos.energy = 3.0
    objeto = bpy.data.objects.new("01_sol", datos)
    objeto.rotation_euler = (
        math.radians(90.0 - SOL["elevacion_deg"]),
        0.0,
        math.radians(180.0 - SOL["azimut_deg"]),
    )
    objeto.location = (0.0, 0.0, MARGEN_M)
    coleccion.objects.link(objeto)
    return objeto


def main():
    configurar_escena()
    coleccion = limpiar()
    construir_relieve(coleccion)
    construir_lote(coleccion)
    construir_sol(coleccion)
    print(
        f"Assambl: relieve {{NX}}×{{NY}} posts cada {{DX:.1f}}×{{DY:.1f}} m; "
        f"sol a {{SOL['azimut_deg']}}° / {{SOL['elevacion_deg']}}° ({{SOL['momento_local']}})"
    )


if __name__ == "__main__":
    main()
'''

AVISO_PROVISIONAL = (
    "AVISO: escena plana provisional. No hubo datos de relieve; no representa el terreno."
)
AVISO_DEM = (
    "AVISO: modelo de elevación de resolución aproximada 30 m. No es una mensura y no\n"
    "sirve para definir fundaciones."
)


def _lista_compacta(valores, por_linea: int = 12, decimales: int = 2, sangria: str = "    ") -> str:
    textos = [f"{round(float(v), decimales)!r}" for v in valores]
    filas = [", ".join(textos[i : i + por_linea]) for i in range(0, len(textos), por_linea)]
    return "[\n" + "\n".join(f"{sangria}{f}," for f in filas) + "\n]"


def _lista_puntos(puntos, sangria: str = "    ") -> str:
    if len(puntos) == 0:
        return "[]"
    filas = [f"{sangria}({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})," for p in puntos]
    return "[\n" + "\n".join(filas) + "\n]"


def generar(escena: EscenaTerreno, lat: float, lon: float, margen_m: float, sol: PosicionSolar) -> str:
    """Devuelve el texto del script de Blender para la escena dada."""
    malla = escena.malla
    provisional = escena.relieve.provisional
    aviso = AVISO_PROVISIONAL if provisional else AVISO_DEM
    fuente = escena.fuentes[0].nombre if escena.fuentes else "sin fuente"
    resolucion = escena.fuentes[0].resolucion if escena.fuentes else "sin dato"

    datos_sol = {
        "momento_utc": sol.momento_utc,
        "momento_local": sol.momento_local,
        "azimut_deg": sol.azimut_deg,
        "elevacion_deg": sol.elevacion_deg,
        "sobre_horizonte": sol.sobre_horizonte,
    }

    return PLANTILLA.format(
        generado=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        lat=lat,
        lon=lon,
        margen=margen_m,
        cota=escena.relieve.cota_origen_msnm,
        provisional=provisional,
        fuente_relieve=fuente,
        resolucion=resolucion,
        aviso=aviso,
        nx=malla.nx,
        ny=malla.ny,
        x0=round(malla.x0, 3),
        y0=round(malla.y0, 3),
        dx=round(malla.dx, 6),
        dy=round(malla.dy, 6),
        alturas=_lista_compacta(malla.vertices[:, 2]),
        lote=_lista_puntos(escena.lote_3d),
        sol=_formato_dict(datos_sol),
    )


def _formato_dict(d: dict, sangria: str = "    ") -> str:
    filas = [f"{sangria}{k!r}: {v!r}," for k, v in d.items()]
    return "{\n" + "\n".join(filas) + "\n}"
