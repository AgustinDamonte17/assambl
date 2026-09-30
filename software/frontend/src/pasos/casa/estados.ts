/** Lenguaje visual de los estados sobre la planta (MVP_01 §4.4).
 *
 *  Tres canales redundantes para que se lea sin depender del color: relleno,
 *  trama y una insignia con glifo. Lo resuelto se ve «como un plano» (negro sólido);
 *  lo que pide atención se destaca, y lo que no se sabe todavía se ve hueco. */

import type { Estado } from "../../modelo/proyecto";
import type { AnalisisPlanta, Casa, Pieza } from "../../modelo/casa";

export interface Aspecto {
  /** Relleno del muro. */
  muro: string;
  /** Trazo del muro (solo en estados «huecos»). */
  borde?: string;
  /** Trama superpuesta al relleno (id de <pattern>). */
  trama?: "rayado" | "punteado";
  /** Tinte del ambiente. */
  ambiente: string;
  /** Color de las aberturas y de la insignia. */
  acento: string;
  /** Glifo de la insignia; sin glifo, no hay insignia. */
  glifo?: string;
  nombre: string;
  explicacion: string;
}

export const ASPECTO: Record<Estado, Aspecto> = {
  comprobado_por_reglas: {
    muro: "var(--ink)",
    ambiente: "var(--concrete-2)",
    acento: "var(--ink)",
    nombre: "Comprobado",
    explicacion: "Cumple todas las reglas que se le aplican.",
  },
  propuesto: {
    muro: "var(--rebar)",
    ambiente: "var(--concrete-2)",
    acento: "var(--rebar)",
    nombre: "Propuesto",
    explicacion: "Recién creado; todavía no se verificó.",
  },
  pendiente_datos: {
    muro: "var(--concrete-2)",
    borde: "var(--ink)",
    trama: "punteado",
    ambiente: "var(--concrete-3)",
    acento: "var(--rebar)",
    glifo: "…",
    nombre: "Faltan datos",
    explicacion: "Le falta algo para poder verificarse: una ventana, una puerta, un contorno.",
  },
  pendiente_calculo: {
    muro: "var(--warn)",
    ambiente: "color-mix(in srgb, var(--warn) 14%, var(--concrete-2))",
    acento: "var(--warn)",
    glifo: "∑",
    nombre: "Requiere cálculo",
    explicacion: "Excede lo que las reglas resuelven solas (por ejemplo, un vano muy ancho). Lo tiene que calcular un profesional.",
  },
  pendiente_revision: {
    muro: "var(--warn)",
    trama: "rayado",
    ambiente: "color-mix(in srgb, var(--warn) 10%, var(--concrete-2))",
    acento: "var(--warn)",
    glifo: "!",
    nombre: "Revisar",
    explicacion: "Lo propuso la IA o una heurística: miralo y confirmalo.",
  },
  revisado: {
    muro: "var(--ink)",
    ambiente: "color-mix(in srgb, var(--resolved) 10%, var(--concrete-2))",
    acento: "var(--resolved)",
    glifo: "✓",
    nombre: "Revisado",
    explicacion: "Lo aprobaste vos.",
  },
  desactualizado: {
    muro: "var(--signal)",
    ambiente: "color-mix(in srgb, var(--signal) 12%, var(--concrete-2))",
    acento: "var(--signal)",
    glifo: "↻",
    nombre: "Desactualizado",
    explicacion: "Estaba revisado y un cambio posterior lo invalidó.",
  },
};

export const ORDEN_ESTADOS: Estado[] = [
  "pendiente_calculo",
  "pendiente_datos",
  "pendiente_revision",
  "desactualizado",
  "propuesto",
  "comprobado_por_reglas",
  "revisado",
];

/** Estados que pone una persona o el origen de la pieza: las reglas no los pisan. */
const DECLARADOS: Estado[] = ["revisado", "desactualizado", "pendiente_revision"];

/** Estado que se muestra: lo declarado manda; si no, lo que dicen las reglas. */
export function estadoPieza(estadoGuardado: Estado | null | undefined, id: string, analisis: AnalisisPlanta | null): Estado {
  const regla = analisis?.por_pieza[id];
  // Lo que pide cálculo no se tapa con una revisión: lo tiene que resolver un profesional.
  if (regla === "pendiente_calculo") return regla;
  if (estadoGuardado && DECLARADOS.includes(estadoGuardado)) return estadoGuardado;
  return regla ?? estadoGuardado ?? "propuesto";
}

export function estadoDe(casa: Casa, pieza: Pieza, analisis: AnalisisPlanta | null): Estado {
  if (pieza.tipo === "muro") {
    const m = casa.muros.find((x) => x.id === pieza.id);
    return estadoPieza(m?.estado, pieza.id, analisis);
  }
  if (pieza.tipo === "abertura") {
    const m = casa.muros.find((x) => x.id === pieza.muro);
    const a = m?.aberturas.find((x) => x.id === pieza.id);
    return estadoPieza(a?.estado, pieza.id, analisis);
  }
  const a = casa.ambientes.find((x) => x.id === pieza.id);
  return estadoPieza(a?.estado, pieza.id, analisis);
}

/** Cuenta de piezas por estado mostrado. */
export function contarEstados(casa: Casa, analisis: AnalisisPlanta | null): Partial<Record<Estado, number>> {
  const c: Partial<Record<Estado, number>> = {};
  const sumar = (e: Estado) => (c[e] = (c[e] ?? 0) + 1);
  for (const m of casa.muros) {
    sumar(estadoPieza(m.estado, m.id, analisis));
    for (const a of m.aberturas) sumar(estadoPieza(a.estado, a.id, analisis));
  }
  for (const a of casa.ambientes) sumar(estadoPieza(a.estado, a.id, analisis));
  return c;
}

/** Piezas marcadas a revisar por su origen (IA, imagen) o invalidadas por un cambio. */
export function contarDeclaradas(casa: Casa): number {
  const d = (e?: Estado | null) => (e === "pendiente_revision" || e === "desactualizado" ? 1 : 0);
  let n = 0;
  for (const m of casa.muros) {
    n += d(m.estado);
    for (const a of m.aberturas) n += d(a.estado);
  }
  for (const a of casa.ambientes) n += d(a.estado);
  return n;
}
