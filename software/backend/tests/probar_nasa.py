"""Comprobación manual contra los servicios reales de la NASA.

    python tests/probar_nasa.py            -> token y ruta de descarga
    python tests/probar_nasa.py --descarga -> además descarga un recorte real
    python tests/probar_nasa.py --cotas    -> coteja el mosaico contra cotas conocidas

El cotejo de cotas es la única forma de detectar un error de indexado: una malla
con filas o columnas invertidas se ve perfectamente razonable en el visor, pero
pone la ladera del lado equivocado.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from assambl.config import carpeta_cache, token_earthdata
from assambl.fuentes import nasadem

# Cotas de referencia tomadas de cartografía pública, para el mosaico s32w065.
# No son exactas: sirven para descartar un error de indexado, que daría diferencias
# de cientos de metros en todos los puntos a la vez. Se eligen lugares llanos: sobre
# una ladera empinada, cien metros de imprecisión en la coordenada ya mueven la cota
# lo suficiente como para que la comparación no signifique nada.
REFERENCIAS = [
    ("Córdoba, plaza San Martín", -31.4201, -64.1888, 400),
    ("Aeropuerto de Córdoba", -31.3236, -64.2080, 474),
    ("Villa Carlos Paz", -31.4241, -64.4978, 640),
    ("Alta Gracia", -31.6539, -64.4283, 580),
]

# El techo del mosaico es otra comprobación independiente: s32w065 contiene el cerro
# Champaquí (2790 m), el punto más alto de Córdoba.
CIMA_ESPERADA = 2790


def cotejar_cotas() -> None:
    ruta = Path(carpeta_cache("nasadem")) / "s32w065.hgt"
    if not ruta.exists():
        print("No hay mosaico s32w065 en la caché; corré primero con --descarga")
        return
    matriz = nasadem._leer_hgt(ruta.read_bytes())
    print(f"mosaico {matriz.shape}, cotas de {matriz.min():.0f} a {matriz.max():.0f} m\n")
    print(f"{'punto':28} {'esperado':>9} {'NASADEM':>9} {'dif':>7}")
    for nombre, lat, lon, esperado in REFERENCIAS:
        fila = round((lat + 32) * nasadem.POSTS_POR_GRADO)
        col = round((lon + 65) * nasadem.POSTS_POR_GRADO)
        valor = float(matriz[fila, col])
        print(f"{nombre:28} {esperado:9.0f} {valor:9.0f} {valor - esperado:+7.0f}")

    cima = float(matriz.max())
    fila, col = np.unravel_index(int(matriz.argmax()), matriz.shape)
    lat = -32 + fila / nasadem.POSTS_POR_GRADO
    lon = -65 + col / nasadem.POSTS_POR_GRADO
    print(f"\n{'cima del mosaico (Champaquí)':28} {CIMA_ESPERADA:9.0f} {cima:9.0f} {cima - CIMA_ESPERADA:+7.0f}")
    print(f"{'':28} en {lat:.4f}, {lon:.4f}")


async def principal() -> None:
    lat, lon = -31.42, -64.19
    tesela = nasadem.nombre_tesela(-32, -65)
    print("tesela para el punto:", tesela)
    print("url de descarga:", nasadem.url_descarga(tesela))
    print("token EARTHDATA:", "presente" if token_earthdata() else "AUSENTE")
    if token_earthdata():
        ok, mensaje = await nasadem.probar_credencial()
        print("credencial:", ok, "-", mensaje)

    if "--descarga" in sys.argv:
        d = 0.01
        malla = await nasadem.descargar_recorte(lat - d, lat + d, lon - d, lon + d)
        print(f"\nmalla {malla.nx}×{malla.ny} posts, huecos={malla.huecos}, teselas={malla.teselas}")
        print("altura mínima/máxima:", min(malla.alturas_msnm), max(malla.alturas_msnm))

    if "--cotas" in sys.argv:
        print()
        cotejar_cotas()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(principal())
