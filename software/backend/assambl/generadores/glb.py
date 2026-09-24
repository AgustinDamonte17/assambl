"""Escritor de glTF 2.0 binario (.glb), sin dependencias externas.

Especificación: Khronos glTF 2.0, sección 4.4.3 (contenedor GLB).

Conversión de ejes. El proyecto trabaja en +X este, +Y norte, +Z arriba, en metros;
glTF define +Y arriba. En lugar de rotar los datos se agrega un nodo raíz con una
rotación de −90° alrededor de X. Así los números del archivo siguen siendo las
coordenadas del proyecto, y el importador de Blender cancela esa rotación y
devuelve la escena con Z arriba.

Cada nodo lleva en `extras` la procedencia y la resolución de su capa, de modo que
el archivo se explique solo sin depender de la interfaz que lo abra.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field

import numpy as np

MAGIA = 0x46546C67  # "glTF"
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

TRIANGULOS = 4
LINEAS = 1
TIRA_DE_LINEAS = 3

FLOTANTE = 5126
ENTERO_LARGO = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963

# Rotación de −90° en X: lleva el sistema Z arriba del proyecto al Y arriba de glTF.
ROTACION_A_GLTF = [-0.7071067811865475, 0.0, 0.0, 0.7071067811865476]


@dataclass
class Material:
    nombre: str
    color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
    metalico: float = 0.0
    rugosidad: float = 0.9
    doble_cara: bool = True
    sin_iluminacion: bool = False
    emision: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class Primitiva:
    posiciones: np.ndarray
    indices: np.ndarray | None = None
    normales: np.ndarray | None = None
    modo: int = TRIANGULOS
    material: Material | None = None


@dataclass
class Nodo:
    nombre: str
    primitivas: list[Primitiva]
    extras: dict = field(default_factory=dict)


def normales_planas(posiciones: np.ndarray, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Desindexa la malla y calcula una normal por cara.

    Se usa sombreado plano a propósito: suavizar las normales de una malla de posts
    de 30 m daría la apariencia de un relieve más detallado del que hay. Las facetas
    visibles son la resolución real del dato.
    """
    triangulos = posiciones[indices.reshape(-1, 3)]
    a, b, c = triangulos[:, 0], triangulos[:, 1], triangulos[:, 2]
    n = np.cross(b - a, c - a)
    largo = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, largo, out=np.zeros_like(n), where=largo > 0)
    return triangulos.reshape(-1, 3), np.repeat(n, 3, axis=0)


class _Buffer:
    def __init__(self) -> None:
        self.datos = bytearray()
        self.vistas: list[dict] = []
        self.accesores: list[dict] = []

    def _alinear(self, multiplo: int = 4) -> None:
        sobra = len(self.datos) % multiplo
        if sobra:
            self.datos.extend(b"\x00" * (multiplo - sobra))

    def _vista(self, crudo: bytes, destino: int | None) -> int:
        self._alinear()
        vista = {"buffer": 0, "byteOffset": len(self.datos), "byteLength": len(crudo)}
        if destino is not None:
            vista["target"] = destino
        self.datos.extend(crudo)
        self.vistas.append(vista)
        return len(self.vistas) - 1

    def vec3(self, valores: np.ndarray) -> int:
        a = np.ascontiguousarray(valores, dtype="<f4")
        vista = self._vista(a.tobytes(), ARRAY_BUFFER)
        self.accesores.append(
            {
                "bufferView": vista,
                "componentType": FLOTANTE,
                "count": int(a.shape[0]),
                "type": "VEC3",
                "min": [float(v) for v in a.min(axis=0)],
                "max": [float(v) for v in a.max(axis=0)],
            }
        )
        return len(self.accesores) - 1

    def escalar_entero(self, valores: np.ndarray) -> int:
        a = np.ascontiguousarray(valores.ravel(), dtype="<u4")
        vista = self._vista(a.tobytes(), ELEMENT_ARRAY_BUFFER)
        self.accesores.append(
            {
                "bufferView": vista,
                "componentType": ENTERO_LARGO,
                "count": int(a.size),
                "type": "SCALAR",
                "min": [int(a.min())] if a.size else [0],
                "max": [int(a.max())] if a.size else [0],
            }
        )
        return len(self.accesores) - 1


def _material_json(m: Material) -> dict:
    salida: dict = {
        "name": m.nombre,
        "pbrMetallicRoughness": {
            "baseColorFactor": list(m.color),
            "metallicFactor": m.metalico,
            "roughnessFactor": m.rugosidad,
        },
        "doubleSided": m.doble_cara,
    }
    if m.color[3] < 1.0:
        salida["alphaMode"] = "BLEND"
    if any(m.emision):
        salida["emissiveFactor"] = list(m.emision)
    if m.sin_iluminacion:
        salida["extensions"] = {"KHR_materials_unlit": {}}
    return salida


def construir(nodos: list[Nodo], extras_escena: dict | None = None, generador: str = "Assambl") -> bytes:
    """Arma el .glb completo en memoria."""
    buf = _Buffer()
    materiales: list[dict] = []
    indice_material: dict[int, int] = {}
    mallas: list[dict] = []
    nodos_json: list[dict] = []
    usa_unlit = False

    for nodo in nodos:
        primitivas = []
        for p in nodo.primitivas:
            atributos = {"POSITION": buf.vec3(p.posiciones)}
            if p.normales is not None:
                atributos["NORMAL"] = buf.vec3(p.normales)
            prim: dict = {"attributes": atributos, "mode": p.modo}
            if p.indices is not None:
                prim["indices"] = buf.escalar_entero(p.indices)
            if p.material is not None:
                clave = id(p.material)
                if clave not in indice_material:
                    indice_material[clave] = len(materiales)
                    materiales.append(_material_json(p.material))
                    usa_unlit = usa_unlit or p.material.sin_iluminacion
                prim["material"] = indice_material[clave]
            primitivas.append(prim)
        mallas.append({"name": nodo.nombre, "primitives": primitivas})
        entrada: dict = {"name": nodo.nombre, "mesh": len(mallas) - 1}
        if nodo.extras:
            entrada["extras"] = nodo.extras
        nodos_json.append(entrada)

    raiz = {
        "name": "assambl_raiz",
        "rotation": ROTACION_A_GLTF,
        "children": list(range(len(nodos_json))),
        "extras": {
            "sistema": "+X este, +Y norte, +Z arriba; 1 unidad = 1 metro",
            "origen": "punto del proyecto",
            **(extras_escena or {}),
        },
    }
    nodos_json.append(raiz)

    gltf: dict = {
        "asset": {"version": "2.0", "generator": generador},
        "scene": 0,
        "scenes": [{"nodes": [len(nodos_json) - 1]}],
        "nodes": nodos_json,
        "meshes": mallas,
        "accessors": buf.accesores,
        "bufferViews": buf.vistas,
        "buffers": [{"byteLength": len(buf.datos)}],
    }
    if materiales:
        gltf["materials"] = materiales
    if usa_unlit:
        gltf["extensionsUsed"] = ["KHR_materials_unlit"]

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    bin_bytes = bytes(buf.datos)
    bin_bytes += b"\x00" * (-len(bin_bytes) % 4)

    total = 12 + 8 + len(json_bytes) + (8 + len(bin_bytes) if bin_bytes else 0)
    salida = bytearray(struct.pack("<III", MAGIA, 2, total))
    salida += struct.pack("<II", len(json_bytes), CHUNK_JSON) + json_bytes
    if bin_bytes:
        salida += struct.pack("<II", len(bin_bytes), CHUNK_BIN) + bin_bytes
    return bytes(salida)


def rejilla_indices(nx: int, ny: int) -> np.ndarray:
    """Índices de triángulos de una rejilla regular de nx × ny vértices.

    El vértice (fila j, columna i) está en j*nx + i. Cada celda se parte en dos
    triángulos con el vértice común en la diagonal suroeste–noreste.
    """
    j, i = np.mgrid[0 : ny - 1, 0 : nx - 1]
    so = (j * nx + i).ravel()
    se = so + 1
    no = so + nx
    ne = no + 1
    return np.column_stack([so, se, ne, so, ne, no]).reshape(-1, 3).astype(np.uint32)


def contorno_a_lineas(vertices: np.ndarray, cerrado: bool = True) -> Primitiva:
    """Polilínea en modo LINE_STRIP; si es cerrada repite el primer vértice."""
    puntos = np.asarray(vertices, dtype=np.float32)
    if cerrado and len(puntos) > 1:
        puntos = np.vstack([puntos, puntos[:1]])
    return Primitiva(posiciones=puntos, modo=TIRA_DE_LINEAS)
