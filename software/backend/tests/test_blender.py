"""El script de Blender tiene que ser Python válido y traer los mismos números
que el .glb, porque sale del mismo generador."""

import math
import sys
import types
from datetime import date, datetime, timedelta, timezone

import pytest

from assambl.capas import terreno
from assambl.clima import sol
from assambl.generadores import blender
from assambl.modelo.sitio import MallaDem

LAT, LON, MARGEN = -31.42, -64.19, 300.0
LOTE = [(-6.0, -15.0), (6.0, -15.0), (6.0, 15.0), (-6.0, 15.0)]


def dem() -> MallaDem:
    paso = 1 / 3600
    n = 25
    alturas = [800.0 + 0.5 * i + 0.25 * j for j in range(n) for i in range(n)]
    return MallaDem(lat_sur=LAT - (n // 2) * paso, lon_oeste=LON - (n // 2) * paso,
                    paso_deg=paso, nx=n, ny=n, alturas_msnm=alturas)


@pytest.fixture
def escena():
    return terreno.componer(LAT, LON, MARGEN, dem(), LOTE, [], [])


@pytest.fixture
def posicion_sol():
    momento = datetime(2024, 12, 21, 10, 0, tzinfo=timezone(timedelta(hours=-3)))
    return sol.posicion(LAT, LON, momento.astimezone(timezone.utc), -3.0)


@pytest.fixture
def bpy_falso(monkeypatch):
    """El script importa bpy; fuera de Blender alcanza con un módulo vacío porque
    main() solo corre cuando se ejecuta como programa."""
    monkeypatch.setitem(sys.modules, "bpy", types.ModuleType("bpy"))


def constantes(texto: str) -> dict:
    espacio: dict = {}
    exec(compile(texto, "<script>", "exec"), {"__name__": "importado"}, espacio)
    return espacio


def test_el_script_compila(escena, posicion_sol):
    texto = blender.generar(escena, LAT, LON, MARGEN, posicion_sol)
    compile(texto, "terreno_blender.py", "exec")


def test_el_script_declara_la_rejilla_del_dem(escena, posicion_sol, bpy_falso):
    espacio = constantes(blender.generar(escena, LAT, LON, MARGEN, posicion_sol))
    assert espacio["NX"] == escena.malla.nx
    assert espacio["NY"] == escena.malla.ny
    assert len(espacio["ALTURAS"]) == escena.malla.nx * escena.malla.ny
    assert espacio["DX"] == pytest.approx(escena.malla.dx, abs=1e-6)
    assert espacio["COTA_ORIGEN_MSNM"] == escena.relieve.cota_origen_msnm


def test_las_alturas_coinciden_con_la_malla(escena, posicion_sol, bpy_falso):
    espacio = constantes(blender.generar(escena, LAT, LON, MARGEN, posicion_sol))
    for esperada, obtenida in zip(escena.malla.vertices[:, 2], espacio["ALTURAS"]):
        assert obtenida == pytest.approx(esperada, abs=0.005)


def test_el_lote_viene_apoyado_en_tres_dimensiones(escena, posicion_sol, bpy_falso):
    espacio = constantes(blender.generar(escena, LAT, LON, MARGEN, posicion_sol))
    assert len(espacio["LOTE"]) == len(LOTE)
    for (x, y), punto in zip(LOTE, espacio["LOTE"]):
        assert punto[0] == pytest.approx(x, abs=1e-3)
        assert punto[1] == pytest.approx(y, abs=1e-3)
        esperada = escena.malla.altura_en(x, y) + terreno.SEPARACION_SUPERFICIE_M
        assert punto[2] == pytest.approx(esperada, abs=0.01)


def test_la_escena_provisional_queda_avisada(posicion_sol):
    from assambl.fuentes import nasadem

    plana = nasadem.malla_provisional(LAT, LON, MARGEN)
    e = terreno.componer(LAT, LON, MARGEN, plana, LOTE, [], ["sin datos"])
    texto = blender.generar(e, LAT, LON, MARGEN, posicion_sol)
    assert "PROVISIONAL = True" in texto
    assert "provisional" in texto.lower()


def test_el_script_no_provisional_avisa_que_no_es_mensura(escena, posicion_sol):
    texto = blender.generar(escena, LAT, LON, MARGEN, posicion_sol)
    assert "PROVISIONAL = False" in texto
    assert "no es una mensura" in texto.lower()


def test_la_rotacion_del_sol_apunta_al_lugar_correcto(escena, posicion_sol, bpy_falso):
    """El eje +Z del objeto sol debe coincidir con el vector hacia el sol."""
    espacio = constantes(blender.generar(escena, LAT, LON, MARGEN, posicion_sol))
    rx = math.radians(90.0 - espacio["SOL"]["elevacion_deg"])
    rz = math.radians(180.0 - espacio["SOL"]["azimut_deg"])
    # Euler XYZ aplicado a (0, 0, 1): primero X, después Z.
    tras_x = (0.0, -math.sin(rx), math.cos(rx))
    eje_z = (
        tras_x[0] * math.cos(rz) - tras_x[1] * math.sin(rz),
        tras_x[0] * math.sin(rz) + tras_x[1] * math.cos(rz),
        tras_x[2],
    )
    for obtenido, esperado in zip(eje_z, posicion_sol.direccion):
        assert obtenido == pytest.approx(esperado, abs=1e-4)


def test_fechas_clave_para_asoleamiento():
    f = sol.fechas_clave(date.today().year)
    assert set(f) == {"equinoccio_marzo", "solsticio_invierno", "equinoccio_septiembre", "solsticio_verano"}
