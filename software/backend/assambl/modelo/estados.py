"""Estados por pieza, regla y capa (MVP_01 §4.4)."""

from enum import StrEnum


class Estado(StrEnum):
    PROPUESTO = "propuesto"
    COMPROBADO_POR_REGLAS = "comprobado_por_reglas"
    PENDIENTE_DATOS = "pendiente_datos"
    PENDIENTE_CALCULO = "pendiente_calculo"
    PENDIENTE_REVISION = "pendiente_revision"
    REVISADO = "revisado"
    DESACTUALIZADO = "desactualizado"


class EstadoFuente(StrEnum):
    """Resultado de una descarga de datos externos."""

    OK = "ok"
    PARCIAL = "parcial"
    PENDIENTE_DATOS = "pendiente_datos"
