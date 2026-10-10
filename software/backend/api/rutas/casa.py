"""Rutas de la capa 03 — Casa (planta).

- `GET  /api/casa/ia`                   qué proveedor de IA está activo
- `GET  /api/casa/catalogo`             aberturas del catálogo del mercado
- `POST /api/casa/lumo`                 un turno con Lumo: la pregunta que sigue y la planta base
- `POST /api/casa/lumo/editar`          un pedido en palabras → acciones para el editor, o una pregunta
- `POST /api/casa/interpretar-imagen`   bosquejo o plano → planta a revisar
- `POST /api/casa/analizar`             reglas R03 sobre la planta: estado por pieza
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from assambl.capas import casa as capa
from assambl.capas import planta_base
from assambl.ia import asistente, lumo, lumo_editor, proveedores
from assambl.modelo.casa import Decisiones
from assambl.modelo.estados import Estado
from assambl.reglas import r03_planta

router = APIRouter()

MAX_IMAGEN_BYTES = 8 * 1024 * 1024


def _proveedor() -> proveedores.Proveedor:
    try:
        return proveedores.obtener()
    except proveedores.ErrorIA as e:
        raise HTTPException(503, str(e)) from e


@router.get("/ia")
def estado_ia() -> dict:
    return _proveedor().describir()


@router.get("/catalogo")
def catalogo() -> dict:
    return capa.catalogo()


class PedidoLumo(BaseModel):
    decisiones: Decisiones = Decisiones()
    texto: str = Field(default="", max_length=500, description="Respuesta escrita, si no se tocó una opción")
    cambio: Literal["dormitorios", "cocina", "tamano"] | None = Field(
        default=None, description="Decisión cambiada desde los controles, fuera del orden de las preguntas")
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/lumo")
def turno_lumo(pedido: PedidoLumo) -> dict:
    """La planta base aparece en cuanto se sabe cuántos dormitorios; lo que falta decidir va con el valor más común."""
    r = lumo.responder(pedido.decisiones, pedido.texto, pedido.cambio)
    propuesta = None
    if r.decisiones.dormitorios is not None:
        propuesta = planta_base.planta_base(r.decisiones, lat=pedido.lat)
        propuesta["analisis"] = r03_planta.analizar_planta(propuesta["casa"])
        if r.listo:
            mensaje = (lumo.mensaje_cambio(pedido.cambio, r.decisiones, propuesta["resumen"]) if pedido.cambio
                       else lumo.mensaje_listo(propuesta["resumen"]))
            r = r.model_copy(update={"mensaje": mensaje})
    return {**r.model_dump(), "propuesta": propuesta}


class PedidoEditar(BaseModel):
    texto: str = Field(min_length=1, max_length=600)
    contexto: dict = Field(description="Resumen de la planta que arma el editor: ambientes, muros, selección")
    historial: list[lumo_editor.MensajeEditor] = []


@router.post("/lumo/editar")
async def lumo_editar(pedido: PedidoEditar) -> dict:
    proveedor = _proveedor()
    try:
        turno = await lumo_editor.pedir_cambios(proveedor, pedido.texto, pedido.contexto, pedido.historial)
    except proveedores.ErrorIA as e:
        raise HTTPException(502, str(e)) from e
    return {**turno.model_dump(exclude_none=True), "simulado": proveedor.simulado}


class PedidoImagen(BaseModel):
    imagen: str = Field(description="data URL (data:image/png;base64,...)")
    notas: str = Field(default="", max_length=2000)
    ancho_total_m: float | None = Field(default=None, gt=2, lt=60)
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/interpretar-imagen")
async def interpretar_imagen(pedido: PedidoImagen) -> dict:
    if len(pedido.imagen) > MAX_IMAGEN_BYTES * 4 / 3:
        raise HTTPException(413, "La imagen supera los 8 MB; exportala más chica.")
    try:
        imagen = proveedores.Imagen.desde_data_url(pedido.imagen)
        proveedor = _proveedor()
        lectura = await asistente.interpretar_imagen(proveedor, imagen, pedido.notas, pedido.ancho_total_m)
    except proveedores.ErrorIA as e:
        raise HTTPException(502, str(e)) from e
    rects, advertencias = capa.normalizar_rectangulos(lectura.ambientes)
    if not rects:
        raise HTTPException(422, "No se reconocieron ambientes en la imagen. Probá con un dibujo más claro o con cotas.")
    casa, adv = capa.planta_desde_rectangulos(
        rects, estado=Estado.PENDIENTE_REVISION, lat=pedido.lat,
        origen={"fuente": "imagen", "proveedor": proveedor.describir(), "escala": lectura.escala.model_dump(),
                "confianza": lectura.confianza,
                "nota": "Interpretada por IA a partir de una imagen: cada pieza queda pendiente de revisión."})
    return {
        "lectura": lectura.model_dump(),
        "rectangulos": [r.model_dump() for r in rects],
        "casa": casa,
        "advertencias": lectura.advertencias + advertencias + adv,
        "analisis": r03_planta.analizar_planta(casa),
        "simulado": proveedor.simulado,
    }


class PedidoAnalizar(BaseModel):
    casa: dict


@router.post("/analizar")
def analizar(pedido: PedidoAnalizar) -> dict:
    return r03_planta.analizar_planta(pedido.casa)
