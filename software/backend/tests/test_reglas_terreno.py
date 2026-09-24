import numpy as np
import pytest

from assambl.geometria.malla import MallaLocal
from assambl.reglas import r01_terreno


def malla_inclinada(pendiente_pct: float, n: int = 41, paso: float = 30.0) -> MallaLocal:
    """Plano que baja hacia el este con la pendiente pedida, con posts cada `paso`."""
    x0 = y0 = -paso * (n - 1) / 2
    coord = x0 + np.arange(n) * paso
    mx, my = np.meshgrid(coord, coord)
    z = -mx * pendiente_pct / 100.0
    return MallaLocal(
        vertices=np.column_stack([mx.ravel(), my.ravel(), z.ravel()]),
        nx=n, ny=n, x0=x0, y0=y0, dx=paso, dy=paso,
    )


def lote_grande():
    """120 × 120 m: bien mayor que los posts de 30 m, para que R01.06 se cumpla."""
    return [(-60, -60), (60, -60), (60, 60), (-60, 60)]


def test_lote_valido_con_pendiente_suave():
    r = r01_terreno.analizar_lote(lote_grande(), malla_inclinada(2.0), margen_m=500)
    assert r["area_m2"] == 14400
    assert r["estado"] == "comprobado_por_reglas"
    assert r["pendiente"]["porcentaje"] == pytest.approx(2.0, abs=0.05)
    assert r["pendiente"]["direccion_deg"] == pytest.approx(90.0, abs=1.0)


def test_pendiente_excesiva_marca_revision():
    r = r01_terreno.analizar_lote(lote_grande(), malla_inclinada(8.0), margen_m=500)
    assert r["estado"] == "pendiente_revision"
    assert any(v["id"] == "R01.05" and v["estado"] == "pendiente_revision" for v in r["verificaciones"])


def test_lote_mas_chico_que_el_paso_del_dem_avisa():
    """Un lote de 12 × 30 m frente a posts de 30 m: el DEM no resuelve su interior."""
    lote = [(-6, -15), (6, -15), (6, 15), (-6, 15)]
    r = r01_terreno.analizar_lote(lote, malla_inclinada(2.0), margen_m=500)
    r06 = next(v for v in r["verificaciones"] if v["id"] == "R01.06")
    assert r06["estado"] == "pendiente_datos"
    assert "mensura" in r06["detalle"]
    assert r["estado"] == "pendiente_datos"


def test_escena_provisional_no_informa_pendiente():
    r = r01_terreno.analizar_lote(lote_grande(), malla_inclinada(2.0), margen_m=500, provisional=True)
    assert r["pendiente"] is None
    r05 = next(v for v in r["verificaciones"] if v["id"] == "R01.05")
    assert r05["estado"] == "pendiente_datos"
    assert "provisional" in r05["detalle"]


def test_lote_fuera_del_margen():
    lote = [(-600, -600), (600, -600), (600, 600), (-600, 600)]
    r = r01_terreno.analizar_lote(lote, None, margen_m=500)
    r04 = next(v for v in r["verificaciones"] if v["id"] == "R01.04")
    assert r04["estado"] == "pendiente_datos"


def test_poligono_incompleto():
    r = r01_terreno.analizar_lote([(0, 0), (10, 0)])
    assert r["estado"] == "pendiente_datos"
    assert r["verificaciones"][0]["estado"] == "pendiente_datos"


def test_sin_relieve_la_pendiente_queda_pendiente_de_datos():
    r = r01_terreno.analizar_lote(lote_grande(), None, margen_m=500)
    r05 = next(v for v in r["verificaciones"] if v["id"] == "R01.05")
    assert r05["estado"] == "pendiente_datos"
    assert r["pendiente"] is None
