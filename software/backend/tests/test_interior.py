"""Interior: catálogo de muebles, amoblado automático, galería, reglas RI y Lumo sin IA."""

import json
from pathlib import Path

import pytest

from assambl.capas import casa as capa
from assambl.capas import interior as ci
from assambl.ia import interior as lumo
from assambl.modelo.casa import Programa
from assambl.reglas import r03_planta, r_interior

ANGUS = Path(__file__).resolve().parents[2] / "casos" / "angus_ranch.assambl.json"


def _programa(**extra) -> Programa:
    return Programa.model_validate({
        "superficie_objetivo_m2": 110, "cocina_integrada": True, **extra,
        "ambientes": [
            {"id": "estar", "nombre": "Estar", "uso": "social", "area_m2": 32},
            {"id": "dorm_principal", "nombre": "Dormitorio principal", "uso": "dormitorio", "area_m2": 13, "principal": True},
            {"id": "dorm_2", "nombre": "Dormitorio 2", "uso": "dormitorio", "area_m2": 10},
            {"id": "bano", "nombre": "Baño", "uso": "bano", "area_m2": 5},
            {"id": "lavadero", "nombre": "Lavadero", "uso": "lavadero", "area_m2": 4},
            {"id": "oficina", "nombre": "Oficina", "uso": "oficina", "area_m2": 8},
        ]})


@pytest.fixture(autouse=True)
def _sin_ia(monkeypatch):
    """Las pruebas no salen a internet: Lumo responde con su guion."""
    monkeypatch.setenv("IA_PROVEEDOR", "simulado")


@pytest.fixture(scope="module")
def plantas() -> list[dict]:
    return [a["casa"] for a in capa.alternativas(_programa(), lat=-31.4)]


def _angus() -> dict:
    return json.loads(ANGUS.read_text(encoding="utf-8"))["casa"]


def _tipos(casa: dict, ambiente: str) -> list[str]:
    return [p["tipo"] for p in ci.piezas(casa) if p.get("ambiente") == ambiente]


# ---------------------------------------------------------------- catálogo

def test_catalogo_de_muebles_completo():
    items = ci.items_catalogo()
    assert len(items) >= 45
    for it in items:
        a, f, h = it["medidas_m"]
        assert 0 < a <= 3 and 0 < f <= 2.5 and 0 < h <= 2.6, it["codigo"]
        assert it["apoyo"] in ("muro", "esquina", "libre")
        assert it["familia"] in ("mueble", "artefacto")
    # Lo que lleva agua es artefacto: alimenta la plomería.
    assert all(i["familia"] == "artefacto" for i in items if i.get("agua"))
    assert ci.lista_de("inodoro") == "artefactos" and ci.lista_de("sofa_3") == "mobiliario"


def test_angus_usa_codigos_del_catalogo():
    c = _angus()
    assert all(ci.item(p["tipo"]) for p in ci.piezas(c))
    assert any(a["uso"] == "galeria" for a in c["ambientes"])


# ---------------------------------------------------------------- geometría de piezas

def test_huella_y_frente_segun_el_giro():
    p = {"id": "x", "tipo": "placard_180", "centro_m": [1.0, 0.3], "medidas_m": [1.8, 0.6, 2.4], "giro_deg": 0}
    assert ci.huella(p) == pytest.approx((0.1, 0.0, 1.9, 0.6))
    assert ci.zona_frente(p) == pytest.approx((0.1, 0.6, 1.9, 1.3))  # frente al norte
    p["giro_deg"] = 90  # espalda al este, frente al oeste
    x0, y0, x1, y1 = ci.huella(p)
    assert (x1 - x0, y1 - y0) == pytest.approx((0.6, 1.8))
    assert ci.zona_frente(p)[2] == pytest.approx(x0)


# ---------------------------------------------------------------- amoblado

def test_amoblado_completo_y_sin_conflictos(plantas):
    for casa in plantas:
        amoblada, _ = ci.amoblar(casa)
        assert any(t.startswith("cama") for t in _tipos(amoblada, "dorm_principal"))
        assert {"inodoro", "vanitory_60"} <= set(_tipos(amoblada, "bano"))
        assert any(t.startswith("ducha") or t == "banera" for t in _tipos(amoblada, "bano"))
        assert "mesada_bacha" in _tipos(amoblada, "estar")  # cocina integrada
        assert "escritorio" in _tipos(amoblada, "oficina")
        assert "pileta_lavadero" in _tipos(amoblada, "lavadero")
        malas = [v for v in r_interior.verificar(amoblada)
                 if v["estado"] != "comprobado_por_reglas" and v["id"] in ("RI.01", "RI.02", "RI.04", "RI.05")]
        assert not malas, malas


def test_amoblar_no_toca_ambientes_con_muebles(plantas):
    casa, _ = ci.amoblar(plantas[0], ["bano"])
    antes = _tipos(casa, "bano")
    otra, _ = ci.amoblar(casa)
    assert _tipos(otra, "bano") == antes
    reemplazada, _ = ci.amoblar(casa, ["bano"], reemplazar=True)
    assert sorted(_tipos(reemplazada, "bano")) == sorted(antes)  # mismo algoritmo, mismo resultado


def test_colocar_respeta_usos_y_espacio(plantas):
    casa = plantas[0]
    _, p, motivo = ci.colocar(casa, "inodoro", "dorm_principal")
    assert p is None and "no va" in motivo
    _, p, _ = ci.colocar(casa, "reposera", "estar")
    assert p is None  # es de galería
    nueva, p, _ = ci.colocar(casa, "escritorio", "dorm_2")
    assert p and p["ambiente"] == "dorm_2" and p in nueva["mobiliario"]


# ---------------------------------------------------------------- galería

def test_galeria_al_norte_con_salida(plantas):
    casa, gid, notas = ci.agregar_galeria(plantas[0], lat=-31.4)
    g = next(a for a in casa["ambientes"] if a["id"] == gid)
    assert g["uso"] == "galeria"
    ys = [v[1] for v in g["contorno_m"]]
    huella_y = max(v[1] for v in casa["huella_m"])
    assert min(ys) == pytest.approx(huella_y)  # pegada a la cara norte
    assert max(ys) - min(ys) == pytest.approx(3.0)
    # No suma a la huella cubierta y tiene por dónde salir.
    assert casa["huella_m"] == plantas[0]["huella_m"]
    salidas = [o for m in casa["muros"] for o in m["aberturas"] if o["tipo"] in ("puerta", "ventana_corrediza")]
    assert salidas
    r = r03_planta.analizar_planta(casa)
    assert r["por_pieza"][gid] == "comprobado_por_reglas"


def test_galeria_en_alternativas_si_el_programa_la_pide():
    from fastapi.testclient import TestClient

    from api.main import app
    cliente = TestClient(app)
    r = cliente.post("/api/casa/alternativas", json={"programa": _programa(galeria=True).model_dump(), "lat": -31.4})
    assert r.status_code == 200
    assert all(any(a["uso"] == "galeria" for a in alt["casa"]["ambientes"]) for alt in r.json()["alternativas"])


# ---------------------------------------------------------------- reglas

def test_reglas_marcan_pieza_fuera_y_superpuesta(plantas):
    casa, _ = ci.amoblar(plantas[0], ["dorm_principal"])
    cama = next(p for p in casa["mobiliario"] if p["tipo"].startswith("cama"))
    cama["centro_m"] = [-3.0, -3.0]
    r = r03_planta.analizar_planta(casa)
    assert r["por_pieza"][cama["id"]] == "pendiente_revision"
    assert any(v["id"] == "RI.01" and cama["id"] in v["piezas"] for v in r["verificaciones"])

    casa, _ = ci.amoblar(plantas[0], ["bano"])
    ino = next(p for p in casa["artefactos"] if p["tipo"] == "inodoro")
    casa["artefactos"].append({**ino, "id": "otro_inodoro"})
    vs = r_interior.verificar(casa)
    assert any(v["id"] == "RI.02" and "otro_inodoro" in v["piezas"] for v in vs)


# ---------------------------------------------------------------- Lumo sin IA

@pytest.mark.parametrize("texto, tipo", [
    ("sumá un sillón en el estar", "agregar"),
    ("sacá la alfombra", "quitar"),
    ("amoblá el dormitorio 2", "amoblar"),
    ("agrandá el baño", "mover_muro"),
    ("cambiá la cama del dormitorio principal por una king", "cambiar"),
    ("quiero una galería al sur", "galeria"),
])
def test_guion_interior(texto, tipo):
    c = _angus()
    r = lumo.guion_interior(texto, c)
    assert [o.tipo for o in r.operaciones] == [tipo]
    nueva, pendientes, _ = lumo.aplicar(c, r.operaciones, -31.4)
    if tipo == "mover_muro":
        assert pendientes and pendientes[0]["muro"] == "Bano_Lavadero" and pendientes[0]["delta_m"] > 0
    else:
        assert nueva != c


def test_conversar_interior_por_api():
    from fastapi.testclient import TestClient

    from api.main import app
    cliente = TestClient(app)
    r = cliente.post("/api/casa/interior/conversar", json={
        "casa": _angus(), "historial": [{"rol": "usuario", "texto": "poné dos plantas en la galería"}]})
    assert r.status_code == 200
    d = r.json()
    assert len([p for p in d["casa"]["mobiliario"] if p["tipo"] == "planta" and p["ambiente"] == "galeria"]) == 3
    assert "analisis" in d and d["mensaje"]
