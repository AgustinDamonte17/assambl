"""Requisitos para cerrar la capa 01 y empezar a diseñar la casa sobre el terreno.

Los requisitos bloqueantes son los que el diseño necesita para existir: un origen,
un relieve reconstruido para ese origen y un lote cerrado dentro del entorno. Lo
que R01 marca como pendiente sin que impida dibujar (pendiente sin relieve real,
lote más chico que el paso del DEM, superficie chica) viaja como aviso: el diseño
avanza y esos estados siguen visibles.
"""

from __future__ import annotations

from ..modelo.estados import Estado
from ..modelo.operaciones import Contexto, SinContexto, escena_vigente
from ..modelo.proyecto import Proyecto
from ..reglas import r01_terreno


def _requisito(id_: str, descripcion: str, cumple: bool, detalle: str = "", bloquea: bool = True,
               paso: str = "") -> dict:
    return {"id": id_, "descripcion": descripcion, "cumple": cumple, "bloquea": bloquea,
            "detalle": "" if cumple else detalle, "paso": paso}


def requisitos(proyecto: Proyecto, contexto: Contexto | None = None) -> dict:
    contexto = contexto or SinContexto()
    t = proyecto.terreno
    salida: list[dict] = []

    salida.append(_requisito(
        "ubicacion", "Ubicación del terreno definida", t.ubicacion is not None,
        "Buscá la dirección, escribí las coordenadas o hacé clic en el mapa.", paso="ubicacion"))

    escena = escena_vigente(proyecto, contexto)
    salida.append(_requisito(
        "relieve", "Relieve reconstruido para esta ubicación y este entorno", escena is not None,
        "Generá la escena 3D en el paso Ubicación." if t.escena_ref is None
        else "La escena no corresponde a la ubicación o al entorno actuales; se está regenerando.",
        paso="ubicacion"))

    v = t.lote.vertices
    analisis = r01_terreno.analizar_lote(
        v, escena.malla if escena else None, t.margen_m, escena.provisional if escena else False)
    verificaciones = {x["id"]: x for x in analisis["verificaciones"]}

    cerrado = verificaciones["R01.01"]
    salida.append(_requisito(
        "lote", "Lote cerrado, sin lados que se crucen",
        cerrado["estado"] == Estado.COMPROBADO_POR_REGLAS, cerrado["detalle"] or "Dibujá el lote.", paso="lote"))

    if "R01.04" in verificaciones:
        dentro = verificaciones["R01.04"]
        salida.append(_requisito(
            "lote_en_entorno", "Lote dentro del entorno reconstruido",
            dentro["estado"] == Estado.COMPROBADO_POR_REGLAS, dentro["detalle"], paso="ubicacion"))

    salida.append(_requisito(
        "lote_confirmado", "Lote confirmado en la ubicación actual", t.estado != Estado.DESACTUALIZADO,
        "El origen se movió después de dibujar el lote: confirmalo en el paso Lote.", paso="lote"))

    # Lo que R01 deja pendiente sin impedir el diseño.
    for vid in ("R01.02", "R01.03", "R01.05", "R01.06"):
        x = verificaciones.get(vid)
        if x and x["estado"] != Estado.COMPROBADO_POR_REGLAS:
            salida.append(_requisito(vid, x["descripcion"], False, x["detalle"], bloquea=False,
                                     paso="lote" if vid in ("R01.02", "R01.03") else "modelo"))

    return {
        "listo": all(r["cumple"] for r in salida if r["bloquea"]),
        "requisitos": salida,
    }
