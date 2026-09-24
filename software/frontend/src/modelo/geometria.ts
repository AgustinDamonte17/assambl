/** Geometría plana y coordenadas locales. Mismo criterio que backend/assambl/geometria. */

import type { Lado, Punto } from "./proyecto";

const RADIO_TIERRA_M = 6_371_008.8;
const K = (RADIO_TIERRA_M * Math.PI) / 180;

/** Equirrectangular local centrada en (lat0, lon0). +X este, +Y norte. */
export class SistemaLocal {
  private cos: number;
  constructor(
    public lat0: number,
    public lon0: number,
  ) {
    this.cos = Math.cos((lat0 * Math.PI) / 180);
  }
  aLocal(lat: number, lon: number): Punto {
    return [(lon - this.lon0) * this.cos * K, (lat - this.lat0) * K];
  }
  aGeografica(x: number, y: number): { lat: number; lon: number } {
    return { lat: this.lat0 + y / K, lon: this.lon0 + x / (this.cos * K) };
  }
}

export function areaConSigno(p: Punto[]): number {
  if (p.length < 3) return 0;
  let s = 0;
  for (let i = 0; i < p.length; i++) {
    const [x1, y1] = p[i];
    const [x2, y2] = p[(i + 1) % p.length];
    s += x1 * y2 - x2 * y1;
  }
  return s / 2;
}

export const area = (p: Punto[]) => Math.abs(areaConSigno(p));

export function perimetro(p: Punto[]): number {
  let s = 0;
  for (let i = 0; i < p.length; i++) s += dist(p[i], p[(i + 1) % p.length]);
  return s;
}

export const dist = (a: Punto, b: Punto) => Math.hypot(b[0] - a[0], b[1] - a[1]);

/** Azimut a→b desde el norte, horario, en [0, 360). */
export function rumbo(a: Punto, b: Punto): number {
  const d = (Math.atan2(b[0] - a[0], b[1] - a[1]) * 180) / Math.PI;
  return (d + 360) % 360;
}

export function lados(p: Punto[]): Lado[] {
  return p.map((a, i) => {
    const b = p[(i + 1) % p.length];
    return { longitud_m: dist(a, b), rumbo_deg: rumbo(a, b) };
  });
}

/** Vértices desde el origen y los lados; el último lado cierra y se ignora si hay ≥ 3. */
export function desdeLados(origen: Punto, l: Lado[]): Punto[] {
  const usados = l.length >= 3 ? l.slice(0, -1) : l;
  const puntos: Punto[] = [origen];
  for (const lado of usados) {
    const [x, y] = puntos[puntos.length - 1];
    const r = (lado.rumbo_deg * Math.PI) / 180;
    puntos.push([x + lado.longitud_m * Math.sin(r), y + lado.longitud_m * Math.cos(r)]);
  }
  return puntos;
}

export function centroide(p: Punto[]): Punto {
  const a = areaConSigno(p);
  if (Math.abs(a) < 1e-12) {
    const n = p.length || 1;
    return [p.reduce((s, q) => s + q[0], 0) / n, p.reduce((s, q) => s + q[1], 0) / n];
  }
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < p.length; i++) {
    const [x1, y1] = p[i];
    const [x2, y2] = p[(i + 1) % p.length];
    const cruz = x1 * y2 - x2 * y1;
    cx += (x1 + x2) * cruz;
    cy += (y1 + y2) * cruz;
  }
  return [cx / (6 * a), cy / (6 * a)];
}

function orient(a: Punto, b: Punto, c: Punto) {
  return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

function seCruzan(p1: Punto, p2: Punto, p3: Punto, p4: Punto) {
  const d1 = orient(p3, p4, p1);
  const d2 = orient(p3, p4, p2);
  const d3 = orient(p1, p2, p3);
  const d4 = orient(p1, p2, p4);
  return d1 > 0 !== d2 > 0 && d3 > 0 !== d4 > 0 && [d1, d2, d3, d4].every((d) => Math.abs(d) > 1e-9);
}

export function esSimple(p: Punto[]): boolean {
  const n = p.length;
  if (n < 3) return false;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++) {
      if (Math.abs(i - j) === 1 || Math.abs(i - j) === n - 1) continue;
      if (seCruzan(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n])) return false;
    }
  return true;
}

/** Rectángulo centrado en el origen: frente sobre el lado sur, rotado por el rumbo del frente. */
export function rectangulo(frente: number, fondo: number, rumboFrenteDeg = 90, centro: Punto = [0, 0]): Punto[] {
  const r = ((rumboFrenteDeg - 90) * Math.PI) / 180;
  const base: Punto[] = [
    [-frente / 2, -fondo / 2],
    [frente / 2, -fondo / 2],
    [frente / 2, fondo / 2],
    [-frente / 2, fondo / 2],
  ];
  return base.map(([x, y]) => [
    centro[0] + x * Math.cos(r) - y * Math.sin(r),
    centro[1] + x * Math.sin(r) + y * Math.cos(r),
  ]);
}

export const fmt = (n: number, dec = 2) =>
  n.toLocaleString("es-AR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
