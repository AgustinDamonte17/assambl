"""Rutas de operaciones: el contrato único para modificar un proyecto (MVP_01 §4.4).

Hoy el backend no guarda proyectos: recibe el proyecto, aplica la operación y lo
devuelve con su registro para el historial. Cuando exista el repositorio de
proyectos (docs/decisiones/0001_almacenamiento.md), esta misma ruta guardará la
versión y el registro sin que cambie el contrato de las operaciones.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from assambl.modelo import operaciones as ops
from assambl.modelo.proyecto import Proyecto

from .terreno import ContextoEscenas

router = APIRouter()


class PedidoOperacion(BaseModel):
    proyecto: Proyecto
    operacion: ops.Operacion
    autor: ops.Autor = "usuario"


@router.get("")
def catalogo() -> list[dict]:
    """Operaciones disponibles con el esquema de sus parámetros."""
    return ops.catalogo()


@router.post("/aplicar", response_model=ops.Resultado)
def aplicar(pedido: PedidoOperacion) -> ops.Resultado:
    try:
        return ops.aplicar(pedido.proyecto, pedido.operacion, pedido.autor, ContextoEscenas())
    except ops.OperacionInvalida as e:
        raise HTTPException(409, str(e)) from e
