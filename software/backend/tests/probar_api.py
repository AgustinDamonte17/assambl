"""Recorre la API levantada en localhost con un lote real.

    python tests/probar_api.py [http://127.0.0.1:8765]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows usa cp1252 por defecto

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
LAT, LON, MARGEN = -31.42, -64.19, 500.0
LOTE = [[-6.0, -15.0], [6.0, -15.0], [6.0, 15.0], [-6.0, 15.0]]


def principal() -> None:
    with httpx.Client(base_url=BASE, timeout=600) as c:
        print("salud:", c.get("/api/salud").json())

        print("\ncredencial Earthdata:", c.get("/api/terreno/credencial").json())

        r = c.post("/api/terreno/escena", json={"lat": LAT, "lon": LON, "margen_m": MARGEN, "vertices": LOTE})
        r.raise_for_status()
        escena = r.json()
        print(f"\nescena {escena['ref']}: {escena['posts']} posts cada {escena['paso_m']} m, "
              f"extensión {escena['extension_m']} m, glb {escena['bytes_glb'] / 1024:.0f} kB")
        print(f"  provisional: {escena['relieve']['provisional']}  cota origen: {escena['relieve']['cota_origen_msnm']} msnm")
        print(f"  pendiente: {escena['pendiente_pct']} % hacia {escena['pendiente_azimut_deg']}°")
        for f in escena["fuentes"]:
            print(f"  fuente: {f['nombre']} [{f['estado']}] {f['naturaleza']} — {f['resolucion']}")
        for a in escena["advertencias"]:
            print(f"  advertencia: {a}")
        print("  reglas:", escena["reglas"]["estado"])
        for v in escena["reglas"]["verificaciones"]:
            print(f"    {v['id']} {v['estado']:22} {v['detalle'][:90]}")

        glb = c.get(f"/api/terreno/escena/{escena['ref']}.glb")
        glb.raise_for_status()
        destino = Path("cache/salidas")
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "api_terreno.glb").write_bytes(glb.content)
        print(f"\nglb: {len(glb.content) / 1024:.0f} kB, tipo {glb.headers['content-type']}")

        script = c.get(f"/api/terreno/escena/{escena['ref']}.py", params={"fecha": "2026-06-21", "hora": 10})
        script.raise_for_status()
        (destino / "api_terreno.py").write_text(script.text, encoding="utf-8")
        print(f"script blender: {len(script.text) / 1024:.0f} kB")

        s = c.get("/api/terreno/sol", params={"lat": LAT, "lon": LON, "fecha": "2026-06-21", "huso_h": -3})
        s.raise_for_status()
        sol = s.json()
        ev = sol["eventos"]
        print(f"\nsol 2026-06-21: amanece {ev['amanecer_local']}, mediodía {ev['mediodia_solar_local']}, "
              f"atardece {ev['atardecer_local']} ({ev['duracion_dia_h']} h)")
        print(f"  {len(sol['muestras'])} muestras cada {sol['paso_min']} min")
        print(f"  fechas clave: {json.dumps(sol['fechas_clave'], ensure_ascii=False)}")
        print(f"  procedencia: {sol['procedencia']['naturaleza']} — {sol['procedencia']['algoritmo']}")

        k = c.get("/api/clima", params={"lat": LAT, "lon": LON, "anios": 1})
        k.raise_for_status()
        clima = k.json()
        ene = clima["clima"]["meses"][0]
        jul = clima["clima"]["meses"][6]
        print(f"\nclima: {clima['clima']['periodo_climatologia']}")
        print(f"  enero  media {ene['t_media_c']} °C, radiación {ene['radiacion_kwh_m2_dia']} kWh/m²/día")
        print(f"  julio  media {jul['t_media_c']} °C, radiación {jul['radiacion_kwh_m2_dia']} kWh/m²/día")
        dominante = max(clima["clima"]["rosa"], key=lambda s: s["frecuencia_pct"])
        print(f"  viento dominante: {dominante['centro_deg']}° con {dominante['frecuencia_pct']} %")
        print(f"  fuente: {clima['fuente']['naturaleza']} — {clima['fuente']['resolucion']}")


if __name__ == "__main__":
    principal()
