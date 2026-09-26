import type { Autor, Operacion, ResultadoOperacion } from "../modelo/operaciones";
import type {
  AnalisisLote,
  CurvasNivel,
  Proyecto,
  Punto,
  RequisitosTerreno,
  RespuestaClima,
  RespuestaEscena,
  Trayectoria,
} from "../modelo/proyecto";

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!r.ok) {
    let detalle = r.statusText;
    try {
      const j = await r.json();
      detalle = typeof j.detail === "string" ? j.detail : describirErrores(j.detail);
    } catch {
      /* sin cuerpo */
    }
    throw new Error(`${r.status}: ${detalle}`);
  }
  return (await r.json()) as T;
}

/** Errores de validación de FastAPI: se muestran como «campo: motivo». */
function describirErrores(detalle: unknown): string {
  if (!Array.isArray(detalle)) return JSON.stringify(detalle);
  return detalle
    .map((e: { loc?: unknown[]; msg?: string }) => `${(e.loc ?? []).slice(-1).join(".")}: ${e.msg ?? ""}`)
    .join("; ");
}

export interface ResultadoGeo {
  nombre: string;
  lat: number;
  lon: number;
  tipo?: string;
}

export interface EstadoCredencial {
  earthdata: boolean;
  mensaje: string;
  mosaicos_en_cache: string[];
}

export const api = {
  salud: () => pedir<{ estado: string; version: string }>("/api/salud"),

  /** Nominatim: solo para encontrar un lugar en el mapa. No aporta datos al modelo. */
  geocodificar: (q: string) => pedir<ResultadoGeo[]>(`/api/geocodificar?q=${encodeURIComponent(q)}`),
  inverso: (lat: number, lon: number) =>
    pedir<{ direccion: string | null }>(`/api/geocodificar/inverso?lat=${lat}&lon=${lon}`),

  credencial: () => pedir<EstadoCredencial>("/api/terreno/credencial"),

  generarEscena: (lat: number, lon: number, margen_m: number, vertices: Punto[]) =>
    pedir<RespuestaEscena>("/api/terreno/escena", {
      method: "POST",
      body: JSON.stringify({ lat, lon, margen_m, vertices }),
    }),

  urlGlb: (ref: string) => `/api/terreno/escena/${ref}.glb`,

  curvas: (ref: string) => pedir<CurvasNivel>(`/api/terreno/escena/${ref}/curvas`),

  /** Qué falta para cerrar el terreno y pasar al diseño de la casa. */
  requisitosTerreno: (proyecto: Proyecto) =>
    pedir<RequisitosTerreno>("/api/terreno/requisitos", { method: "POST", body: JSON.stringify(proyecto) }),

  urlScriptBlender: (ref: string, fecha: string, hora: number, huso_h: number | null) => {
    const p = new URLSearchParams({ fecha, hora: String(hora) });
    if (huso_h !== null) p.set("huso_h", String(huso_h));
    return `/api/terreno/escena/${ref}.py?${p}`;
  },

  sol: (lat: number, lon: number, fecha: string, huso_h: number | null) => {
    const p = new URLSearchParams({ lat: String(lat), lon: String(lon), fecha });
    if (huso_h !== null) p.set("huso_h", String(huso_h));
    return pedir<Trayectoria>(`/api/terreno/sol?${p}`);
  },

  clima: (lat: number, lon: number, anios = 5) =>
    pedir<RespuestaClima>(`/api/clima?lat=${lat}&lon=${lon}&anios=${anios}`),

  /** Único camino para modificar el proyecto: el backend valida, aplica y devuelve el registro. */
  aplicarOperacion: (proyecto: Proyecto, operacion: Operacion, autor: Autor = "usuario") =>
    pedir<ResultadoOperacion>("/api/operaciones/aplicar", {
      method: "POST",
      body: JSON.stringify({ proyecto, operacion, autor }),
    }),

  analizarLote: (vertices: Punto[], escena_ref: string | null, margen_m: number | null) =>
    pedir<AnalisisLote>("/api/terreno/lote/analizar", {
      method: "POST",
      body: JSON.stringify({ vertices, escena_ref, margen_m }),
    }),
};
