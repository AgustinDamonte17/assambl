"""Rutas de la capa 03 — Casa (planta).

- `GET  /api/casa/ia`                   qué proveedor de IA está activo
- `GET  /api/casa/catalogo`             aberturas del catálogo del mercado
- `POST /api/casa/conversar`            un turno de la charla con el asistente
- `POST /api/casa/alternativas`         partidos de planta para un programa
- `POST /api/casa/interpretar-imagen`   bosquejo o plano → planta a revisar
- `POST /api/casa/analizar`             reglas R03 y RI sobre la planta: estado por pieza
- `POST /api/casa/amoblar`              propuesta de muebles y artefactos por ambiente
- `POST /api/casa/colocar`              una pieza del catálogo donde entre en un ambiente
- `POST /api/casa/galeria`              galería adosada a un muro exterior, amoblada
- `POST /api/casa/interior/conversar`   un pedido a Lumo en la vista 3D: operaciones y vista previa
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from assambl.capas import casa as capa
from assambl.capas import interior
from assambl.ia import asistente, proveedores
from assambl.ia import interior as lumo_interior
from assambl.modelo.casa import MensajeChat, Programa, RespuestaAsistente
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


class PedidoConversar(BaseModel):
    modo: Literal["libre", "orientador"] = "orientador"
    historial: list[MensajeChat] = []
    programa: Programa | None = None
    opciones: list[str] = Field(default=[], description="Ids de las opciones que tocó el usuario en el último turno")


@router.post("/conversar", response_model=RespuestaAsistente)
async def conversar(pedido: PedidoConversar) -> RespuestaAsistente:
    try:
        return await asistente.conversar(_proveedor(), pedido.modo, pedido.historial[-30:], pedido.programa,
                                         pedido.opciones)
    except proveedores.ErrorIA as e:
        raise HTTPException(502, str(e)) from e


class PedidoAlternativas(BaseModel):
    programa: Programa
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/alternativas")
def alternativas(pedido: PedidoAlternativas) -> dict:
    if not [a for a in pedido.programa.ambientes if a.uso != "circulacion"]:
        raise HTTPException(422, "El programa no tiene ambientes")
    alts = capa.alternativas(pedido.programa, lat=pedido.lat)
    for a in alts:
        if pedido.programa.galeria:
            a["casa"], _, notas = interior.agregar_galeria(a["casa"], lat=pedido.lat)
            a["advertencias"] = a.get("advertencias", []) + notas
        a["analisis"] = r03_planta.analizar_planta(a["casa"])
    return {"alternativas": alts}


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


# ---------------------------------------------------------------- interior

class PedidoAmoblar(BaseModel):
    casa: dict
    ambientes: list[str] | None = None
    reemplazar: bool = False


@router.post("/amoblar")
def amoblar(pedido: PedidoAmoblar) -> dict:
    casa, notas = interior.amoblar(pedido.casa, pedido.ambientes, pedido.reemplazar)
    return {"casa": casa, "notas": notas, "analisis": r03_planta.analizar_planta(casa)}


class PedidoColocar(BaseModel):
    casa: dict
    codigo: str
    ambiente: str


@router.post("/colocar")
def colocar(pedido: PedidoColocar) -> dict:
    casa, pieza, motivo = interior.colocar(pedido.casa, pedido.codigo, pedido.ambiente)
    return {"casa": casa, "pieza": pieza, "motivo": motivo, "analisis": r03_planta.analizar_planta(casa)}


class PedidoGaleria(BaseModel):
    casa: dict
    lado: Literal["norte", "sur", "este", "oeste"] | None = None
    fondo_m: float = Field(default=3.0, ge=1.2, le=5)
    largo_m: float | None = Field(default=None, gt=1, le=20)
    lat: float | None = Field(default=None, ge=-90, le=90)
    amoblar: bool = True


@router.post("/galeria")
def galeria(pedido: PedidoGaleria) -> dict:
    casa, gid, notas = interior.agregar_galeria(pedido.casa, pedido.lado, pedido.fondo_m, pedido.largo_m, pedido.lat)
    if gid is None:
        raise HTTPException(422, notas[0] if notas else "No se pudo armar la galería.")
    if pedido.amoblar:
        casa, n = interior.amoblar(casa, [gid], reemplazar=True)
        notas += n
    return {"casa": casa, "galeria": gid, "notas": notas, "analisis": r03_planta.analizar_planta(casa)}


class PedidoInterior(BaseModel):
    casa: dict
    historial: list[MensajeChat] = []
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/interior/conversar")
async def conversar_interior(pedido: PedidoInterior) -> dict:
    try:
        r = await lumo_interior.conversar(_proveedor(), pedido.casa, pedido.historial[-20:], pedido.lat)
    except proveedores.ErrorIA as e:
        raise HTTPException(502, str(e)) from e
    r["analisis"] = r03_planta.analizar_planta(r["casa"])
    return r
