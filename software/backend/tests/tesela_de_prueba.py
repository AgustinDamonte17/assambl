"""Coloca un mosaico .hgt SINTÉTICO en la caché para probar la cadena completa
sin credencial de Earthdata, y lo borra al terminar.

No es un sustituto de NASADEM: el relieve que genera es inventado. Sirve para
verificar la lectura del formato .hgt, el armado de la malla, el .glb y las
sombras del visor cuando todavía no hay token.

    python tests/tesela_de_prueba.py poner
    python tests/tesela_de_prueba.py quitar
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assambl.config import carpeta_cache
from assambl.fuentes.nasadem import LADO_HGT

TESELA = "s32w065"  # cubre el punto de prueba en Córdoba


def ruta() -> Path:
    return Path(carpeta_cache("nasadem")) / f"{TESELA}.hgt"


def poner() -> None:
    # Lomas en el rango de alturas de las sierras de Córdoba. Las longitudes de onda
    # se dan en posts (1 post ≈ 30 m) para que el relieve se vea dentro del entorno
    # de 1 km que se modela, no sólo a escala de la tesela entera.
    j, i = np.mgrid[0:LADO_HGT, 0:LADO_HGT]
    onda = lambda n, paso: 2 * np.pi * n / paso
    z = (
        700
        + 90 * np.sin(onda(i, 67)) * np.cos(onda(j, 83))
        + 25 * np.sin(onda(i, 21) + 1.2)
        + 14 * np.cos(onda(j, 13) + 0.4)
    )
    # El archivo .hgt guarda la fila 0 al norte.
    datos = np.flipud(z).astype(">i2")
    destino = ruta()
    destino.write_bytes(datos.tobytes())
    print(f"mosaico sintético escrito en {destino} ({destino.stat().st_size / 1e6:.1f} MB)")
    print("ATENCIÓN: no son datos de NASADEM. Borralo con 'quitar' cuando termines.")


def quitar() -> None:
    destino = ruta()
    if destino.exists():
        destino.unlink()
        print(f"borrado {destino}")
    else:
        print("no había mosaico de prueba")


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "poner"
    {"poner": poner, "quitar": quitar}[accion]()
