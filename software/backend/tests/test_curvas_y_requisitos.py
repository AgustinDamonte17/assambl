import numpy as np
import pytest
from pydantic import ValidationError

from assambl.geometria import curvas
from assambl.geometria.malla import MallaLocal
from assambl.guia import terreno as guia
from assambl.modelo import operaciones as ops
from assambl.modelo.proyecto import Proyecto
from tests.test_operaciones import LOTE_GRANDE, ContextoFijo, aplicar, escena, proyecto_nuevo, ubicado


def malla(z: np.ndarray, paso: float = 30.0) -> MallaLocal:
    ny, nx = z.shape
    x0, y0 = -paso * (nx - 1) / 2, -paso * (ny - 1) / 2
    mx, my = np.meshgrid(x0 + np.arange(nx) * paso, y0 + np.arange(ny) * paso)
    return MallaLocal(vertices=np.column_stack([mx.ravel(), my.ravel(), z.ravel()]),
                      nx=nx, ny=ny, x0=x0, y0=y0, dx=paso, dy=paso)


def test_plano_inclinado_da_curvas_rectas_en_su_lugar():
    # Baja 1 m cada 30 m hacia el este: z = -x / 30.
    n = 11
    x = -150 + np.arange(n) * 30.0
    z = np.tile(-x / 30.0, (n, 1))
    assert curvas.equidistancia(10.0) == 0.5  # 20 curvas, dentro del máximo
    r = curvas.curvas(malla(z), cota_origen_msnm=100.0, equidistancia_m=1.0)
    assert r["cota_min"] == 95.0 and r["cota_max"] == 105.0
    c100 = next(c for c in r["curvas"] if c["cota"] == 100.0)
    assert c100["maestra"]
    # La curva de 100 m pasa por x = 0 a lo largo de todo el norte-sur.
    xs = {p[0] for s in c100["segmentos"] for p in s}
    assert xs == {0.0}
    assert len(c100["segmentos"]) == n - 1


def test_relieve_plano_no_tiene_curvas():
    r = curvas.curvas(malla(np.zeros((5, 5))))
    assert r["equidistancia_m"] is None and r["curvas"] == []


def test_silla_no_cruza_segmentos():
    z = np.array([[1.0, -1.0], [-1.0, 1.0]]) + 0.2  # centro positivo, como el suroeste
    segs = curvas._segmentos(malla(z), z, 0.0)
    assert len(segs) == 2
    # Cada segmento corta una sola esquina negativa: sureste o noroeste.
    for (a, b) in segs:
        assert (a[0] > 0) == (b[0] > 0) or (a[1] > 0) == (b[1] > 0)


@pytest.mark.parametrize("desnivel,esperada", [(0.1, None), (3, 0.5), (20, 1.0), (40, 2.0), (400, 20.0), (5000, 50.0)])
def test_equidistancia_estandar(desnivel, esperada):
    assert curvas.equidistancia(desnivel) == esperada


def _ids(r, solo_bloqueantes=True):
    return {q["id"] for q in r["requisitos"] if not q["cumple"] and (q["bloquea"] or not solo_bloqueantes)}


def test_proyecto_nuevo_no_esta_listo():
    r = guia.requisitos(proyecto_nuevo())
    assert not r["listo"]
    assert {"ubicacion", "relieve", "lote"} <= _ids(r)


def test_listo_con_escena_y_lote_valido():
    ctx = ContextoFijo(escena(pendiente=2.0))
    p = aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx).proyecto
    p = aplicar(p, {"tipo": "definir_lote", "vertices": LOTE_GRANDE}, ctx).proyecto
    r = guia.requisitos(p, ctx)
    assert r["listo"], r
    assert _ids(r, solo_bloqueantes=False) == set()


def test_pendiente_excesiva_avisa_pero_no_bloquea():
    ctx = ContextoFijo(escena(pendiente=8.0))
    p = aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx).proyecto
    p = aplicar(p, {"tipo": "definir_lote", "vertices": LOTE_GRANDE}, ctx).proyecto
    r = guia.requisitos(p, ctx)
    assert r["listo"]
    assert "R01.05" in _ids(r, solo_bloqueantes=False)


def test_escena_perdida_o_lote_desactualizado_bloquean():
    ctx = ContextoFijo(escena())
    p = aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx).proyecto
    p = aplicar(p, {"tipo": "definir_lote", "vertices": LOTE_GRANDE}, ctx).proyecto
    assert "relieve" in _ids(guia.requisitos(p, ContextoFijo()))  # el servidor perdió la caché
    movido = aplicar(p, {"tipo": "definir_ubicacion", "lat": -34.7, "lon": -58.4}, ctx).proyecto
    assert {"relieve", "lote_confirmado"} <= _ids(guia.requisitos(movido, ctx))


def test_lote_fuera_del_entorno_bloquea():
    ctx = ContextoFijo(escena())
    p = aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx).proyecto
    lejos = [(400.0, 400.0), (600.0, 400.0), (600.0, 600.0)]
    p = aplicar(p, {"tipo": "definir_lote", "vertices": lejos}, ctx).proyecto
    assert "lote_en_entorno" in _ids(guia.requisitos(p, ctx))


def test_margen_maximo_es_1000_y_los_proyectos_viejos_se_recortan():
    with pytest.raises(ValidationError):
        ops.ADAPTADOR.validate_python({"tipo": "definir_margen", "margen_m": 1500})
    datos = proyecto_nuevo().model_dump(mode="json")
    datos["terreno"]["margen_m"] = 2000
    assert Proyecto.model_validate(datos).terreno.margen_m == 1000
