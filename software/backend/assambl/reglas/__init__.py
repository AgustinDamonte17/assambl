"""Registro de reglas. Cada regla tiene ID, versión, origen y el estado que otorga (MVP_01 §5)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..modelo.estados import Estado


@dataclass
class Verificacion:
    id: str
    version: str
    descripcion: str
    estado: Estado
    detalle: str = ""
    origen: str = ""
    parametros: dict = field(default_factory=dict)

    def como_dict(self) -> dict:
        return {
            "id": self.id, "version": self.version, "descripcion": self.descripcion,
            "estado": self.estado.value, "detalle": self.detalle, "origen": self.origen,
            "parametros": self.parametros,
        }
