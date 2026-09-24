"""La malla debe reproducir los posts del DEM sin agregar ni suavizar nada."""

import math

import numpy as np
import pytest

from assambl.generadores import glb
from assambl.geometria import malla as gmalla
from assambl.geometria import poligono
from assambl.geometria.coordenadas import SistemaLocal
from assambl.modelo.sitio import MallaDem

LAT, LON = -31.42, -64.19


def dem_rampa(nx=5, ny=5, pendiente_por_post=3.0) -> MallaDem:
    """Rampa que sube hacia el este, con el post central en 1000 msnm."""
    alturas = [1000.0 + (i - nx // 2) * pendiente_por_post for _ in range(ny) for i in range(nx)]
    paso = 1 / 3600
    return MallaDem(
        lat_sur=LAT - (ny // 2) * paso,
        lon_oeste=LON - (nx // 2) * paso,
        paso_deg=paso,
        nx=nx,
        ny=ny,
        alturas_msnm=alturas,
    )


def test_cantidad_de_vertices_igual_a_posts():
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    assert m.vertices.shape == (25, 3)
    assert (m.nx, m.ny) == (5, 5)


def test_paso_en_metros_cercano_a_30():
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    assert m.dy == pytest.approx(30.87, abs=0.05)  # 1 arcosegundo de latitud
    assert m.dx == pytest.approx(30.87 * math.cos(math.radians(LAT)), abs=0.05)


def test_origen_queda_en_cero():
    m, cota = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    assert cota == pytest.approx(1000.0, abs=1e-6)
    assert m.altura_en(0.0, 0.0) == pytest.approx(0.0, abs=1e-6)


def test_altura_en_un_post_es_exactamente_la_del_dem():
    """Consultar sobre un post no debe devolver un valor promediado."""
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    assert m.altura_en(m.dx, 0.0) == pytest.approx(3.0, abs=1e-6)
    assert m.altura_en(-2 * m.dx, 0.0) == pytest.approx(-6.0, abs=1e-6)


def test_altura_coincide_con_la_cara_visible():
    """altura_en debe caer sobre el triángulo que dibuja glb.rejilla_indices."""
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    vertices, _ = glb.normales_planas(m.vertices, glb.rejilla_indices(m.nx, m.ny))
    caras = vertices.reshape(-1, 3, 3)
    for x, y in [(5.0, 3.0), (12.0, 25.0), (-20.0, -7.0), (0.4, 0.4)]:
        z = m.altura_en(x, y)
        assert any(_punto_en_cara(cara, x, y, z) for cara in caras), (x, y, z)


def _punto_en_cara(cara: np.ndarray, x: float, y: float, z: float) -> bool:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = cara
    det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(det) < 1e-12:
        return False
    l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / det
    l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / det
    l3 = 1 - l1 - l2
    if min(l1, l2, l3) < -1e-6:
        return False
    return abs(l1 * az + l2 * bz + l3 * cz - z) < 1e-4


def test_apoyar_pone_los_puntos_sobre_la_superficie():
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    puntos = [(0.0, 0.0), (10.0, 5.0), (-8.0, 12.0)]
    apoyados = gmalla.apoyar(m, puntos, separacion_m=0.2)
    for (x, y), p in zip(puntos, apoyados):
        assert p[2] == pytest.approx(m.altura_en(x, y) + 0.2, abs=1e-4)


def test_pendiente_de_la_rampa():
    """3 m cada 30,87·cos(lat) m hacia el este: la bajada apunta al oeste."""
    m, _ = gmalla.desde_dem(dem_rampa(), SistemaLocal(LAT, LON))
    lote = [(-20.0, -20.0), (20.0, -20.0), (20.0, 20.0), (-20.0, 20.0)]
    pct, azimut = gmalla.pendiente_media(m, lote)
    assert pct == pytest.approx(100 * 3.0 / m.dx, abs=0.2)
    assert azimut == pytest.approx(270.0, abs=1.0)


def test_recortar_conserva_el_area_pedida():
    dem = dem_rampa(nx=41, ny=41)
    m, _ = gmalla.desde_dem(dem, SistemaLocal(LAT, LON))
    r = gmalla.recortar(m, 100.0)
    ancho, alto = r.extension_m()
    assert ancho >= 200.0 and alto >= 200.0
    assert ancho < 200.0 + 2 * m.dx and alto < 200.0 + 2 * m.dy


def test_malla_plana_es_horizontal():
    m = gmalla.malla_plana(SistemaLocal(LAT, LON), 500.0)
    assert np.allclose(m.vertices[:, 2], 0.0)
    assert m.extension_m() == pytest.approx((1000.0, 1000.0))


def test_triangular_lote_en_ele():
    """Un abanico desde el centroide fallaría; el recorte de orejas no."""
    ele = [(0, 0), (20, 0), (20, 10), (10, 10), (10, 20), (0, 20)]
    triangulos = poligono.triangular(ele)
    assert len(triangulos) == len(ele) - 2
    total = sum(
        abs(poligono.area_con_signo([ele[a], ele[b], ele[c]])) for a, b, c in triangulos
    )
    assert total == pytest.approx(poligono.area(ele), abs=1e-6)


def test_densificar_respeta_el_paso():
    cuadrado = [(0, 0), (10, 0), (10, 10), (0, 10)]
    denso = poligono.densificar(cuadrado, 2.0)
    assert len(denso) == 20  # 4 lados × 5 tramos
    assert all(math.dist(a, b) <= 2.0 + 1e-9 for a, b in zip(denso, denso[1:] + denso[:1]))
