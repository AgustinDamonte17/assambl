"""Geocodificación con Nominatim (OpenStreetMap). Máximo 1 consulta por segundo."""

from __future__ import annotations

import httpx

from . import USER_AGENT

BASE = "https://nominatim.openstreetmap.org"
NOMBRE = "Nominatim (OpenStreetMap)"


async def buscar(texto: str, limite: int = 6, pais: str = "ar") -> list[dict]:
    params = {"format": "jsonv2", "q": texto, "limit": limite, "addressdetails": 0}
    if pais:
        params["countrycodes"] = pais
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": USER_AGENT, "Accept-Language": "es"}) as c:
        r = await c.get(f"{BASE}/search", params=params)
        r.raise_for_status()
        return [
            {"nombre": e["display_name"], "lat": float(e["lat"]), "lon": float(e["lon"]), "tipo": e.get("type")}
            for e in r.json()
        ]


async def inverso(lat: float, lon: float) -> str | None:
    params = {"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 18}
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": USER_AGENT, "Accept-Language": "es"}) as c:
        r = await c.get(f"{BASE}/reverse", params=params)
        r.raise_for_status()
        return r.json().get("display_name")
