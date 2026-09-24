"""Genera una escena .glb de ejemplo para inspeccionarla o validarla.

    python tests/generar_escena.py                 -> relieve sintético
    python tests/generar_escena.py --nasadem       -> descarga NASADEM real

La salida queda en cache/salidas/terreno_ejemplo.glb, lista para abrir en Blender,
en el visor web o en https://github.khronos.org/glTF-Validator/
"""

from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assambl.capas import terreno
from assambl.config import carpeta_cache
from assambl.modelo.sitio import MallaDem

LAT, LON, MARGEN = -31.42, -64.19, 500.0
LOTE = [(-6.0, -15.0), (6.0, -15.0), (6.0, 15.0), (-6.0, 15.0)]


def dem_sintetico() -> MallaDem:
    """Loma suave, solo para probar la cadena sin depender de la red."""
    paso = 1 / 3600
    n = 41
    alturas = []
    for j in range(n):
        for i in range(n):
            dx, dy = i - n // 2, j - n // 2
            alturas.append(900.0 + 25 * math.exp(-(dx**2 + dy**2) / 120) - 0.8 * dx)
    return MallaDem(lat_sur=LAT - (n // 2) * paso, lon_oeste=LON - (n // 2) * paso,
                    paso_deg=paso, nx=n, ny=n, alturas_msnm=alturas)


async def principal() -> None:
    real = "--nasadem" in sys.argv
    if real:
        escena = await terreno.generar(LAT, LON, MARGEN, LOTE)
    else:
        escena = terreno.componer(LAT, LON, MARGEN, dem_sintetico(), LOTE, [], [])
    # Sin esto las dos salidas se confunden: el relieve sintético también sale con
    # provisional=False, porque el que lo marca es el camino de descarga.
    print("relieve:", "NASADEM real" if real else "SINTÉTICO (no son datos de la NASA)")

    destino = Path(carpeta_cache("salidas")) / "terreno_ejemplo.glb"
    destino.write_bytes(escena.glb)

    print(f"archivo: {destino}  ({len(escena.glb) / 1024:.1f} kB)")
    print(f"malla: {escena.malla.nx}×{escena.malla.ny} posts, paso {escena.malla.dx:.1f} × {escena.malla.dy:.1f} m")
    print(f"cota del origen: {escena.relieve.cota_origen_msnm} msnm")
    print(f"altura relativa: {escena.relieve.z_min_m} a {escena.relieve.z_max_m} m")
    print(f"lote: {escena.area_m2} m², pendiente {escena.pendiente_pct} % hacia {escena.pendiente_azimut_deg}°")
    print(f"provisional: {escena.relieve.provisional}")
    for f in escena.fuentes:
        print(f"fuente: {f.nombre} [{f.estado}] {f.resolucion} — {f.detalle}")
    for a in escena.advertencias:
        print(f"advertencia: {a}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows es cp1252 y no traga «≈»
    asyncio.run(principal())
