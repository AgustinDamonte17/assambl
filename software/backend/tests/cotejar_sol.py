"""Coteja assambl.clima.sol contra la biblioteca astral (implementación independiente).

Es una verificación puntual, no parte de la suite: se corre a mano y sus resultados
se fijan como valores esperados en test_sol.py. astral no es dependencia del
proyecto; para correr este cotejo hace falta instalarla:

    pip install astral
    python tests/cotejar_sol.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from astral import LocationInfo, sun as asun

from assambl.clima import sol

LAT, LON, HUSO = -31.42, -64.19, -3.0
TZ = timezone(timedelta(hours=HUSO))
lugar = LocationInfo("Cordoba", "AR", "Etc/GMT+3", LAT, LON)

print(f"{'fecha':12} {'orto assambl':13} {'orto astral':12} {'ocaso assambl':14} {'ocaso astral':12} {'mediodia':9} {'astral':8}")
for dia in [date(2024, 3, 21), date(2024, 6, 21), date(2024, 9, 23), date(2024, 12, 21)]:
    ev = sol.eventos(LAT, LON, dia, HUSO)
    a = asun.sun(lugar.observer, date=dia, tzinfo=TZ)
    print(
        f"{dia}   {ev.amanecer_local:13} {a['sunrise'].strftime('%H:%M'):12} "
        f"{ev.atardecer_local:14} {a['sunset'].strftime('%H:%M'):12} "
        f"{ev.mediodia_solar_local:9} {a['noon'].strftime('%H:%M'):8}"
    )

print()
print(f"{'momento local':17} {'elev assambl':12} {'elev astral':11} {'azim assambl':12} {'azim astral':11}")
for h in (7, 9, 12, 15, 18):
    momento = datetime(2024, 12, 21, h, 0, tzinfo=TZ)
    p = sol.posicion(LAT, LON, momento.astimezone(timezone.utc), HUSO)
    ea = asun.elevation(lugar.observer, momento)
    aa = asun.azimuth(lugar.observer, momento)
    print(f"{momento:%Y-%m-%d %H:%M}  {p.elevacion_deg:12.3f} {ea:11.3f} {p.azimut_deg:12.3f} {aa:11.3f}")
