"""Posición solar por cálculo local, sin consultar ningún servicio.

Implementa el algoritmo del NOAA Solar Calculator (Global Monitoring Laboratory),
derivado de Meeus, J. (1998), *Astronomical Algorithms*, 2ª edición, capítulos 7,
12, 22, 25 y 28. Exactitud del orden de ±0,01° en declinación y ±1 minuto en la
ecuación del tiempo para fechas entre 1800 y 2100.

Convención de salida: azimut en grados desde el norte hacia el este (0° = norte,
90° = este, 180° = sur, 270° = oeste), elevación en grados sobre el horizonte.
El vector cartesiano usa el sistema local del proyecto: +X este, +Y norte, +Z arriba.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, Field

ALGORITMO = "NOAA Solar Calculator (Meeus, Astronomical Algorithms, 2ª ed.)"
# Elevación del centro del disco solar cuando el borde superior toca el horizonte,
# incluida la refracción atmosférica estándar.
ELEVACION_ORTO_OCASO = -0.833


class PosicionSolar(BaseModel):
    momento_utc: str
    momento_local: str
    minuto_local: int = Field(description="Minutos desde la medianoche local, para ubicar la muestra en el día")
    azimut_deg: float
    elevacion_deg: float = Field(description="Elevación geométrica, sin refracción")
    elevacion_aparente_deg: float = Field(description="Elevación corregida por refracción atmosférica")
    sobre_horizonte: bool
    direccion: list[float] = Field(description="Vector unitario hacia el sol en el sistema local (+X este, +Y norte, +Z arriba)")


class EventosSolares(BaseModel):
    fecha: str
    amanecer_local: str | None
    mediodia_solar_local: str
    atardecer_local: str | None
    duracion_dia_h: float
    declinacion_deg: float
    ecuacion_tiempo_min: float


class Trayectoria(BaseModel):
    algoritmo: str = ALGORITMO
    lat: float
    lon: float
    fecha: str
    huso_horario_h: float
    paso_min: int
    muestras: list[PosicionSolar]
    eventos: EventosSolares


def huso_por_longitud(lon: float) -> float:
    """Huso solar medio para la longitud. Se usa como valor inicial cuando el
    proyecto no declara uno; el huso civil puede diferir (Argentina usa UTC−3
    aunque su meridiano central sea −60°)."""
    return round(lon / 15.0)


def _dia_juliano(momento: datetime) -> float:
    m = momento.astimezone(timezone.utc)
    a, mes, d = m.year, m.month, m.day
    if mes <= 2:
        a -= 1
        mes += 12
    A = a // 100
    B = 2 - A + A // 4
    jd = math.floor(365.25 * (a + 4716)) + math.floor(30.6001 * (mes + 1)) + d + B - 1524.5
    return jd + (m.hour + m.minute / 60 + (m.second + m.microsecond / 1e6) / 3600) / 24


def _parametros_solares(t: float) -> tuple[float, float, float]:
    """Declinación (grados), ecuación del tiempo (minutos) y longitud media, para
    el siglo juliano t."""
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    m_rad = math.radians(m)
    c = (
        math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2 * m_rad) * (0.019993 - 0.000101 * t)
        + math.sin(3 * m_rad) * 0.000289
    )
    long_verdadera = l0 + c
    omega = 125.04 - 1934.136 * t
    long_aparente = long_verdadera - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    obl_media = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    obl = obl_media + 0.00256 * math.cos(math.radians(omega))

    declinacion = math.degrees(math.asin(math.sin(math.radians(obl)) * math.sin(math.radians(long_aparente))))

    y = math.tan(math.radians(obl / 2)) ** 2
    l0_rad = math.radians(l0)
    ecuacion = 4 * math.degrees(
        y * math.sin(2 * l0_rad)
        - 2 * e * math.sin(m_rad)
        + 4 * e * y * math.sin(m_rad) * math.cos(2 * l0_rad)
        - 0.5 * y * y * math.sin(4 * l0_rad)
        - 1.25 * e * e * math.sin(2 * m_rad)
    )
    return declinacion, ecuacion, l0


def _refraccion(elevacion_deg: float) -> float:
    """Refracción atmosférica aproximada en grados (NOAA), para 1010 hPa y 10 °C."""
    if elevacion_deg > 85.0:
        return 0.0
    te = math.tan(math.radians(elevacion_deg))
    if elevacion_deg > 5.0:
        r = 58.1 / te - 0.07 / te**3 + 0.000086 / te**5
    elif elevacion_deg > -0.575:
        r = 1735.0 + elevacion_deg * (-518.2 + elevacion_deg * (103.4 + elevacion_deg * (-12.79 + elevacion_deg * 0.711)))
    else:
        r = -20.772 / te
    return r / 3600.0


def posicion(lat: float, lon: float, momento_utc: datetime, huso_horario_h: float | None = None) -> PosicionSolar:
    if momento_utc.tzinfo is None:
        momento_utc = momento_utc.replace(tzinfo=timezone.utc)
    huso = huso_por_longitud(lon) if huso_horario_h is None else huso_horario_h
    local = momento_utc.astimezone(timezone(timedelta(hours=huso)))

    t = (_dia_juliano(momento_utc) - 2451545.0) / 36525.0
    declinacion, ecuacion, _ = _parametros_solares(t)

    utc = momento_utc.astimezone(timezone.utc)
    minutos_utc = utc.hour * 60 + utc.minute + utc.second / 60
    tiempo_solar_verdadero = (minutos_utc + ecuacion + 4 * lon) % 1440
    angulo_horario = tiempo_solar_verdadero / 4 - 180

    lat_r = math.radians(lat)
    dec_r = math.radians(declinacion)
    ah_r = math.radians(angulo_horario)
    cos_cenit = math.sin(lat_r) * math.sin(dec_r) + math.cos(lat_r) * math.cos(dec_r) * math.cos(ah_r)
    cos_cenit = max(-1.0, min(1.0, cos_cenit))
    cenit = math.degrees(math.acos(cos_cenit))
    elevacion = 90.0 - cenit

    sen_cenit = math.sin(math.radians(cenit))
    if abs(sen_cenit) < 1e-9:
        azimut = 180.0
    else:
        coc = (math.sin(lat_r) * cos_cenit - math.sin(dec_r)) / (math.cos(lat_r) * sen_cenit)
        coc = max(-1.0, min(1.0, coc))
        azimut = math.degrees(math.acos(coc))
        azimut = (180.0 + azimut) % 360.0 if angulo_horario > 0 else (540.0 - azimut) % 360.0

    aparente = elevacion + _refraccion(elevacion)
    el_r = math.radians(elevacion)
    az_r = math.radians(azimut)
    direccion = [
        round(math.cos(el_r) * math.sin(az_r), 6),
        round(math.cos(el_r) * math.cos(az_r), 6),
        round(math.sin(el_r), 6),
    ]

    return PosicionSolar(
        momento_utc=utc.isoformat(),
        momento_local=local.isoformat(),
        minuto_local=local.hour * 60 + local.minute,
        azimut_deg=round(azimut, 3),
        elevacion_deg=round(elevacion, 3),
        elevacion_aparente_deg=round(aparente, 3),
        sobre_horizonte=aparente > 0,
        direccion=direccion,
    )


def _hhmm(minutos: float) -> str:
    minutos = minutos % 1440
    return f"{int(minutos // 60):02d}:{int(round(minutos % 60)) % 60:02d}"


def eventos(lat: float, lon: float, dia: date, huso_horario_h: float | None = None) -> EventosSolares:
    """Mediodía solar, orto y ocaso en hora local del huso indicado."""
    huso = huso_por_longitud(lon) if huso_horario_h is None else huso_horario_h
    medio = datetime(dia.year, dia.month, dia.day, 12, 0, tzinfo=timezone(timedelta(hours=huso)))
    t = (_dia_juliano(medio) - 2451545.0) / 36525.0
    declinacion, ecuacion, _ = _parametros_solares(t)

    mediodia_min = 720 - 4 * lon - ecuacion + huso * 60

    lat_r = math.radians(lat)
    dec_r = math.radians(declinacion)
    cos_h = (
        math.cos(math.radians(90.0 - ELEVACION_ORTO_OCASO)) / (math.cos(lat_r) * math.cos(dec_r))
        - math.tan(lat_r) * math.tan(dec_r)
    )
    if cos_h > 1.0:  # noche polar
        amanecer = atardecer = None
        duracion = 0.0
    elif cos_h < -1.0:  # sol de medianoche
        amanecer = atardecer = None
        duracion = 24.0
    else:
        semiarco = math.degrees(math.acos(cos_h)) * 4  # 4 minutos por grado
        amanecer = _hhmm(mediodia_min - semiarco)
        atardecer = _hhmm(mediodia_min + semiarco)
        duracion = 2 * semiarco / 60

    return EventosSolares(
        fecha=dia.isoformat(),
        amanecer_local=amanecer,
        mediodia_solar_local=_hhmm(mediodia_min),
        atardecer_local=atardecer,
        duracion_dia_h=round(duracion, 3),
        declinacion_deg=round(declinacion, 3),
        ecuacion_tiempo_min=round(ecuacion, 3),
    )


def trayectoria(lat: float, lon: float, dia: date, huso_horario_h: float | None = None, paso_min: int = 5) -> Trayectoria:
    """Recorrido del sol a lo largo del día, muestreado a paso fijo.

    El visor interpola entre muestras en lugar de repetir el cálculo, para que el
    algoritmo esté implementado una sola vez.
    """
    if paso_min < 1 or 1440 % paso_min:
        raise ValueError("El paso debe ser un divisor entero de 1440 minutos")
    huso = huso_por_longitud(lon) if huso_horario_h is None else huso_horario_h
    tz = timezone(timedelta(hours=huso))
    inicio = datetime(dia.year, dia.month, dia.day, 0, 0, tzinfo=tz)
    muestras = [
        posicion(lat, lon, (inicio + timedelta(minutes=m)).astimezone(timezone.utc), huso)
        for m in range(0, 1440 + paso_min, paso_min)
    ]
    return Trayectoria(
        lat=lat,
        lon=lon,
        fecha=dia.isoformat(),
        huso_horario_h=huso,
        paso_min=paso_min,
        muestras=muestras,
        eventos=eventos(lat, lon, dia, huso),
    )


def fechas_clave(anio: int, hemisferio_sur: bool = True) -> dict[str, str]:
    """Fechas de referencia para estudiar asoleamiento. Son aproximadas al día
    (los solsticios varían algunas horas entre años)."""
    solsticio_junio = date(anio, 6, 21)
    solsticio_diciembre = date(anio, 12, 21)
    return {
        "equinoccio_marzo": date(anio, 3, 21).isoformat(),
        "solsticio_invierno": (solsticio_junio if hemisferio_sur else solsticio_diciembre).isoformat(),
        "equinoccio_septiembre": date(anio, 9, 23).isoformat(),
        "solsticio_verano": (solsticio_diciembre if hemisferio_sur else solsticio_junio).isoformat(),
    }
