"""El .glb se vuelve a leer con un analizador propio para comprobar que respeta
el contenedor descrito en glTF 2.0 §4.4.3."""

import json
import struct

import numpy as np
import pytest

from assambl.generadores import glb


def leer_glb(datos: bytes) -> tuple[dict, bytes]:
    magia, version, total = struct.unpack("<III", datos[:12])
    assert magia == glb.MAGIA
    assert version == 2
    assert total == len(datos)
    cuerpo = datos[12:]
    trozos = {}
    while cuerpo:
        largo, tipo = struct.unpack("<II", cuerpo[:8])
        trozos[tipo] = cuerpo[8 : 8 + largo]
        cuerpo = cuerpo[8 + largo :]
    return json.loads(trozos[glb.CHUNK_JSON]), trozos.get(glb.CHUNK_BIN, b"")


def cuadrado() -> glb.Nodo:
    posiciones = np.array([[0, 0, 0], [10, 0, 0], [10, 20, 0], [0, 20, 0]], dtype=np.float32)
    indices = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
    vertices, normales = glb.normales_planas(posiciones, indices)
    return glb.Nodo(
        nombre="prueba",
        primitivas=[glb.Primitiva(posiciones=vertices, normales=normales, material=glb.Material("suelo"))],
        extras={"fuente": "sintética"},
    )


def test_contenedor_valido():
    gltf, binario = leer_glb(glb.construir([cuadrado()]))
    assert gltf["asset"]["version"] == "2.0"
    assert len(binario) % 4 == 0
    assert gltf["buffers"][0]["byteLength"] <= len(binario)


def test_nodo_raiz_convierte_ejes():
    """Un vértice al norte debe quedar sobre +Z de glTF tras la rotación del nodo raíz."""
    gltf, _ = leer_glb(glb.construir([cuadrado()]))
    raiz = gltf["nodes"][gltf["scenes"][0]["nodes"][0]]
    assert raiz["rotation"] == pytest.approx(glb.ROTACION_A_GLTF, abs=1e-9)
    x, y, z, w = raiz["rotation"]
    # El cuaternión debe ser unitario y equivalente a −90° alrededor de X.
    assert x * x + y * y + z * z + w * w == pytest.approx(1.0)
    assert np.degrees(2 * np.arctan2(-x, w)) == pytest.approx(90.0)


def test_extras_viajan_en_el_archivo():
    gltf, _ = leer_glb(glb.construir([cuadrado()], extras_escena={"margen_m": 500}))
    nodos = {n["name"]: n for n in gltf["nodes"]}
    assert nodos["prueba"]["extras"]["fuente"] == "sintética"
    assert nodos["assambl_raiz"]["extras"]["margen_m"] == 500
    assert "metro" in nodos["assambl_raiz"]["extras"]["sistema"]


def test_accesores_declaran_limites():
    gltf, _ = leer_glb(glb.construir([cuadrado()]))
    posicion = gltf["accessors"][gltf["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    assert posicion["type"] == "VEC3"
    assert posicion["min"] == [0.0, 0.0, 0.0]
    assert posicion["max"] == [10.0, 20.0, 0.0]


def test_normales_planas_apuntan_arriba():
    posiciones = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float32)
    indices = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
    vertices, normales = glb.normales_planas(posiciones, indices)
    assert vertices.shape == (6, 3)
    assert normales.shape == (6, 3)
    assert np.allclose(normales, [0, 0, 1])


def test_normales_planas_en_rampa():
    """Una rampa que sube 1 m cada 1 m hacia el este tiene normal a 45°."""
    posiciones = np.array([[0, 0, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]], dtype=np.float32)
    indices = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
    _, normales = glb.normales_planas(posiciones, indices)
    assert np.allclose(np.linalg.norm(normales, axis=1), 1.0)
    assert normales[0][0] == pytest.approx(-np.sqrt(0.5), abs=1e-5)
    assert normales[0][2] == pytest.approx(np.sqrt(0.5), abs=1e-5)


def test_rejilla_indices():
    idx = glb.rejilla_indices(3, 2)
    assert idx.shape == (4, 3)  # 2 celdas × 2 triángulos
    assert set(idx.ravel().tolist()) == {0, 1, 2, 3, 4, 5}


def test_rejilla_produce_triangulos_antihorarios_vista_desde_arriba():
    nx = ny = 3
    j, i = np.mgrid[0:ny, 0:nx]
    posiciones = np.column_stack([i.ravel(), j.ravel(), np.zeros(nx * ny)]).astype(np.float32)
    _, normales = glb.normales_planas(posiciones, glb.rejilla_indices(nx, ny))
    assert np.allclose(normales, [0, 0, 1])


def test_lineas_cerradas_repiten_el_primer_vertice():
    p = glb.contorno_a_lineas(np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]]), cerrado=True)
    assert p.modo == glb.TIRA_DE_LINEAS
    assert len(p.posiciones) == 4
    assert np.allclose(p.posiciones[0], p.posiciones[-1])


def test_material_transparente_declara_mezcla():
    nodo = glb.Nodo("x", [glb.Primitiva(posiciones=np.zeros((3, 3), dtype=np.float32),
                                        material=glb.Material("vidrio", color=(1, 1, 1, 0.3)))])
    gltf, _ = leer_glb(glb.construir([nodo]))
    assert gltf["materials"][0]["alphaMode"] == "BLEND"
