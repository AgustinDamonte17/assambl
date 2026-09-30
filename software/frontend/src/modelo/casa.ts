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
  | "toilette"
  | "garage"
  | "galeria"
  | "otro";

export const USOS: { id: Uso; nombre: string }[] = [
  { id: "social", nombre: "Estar / comedor" },
  { id: "cocina", nombre: "Cocina" },
  { id: "dormitorio", nombre: "Dormitorio" },
  { id: "bano", nombre: "Baño" },
  { id: "toilette", nombre: "Toilette" },
  { id: "lavadero", nombre: "Lavadero" },
  { id: "oficina", nombre: "Oficina" },
  { id: "vestidor", nombre: "Vestidor" },
  { id: "deposito", nombre: "Depósito" },
  { id: "circulacion", nombre: "Pasillo / circulación" },
  { id: "garage", nombre: "Garage" },
  { id: "galeria", nombre: "Galería" },
  { id: "otro", nombre: "Otro" },
];

export type TipoAbertura = "puerta" | "ventana" | "ventana_corrediza" | "paso" | "porton";

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
  [extra: string]: unknown;
}

export type Pieza =
  | { tipo: "muro"; id: string }
  | { tipo: "abertura"; id: string; muro: string }
  | { tipo: "ambiente"; id: string };

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

/* Asistente */

export interface AmbientePrograma {
  id: string;
  nombre: string;
  uso: Uso;
  area_m2?: number | null;
  principal?: boolean;
  notas?: string;
}

export interface Programa {
  superficie_objetivo_m2?: number | null;
  ambientes: AmbientePrograma[];
  cocina_integrada?: boolean | null;
  galeria?: boolean | null;
  garage?: boolean | null;
  dormitorios?: "juntos" | "divididos" | null;
  entrada?: "recibidor" | "directa" | null;
  prioridades?: string[];
  notas?: string[];
  [extra: string]: unknown;
}

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

export interface RespuestaAsistente {
  mensaje: string;
  pregunta: Pregunta | null;
  programa: Programa;
  listo: boolean;
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
}

export interface AnalisisPlanta {
  fundamentos?: Evaluacion | null;
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
  grupo?: string | null;
  abre_a?: string | null;
}

/* Fundamentos de diseño: conocimiento propio de Assambl (backend/assambl/fundamentos, docs/fundamentos_diseno.md) */

export type NivelObservacion = "a_favor" | "neutral" | "a_considerar" | "info";

export interface Observacion {
  fundamento: string | null;
  criterio: string | null;
  titulo: string;
  puntaje: number | null;
  nivel: NivelObservacion;
  texto: string;
  piezas: string[];
}

export interface Criterio {
  id: string;
  nombre: string;
  pregunta: string;
  puntaje: number | null;
}

export interface Evaluacion {
  criterios: Criterio[];
  observaciones: Observacion[];
  puntaje: number | null;
}

export interface Fundamento {
  id: string;
  criterio: string;
  titulo: string;
  principio: string;
  por_que: string;
  mide: string;
  tension: string;
}

export interface PlantaReferencia {
  id: string;
  nombre: string;
  archivo: string;
  superficie_m2: number;
  dormitorios: number;
  banos: number;
  garage: boolean;
  forma: string;
  rasgos: string[];
  rasgos_texto: string[];
  lectura: string;
}

export interface Alternativa {
  id: string;
  nombre: string;
  descripcion: string;
  rectangulos: Rectangulo[];
  casa: Casa;
  advertencias: string[];
  analisis: AnalisisPlanta;
  evaluacion?: Evaluacion;
  origen?: { tipo: "referencia" | "generada"; id: string; archivo?: string; superficie_m2?: number; rasgos?: string[] };
  adaptacion?: string[];
  parecido?: number;
  resumen: {
    superficie_cubierta_m2: number;
    ancho_m: number;
    profundidad_m: number;
    muro_exterior_m: number;
    ambientes: number;
  };
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
  evaluacion?: Evaluacion;
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

export function centroide(p: Punto[]): Punto {
  const n = p.length || 1;
  return [p.reduce((s, v) => s + v[0], 0) / n, p.reduce((s, v) => s + v[1], 0) / n];
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
