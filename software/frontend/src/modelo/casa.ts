/** Espejo TypeScript de la capa 03 · Casa (backend/assambl/modelo/casa.py, esquema assambl/casa@0.1).
 *  La casa lleva secciones de otras capas (cubiertas, instalaciones, mobiliario) que el editor
 *  de planta no toca: por eso los tipos admiten campos extra y las operaciones copian el resto. */

import type { Estado, Punto } from "./proyecto";

export type Uso =
  | "social"
  | "cocina"
  | "dormitorio"
  | "bano"
  | "lavadero"
  | "oficina"
  | "vestidor"
  | "deposito"
  | "circulacion"
  | "galeria"
  | "otro";

export const USOS: { id: Uso; nombre: string }[] = [
  { id: "social", nombre: "Estar / comedor" },
  { id: "cocina", nombre: "Cocina" },
  { id: "dormitorio", nombre: "Dormitorio" },
  { id: "bano", nombre: "Baño" },
  { id: "lavadero", nombre: "Lavadero" },
  { id: "oficina", nombre: "Oficina" },
  { id: "vestidor", nombre: "Vestidor" },
  { id: "deposito", nombre: "Depósito" },
  { id: "circulacion", nombre: "Pasillo / circulación" },
  { id: "galeria", nombre: "Galería (exterior)" },
  { id: "otro", nombre: "Otro" },
];

/** Ambientes exteriores: piso y techo sin muros. No suman a la superficie cubierta cerrada. */
export const USOS_EXTERIORES: Uso[] = ["galeria"];

export type TipoAbertura = "puerta" | "ventana" | "ventana_corrediza" | "paso";

export interface Abertura {
  id: string;
  tipo: TipoAbertura;
  /** Distancia desde el inicio del eje hasta el borde de la abertura. */
  posicion_m: number;
  ancho_m: number;
  antepecho_m: number;
  dintel_m: number;
  catalogo?: string | null;
  hoja?: { bisagra: "inicio" | "fin"; apertura_deg: number };
  estado?: Estado | null;
  revision?: { fecha: string } | null;
  [extra: string]: unknown;
}

export interface Muro {
  id: string;
  sistema: string;
  eje: { desde_m: Punto; hasta_m: Punto };
  aberturas: Abertura[];
  lado_exterior?: string;
  altura?: unknown;
  estado?: Estado | null;
  revision?: { fecha: string } | null;
  [extra: string]: unknown;
}

export interface Ambiente {
  id: string;
  nombre: string;
  uso: Uso;
  contorno_m: Punto[] | null;
  estado?: Estado | null;
  revision?: { fecha: string } | null;
  [extra: string]: unknown;
}

export interface Sistema {
  descripcion: string;
  espesor_arquitectonico_m: number;
  [extra: string]: unknown;
}

/** Mueble o artefacto ubicado (`casa.mobiliario` o `casa.artefactos`). `tipo` es el código del catálogo.
 *  `medidas_m` = [ancho, fondo, alto] en el sistema de la pieza; con `giro_deg` = 0 la espalda mira al sur
 *  (−Y) y el frente al norte (+Y); el giro es antihorario. */
export interface PiezaInterior {
  id: string;
  tipo: string;
  ambiente?: string | null;
  centro_m: Punto;
  medidas_m?: number[] | null;
  giro_deg: number;
  estado?: Estado | null;
  origen?: string;
  revision?: { fecha: string } | null;
  [extra: string]: unknown;
}

export interface Casa {
  esquema: string;
  nombre: string;
  origen?: Record<string, unknown>;
  unidades: "m";
  implantacion?: { origen_en_lote_m: Punto; giro_deg: number; cota_piso_sobre_terreno_m?: number };
  huella_m?: Punto[];
  sistemas: Record<string, Sistema>;
  muros: Muro[];
  ambientes: Ambiente[];
  mobiliario?: PiezaInterior[];
  artefactos?: PiezaInterior[];
  parametros?: { altura_tabiques_m?: number; [extra: string]: unknown };
  [extra: string]: unknown;
}

export type Pieza =
  | { tipo: "muro"; id: string }
  | { tipo: "abertura"; id: string; muro: string }
  | { tipo: "ambiente"; id: string }
  | { tipo: "mueble"; id: string };

/* Catálogo (backend/assambl/catalogo/ar.json) */

export interface ItemCatalogo {
  codigo: string;
  tipo: TipoAbertura;
  nombre: string;
  ancho_m: number;
  alto_m: number;
  antepecho_m: number;
  uso: "interior" | "exterior";
  sugerida_para: Uso[];
}

/* Lumo */

/** Lo que el usuario decide con Lumo. Lo que falta se completa con el valor más común. */
export interface Decisiones {
  dormitorios: number | null;
  cocina: "abierta" | "cerrada" | null;
  tamano: "compacta" | "comoda" | "amplia" | null;
}

export const SIN_DECISIONES: Decisiones = { dormitorios: null, cocina: null, tamano: null };

export interface Opcion {
  id: string;
  etiqueta: string;
  detalle?: string;
}

export interface Pregunta {
  texto: string;
  opciones: Opcion[];
  multiple?: boolean;
  importante?: boolean;
}

export interface MensajeChat {
  rol: "usuario" | "asistente";
  texto: string;
}

/** La planta base para las decisiones tomadas hasta ahora, con el porqué de su orden. */
export interface Propuesta {
  decisiones: Decisiones;
  rectangulos: Rectangulo[];
  casa: Casa;
  advertencias: string[];
  razones: { titulo: string; texto: string }[];
  analisis: AnalisisPlanta;
  resumen: {
    superficie_cubierta_m2: number;
    ancho_m: number;
    profundidad_m: number;
    muro_exterior_m: number;
    ambientes: number;
  };
}

export interface RespuestaLumo {
  mensaje: string;
  pregunta: Pregunta | null;
  decisiones: Decisiones;
  listo: boolean;
  propuesta: Propuesta | null;
}

export interface EstadoIA {
  proveedor: string;
  modelo: string;
  vision: boolean;
  simulado: boolean;
  motivo?: string;
  url_base?: string;
}

/* Reglas R03 */

export interface VerificacionPlanta {
  id: string;
  version: string;
  descripcion: string;
  estado: Estado;
  detalle: string;
  origen: string;
  parametros: Record<string, number>;
  piezas: string[];
  /** «grave»: a la casa le falta algo que no puede faltar. «sugerencia»: algo para mirar, no un error. */
  gravedad?: "grave" | "sugerencia";
}

export interface AnalisisPlanta {
  estado: Estado;
  verificaciones: VerificacionPlanta[];
  por_pieza: Record<string, Estado>;
  resumen: Partial<Record<Estado, number>>;
  version: string;
}

export interface Rectangulo {
  id: string;
  nombre: string;
  uso: Uso;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  /** Rectángulos del mismo grupo forman un solo ambiente. */
  grupo?: string | null;
}

export interface RespuestaImagen {
  lectura: {
    resumen: string;
    escala: { fuente: string; detalle: string };
    confianza: number;
    recuadro_imagen: { x0: number; y0: number; x1: number; y1: number } | null;
    advertencias: string[];
    preguntas: Pregunta[];
  };
  rectangulos: Rectangulo[];
  casa: Casa;
  advertencias: string[];
  analisis: AnalisisPlanta;
  simulado: boolean;
}

/* Geometría de muros */

export const ESPESOR_POR_DEFECTO: Record<string, number> = { exterior: 0.2, interior_portante: 0.2, tabique: 0.15 };

export function espesor(casa: Casa, sistema: string): number {
  return casa.sistemas?.[sistema]?.espesor_arquitectonico_m ?? ESPESOR_POR_DEFECTO[sistema] ?? 0.15;
}

export function largo(m: Muro): number {
  const [x0, y0] = m.eje.desde_m;
  const [x1, y1] = m.eje.hasta_m;
  return Math.hypot(x1 - x0, y1 - y0);
}

/** Vector unitario del eje (de desde a hasta). */
export function direccion(m: Muro): Punto {
  const l = largo(m) || 1;
  return [(m.eje.hasta_m[0] - m.eje.desde_m[0]) / l, (m.eje.hasta_m[1] - m.eje.desde_m[1]) / l];
}

export function puntoEnMuro(m: Muro, t: number): Punto {
  const d = direccion(m);
  return [m.eje.desde_m[0] + d[0] * t, m.eje.desde_m[1] + d[1] * t];
}

/** Proyección de un punto sobre el eje: distancia a lo largo y distancia perpendicular. */
export function proyectar(m: Muro, p: Punto): { t: number; dist: number } {
  const d = direccion(m);
  const vx = p[0] - m.eje.desde_m[0];
  const vy = p[1] - m.eje.desde_m[1];
  const t = vx * d[0] + vy * d[1];
  const dist = Math.abs(vx * -d[1] + vy * d[0]);
  return { t, dist };
}

export function esHorizontal(m: Muro): boolean {
  return Math.abs(m.eje.desde_m[1] - m.eje.hasta_m[1]) < 1e-6;
}

export function esVertical(m: Muro): boolean {
  return Math.abs(m.eje.desde_m[0] - m.eje.hasta_m[0]) < 1e-6;
}

export function areaPoligono(p: Punto[]): number {
  let s = 0;
  for (let i = 0; i < p.length; i++) {
    const [x1, y1] = p[i];
    const [x2, y2] = p[(i + 1) % p.length];
    s += x1 * y2 - x2 * y1;
  }
  return Math.abs(s) / 2;
}

/** Centro de área del polígono (no el promedio de vértices, que en un ambiente en L cae sobre un borde). */
export function centroide(p: Punto[]): Punto {
  let a = 0;
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < p.length; i++) {
    const [x1, y1] = p[i];
    const [x2, y2] = p[(i + 1) % p.length];
    const f = x1 * y2 - x2 * y1;
    a += f;
    cx += (x1 + x2) * f;
    cy += (y1 + y2) * f;
  }
  if (Math.abs(a) < 1e-9) {
    const n = p.length || 1;
    return [p.reduce((s, v) => s + v[0], 0) / n, p.reduce((s, v) => s + v[1], 0) / n];
  }
  return [cx / (3 * a), cy / (3 * a)];
}

export function extension(casa: Casa): { x0: number; y0: number; x1: number; y1: number } | null {
  const pts: Punto[] = [];
  for (const m of casa.muros) pts.push(m.eje.desde_m, m.eje.hasta_m);
  for (const a of casa.ambientes) if (a.contorno_m) pts.push(...a.contorno_m);
  for (const p of casa.huella_m ?? []) pts.push(p);
  if (!pts.length) return null;
  return {
    x0: Math.min(...pts.map((p) => p[0])),
    y0: Math.min(...pts.map((p) => p[1])),
    x1: Math.max(...pts.map((p) => p[0])),
    y1: Math.max(...pts.map((p) => p[1])),
  };
}

export function buscarAbertura(casa: Casa, id: string): { muro: Muro; abertura: Abertura } | null {
  for (const m of casa.muros) {
    const a = m.aberturas.find((o) => o.id === id);
    if (a) return { muro: m, abertura: a };
  }
  return null;
}

export function superficieCubierta(casa: Casa): number | null {
  return casa.huella_m && casa.huella_m.length >= 3 ? areaPoligono(casa.huella_m) : null;
}

/** Superficie de galerías (exterior, techada). */
export function superficieGaleria(casa: Casa): number {
  return casa.ambientes
    .filter((a) => USOS_EXTERIORES.includes(a.uso) && a.contorno_m && a.contorno_m.length >= 3)
    .reduce((s, a) => s + areaPoligono(a.contorno_m!), 0);
}

export function contiene(poly: Punto[], x: number, y: number): boolean {
  let dentro = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dentro = !dentro;
  }
  return dentro;
}

/** Altura de los muros (piso terminado a cielorraso). */
export function alturaMuros(casa: Casa): number {
  return casa.parametros?.altura_tabiques_m ?? 2.6;
}

export function casaVacia(nombre = "Casa"): Casa {
  return {
    esquema: "assambl/casa@0.1",
    nombre,
    origen: { fuente: "dibujo libre" },
    unidades: "m",
    implantacion: { origen_en_lote_m: [0, 0], giro_deg: 0, cota_piso_sobre_terreno_m: 0.2 },
    huella_m: [],
    sistemas: {
      exterior: { descripcion: "Muro exterior woodframe 45 × 140", espesor_arquitectonico_m: 0.2 },
      interior_portante: { descripcion: "Tabique portante 45 × 140", espesor_arquitectonico_m: 0.2 },
      tabique: { descripcion: "Tabique no portante 45 × 90", espesor_arquitectonico_m: 0.15 },
    },
    muros: [],
    ambientes: [],
  };
}
