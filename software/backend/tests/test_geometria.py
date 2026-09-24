import math

from assambl.geometria import poligono
from assambl.geometria.coordenadas import SistemaLocal, lonlat_a_pixel, pixel_a_lonlat


def test_area_perimetro_rectangulo():
    rect = [(0, 0), (20, 0), (20, 30), (0, 30)]
    assert poligono.area(rect) == 600
    assert poligono.perimetro(rect) == 100
    assert poligono.es_simple(rect)


def test_lados_y_reconstruccion():
    rect = [(0, 0), (20, 0), (20, 30), (0, 30)]
    lados = poligono.lados(rect)
    assert [round(l["rumbo_deg"]) for l in lados] == [90, 0, 270, 180]
    rec = poligono.desde_lados((0, 0), lados)
    for a, b in zip(rec, rect):
        assert math.dist(a, b) < 1e-9


def test_autointerseccion():
    moño = [(0, 0), (10, 10), (10, 0), (0, 10)]
    assert not poligono.es_simple(moño)


def test_sistema_local_ida_y_vuelta():
    s = SistemaLocal(-31.42, -64.19)
    x, y = s.a_local(-31.41, -64.18)
    assert 900 < x < 1000 and 1100 < y < 1120
    lat, lon = s.a_geografica(x, y)
    assert abs(lat + 31.41) < 1e-9 and abs(lon + 64.18) < 1e-9


def test_pixel_ida_y_vuelta():
    px, py = lonlat_a_pixel(-64.19, -31.42, 13)
    lon, lat = pixel_a_lonlat(px, py, 13)
    assert abs(lon + 64.19) < 1e-9 and abs(lat + 31.42) < 1e-9
