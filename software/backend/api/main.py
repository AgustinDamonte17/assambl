"""API de Assambl. Rutas finas: validan entrada y delegan en el paquete `assambl`.

Las únicas fuentes externas son de la NASA: NASADEM para el relieve y NASA POWER
para el clima. La posición del sol y toda la geometría se calculan localmente.
Nominatim se usa solo como ayuda de navegación para encontrar una dirección en el
mapa; no aporta ningún dato al modelo.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assambl import __version__

from .rutas import clima, geocodificacion, terreno

app = FastAPI(title="Assambl API", version=__version__, docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(geocodificacion.router, prefix="/api/geocodificar", tags=["geocodificación"])
app.include_router(terreno.router, prefix="/api/terreno", tags=["terreno"])
app.include_router(clima.router, prefix="/api", tags=["clima"])


@app.get("/api/salud")
def salud() -> dict:
    return {"estado": "ok", "version": __version__}
