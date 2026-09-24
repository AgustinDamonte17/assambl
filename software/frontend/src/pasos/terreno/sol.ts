/**
 * Interpolación de la trayectoria solar que calcula el backend.
 *
 * El algoritmo astronómico vive en un solo lugar (backend/assambl/clima/sol.py).
 * Acá solo se interpola entre las muestras que llegan cada 5 minutos, para que
 * mover el control horario se sienta continuo sin reimplementar el cálculo.
 */

import type { PosicionSolar, Trayectoria } from "../../modelo/proyecto";

export interface EstadoSol {
  azimut_deg: number;
  elevacion_deg: number;
  /** Vector unitario hacia el sol: +X este, +Y norte, +Z arriba. */
  direccion: [number, number, number];
  sobre_horizonte: boolean;
}

function normalizar(v: [number, number, number]): [number, number, number] {
  const n = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / n, v[1] / n, v[2] / n];
}

function mezclarAngulo(a: number, b: number, t: number): number {
  // El azimut cruza 360°/0° en el norte: se interpola por el camino corto.
  let d = ((b - a + 540) % 360) - 180;
  return (a + d * t + 360) % 360;
}

/** Estado del sol a la hora local pedida, interpolando entre muestras. */
export function solALaHora(t: Trayectoria, horaLocal: number): EstadoSol {
  const minuto = Math.min(Math.max(horaLocal * 60, 0), 1440);
  const i = Math.min(Math.floor(minuto / t.paso_min), t.muestras.length - 2);
  const a: PosicionSolar = t.muestras[i];
  const b: PosicionSolar = t.muestras[i + 1];
  const f = (minuto - i * t.paso_min) / t.paso_min;

  const direccion = normalizar([
    a.direccion[0] + (b.direccion[0] - a.direccion[0]) * f,
    a.direccion[1] + (b.direccion[1] - a.direccion[1]) * f,
    a.direccion[2] + (b.direccion[2] - a.direccion[2]) * f,
  ]);
  const elevacion = a.elevacion_deg + (b.elevacion_deg - a.elevacion_deg) * f;
  return {
    azimut_deg: mezclarAngulo(a.azimut_deg, b.azimut_deg, f),
    elevacion_deg: elevacion,
    direccion,
    sobre_horizonte: elevacion > 0,
  };
}

/** Puntos del arco solar del día, para dibujarlo en la escena. Solo el tramo diurno. */
export function arcoDiurno(t: Trayectoria, radio: number): number[] {
  const puntos: number[] = [];
  for (const m of t.muestras) {
    if (m.elevacion_deg <= 0) continue;
    puntos.push(m.direccion[0] * radio, m.direccion[1] * radio, m.direccion[2] * radio);
  }
  return puntos;
}

export function horaTexto(hora: number): string {
  const h = Math.floor(hora);
  const m = Math.round((hora - h) * 60);
  return `${String(h).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}
