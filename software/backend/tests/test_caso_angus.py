"""El caso Angus Ranch (casos/angus_ranch.assambl.json) contra el script V11.

El JSON es la fuente de verdad declarativa; V11 es la referencia que tiene que
reproducir. Estas pruebas ejecutan V11 en memoria (sin Blender, como su
`--check`) y comparan dato por dato. Si V11 cambia, se regenera el caso con
`python scripts/armar_caso_angus.py` y estas pruebas dicen si quedó alineado.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
from pathlib import Path

import pytest

from assambl.modelo.casa import Casa, Muro
from assambl.modelo.proyecto import Proyecto

SOFTWARE = Path(__file__).resolve().parents[2]
CASO = SOFTWARE / "casos" / "angus_ranch.assambl.json"
SCRIPT_V11 = SOFTWARE.parent / "angus_ranch_V11_11_capas.py"
TOL = 1e-4  # el caso redondea a 0,1 mm
TIPOS_V11 = {"ventana": "ventana", "corrediza": "ventana_corrediza", "puerta": "puerta", "paso": "paso"}


@pytest.fixture(scope="module")
def datos() -> dict:
    return json.loads(CASO.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def casa(datos) -> Casa:
    return Casa.model_validate(datos["casa"])


@pytest.fixture(scope="module")
def v11():
    """Ejecuta V11 hasta las instalaciones y el cómputo de madera, sin Blender."""
    if not SCRIPT_V11.exists():
        pytest.skip(f"No está {SCRIPT_V11.name} en la raíz del repositorio")
    pytest.importorskip("numpy")
    spec = importlib.util.spec_from_file_location("angus_v11", SCRIPT_V11)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    c, t = modulo.cargar_fuentes()
    with contextlib.redirect_stdout(io.StringIO()):
        modulo.preparar_y_comprobar(c, t)
    anclajes, especiales = modulo.augment_v06(c)
    inst = modulo.agregar_instalaciones(c)
    filas = modulo.timber_inventory(c)
    return {"modulo": modulo, "casa": c, "terreno": t, "anclajes": anclajes, "especiales": especiales,
            "instalaciones": inst, "filas": filas}


# ------------------------------------------------------------------ esquema

def test_el_caso_valida_contra_el_esquema(datos, casa):
    assert casa.esquema == "assambl/casa@0.1"
    assert Proyecto.model_validate(datos).casa is not None
    # El proyecto sigue en @0.2: la app actual lo abre sin cambios.
    assert datos["esquema"] == "assambl/proyecto@0.2"


def test_una_referencia_rota_se_rechaza(datos):
    roto = json.loads(json.dumps(datos["casa"]))
    roto["muros"][0]["sistema"] = "inexistente"
    with pytest.raises(ValueError, match="sistema 'inexistente' no existe"):
        Casa.model_validate(roto)


def test_una_abertura_fuera_del_muro_se_rechaza(datos):
    roto = json.loads(json.dumps(datos["casa"]))
    roto["muros"][0]["aberturas"][0]["posicion_m"] = 50
    with pytest.raises(ValueError, match="termina fuera del muro"):
        Casa.model_validate(roto)


def test_un_campo_desconocido_se_rechaza(datos):
    roto = json.loads(json.dumps(datos["casa"]))
    roto["muros"][0]["alto"] = 3
    with pytest.raises(ValueError, match="alto"):
        Casa.model_validate(roto)


def test_la_huella_es_la_de_v11(casa):
    x = [p[0] for p in casa.huella_m]
    y = [p[1] for p in casa.huella_m]
    area = abs(sum(x[i] * y[i - 1] - x[i - 1] * y[i] for i in range(len(x)))) / 2
    assert area == pytest.approx(164.16)  # 18 × 8 + 8,4 × 2,4, informado por V04


# ------------------------------------------------------------------ muros

def extremos_reales(casa: Casa, muro: Muro) -> tuple[float, float]:
    """Regla de esquina de V11: el muro paralelo a X pasa de largo y el paralelo a Y
    apoya contra él. Devuelve el inicio y el fin del entramado sobre el eje."""
    fondo = casa.sistemas[muro.sistema].entramado.seccion_mm[1] / 1000
    eje = muro.eje
    i = 0 if eje.paralelo_a == "x" else 1
    u0, u1 = eje.desde_m[i], eje.hasta_m[i]
    if muro.sistema != "exterior":
        return u0, u1
    otros = [m for m in casa.muros if m.sistema == "exterior" and m.eje.paralelo_a != eje.paralelo_a]

    def es_esquina(p):
        return any(math.dist(p, q) < 1e-6 for m in otros for q in (m.eje.desde_m, m.eje.hasta_m))

    signo = 1 if eje.paralelo_a == "x" else -1  # X se extiende; Y se retrae
    if es_esquina(eje.desde_m):
        u0 -= signo * fondo / 2
    if es_esquina(eje.hasta_m):
        u1 += signo * fondo / 2
    return u0, u1


def test_mismos_muros_que_v11(casa, v11):
    assert [m.id for m in casa.muros] == [w["name"] for w in v11["casa"]["WALLS"]]


def test_eje_sistema_y_lado_de_cada_muro(casa, v11):
    for w in v11["casa"]["WALLS"]:
        m = casa.muro(w["name"])
        assert m.eje.paralelo_a == w["axis"].lower(), m.id
        fijo = m.eje.desde_m[1] if m.eje.paralelo_a == "x" else m.eje.desde_m[0]
        assert fijo == pytest.approx(w["pos"], abs=TOL), m.id
        inicio, fin = extremos_reales(casa, m)
        assert inicio == pytest.approx(w["start"], abs=TOL), m.id
        assert fin == pytest.approx(w["end"], abs=TOL), m.id
        esperado = "exterior" if w["external"] else ("interior_portante" if w["bearing"] else "tabique")
        assert m.sistema == esperado, m.id
        assert casa.sistemas[m.sistema].espesor_arquitectonico_m == pytest.approx(w["thickness"]), m.id
        if w["external"]:
            lado = {("x", 1): "norte", ("x", -1): "sur", ("y", 1): "este", ("y", -1): "oeste"}
            assert m.lado_exterior == lado[(m.eje.paralelo_a, w["outside"])], m.id


def test_altura_de_cada_muro(casa, v11):
    """`hasta_cubierta` + el plano de apoyo alcanzan para reproducir los topes inclinados."""
    for w in v11["casa"]["WALLS"]:
        m = casa.muro(w["name"])
        for u, tope in [(w["start"], w["top_start"]), (w["end"], w["top_end"])]:
            x, y = (u, w["pos"]) if w["axis"] == "X" else (w["pos"], u)
            assert casa.altura_muro(m, x, y) == pytest.approx(tope, abs=TOL), (m.id, u)


def test_aberturas_de_cada_muro(casa, v11):
    for w in v11["casa"]["WALLS"]:
        m = casa.muro(w["name"])
        u0 = m.eje.desde_m[0 if m.eje.paralelo_a == "x" else 1]
        assert len(m.aberturas) == len(w["holes"]), m.id
        for i, (ab, (a, b, antepecho, dintel, tipo)) in enumerate(zip(m.aberturas, w["holes"])):
            assert ab.id == f"{m.id}/O{i}"
            assert ab.tipo == TIPOS_V11[tipo], ab.id
            assert u0 + ab.posicion_m == pytest.approx(a, abs=TOL), ab.id
            assert u0 + ab.fin_m == pytest.approx(b, abs=TOL), ab.id
            assert ab.antepecho_m == pytest.approx(antepecho, abs=TOL), ab.id
            assert ab.dintel_m == pytest.approx(dintel, abs=TOL), ab.id
            if tipo == "puerta":
                giro = v11["casa"]["DOOR_SWINGS"].get(f"{m.id}_puerta", 70)
                assert ab.hoja.apertura_deg == giro, ab.id


def test_dinteles_derivados_de_v11(casa, v11):
    """La altura del dintel no se guarda: sale de la regla de carpinterias.dintel."""
    regla = casa.carpinterias.dintel.altura_m
    for op in v11["casa"]["OPENINGS"]:
        ancho = op["b"] - op["a"]
        assert (regla.mayor if ancho > 2.6 else regla.hasta_2_6_m) == pytest.approx(op["header_depth"]), op["id"]


# ------------------------------------------------------------------ cubiertas

def test_planos_de_apoyo_de_las_cubiertas(casa, v11):
    config = v11["casa"]["CONFIG"]
    principal = casa.cubierta("principal").plano_apoyo
    anexo = casa.cubierta("anexo_sur").plano_apoyo
    galeria = casa.cubierta("galeria").plano_apoyo
    for y in (-0.35, 0.0, 4.0, 8.35):
        assert principal.cota(3.0, y) == pytest.approx(v11["casa"]["roof_level"](y))
        assert principal.cota(3.0, y) == pytest.approx(config["cota_apoyo_sur"] + config["pendiente_techo"] * y)
    for y in (-2.7, -2.3, 0.0, 0.15):
        assert anexo.cota(12.0, y) == pytest.approx(3.0 + 0.10 * (y + 2.3))  # build_roof: low(y)
    for y in (8.0, 9.5, 11.1):
        assert galeria.cota(10.0, y) == pytest.approx(3.03 - 0.06 * (y - 8.0))  # build_exterior: level(y)


def test_cabios_de_la_cubierta_principal(casa, v11):
    cabios = [o for o in v11["casa"]["OBJECTS"] if o["name"] == "Cabio_inclinado"]
    spec = casa.cubierta("principal").cabios
    assert len(cabios) == spec.cantidad
    centros = sorted((min(v[0] for v in o["vertices"]) + max(v[0] for v in o["vertices"])) / 2 for o in cabios)
    assert centros[0] == pytest.approx(spec.desde_x_m) and centros[-1] == pytest.approx(spec.hasta_x_m)


# ------------------------------------------------------------------ ambientes

def test_ambientes_de_v11(casa, v11):
    delimitados = [a for a in casa.ambientes if a.contorno_m is not None]
    assert len(delimitados) == len(v11["casa"]["ROOMS"])
    for a, room in zip(delimitados, v11["casa"]["ROOMS"]):
        x0, y0, x1, y1 = room["bounds"]
        assert [tuple(p) for p in a.contorno_m] == pytest.approx([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], abs=TOL)
    # Lo que V11 no define queda explícitamente pendiente, no inventado.
    social = next(a for a in casa.ambientes if a.id == "estar_comedor_cocina")
    assert social.contorno_m is None and social.estado == "pendiente_datos"


# ------------------------------------------------------------------ instalaciones

def terminales(v11, tipo=None):
    return {t["nombre"]: t for t in v11["instalaciones"]["terminales"] if tipo is None or t["tipo"] == tipo}


def test_artefactos_sanitarios(casa, v11):
    sanitarios = terminales(v11, "sanitario")
    assert {a.id for a in casa.artefactos} == set(sanitarios)
    for a in casa.artefactos:
        assert a.desague.salida_m == pytest.approx(sanitarios[a.id]["posicion"], abs=TOL), a.id


def test_tomas_y_bocas_de_luz(casa, v11):
    elec = casa.instalaciones.electrica
    tomas = terminales(v11, "toma")
    bocas = terminales(v11, "boca_luz")
    assert {t.id.removeprefix("Toma_") for t in elec.tomas} == set(tomas)
    assert {b.id.removeprefix("Luz_") for b in elec.bocas_luz} == set(bocas)
    for t in elec.tomas:
        ref = tomas[t.id.removeprefix("Toma_")]
        assert t.posicion_m == pytest.approx(ref["posicion"], abs=TOL), t.id
        assert t.circuito == ref["circuito"], t.id
    for b in elec.bocas_luz:
        ref = bocas[b.id.removeprefix("Luz_")]
        assert b.posicion_m == pytest.approx(ref["posicion"], abs=TOL), b.id
        assert b.circuito == ref["circuito"], b.id
    circuitos = v11["instalaciones"]["circuitos"]
    assert {c.id: c.seccion_mm2 for c in elec.circuitos} == {k: v["seccion_orientativa_mm2"] for k, v in circuitos.items()}
    assert elec.tablero.posicion_m == pytest.approx(v11["instalaciones"]["tablero_xyz_local_m"])


def test_parametros_de_desague(casa, v11):
    criterios = v11["instalaciones"]["criterios"]
    desague = casa.instalaciones.sanitaria.desague
    assert desague.pendiente == criterios["pendiente_desague"]
    assert desague.colector_y_m == criterios["y_colector_cloacal_m"]
    assert desague.cota_eje_inicio_m == criterios["cota_eje_inicio_colectores_m"]


# ------------------------------------------------------------------ implantación y regresión

def test_implantacion_y_lote(datos, casa, v11):
    modulo = v11["modulo"]
    assert casa.implantacion.origen_en_lote_m == pytest.approx(modulo.local_a_lote(0, 0))
    assert casa.implantacion.giro_deg == modulo.IMPLANTACION["giro_grados"]
    assert casa.implantacion.cota_piso_sobre_terreno_m == modulo.IMPLANTACION["cota_piso_m"]
    lote = datos["terreno"]["lote"]["vertices"]
    assert len(lote) == len(v11["terreno"]["POLY"])
    for p, q in zip(lote, v11["terreno"]["POLY"]):
        assert p == pytest.approx(q, abs=0.006)  # el caso redondea el lote a 1 cm


def test_objetivo_de_regresion(casa, v11):
    """Los números que el generador de la capa 03 tiene que reproducir desde el JSON."""
    reg = casa.origen.regresion
    assert reg.piezas_madera == len(v11["filas"]) == 828
    assert reg.pernos_solera == len(v11["anclajes"])
    assert reg.soleras_con_anclaje_especial == len(v11["especiales"])
