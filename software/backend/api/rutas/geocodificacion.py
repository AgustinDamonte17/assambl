from fastapi import APIRouter, HTTPException, Query

from assambl.fuentes import nominatim

router = APIRouter()


@router.get("")
async def buscar(q: str = Query(min_length=3), pais: str = "ar") -> list[dict]:
    try:
        return await nominatim.buscar(q, pais=pais)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Geocodificador no disponible: {e}") from e


@router.get("/inverso")
async def inverso(lat: float, lon: float) -> dict:
    try:
        return {"direccion": await nominatim.inverso(lat, lon)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Geocodificador no disponible: {e}") from e
