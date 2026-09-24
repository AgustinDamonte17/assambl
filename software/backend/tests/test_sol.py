"""El cálculo solar se contrasta con valores publicados por el NOAA Solar Calculator."""

from datetime import date, datetime, timedelta, timezone

import pytest

from assambl.clima import sol

CORDOBA = (-31.42, -64.19)
HUSO_AR = -3.0


def test_declinacion_en_solsticios():
    inv = sol.eventos(*CORDOBA, date(2024, 6, 21), HUSO_AR)
    ver = sol.eventos(*CORDOBA, date(2024, 12, 21), HUSO_AR)
    assert inv.declinacion_deg == pytest.approx(23.44, abs=0.05)
    assert ver.declinacion_deg == pytest.approx(-23.44, abs=0.05)


def test_elevacion_al_mediodia_solar():
    """Al mediodía solar la elevación vale 90° − |latitud − declinación|."""
    for dia, esperado in [(date(2024, 6, 21), 35.14), (date(2024, 12, 21), 82.02)]:
        ev = sol.eventos(*CORDOBA, dia, HUSO_AR)
        h, m = (int(x) for x in ev.mediodia_solar_local.split(":"))
        momento = datetime(dia.year, dia.month, dia.day, h, m, tzinfo=timezone(timedelta(hours=HUSO_AR)))
        p = sol.posicion(*CORDOBA, momento.astimezone(timezone.utc), HUSO_AR)
        assert p.elevacion_deg == pytest.approx(esperado, abs=0.3)


def test_azimut_al_mediodia_apunta_al_norte_en_hemisferio_sur():
    dia = date(2024, 6, 21)
    ev = sol.eventos(*CORDOBA, dia, HUSO_AR)
    h, m = (int(x) for x in ev.mediodia_solar_local.split(":"))
    momento = datetime(dia.year, dia.month, dia.day, h, m, tzinfo=timezone(timedelta(hours=HUSO_AR)))
    p = sol.posicion(*CORDOBA, momento.astimezone(timezone.utc), HUSO_AR)
    assert p.azimut_deg == pytest.approx(0.0, abs=1.0) or p.azimut_deg == pytest.approx(360.0, abs=1.0)


@pytest.mark.parametrize(
    "dia, amanecer, atardecer",
    [
        (date(2024, 3, 21), "07:21", "19:26"),
        (date(2024, 6, 21), "08:16", "18:22"),
        (date(2024, 9, 23), "07:04", "19:14"),
        (date(2024, 12, 21), "06:09", "20:21"),
    ],
)
def test_orto_y_ocaso_en_cordoba(dia, amanecer, atardecer):
    """Cotejado con la biblioteca astral (ver tests/cotejar_sol.py): coincide
    dentro del minuto en las cuatro fechas de referencia."""
    ev = sol.eventos(*CORDOBA, dia, HUSO_AR)
    assert ev.amanecer_local == amanecer
    assert ev.atardecer_local == atardecer


@pytest.mark.parametrize(
    "hora, elevacion, azimut",
    [(7, 9.073, 112.049), (9, 33.625, 98.844), (12, 71.556, 69.007), (15, 65.496, 282.490), (18, 27.411, 257.965)],
)
def test_posicion_cotejada_con_astral(hora, elevacion, azimut):
    """Valores de astral para Córdoba el 21/12/2024, que aplica refracción."""
    momento = datetime(2024, 12, 21, hora, 0, tzinfo=timezone(timedelta(hours=HUSO_AR)))
    p = sol.posicion(*CORDOBA, momento.astimezone(timezone.utc), HUSO_AR)
    assert p.elevacion_aparente_deg == pytest.approx(elevacion, abs=0.02)
    assert p.azimut_deg == pytest.approx(azimut, abs=0.02)


def test_al_amanecer_el_sol_esta_en_el_horizonte():
    """Cruza los dos caminos de cálculo: eventos() y posicion() deben coincidir."""
    dia = date(2024, 12, 21)
    ev = sol.eventos(*CORDOBA, dia, HUSO_AR)
    h, m = (int(x) for x in ev.amanecer_local.split(":"))
    momento = datetime(dia.year, dia.month, dia.day, h, m, tzinfo=timezone(timedelta(hours=HUSO_AR)))
    p = sol.posicion(*CORDOBA, momento.astimezone(timezone.utc), HUSO_AR)
    assert p.elevacion_deg == pytest.approx(sol.ELEVACION_ORTO_OCASO, abs=0.2)


def test_ecuacion_del_tiempo():
    """Máximos anuales conocidos: ≈ −14 min a comienzos de febrero y ≈ +16 min a comienzos de noviembre."""
    feb = sol.eventos(*CORDOBA, date(2024, 2, 11), HUSO_AR).ecuacion_tiempo_min
    nov = sol.eventos(*CORDOBA, date(2024, 11, 3), HUSO_AR).ecuacion_tiempo_min
    assert feb == pytest.approx(-14.2, abs=0.5)
    assert nov == pytest.approx(16.4, abs=0.5)


def test_duracion_del_dia_coincide_con_orto_y_ocaso():
    ev = sol.eventos(*CORDOBA, date(2024, 9, 23), HUSO_AR)
    assert ev.duracion_dia_h == pytest.approx(12.15, abs=0.1)


def test_direccion_es_unitaria_y_orientada():
    momento = datetime(2024, 12, 21, 9, 0, tzinfo=timezone(timedelta(hours=HUSO_AR)))
    p = sol.posicion(*CORDOBA, momento.astimezone(timezone.utc), HUSO_AR)
    x, y, z = p.direccion
    assert (x * x + y * y + z * z) == pytest.approx(1.0, abs=1e-4)
    assert x > 0  # a media mañana el sol está al este
    assert z > 0  # y sobre el horizonte


def test_trayectoria_muestrea_el_dia_completo():
    t = sol.trayectoria(*CORDOBA, date(2024, 12, 21), HUSO_AR, paso_min=5)
    assert t.paso_min == 5
    assert len(t.muestras) == 1440 // 5 + 1
    assert t.muestras[0].minuto_local == 0
    assert max(m.elevacion_deg for m in t.muestras) == pytest.approx(82.02, abs=0.3)
    assert min(m.elevacion_deg for m in t.muestras) < 0


def test_paso_invalido():
    with pytest.raises(ValueError):
        sol.trayectoria(*CORDOBA, date(2024, 1, 1), HUSO_AR, paso_min=7)


def test_fechas_clave_hemisferio_sur():
    f = sol.fechas_clave(2024)
    assert f["solsticio_invierno"] == "2024-06-21"
    assert f["solsticio_verano"] == "2024-12-21"
