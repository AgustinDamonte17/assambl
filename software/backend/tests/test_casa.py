"""Capa 03 · Casa: generador de plantas, reglas R03, guion del asistente y proveedores de IA."""

import asyncio
import json
from pathlib import Path

import pytest

from assambl import config
from assambl.capas import casa
from assambl.geometria import poligono
from assambl.ia import asistente, guion, proveedores
from assambl.modelo.casa import MensajeChat, Programa, Rectangulo
from assambl.modelo.estados import Estado
from assambl.reglas import r03_planta

ANGUS = Path(__file__).resolve().parents[2] / "casos" / "angus_ranch.assambl.json"


def programa_familia() -> Programa:
    return guion.programa_desde_conteos(3, 2, 120, cocina_integrada=True, extras=["lavadero", "oficina"])


# ---------------------------------------------------------------- generador

@pytest.mark.parametrize("lat", [-31.4, 40.4])
def test_partidos_generados_cierran_y_todos_los_ambientes_tienen_puerta(lat):
    alts = casa.generadas(programa_familia(), lat=lat)
    assert [a["id"] for a in alts] == ["compacta", "lineal", "compacta_espejada"]
    for a in alts:
        c = a["casa"]
        assert not a["advertencias"], a["advertencias"]
        # La huella encierra exactamente la suma de rectángulos más medio muro exterior.
        area_rect = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in a["rectangulos"])
        assert poligono.area([tuple(p) for p in c["huella_m"]]) > area_rect
        analisis = r03_planta.analizar_planta(c)
        problemas = [v for v in analisis["verificaciones"] if v["estado"] != "comprobado_por_reglas"]
        assert not problemas, problemas


def test_el_estar_mira_al_sol_segun_el_hemisferio():
    for lat, lado in [(-31.4, "norte"), (40.4, "sur")]:
        c = casa.generadas(programa_familia(), lat=lat)[0]["casa"]
        fachada = next(m for m in c["muros"] if m.get("lado_exterior") == lado)
        assert any(o["tipo"] == "ventana_corrediza" for o in fachada["aberturas"])


def test_muros_exteriores_y_tabiques():
    c, adv = casa.planta_desde_rectangulos([
        Rectangulo(id="estar", nombre="Estar", uso="social", x0=0, y0=0, x1=5, y1=6),
        Rectangulo(id="dorm", nombre="Dormitorio", uso="dormitorio", x0=5, y0=0, x1=8.5, y1=6),
    ])
    sistemas = sorted(m["sistema"] for m in c["muros"])
    assert sistemas == ["exterior"] * 4 + ["tabique"]
    tabique = next(m for m in c["muros"] if m["sistema"] == "tabique")
    assert tabique["eje"] == {"desde_m": [5.0, 0.0], "hasta_m": [5.0, 6.0]}
    assert [o["catalogo"] for o in tabique["aberturas"]] == ["puerta_080"]
    assert c["huella_m"] == [[-0.1, -0.1], [8.6, -0.1], [8.6, 6.1], [-0.1, 6.1]]
    # El contorno del ambiente está en la cara interior: medio muro exterior y medio tabique.
    dorm = next(a for a in c["ambientes"] if a["id"] == "dorm")
    assert dorm["contorno_m"][0] == [5.075, 0.1]
    assert all(m["estado"] == "propuesto" for m in c["muros"])


def test_ambiente_en_l_no_lleva_muro_interno():
    c, _ = casa.planta_desde_rectangulos([
        Rectangulo(id="a", nombre="Estar (a)", uso="social", x0=0, y0=0, x1=4, y1=6),
        Rectangulo(id="b", nombre="Estar (b)", uso="social", x0=4, y0=0, x1=8, y1=3),
    ])
    assert all(m["sistema"] == "exterior" for m in c["muros"])
    assert len(c["huella_m"]) == 6


def test_normalizar_alinea_bordes_casi_iguales():
    rects, adv = casa.normalizar_rectangulos([
        Rectangulo(id="Estar", nombre="Estar", uso="social", x0=1.0, y0=2.0, x1=5.12, y1=8.9),
        Rectangulo(id="Baño", nombre="Baño", uso="bano", x0=4.95, y0=2.1, x1=7.0, y1=4.0),
        Rectangulo(id="x", nombre="Mancha", uso="otro", x0=0, y0=0, x1=0.2, y1=0.2),
    ])
    assert len(rects) == 2 and len(adv) == 1
    estar, bano = rects
    assert estar.x0 == 0 and estar.y0 == 0
    assert estar.x1 == bano.x0  # el borde compartido quedó en una sola coordenada
    assert bano.id == "bano"


# ---------------------------------------------------------------- reglas

def test_reglas_sobre_angus_ranch():
    c = json.loads(ANGUS.read_text(encoding="utf-8"))["casa"]
    r = r03_planta.analizar_planta(c)
    assert r["estado"] == "pendiente_calculo"
    # Las corredizas de 4 m del estar piden cálculo de header; la ventana de 1 m no.
    assert r["por_pieza"]["Norte/O2"] == "pendiente_calculo"
    assert r["por_pieza"]["Norte/O1"] == "comprobado_por_reglas"
    # El espacio social de V11 no tiene contorno: faltan datos.
    assert r["por_pieza"]["estar_comedor_cocina"] == "pendiente_datos"
    assert r["por_pieza"]["Norte"] == "comprobado_por_reglas"


def test_reglas_detectan_abertura_fuera_del_muro_y_muro_oblicuo():
    c = {"muros": [
        {"id": "A", "sistema": "exterior", "eje": {"desde_m": [0, 0], "hasta_m": [3, 0]},
         "aberturas": [{"id": "A/O0", "tipo": "ventana", "posicion_m": 2.5, "ancho_m": 1.0}]},
        {"id": "B", "sistema": "tabique", "eje": {"desde_m": [0, 0], "hasta_m": [2, 1]}, "aberturas": []},
    ], "ambientes": []}
    r = r03_planta.analizar_planta(c)
    assert r["por_pieza"]["A/O0"] == "pendiente_revision"
    assert r["por_pieza"]["B"] == "pendiente_revision"


# ---------------------------------------------------------------- asistente

def charlar(modo, respuestas):
    h, prog, ops, turnos = [], None, [], []
    prov = proveedores.ProveedorSimulado()
    for texto, opcion in [(None, None)] + respuestas:
        if texto:
            h.append(MensajeChat(rol="usuario", texto=texto))
        r = asyncio.run(asistente.conversar(prov, modo, h, prog, [opcion] if opcion else []))
        turnos.append(r)
        h.append(MensajeChat(rol="asistente", texto=r.mensaje))
        prog = r.programa
    return turnos


def test_orientador_pregunta_de_a_una_y_termina_listo():
    turnos = charlar("orientador", [("3 dormitorios", "3"), ("Media", "115"), ("Dos", "2"),
                                    ("Integrada", "integrada"), ("El principal aparte", "divididos"),
                                    ("Con recibidor", "recibidor"), ("No", "no"), ("Lavadero", "lavadero")])
    assert all(t.pregunta and t.pregunta.opciones for t in turnos[:-1])
    fin = turnos[-1]
    assert fin.listo and fin.pregunta is None
    usos = [a.uso for a in fin.programa.ambientes]
    assert usos.count("dormitorio") == 3 and usos.count("bano") == 2 and "lavadero" in usos
    assert fin.programa.superficie_objetivo_m2 == 115
    assert (fin.programa.dormitorios, fin.programa.entrada, fin.programa.garage) == ("divididos", "recibidor", False)
    total = sum(a.area_m2 for a in fin.programa.ambientes)
    assert total == pytest.approx(115 * guion.FRACCION_UTIL, rel=0.12)


def test_prompt_libre_extrae_y_solo_pregunta_lo_que_falta():
    t = charlar("libre", [("Quiero una casa de 120 m2 con dos habitaciones, dos baños y un escritorio", None)])[-1]
    assert t.listo
    usos = [a.uso for a in t.programa.ambientes]
    assert usos.count("dormitorio") == 2 and "oficina" in usos
    t = charlar("libre", [("Una casa luminosa para ir los fines de semana", None)])[-1]
    assert not t.listo and "dormitorios" in t.pregunta.texto


def test_imagen_con_proveedor_simulado_avisa_que_es_demostracion():
    r = asyncio.run(asistente.interpretar_imagen(proveedores.ProveedorSimulado(), proveedores.Imagen("AAAA"), "", 12))
    assert r.confianza == 0 and r.advertencias
    c, _ = casa.planta_desde_rectangulos(casa.normalizar_rectangulos(r.ambientes)[0], estado=Estado.PENDIENTE_REVISION)
    assert {m["estado"] for m in c["muros"]} == {"pendiente_revision"}


class ProveedorFalso(proveedores.Proveedor):
    """Devuelve primero algo inválido, para probar la corrección automática."""

    nombre = "falso"

    def __init__(self, respuestas):
        super().__init__("falso-1")
        self.respuestas = list(respuestas)
        self.pedidos = []

    async def completar_json(self, sistema, mensajes, imagenes=None, esfuerzo="bajo"):
        self.pedidos.append(mensajes)
        return self.respuestas.pop(0)


def test_respuesta_invalida_se_corrige_una_vez():
    valida = {"mensaje": "Listo", "pregunta": None, "listo": True, "programa": {
        "superficie_objetivo_m2": 60, "ambientes": [
            {"id": "estar", "nombre": "Estar", "uso": "social"},
            {"id": "dorm", "nombre": "Dormitorio", "uso": "dormitorio", "area_m2": 12}]}}
    prov = ProveedorFalso(["no es json", "```json\n" + json.dumps(valida) + "\n```"])
    r = asyncio.run(asistente.conversar(prov, "libre", [MensajeChat(rol="usuario", texto="hola")], None))
    assert r.listo and len(prov.pedidos) == 2
    assert all(a.area_m2 for a in r.programa.ambientes)  # completar_programa rellenó el estar


def test_eleccion_de_proveedor_por_entorno(monkeypatch):
    for k in ("IA_PROVEEDOR", "IA_MODELO", "IA_URL_BASE", "IA_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(k, "")
    monkeypatch.setattr(config, "_cargado", True)
    assert proveedores.obtener().simulado
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prueba")
    p = proveedores.obtener()
    assert (p.nombre, p.modelo) == ("openai", proveedores.MODELO_POR_DEFECTO["openai"])
    monkeypatch.setenv("IA_PROVEEDOR", "openai")
    monkeypatch.setenv("IA_URL_BASE", "http://localhost:11434/v1")
    monkeypatch.setenv("IA_MODELO", "llama3.2-vision")
    p = proveedores.obtener()
    assert p.describir()["url_base"] == "http://localhost:11434/v1" and p.modelo == "llama3.2-vision"
    monkeypatch.setenv("IA_PROVEEDOR", "anthropic")
    assert proveedores.obtener().simulado  # sin ANTHROPIC_API_KEY no se inventa nada
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-prueba")
    monkeypatch.setenv("IA_MODELO", "")
    assert proveedores.obtener().modelo == proveedores.MODELO_POR_DEFECTO["anthropic"]


# ---------------------------------------------------------------- fundamentos

from assambl.fundamentos import evaluar, grafo, referencias  # noqa: E402


def _planta_ref(rid: str) -> dict:
    planta = next(p for p in referencias.cargar()["plantas"] if p["id"] == rid)
    c, adv = casa.planta_desde_rectangulos(referencias.rectangulos(planta))
    assert not adv, adv
    return c


@pytest.mark.parametrize("rid", [p["id"] for p in referencias.cargar()["plantas"]])
def test_plantas_de_referencia_se_arman_sin_problemas(rid):
    c = _planta_ref(rid)
    # Lo único que las reglas dejan abierto son rasgos propios de la planta original:
    # el header del portón de garage (necesita cálculo) y algún cuarto chico.
    problemas = {v["id"] for v in r03_planta.analizar_planta(c)["verificaciones"] if v["estado"] != "comprobado_por_reglas"}
    assert problemas <= {"R03.05", "R03.08"}, problemas
    ev = evaluar.evaluar(c, -31.4)
    assert 0.5 <= ev["puntaje"] <= 1
    assert {o["fundamento"] for o in ev["observaciones"]} >= {"F01", "F03", "F04", "F05", "F07", "F08", "F12"}


def test_grafo_reconoce_suite_hall_y_entrada():
    g = grafo.construir(_planta_ref("ref_106"))
    assert g.relacion("dorm_principal", "bano_suite").tipo == "puerta"
    assert g.relacion("estar", "cocina") is None or g.relacion("estar", "cocina").tipo == "abierto"
    assert g.uso(g.accesos[0]) == "circulacion"
    # Una visita llega al toilette sin pasar por un dormitorio.
    assert g.camino(g.accesos[0], "toilette", {"dorm_principal", "dorm_2", "dorm_3"})


def test_fundamentos_distinguen_planta_sin_pasillo_de_planta_con_hall():
    sin_pasillo = {o["fundamento"]: o for o in evaluar.evaluar(_planta_ref("ref_060"))["observaciones"]}
    con_hall = {o["fundamento"]: o for o in evaluar.evaluar(_planta_ref("ref_106"))["observaciones"]}
    assert con_hall["F03"]["puntaje"] > sin_pasillo["F03"]["puntaje"]
    assert sin_pasillo["F04"]["puntaje"] >= con_hall["F04"]["puntaje"]
    assert sin_pasillo["F12"]["puntaje"] >= con_hall["F12"]["puntaje"]


def test_angus_ranch_se_evalua_en_forma_parcial():
    c = json.loads(ANGUS.read_text())["casa"]
    ev = evaluar.evaluar(c, -31.4)
    assert any(o["titulo"] == "Evaluación parcial" for o in ev["observaciones"])
    assert not any(o["fundamento"] == "F01" for o in ev["observaciones"])


def test_alternativas_parten_de_plantas_de_referencia():
    alts = casa.alternativas(programa_familia(), lat=-31.4)
    assert len(alts) == 3
    assert all(a["origen"]["tipo"] == "referencia" for a in alts)
    for a in alts:
        nombres = {x["nombre"] for x in a["casa"]["ambientes"]}
        assert "Dormitorio principal" in nombres, nombres
        assert a["evaluacion"]["criterios"] and a["resumen"]["superficie_cubierta_m2"] > 80
        # El estar mira al sol.
        luz = next(o for o in a["evaluacion"]["observaciones"] if o["fundamento"] == "F09")
        assert "el estar también" in luz["texto"], luz["texto"]


def test_preferencias_del_programa_ordenan_las_referencias():
    prog = programa_familia().model_copy(update={"dormitorios": "divididos", "garage": True})
    alts = casa.alternativas(prog, lat=-31.4)
    assert any(x["uso"] == "garage" for x in alts[0]["casa"]["ambientes"])
    sin_garage = casa.alternativas(programa_familia().model_copy(update={"garage": False}), lat=-31.4)
    assert not any(x["uso"] == "garage" for a in sin_garage for x in a["casa"]["ambientes"])


def test_programa_sin_referencia_usa_el_generador():
    prog = guion.programa_desde_conteos(5, 2, 180, cocina_integrada=True)
    alts = casa.alternativas(prog, lat=-31.4)
    assert [a["origen"]["tipo"] for a in alts] == ["generada"] * 3
    assert all(a["evaluacion"]["puntaje"] is not None for a in alts)
