"""Punto de entrada de la API en Vercel: expone la app FastAPI de backend/ como función Python.

Vercel sirve este archivo en /api/index; vercel.json reescribe todo /api/* hacia acá y FastAPI
resuelve la ruta completa, igual que en desarrollo.
"""

import sys
from pathlib import Path

# backend/ va primero para que `api` sea el paquete de backend/api y no esta carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.main import app  # noqa: E402,F401
