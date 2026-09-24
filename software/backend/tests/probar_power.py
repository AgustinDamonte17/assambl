"""Comprobación manual contra NASA POWER con datos reales.

    python tests/probar_power.py          -> 1 año horario, para ir rápido
    python tests/probar_power.py --cinco  -> los 5 años completos
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assambl.clima import resumen
from assambl.fuentes import power

LAT, LON = -31.42, -64.19
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ROSA = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]


async def principal() -> None:
    anios = 5 if "--cinco" in sys.argv else 1
    crudo = await power.descargar(LAT, LON, anios=anios)
    print("período climatología:", crudo["climatologia"]["header"].get("range"))
    print("fuentes:", crudo["climatologia"]["header"].get("sources"))
    primer = next(iter(crudo["horario"].values()))
    print("cabecera horaria:", {k: v for k, v in primer.get("header", {}).items() if k != "title"})

    c = resumen.resumir(crudo, LAT, LON)
    print(f"\nelevación de la celda POWER: {c.elevacion_power_m} m")
    print(f"horas procesadas: {c.horas}  años: {c.anios_horarios} ({c.periodo_horario})")
    print(f"grados-día base {c.base_grados_dia_c} °C: calefacción {c.grados_dia_calefaccion}  refrigeración {c.grados_dia_refrigeracion}")

    print(f"\n{'mes':4} {'media':>6} {'máx c':>6} {'mín c':>6} {'máx abs':>8} {'mín abs':>8} {'rad':>6} {'viento':>7} {'dir':>5}")
    for m in c.meses:
        print(
            f"{MESES_ES[m.mes - 1]:4} {m.t_media_c!s:>6} {m.t_max_c!s:>6} {m.t_min_c!s:>6} "
            f"{m.t_max_abs_c!s:>8} {m.t_min_abs_c!s:>8} {m.radiacion_kwh_m2_dia!s:>6} "
            f"{m.viento_medio_ms!s:>7} {m.viento_dir_predominante_deg!s:>5}"
        )

    print(f"\nrosa de vientos (calmas {c.calma_pct} %), intervalos {c.bins_velocidad_ms} m/s")
    for i, s in enumerate(c.rosa):
        barra = "#" * int(s.frecuencia_pct * 2)
        print(f"  {ROSA[i]:>3} {s.centro_deg:6.1f}°  {s.frecuencia_pct:5.2f} %  media {s.velocidad_media_ms!s:>5} m/s  {barra}")

    print("\nperfil horario de enero (°C):", c.meses[0].perfil_horario_c)
    for titulo, bloque in [("climatología", c.parametros_climatologia), ("horario", c.parametros_horarios)]:
        print(f"\nparámetros y unidades informados por la fuente ({titulo}):")
        for clave, info in sorted(bloque.items()):
            print(f"  {clave:20} {info['unidad']:12} {info['nombre']}")


if __name__ == "__main__":
    asyncio.run(principal())
