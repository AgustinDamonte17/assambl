"""Resúmenes de diseño a partir de las series de NASA POWER.

Todo lo que sale de acá es una estimación regional derivada de un reanálisis, no
una medición en el terreno. El valor de resolución espacial viaja con el resultado
para que la interfaz pueda decirlo.
"""

from __future__ import annotations

from collections import defaultdict

from ..fuentes import power
from ..modelo.sitio import Clima, ResumenMes, SectorViento

MESES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
SECTORES = 16
ANCHO_SECTOR = 360.0 / SECTORES
# Límites de los intervalos de velocidad en m/s; por debajo del primero se cuenta como calma.
LIMITES_VELOCIDAD = [0.5, 2.0, 4.0, 6.0, 8.0, 10.0]
BASE_GRADOS_DIA = 18.0


def _valido(v) -> bool:
    return v is not None and v > power.RELLENO + 1


def _parametros(bloque: dict) -> dict[str, dict[str, str]]:
    """Unidades y nombre largo de cada parámetro, tal como los informa POWER."""
    info = bloque.get("parameters", {})
    return {
        clave: {"nombre": datos.get("longname", clave), "unidad": datos.get("units", "")}
        for clave, datos in info.items()
    }


def _indice_bin(velocidad: float) -> int:
    for i, limite in enumerate(LIMITES_VELOCIDAD[1:], start=1):
        if velocidad < limite:
            return i - 1
    return len(LIMITES_VELOCIDAD) - 1


def _rosa(direcciones: list[float], velocidades: list[float]) -> tuple[list[SectorViento], float]:
    """Rosa de vientos de 16 sectores. Devuelve los sectores y el porcentaje de calmas."""
    total = len(velocidades)
    if not total:
        return [], 0.0
    n_bins = len(LIMITES_VELOCIDAD)
    conteo = [[0] * n_bins for _ in range(SECTORES)]
    suma_vel = [0.0] * SECTORES
    n_sector = [0] * SECTORES
    calmas = 0
    for direccion, velocidad in zip(direcciones, velocidades):
        if velocidad < LIMITES_VELOCIDAD[0]:
            calmas += 1
            continue
        s = int(((direccion + ANCHO_SECTOR / 2) % 360) / ANCHO_SECTOR)
        conteo[s][_indice_bin(velocidad)] += 1
        suma_vel[s] += velocidad
        n_sector[s] += 1

    sectores = []
    for s in range(SECTORES):
        centro = s * ANCHO_SECTOR
        sectores.append(
            SectorViento(
                desde_deg=round((centro - ANCHO_SECTOR / 2) % 360, 3),
                hasta_deg=round((centro + ANCHO_SECTOR / 2) % 360, 3),
                centro_deg=round(centro, 3),
                frecuencia_pct=round(100 * n_sector[s] / total, 3),
                por_velocidad_pct=[round(100 * c / total, 3) for c in conteo[s]],
                velocidad_media_ms=round(suma_vel[s] / n_sector[s], 2) if n_sector[s] else None,
            )
        )
    return sectores, round(100 * calmas / total, 3)


def resumir(crudo: dict, lat: float, lon: float) -> Clima:
    """Convierte la respuesta de POWER en los resúmenes que usa el diseño."""
    clim = crudo.get("climatologia") or {}
    parametro_clim = clim.get("properties", {}).get("parameter", {})
    cabecera = clim.get("header", {})
    elevacion = None
    coordenadas = clim.get("geometry", {}).get("coordinates") or []
    if len(coordenadas) >= 3:
        elevacion = round(float(coordenadas[2]), 2)

    # Series horarias agrupadas por mes y por hora del día (hora solar local).
    por_mes: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    perfil: dict[int, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    direcciones: list[float] = []
    velocidades: list[float] = []
    # La dirección predominante se toma como el sector más frecuente: promediar
    # ángulos alrededor del norte daría un resultado sin sentido físico.
    sector_por_mes: dict[int, list[int]] = defaultdict(lambda: [0] * SECTORES)
    horas = 0
    grados_dia_cal = 0.0
    grados_dia_ref = 0.0
    horas_temperatura = 0

    horario = crudo.get("horario") or {}
    for datos in horario.values():
        p = datos.get("properties", {}).get("parameter", {})
        temperaturas = p.get("T2M", {})
        vel = p.get("WS10M", {})
        dirs = p.get("WD10M", {})
        for marca, t in temperaturas.items():
            horas += 1
            mes = int(marca[4:6])
            hora = int(marca[8:10])
            if _valido(t):
                por_mes[mes]["T2M"].append(t)
                perfil[mes][hora].append(t)
                grados_dia_cal += max(0.0, BASE_GRADOS_DIA - t)
                grados_dia_ref += max(0.0, t - BASE_GRADOS_DIA)
                horas_temperatura += 1
            v = vel.get(marca)
            d = dirs.get(marca)
            if _valido(v) and _valido(d):
                por_mes[mes]["WS10M"].append(v)
                direcciones.append(d)
                velocidades.append(v)
                if v >= LIMITES_VELOCIDAD[0]:
                    sector_por_mes[mes][int(((d + ANCHO_SECTOR / 2) % 360) / ANCHO_SECTOR)] += 1

    anios = max(1, len(horario))
    meses = []
    for i, sigla in enumerate(MESES, start=1):
        temp_mes = por_mes.get(i, {}).get("T2M", [])
        vel_mes = por_mes.get(i, {}).get("WS10M", [])
        horas_mes = perfil.get(i, {})
        conteo_mes = sector_por_mes.get(i)
        predominante = (
            round(conteo_mes.index(max(conteo_mes)) * ANCHO_SECTOR, 1) if conteo_mes and max(conteo_mes) else None
        )
        meses.append(
            ResumenMes(
                mes=i,
                t_media_c=_redondear(parametro_clim.get("T2M", {}).get(sigla)),
                t_max_c=_redondear(parametro_clim.get("T2M_MAX", {}).get(sigla)),
                t_min_c=_redondear(parametro_clim.get("T2M_MIN", {}).get(sigla)),
                t_max_abs_c=round(max(temp_mes), 2) if temp_mes else None,
                t_min_abs_c=round(min(temp_mes), 2) if temp_mes else None,
                radiacion_kwh_m2_dia=_redondear(parametro_clim.get("ALLSKY_SFC_SW_DWN", {}).get(sigla)),
                viento_medio_ms=round(sum(vel_mes) / len(vel_mes), 2)
                if vel_mes
                else _redondear(parametro_clim.get("WS10M", {}).get(sigla)),
                viento_dir_predominante_deg=predominante,
                perfil_horario_c=[
                    round(sum(horas_mes[h]) / len(horas_mes[h]), 2) if horas_mes.get(h) else 0.0 for h in range(24)
                ]
                if horas_mes
                else [],
            )
        )

    sectores, calmas = _rosa(direcciones, velocidades)
    primer_horario = next(iter(horario.values()), None)

    return Clima(
        lat=lat,
        lon=lon,
        elevacion_power_m=elevacion,
        periodo_climatologia=cabecera.get("range", ""),
        periodo_horario=f"{crudo.get('anio_inicio', '')}–{crudo.get('anio_fin', '')}" if horario else "",
        anios_horarios=len(horario),
        horas=horas,
        meses=meses,
        rosa=sectores,
        bins_velocidad_ms=LIMITES_VELOCIDAD,
        calma_pct=calmas,
        grados_dia_calefaccion=round(grados_dia_cal / 24 / anios, 1) if horas_temperatura else None,
        grados_dia_refrigeracion=round(grados_dia_ref / 24 / anios, 1) if horas_temperatura else None,
        base_grados_dia_c=BASE_GRADOS_DIA,
        altura_medicion_viento_m=10.0,
        parametros_climatologia=_parametros(clim),
        parametros_horarios=_parametros(primer_horario) if primer_horario else {},
    )


def _redondear(valor) -> float | None:
    return round(valor, 2) if _valido(valor) else None
