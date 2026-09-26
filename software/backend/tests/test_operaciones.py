import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from assambl.geometria.malla import MallaLocal
from assambl.modelo import operaciones as ops
from assambl.modelo.estados import Estado
from assambl.modelo.proyecto import ESQUEMA_ACTUAL, Proyecto

AHORA = "2026-09-26T12:00:00Z"
LOTE_GRANDE = [(-60.0, -60.0), (60.0, -60.0), (60.0, 60.0), (-60.0, 60.0)]


def proyecto_nuevo() -> Proyecto:
    """Mismo proyecto que crea el frontend en proyectoNuevo() (frontend/src/modelo/proyecto.ts)."""
    return Proyecto.model_validate({
        "esquema": ESQUEMA_ACTUAL, "id": "p1", "nombre": "Casa sin nombre", "mercado": "AR",
        "creado": "2026-09-01T00:00:00Z", "modificado": "2026-09-01T00:00:00Z",
        "terreno": {
            "estado": "pendiente_datos", "ubicacion": None, "margen_m": 500, "sistema_local": None,
            "escena_ref": None,
            "lote": {"origen": [0, 0], "lados": [], "vertices": [], "area_m2": None, "perimetro_m": None,
                     "fuente": "manual"},
            "retiros": {"frente_m": 3, "fondo_m": 3, "laterales_m": 0},
            "pendiente": None, "fecha_sol": "2026-09-26", "hora_sol": 12, "huso_h": None,
        },
    })


def op(datos: dict):
    return ops.ADAPTADOR.validate_python(datos)


def aplicar(p: Proyecto, datos: dict, contexto=None, autor="usuario") -> ops.Resultado:
    return ops.aplicar(p, op(datos), autor, contexto, AHORA)


def ubicado(lat=-34.6, lon=-58.4) -> Proyecto:
    return aplicar(proyecto_nuevo(), {"tipo": "definir_ubicacion", "lat": lat, "lon": lon}).proyecto


def malla_inclinada(pendiente_pct: float, n: int = 41, paso: float = 30.0) -> MallaLocal:
    x0 = y0 = -paso * (n - 1) / 2
    coord = x0 + np.arange(n) * paso
    mx, my = np.meshgrid(coord, coord)
    z = -mx * pendiente_pct / 100.0
    return MallaLocal(vertices=np.column_stack([mx.ravel(), my.ravel(), z.ravel()]),
                      nx=n, ny=n, x0=x0, y0=y0, dx=paso, dy=paso)


class ContextoFijo:
    def __init__(self, *escenas: ops.EscenaDisponible):
        self.escenas = {e.ref: e for e in escenas}

    def escena(self, ref):
        return self.escenas.get(ref)


def escena(ref="abcdef012345", lat=-34.6, lon=-58.4, margen=500.0, pendiente=2.0, cota=25.0):
    return ops.EscenaDisponible(ref=ref, lat=lat, lon=lon, margen_m=margen, malla=malla_inclinada(pendiente),
                                provisional=False, cota_origen_msnm=cota)


def test_el_proyecto_del_frontend_valida_en_el_esquema_python():
    p = proyecto_nuevo()
    assert p.terreno.margen_m == 500
    assert p.model_dump(mode="json")["terreno"]["lote"]["origen"] == [0.0, 0.0]


def test_renombrar_registra_el_cambio_y_no_toca_el_original():
    p = proyecto_nuevo()
    r = aplicar(p, {"tipo": "renombrar_proyecto", "nombre": "Casa Delta"})
    assert r.proyecto.nombre == "Casa Delta"
    assert p.nombre == "Casa sin nombre"
    assert r.registro.cambios == ["nombre"]
    assert r.registro.autor == "usuario"
    assert r.registro.operacion == {"tipo": "renombrar_proyecto", "nombre": "Casa Delta"}
    assert r.proyecto.modificado == AHORA


def test_operacion_sin_efecto_no_cambia_la_fecha_de_modificacion():
    p = proyecto_nuevo()
    r = aplicar(p, {"tipo": "renombrar_proyecto", "nombre": p.nombre})
    assert r.registro.cambios == []
    assert r.proyecto.modificado == p.modificado


def test_ubicacion_crea_el_sistema_local():
    p = ubicado()
    assert p.terreno.ubicacion.lat == -34.6
    assert p.terreno.sistema_local.origen_lon == -58.4
    assert p.terreno.estado == Estado.PENDIENTE_DATOS


def test_mover_el_origen_desactualiza_el_lote_hasta_redefinirlo():
    p = aplicar(ubicado(), {"tipo": "definir_lote", "vertices": LOTE_GRANDE}).proyecto
    assert p.terreno.estado == Estado.PENDIENTE_DATOS  # sin relieve todavía
    r = aplicar(p, {"tipo": "definir_ubicacion", "lat": -34.7, "lon": -58.4})
    assert r.proyecto.terreno.estado == Estado.DESACTUALIZADO
    assert r.registro.avisos
    # Cambiar el margen no alcanza para confirmar el lote.
    p2 = aplicar(r.proyecto, {"tipo": "definir_margen", "margen_m": 800}).proyecto
    assert p2.terreno.estado == Estado.DESACTUALIZADO
    # Redefinirlo (aunque sea con los mismos vértices) sí.
    p3 = aplicar(p2, {"tipo": "definir_lote", "vertices": LOTE_GRANDE}).proyecto
    assert p3.terreno.estado == Estado.PENDIENTE_DATOS


def test_agregar_la_direccion_no_mueve_el_origen():
    p = aplicar(ubicado(), {"tipo": "definir_lote", "vertices": LOTE_GRANDE}).proyecto
    r = aplicar(p, {"tipo": "definir_ubicacion", "lat": -34.6, "lon": -58.4, "direccion": "Calle 1"})
    assert r.proyecto.terreno.estado != Estado.DESACTUALIZADO
    assert "terreno.ubicacion.direccion" in r.registro.cambios


def test_definir_lote_calcula_medidas_y_corre_r01():
    r = aplicar(ubicado(), {"tipo": "definir_lote", "vertices": LOTE_GRANDE})
    lote = r.proyecto.terreno.lote
    assert lote.area_m2 == 14400
    assert lote.perimetro_m == 480
    assert len(lote.lados) == 4 and lote.lados[0].rumbo_deg == 90
    assert r.analisis_lote is not None
    assert "terreno.lote.vertices" in r.registro.cambios


def test_lote_con_menos_de_tres_vertices_queda_sin_definir():
    r = aplicar(ubicado(), {"tipo": "definir_lote", "vertices": [(0, 0), (10, 0)]})
    assert r.proyecto.terreno.lote.area_m2 is None
    assert r.proyecto.terreno.estado == Estado.PENDIENTE_DATOS


def test_vincular_escena_trae_cota_y_pendiente_de_la_escena():
    ctx = ContextoFijo(escena(pendiente=2.0, cota=25.0))
    p = aplicar(ubicado(), {"tipo": "definir_lote", "vertices": LOTE_GRANDE}).proyecto
    r = aplicar(p, {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx, autor="sistema")
    t = r.proyecto.terreno
    assert t.escena_ref == "abcdef012345"
    assert t.sistema_local.cota_origen_msnm == 25.0
    assert t.pendiente.porcentaje == pytest.approx(2.0, abs=0.05)
    assert t.estado == Estado.COMPROBADO_POR_REGLAS
    assert r.registro.estado_antes == Estado.PENDIENTE_DATOS
    assert r.registro.estado_despues == Estado.COMPROBADO_POR_REGLAS


def test_con_escena_vinculada_el_lote_se_evalua_contra_el_relieve():
    ctx = ContextoFijo(escena(pendiente=8.0))
    p = aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx).proyecto
    r = aplicar(p, {"tipo": "definir_lote", "vertices": LOTE_GRANDE}, ctx)
    assert r.proyecto.terreno.estado == Estado.PENDIENTE_REVISION


def test_escena_de_otro_origen_se_rechaza():
    ctx = ContextoFijo(escena(lat=-31.4))
    with pytest.raises(ops.OperacionInvalida):
        aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"}, ctx)


def test_escena_inexistente_se_rechaza():
    with pytest.raises(ops.OperacionInvalida, match="no encontrada"):
        aplicar(ubicado(), {"tipo": "vincular_escena", "ref": "abcdef012345"})


@pytest.mark.parametrize("datos", [
    {"tipo": "definir_margen", "margen_m": 50},
    {"tipo": "definir_ubicacion", "lat": 95, "lon": 0},
    {"tipo": "definir_retiros", "frente_m": -1, "fondo_m": 3, "laterales_m": 0},
    {"tipo": "renombrar_proyecto", "nombre": ""},
    {"tipo": "vincular_escena", "ref": "../../etc"},
    {"tipo": "definir_lote", "vertices": [[0, 0], [1, "x"]]},
    {"tipo": "definir_lote", "vertices": [[0, 0]], "extra": 1},
    {"tipo": "borrar_todo"},
])
def test_parametros_invalidos_se_rechazan_antes_de_aplicar(datos):
    with pytest.raises(ValidationError):
        op(datos)


def test_esquema_incompatible_se_rechaza():
    p = proyecto_nuevo().model_copy(update={"esquema": "assambl/proyecto@0.1"})
    with pytest.raises(ops.OperacionInvalida, match="Esquema"):
        aplicar(p, {"tipo": "renombrar_proyecto", "nombre": "x"})


def test_catalogo_describe_cada_operacion():
    cat = {o["tipo"]: o for o in ops.catalogo()}
    assert set(cat) == {"renombrar_proyecto", "definir_ubicacion", "definir_margen", "definir_lote",
                        "definir_retiros", "vincular_escena"}
    assert cat["definir_margen"]["parametros"]["properties"]["margen_m"]["minimum"] == 100
    assert "tipo" not in cat["definir_lote"]["parametros"]["properties"]
    assert cat["vincular_escena"]["para_asistente"] is False
    assert all(o["descripcion"] for o in cat.values())


def test_api_aplica_y_devuelve_el_registro():
    cliente = TestClient(app)
    p = proyecto_nuevo().model_dump(mode="json")
    r = cliente.post("/api/operaciones/aplicar", json={
        "proyecto": p, "operacion": {"tipo": "definir_ubicacion", "lat": -34.6, "lon": -58.4, "fuente": "mapa"},
    })
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["proyecto"]["terreno"]["ubicacion"]["fuente"] == "mapa"
    assert cuerpo["registro"]["autor"] == "usuario"

    # Ninguna escena generada tiene esa referencia: conflicto, no error de validación.
    r = cliente.post("/api/operaciones/aplicar", json={
        "proyecto": cuerpo["proyecto"], "operacion": {"tipo": "vincular_escena", "ref": "abcdef012345"},
    })
    assert r.status_code == 409

    r = cliente.post("/api/operaciones/aplicar", json={
        "proyecto": p, "operacion": {"tipo": "definir_margen", "margen_m": 5},
    })
    assert r.status_code == 422

    assert len(cliente.get("/api/operaciones").json()) == 6
