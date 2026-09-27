import asyncio
import json
import struct

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from api.main import app
from assambl.fuentes import imagen_satelital as im
from assambl.fuentes import imagen_sintetica as sin
from assambl.fuentes import osm
from assambl.geometria.coordenadas import SistemaLocal
from assambl.sitio import interpretacion_ia, modelo, vegetacion

S = SistemaLocal(sin.LAT_REF, sin.LON_REF)


async def sintetica(z, x, y):
    return sin.tesela(z, x, y)


def orto(rect, m_px, obtener=sintetica):
    return asyncio.run(im.ortofoto(S, *rect, m_px, obtener=obtener, nombre_fuente="prueba"))


def json_glb(datos: bytes) -> dict:
    largo = struct.unpack("<I", datos[12:16])[0]
    return json.loads(datos[20:20 + largo])


def test_reconoce_el_cartel_de_esri_sin_imagen():
    cartel = Image.new("RGB", (256, 256), (222, 222, 222))
    ImageDraw.Draw(cartel).text((40, 120), "Map data not yet available", fill=(90, 90, 90))
    assert im.es_cartel_sin_imagen(cartel)
    assert not im.es_cartel_sin_imagen(sin.tesela(18, 90000, 150000))


def test_la_ortofoto_queda_georreferenciada():
    # El camino de tierra del mundo sintético corre de norte a sur entre x = 38 y 44 m.
    o = orto((20, 60, -10, 10), 0.25)
    col, fila = o.a_pixel(41.0, 0.0)
    assert tuple(o.rgb[int(fila), int(col)]) == pytest.approx((168, 138, 104), abs=6)
    col, fila = o.a_pixel(30.0, 0.0)
    assert tuple(o.rgb[int(fila), int(col)]) != pytest.approx((168, 138, 104), abs=6)


def test_sin_imagen_a_ese_zoom_usa_la_de_un_zoom_menor():
    pedidos = []

    async def solo_hasta_17(z, x, y):
        pedidos.append(z)
        return sin.tesela(z, x, y) if z <= 17 else None

    o = orto((-20, 20, -20, 20), 0.3, solo_hasta_17)
    assert o.zoom == 19 and o.zoom_min_usado == 17 and o.cobertura == 1.0
    assert 18 in pedidos


def test_sin_red_la_ortofoto_queda_vacia_y_no_falla():
    async def nada(z, x, y):
        return None

    assert orto((-20, 20, -20, 20), 0.3, nada).cobertura == 0.0


def test_detecta_los_arboles_del_lote():
    o = orto((-40, 30, -50, 50), 0.3)
    detectados = vegetacion.detectar(o)
    reales = [a for a in sin.arboles_en_rectangulo(o.xmin, o.xmax, o.ymin, o.ymax)
              if o.xmin + a[2] < a[0] < o.xmax - a[2] and o.ymin + a[2] < a[1] < o.ymax - a[2]]
    assert len(reales) >= 5
    for cx, cy, r in reales:
        mas_cerca = min(detectados, key=lambda a: (a.x - cx) ** 2 + (a.y - cy) ** 2)
        assert np.hypot(mas_cerca.x - cx, mas_cerca.y - cy) < 0.6
        assert mas_cerca.radio_m == pytest.approx(r, abs=0.6)
        assert mas_cerca.altura_supuesta


def test_osm_calles_y_construcciones():
    datos = osm.interpretar(sin.overpass(*S.a_geografica(-200, -200), *S.a_geografica(200, 200)), S)
    assert datos.estado == "ok"
    tipos = {v.tipo: v for v in datos.vias}
    assert not tipos["track"].pavimentada and tipos["track"].ancho_m == 6.0
    assert tipos["residential"].pavimentada and tipos["residential"].ancho_supuesto
    alturas = {c.altura_m for c in datos.construcciones}
    assert osm.ALTURA_POR_DEFECTO_M in alturas and 7.0 in alturas  # 2 plantas × 3 m + 1 m


LOTE = [(-30.0, -40.0), (20.0, -40.0), (20.0, 40.0), (-30.0, 40.0)]


@pytest.fixture
def sintetico(monkeypatch, tmp_path):
    monkeypatch.setenv("ASSAMBL_IMAGEN_SINTETICA", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("assambl.config.DIR_CACHE", tmp_path)


def test_modelo_del_sitio_completo(sintetico):
    m = asyncio.run(modelo.generar(sin.LAT_REF, sin.LON_REF, 150, LOTE))
    nombres = {n["name"] for n in json_glb(m.glb)["nodes"]}
    assert {"01_suelo", "01_suelo_lote", "01_lote", "01_calles", "01_construcciones",
            "01_arboles_lote", "01_arboles_entorno", "01_referencias"} <= nombres
    assert len(json_glb(m.glb)["images"]) == 2
    assert m.resumen["arboles_lote"] > 0 and m.resumen["interpretacion"] == "imagen"
    assert all(a["id"].startswith("A") for a in m.arboles_lote)
    assert any("plano" in a for a in m.advertencias) and any("SINTÉTICA" in a for a in m.advertencias)


def test_con_ia_los_arboles_del_lote_salen_de_la_interpretacion(sintetico, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    rect = modelo.rectangulo_lote(LOTE, 150)
    o = orto(rect, modelo.M_PX_LOTE)
    o.fuente, o.sintetica = sin.NOMBRE, True
    respuesta = interpretacion_ia.InterpretacionIA(
        arboles=[interpretacion_ia.ArbolIA(x_px=o.ancho / 2, y_px=o.alto / 2, radio_px=10, altura_m=9)],
        construcciones=[], observaciones="un árbol")
    interpretacion_ia.guardar_para_prueba(o, LOTE, respuesta)

    ia = asyncio.run(interpretacion_ia.interpretar(o, LOTE))
    assert ia is not None and ia.desde_cache and len(ia.arboles) == 1
    a = ia.arboles[0]
    cx, cy = (o.xmin + o.xmax) / 2, (o.ymin + o.ymax) / 2
    assert a.x == pytest.approx(cx, abs=0.5) and a.y == pytest.approx(cy, abs=0.5)
    assert a.radio_m == pytest.approx(10 * o.m_px, rel=0.02) and not a.altura_supuesta

    m = asyncio.run(modelo.generar(sin.LAT_REF, sin.LON_REF, 150, LOTE))
    assert m.resumen["interpretacion"] == "ia"
    assert [x["fuente"] for x in m.arboles_lote] == [interpretacion_ia.FUENTE]


def test_sin_clave_no_hay_ia(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not interpretacion_ia.disponible()


def test_api_genera_sirve_y_vincula_el_modelo(sintetico):
    cliente = TestClient(app)
    pedido = {"lat": sin.LAT_REF, "lon": sin.LON_REF, "margen_m": 150, "vertices": LOTE}
    r = cliente.post("/api/terreno/escena", json=pedido)
    assert r.status_code == 200, r.text
    escena = r.json()
    assert escena["entrada"]["vertices"] == [list(p) for p in LOTE]
    assert escena["area_m2"] == 4000
    glb = cliente.get(f"/api/terreno/escena/{escena['ref']}.glb")
    assert glb.status_code == 200 and glb.content[:4] == b"glTF"

    from tests.test_operaciones import proyecto_nuevo

    p = proyecto_nuevo().model_dump(mode="json")
    for op in ({"tipo": "definir_ubicacion", "lat": sin.LAT_REF, "lon": sin.LON_REF},
               {"tipo": "definir_margen", "margen_m": 150},
               {"tipo": "definir_lote", "vertices": LOTE},
               {"tipo": "vincular_escena", "ref": escena["ref"]}):
        r = cliente.post("/api/operaciones/aplicar", json={"proyecto": p, "operacion": op})
        assert r.status_code == 200, r.text
        p = r.json()["proyecto"]
    req = cliente.post("/api/terreno/requisitos", json=p).json()
    assert req["listo"], req

    # Si el lote cambia, el modelo ya no le corresponde.
    r = cliente.post("/api/operaciones/aplicar", json={"proyecto": p, "operacion": {
        "tipo": "definir_lote", "vertices": LOTE[:3]}})
    req = cliente.post("/api/terreno/requisitos", json=r.json()["proyecto"]).json()
    assert not req["listo"]
    assert any(q["id"] == "sitio" and not q["cumple"] for q in req["requisitos"])
