"""Rutas de la capa 03 — Casa (planta).

- `GET  /api/casa/ia`                   qué proveedor de IA está activo
- `GET  /api/casa/catalogo`             aberturas del catálogo del mercado
- `POST /api/casa/conversar`            un turno de la charla con el asistente
- `POST /api/casa/alternativas`         partidos de planta para un programa
- `POST /api/casa/interpretar-imagen`   bosquejo o plano → planta a revisar
- `POST /api/casa/analizar`             reglas R03 (estado por pieza) y fundamentos de diseño
- `GET  /api/casa/fundamentos`          los fundamentos de diseño con sus fuentes
- `GET  /api/casa/referencias`          las plantas de referencia (galería)
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from assambl.capas import casa as capa
from assambl.fundamentos import evaluar, referencias
from assambl.ia import asistente, proveedores
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


@router.get("/fundamentos")
def fundamentos() -> dict:
    return {"fuente": evaluar.FUENTE, "criterios": evaluar.CRITERIOS, "fundamentos": evaluar.FUNDAMENTOS}


@router.get("/referencias")
def plantas_referencia() -> dict:
    return {"plantas": referencias.resumen_referencias()}


class PedidoReferencia(BaseModel):
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/referencias/{rid}")
def partir_de_referencia(rid: str, pedido: PedidoReferencia) -> dict:
    """Una planta de referencia tal cual (orientada al sol) para empezar a editar desde ella."""
    planta = next((p for p in referencias.cargar()["plantas"] if p["id"] == rid), None)
    if planta is None:
        raise HTTPException(404, "No existe esa planta de referencia")
    origen = {"fuente": "assambl/fundamentos/plantas_referencia.json", "referencia": rid, "archivo": planta["archivo"],
              "nota": f"Planta de referencia «{planta['nombre']}»."}
    rects, casa, adv, ev, nota = referencias.orientar(referencias.rectangulos(planta), pedido.lat, Estado.PROPUESTO, origen)
    return {"rectangulos": [r.model_dump() for r in rects], "casa": casa, "advertencias": adv,
            "adaptacion": [nota] if nota else [], "evaluacion": ev,
            "analisis": r03_planta.analizar_planta(casa)}


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
        "evaluacion": evaluar.evaluar(casa, pedido.lat),
        "simulado": proveedor.simulado,
    }


class PedidoAnalizar(BaseModel):
    casa: dict
    lat: float | None = Field(default=None, ge=-90, le=90)


@router.post("/analizar")
def analizar(pedido: PedidoAnalizar) -> dict:
    analisis = r03_planta.analizar_planta(pedido.casa)
    try:
        analisis["fundamentos"] = evaluar.evaluar(pedido.casa, pedido.lat)
    except (KeyError, TypeError, ValueError, IndexError):
        # Una planta a medio dibujar no impide ver el estado de las piezas.
        analisis["fundamentos"] = None
    return analisis
