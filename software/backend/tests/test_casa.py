"""Capa 03 · Casa: planta base, generador de muros, reglas R03, Lumo y proveedores de IA."""

import asyncio
import json
from pathlib import Path

import pytest

from assambl import config
from assambl.capas import casa, planta_base
from assambl.geometria import poligono
from assambl.ia import asistente, lumo, lumo_editor, proveedores
from assambl.modelo.casa import Decisiones, PuertaDeseada, Rectangulo
from assambl.modelo.estados import Estado
from assambl.reglas import r03_planta

ANGUS = Path(__file__).resolve().parents[2] / "casos" / "angus_ranch.assambl.json"


# ---------------------------------------------------------------- planta base

TODAS = [Decisiones(dormitorios=n, cocina=c, tamano=t)
         for n in (1, 2, 3, 4) for c in ("abierta", "cerrada") for t in ("compacta", "comoda", "amplia")]


@pytest.mark.parametrize("lat", [-31.4, 40.4])
def test_la_planta_base_cumple_las_reglas_en_todas_sus_variantes(lat):
    for d in TODAS:
        p = planta_base.planta_base(d, lat=lat)
        c = p["casa"]
        assert not p["advertencias"], (d, p["advertencias"])
        problemas = [v for v in r03_planta.analizar_planta(c)["verificaciones"] if v["estado"] != "comprobado_por_reglas"]
        assert not problemas, (d, problemas)
        usos = [a["uso"] for a in c["ambientes"]]
        assert usos.count("dormitorio") == d.dormitorios
        assert usos.count("social") == 1 and usos.count("bano") == 2 and "lavadero" in usos
        assert ("cocina" in usos) == (d.cocina == "cerrada")
        assert "circulacion" not in usos  # el estar reparte: no hay pasillos


def test_la_planta_base_sigue_el_orden_de_angus_ranch():
    c = planta_base.planta_base(Decisiones(dormitorios=3, cocina="abierta", tamano="amplia"), lat=-31.4)["casa"]
    amb = {a["id"]: a["contorno_m"] for a in c["ambientes"]}
    centro = lambda k: poligono.centroide([tuple(v) for v in amb[k]])  # noqa: E731
    xs = [v[0] for v in c["huella_m"]]
    ys = [v[1] for v in c["huella_m"]]
    # La suite en el extremo oeste, sobre el frente del sol; el ala de entrada en el este.
    assert centro("dorm_principal")[0] < centro("estar")[0] < centro("dorm_3")[0]
    assert max(v[1] for v in amb["dorm_principal"]) == pytest.approx(max(ys) - 0.2)
    # Baño y lavadero en el anexo del lado frío.
    assert max(v[1] for v in amb["bano"]) < min(v[1] for v in amb["dorm_principal"])
    # El estar es un solo ambiente que toma el rincón de la suite y el hall de entrada.
    assert len(amb["estar"]) > 4
    este = next(m for m in c["muros"] if m.get("lado_exterior") == "este")
    assert [o["catalogo"] for o in este["aberturas"] if o["tipo"] == "puerta"] == ["puerta_090"]
    # Mismas medidas generales que Angus Ranch, con un margen por los ambientes más holgados.
    assert max(xs) - min(xs) == pytest.approx(18.0, abs=0.6) and max(ys) - min(ys) == pytest.approx(10.4, abs=0.3)


def test_el_estar_mira_al_sol_segun_el_hemisferio():
    for lat, lado in [(-31.4, "norte"), (40.4, "sur")]:
        c = planta_base.planta_base(Decisiones(dormitorios=2), lat=lat)["casa"]
        fachada = max((m for m in c["muros"] if m.get("lado_exterior") == lado), key=casa._largo)
        assert sum(o["tipo"] == "ventana_corrediza" for o in fachada["aberturas"]) >= 1


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


def test_ambiente_en_l_es_un_solo_ambiente_sin_muro_interno():
    c, _ = casa.planta_desde_rectangulos([
        Rectangulo(id="a", nombre="Estar (a)", uso="social", x0=0, y0=0, x1=4, y1=6),
        Rectangulo(id="b", nombre="Estar (b)", uso="social", x0=4, y0=0, x1=8, y1=3),
    ])
    assert all(m["sistema"] == "exterior" for m in c["muros"])
    assert len(c["huella_m"]) == 6
    (estar,) = c["ambientes"]
    assert estar["nombre"] == "Estar"
    assert estar["contorno_m"] == [[0.1, 0.1], [7.9, 0.1], [7.9, 2.9], [3.9, 2.9], [3.9, 5.9], [0.1, 5.9]]


def test_la_puerta_va_donde_la_pide_el_rectangulo():
    rects = [
        Rectangulo(id="estar", nombre="Estar", uso="social", x0=0, y0=0, x1=5, y1=6),
        Rectangulo(id="dorm", nombre="Dormitorio", uso="dormitorio", x0=5, y0=0, x1=8.5, y1=6,
                   puerta=PuertaDeseada(hacia="estar", extremo="fin")),
    ]
    c, _ = casa.planta_desde_rectangulos(rects)
    tabique = next(m for m in c["muros"] if m["sistema"] == "tabique")
    assert tabique["aberturas"][0]["posicion_m"] == pytest.approx(6 - 0.8 - 0.15)


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


def _base():
    return planta_base.planta_base(Decisiones(dormitorios=3, cocina="abierta", tamano="comoda"))["casa"]


def _graves(c):
    return {v["id"]: v for v in r03_planta.analizar_planta(c)["verificaciones"]
            if v.get("gravedad") == "grave" and v["estado"] != "comprobado_por_reglas"}


def test_sin_bano_general_es_grave():
    c = _base()
    assert not _graves(c)
    # Queda solo el baño en suite: sus puertas dan al dormitorio.
    c["ambientes"] = [a for a in c["ambientes"] if a["id"] != "bano"]
    g = _graves(c)
    assert list(g) == ["R03.11"] and "en suite" in g["R03.11"]["detalle"] and g["R03.11"]["piezas"] == ["bano_suite"]
    c["ambientes"] = [a for a in c["ambientes"] if a["uso"] != "bano"]
    assert "ningún baño" in _graves(c)["R03.11"]["detalle"]


def test_sin_dormitorio_sin_cocina_o_sin_entrada_es_grave():
    c = _base()
    for a in c["ambientes"]:
        if a["uso"] == "dormitorio":
            a["uso"] = "oficina"
        if a["uso"] == "social":
            a["nombre"] = "Estar"
    for m in c["muros"]:
        if m["sistema"] == "exterior":
            m["aberturas"] = [o for o in m["aberturas"] if o["tipo"] != "puerta"]
    assert set(_graves(c)) == {"R03.12", "R03.13", "R03.14"}


def test_espacio_sin_ambiente_es_una_sugerencia():
    c = _base()
    quitado = next(a for a in c["ambientes"] if a["id"] == "lavadero")
    c["ambientes"].remove(quitado)
    (s,) = [v for v in r03_planta.analizar_planta(c)["verificaciones"] if v["id"] == "R03.15"]
    assert s["gravedad"] == "sugerencia" and s["estado"] == "propuesto"
    assert s["parametros"]["rectangular"] and s["parametros"]["area_m2"] == pytest.approx(poligono.area(
        [tuple(v) for v in quitado["contorno_m"]]), abs=0.6)


def test_reglas_detectan_abertura_fuera_del_muro_y_muro_oblicuo():
    c = {"muros": [
        {"id": "A", "sistema": "exterior", "eje": {"desde_m": [0, 0], "hasta_m": [3, 0]},
         "aberturas": [{"id": "A/O0", "tipo": "ventana", "posicion_m": 2.5, "ancho_m": 1.0}]},
        {"id": "B", "sistema": "tabique", "eje": {"desde_m": [0, 0], "hasta_m": [2, 1]}, "aberturas": []},
    ], "ambientes": []}
    r = r03_planta.analizar_planta(c)
    assert r["por_pieza"]["A/O0"] == "pendiente_revision"
    assert r["por_pieza"]["B"] == "pendiente_revision"


# ---------------------------------------------------------------- Lumo

def test_lumo_pregunta_de_a_una_y_termina_listo():
    d = Decisiones()
    r = lumo.responder(d)
    assert "Lumo" in r.mensaje and r.pregunta.texto.startswith("¿Cuántos dormitorios")
    r = lumo.responder(d.model_copy(update={"dormitorios": 3}))
    assert "cocina" in r.pregunta.texto and not r.listo
    r = lumo.responder(r.decisiones, "la prefiero cerrada")
    assert r.decisiones.cocina == "cerrada" and "tamaño" in r.pregunta.texto
    # Las opciones de tamaño muestran la superficie real de la planta que saldría.
    assert all("m²" in o.etiqueta for o in r.pregunta.opciones)
    m2 = [float(o.etiqueta.split("·")[1].split()[0]) for o in r.pregunta.opciones]
    assert m2 == sorted(m2) and len(set(m2)) == 3
    r = lumo.responder(r.decisiones, "amplia")
    assert r.listo and r.pregunta is None
    assert r.decisiones == Decisiones(dormitorios=3, cocina="cerrada", tamano="amplia")


def test_lumo_cuenta_el_cambio_cuando_se_toca_otra_decision():
    listo = Decisiones(dormitorios=2, cocina="abierta", tamano="compacta")
    r = lumo.responder(listo, cambio="dormitorios")
    assert r.listo
    resumen = planta_base.planta_base(listo)["resumen"]
    assert lumo.mensaje_cambio("dormitorios", listo, resumen).startswith("Dos dormitorios")
    # A mitad de camino, cuenta el cambio y sigue preguntando lo que falta.
    r = lumo.responder(Decisiones(dormitorios=2, tamano="amplia"), cambio="tamano")
    assert r.mensaje.startswith("Tamaño amplio") and "cocina" in r.pregunta.texto


def test_lumo_lee_respuestas_escritas_y_avisa_si_no_entiende():
    assert lumo.interpretar("dormitorios", "somos cuatro, necesitamos tres cuartos") == 3
    assert lumo.interpretar("dormitorios", "ocho") is None
    assert lumo.interpretar("cocina", "integrada, con isla") == "abierta"
    assert lumo.interpretar("tamano", "algo chico") == "compacta"
    r = lumo.responder(Decisiones(), "no sé")
    assert "No te entendí" in r.mensaje and r.decisiones.dormitorios is None and r.pregunta


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
    valida = {"resumen": "Una casa chica", "ambientes": [
        {"id": "estar", "nombre": "Estar", "uso": "social", "x0": 0, "y0": 0, "x1": 5, "y1": 6}]}
    prov = ProveedorFalso(["no es json", "```json\n" + json.dumps(valida) + "\n```"])
    prov.vision = True
    r = asyncio.run(asistente.interpretar_imagen(prov, proveedores.Imagen("AAAA")))
    assert len(r.ambientes) == 1 and len(prov.pedidos) == 2


def test_lumo_en_el_editor_devuelve_acciones_validadas():
    respuesta = {"mensaje": "Corro el muro norte 1 m.", "pregunta": None,
                 "acciones": [{"tipo": "ampliar", "ambiente": "dorm_2", "lado": "norte", "metros": 1, "sobra": "x"}]}
    prov = ProveedorFalso([json.dumps(respuesta)])
    t = asyncio.run(lumo_editor.pedir_cambios(prov, "agrandá este ambiente", {"seleccion": "dorm_2"}))
    assert [(a.tipo, a.ambiente, a.lado, a.metros) for a in t.acciones] == [("ampliar", "dorm_2", "norte", 1)]
    assert "dorm_2" in prov.pedidos[0][-1].texto  # el contexto viaja con el pedido
    # Una acción que no existe no pasa la validación: se le pide al modelo que corrija.
    mala = {"mensaje": "x", "acciones": [{"tipo": "demoler"}]}
    pregunta = {"mensaje": "¿Hacia dónde?", "acciones": [],
                "pregunta": {"texto": "¿Hacia qué lado?", "opciones": [{"id": "n", "etiqueta": "Norte"}]}}
    prov = ProveedorFalso([json.dumps(mala), json.dumps(pregunta)])
    t = asyncio.run(lumo_editor.pedir_cambios(prov, "agrandalo", {}))
    assert not t.acciones and t.pregunta.opciones[0].etiqueta == "Norte" and len(prov.pedidos) == 2
    # Sin clave de IA lo dice, no inventa.
    t = asyncio.run(lumo_editor.pedir_cambios(proveedores.ProveedorSimulado(), "agrandalo", {}))
    assert not t.acciones and "clave de IA" in t.mensaje


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
