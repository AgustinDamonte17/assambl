import type {
  AnalisisPlanta,
  Casa,
  Decisiones,
  EstadoIA,
  RespuestaImagen,
  RespuestaLumo,
  ItemCatalogo,
  MensajeChat,
  PiezaInterior,
  Pregunta,
} from "../modelo/casa";
import type { Accion } from "../pasos/casa/acciones";
import type { AnalisisLote, Punto, RespuestaClima, RespuestaEscena, Trayectoria } from "../modelo/proyecto";

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!r.ok) {
    let detalle = r.statusText;
    try {
      const j = await r.json();
      detalle = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* sin cuerpo */
    }
    throw new Error(`${r.status}: ${detalle}`);
  }
  return (await r.json()) as T;
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

  analizarLote: (vertices: Punto[], escena_ref: string | null, margen_m: number | null) =>
    pedir<AnalisisLote>("/api/terreno/lote/analizar", {
      method: "POST",
      body: JSON.stringify({ vertices, escena_ref, margen_m }),
    }),

  /* Capa 03 · Casa */
  estadoIA: () => pedir<EstadoIA>("/api/casa/ia"),

  catalogo: () =>
    pedir<{ familias: { aberturas: { items: ItemCatalogo[] } } }>("/api/casa/catalogo").then(
      (c) => c.familias.aberturas.items,
    ),

  /** Un turno con Lumo. `texto` es lo que se escribió en vez de tocar una opción. */
  lumo: (decisiones: Decisiones, texto: string, lat: number | null, cambio: keyof Decisiones | null = null) =>
    pedir<RespuestaLumo>("/api/casa/lumo", {
      method: "POST",
      body: JSON.stringify({ decisiones, texto, lat, cambio }),
    }),

  /** Un pedido en palabras dentro del editor: vuelve con acciones para ejecutar o con una pregunta. */
  lumoEditar: (texto: string, contexto: unknown, historial: { rol: "usuario" | "asistente"; texto: string }[]) =>
    pedir<{ mensaje: string; pregunta?: Pregunta | null; acciones: Accion[]; simulado: boolean }>("/api/casa/lumo/editar", {
      method: "POST",
      body: JSON.stringify({ texto, contexto, historial }),
    }),

  interpretarImagen: (imagen: string, notas: string, ancho_total_m: number | null, lat: number | null) =>
    pedir<RespuestaImagen>("/api/casa/interpretar-imagen", {
      method: "POST",
      body: JSON.stringify({ imagen, notas, ancho_total_m, lat }),
    }),

  analizarPlanta: (casa: Casa) =>
    pedir<AnalisisPlanta>("/api/casa/analizar", { method: "POST", body: JSON.stringify({ casa }) }),

  /* Interior: muebles, galería y Lumo en la vista 3D */
  amoblar: (casa: Casa, ambientes: string[] | null = null, reemplazar = false) =>
    pedir<{ casa: Casa; notas: string[]; analisis: AnalisisPlanta }>("/api/casa/amoblar", {
      method: "POST",
      body: JSON.stringify({ casa, ambientes, reemplazar }),
    }),

  colocar: (casa: Casa, codigo: string, ambiente: string) =>
    pedir<{ casa: Casa; pieza: PiezaInterior | null; motivo: string }>("/api/casa/colocar", {
      method: "POST",
      body: JSON.stringify({ casa, codigo, ambiente }),
    }),

  galeria: (casa: Casa, lado: string | null, fondo_m: number, lat: number | null) =>
    pedir<{ casa: Casa; galeria: string; notas: string[] }>("/api/casa/galeria", {
      method: "POST",
      body: JSON.stringify({ casa, lado, fondo_m, lat }),
    }),

  conversarInterior: (casa: Casa, historial: MensajeChat[], lat: number | null) =>
    pedir<RespuestaInterior>("/api/casa/interior/conversar", {
      method: "POST",
      body: JSON.stringify({ casa, historial, lat }),
    }),
};

export interface RespuestaInterior {
  mensaje: string;
  operaciones: { tipo: string; [k: string]: unknown }[];
  casa: Casa;
  /** Cambios de muros que la interfaz aplica con el editor de planta. */
  pendientes: { tipo: "mover_muro"; muro: string; delta_m: number }[];
  notas: string[];
  simulado: boolean;
  analisis: AnalisisPlanta;
}
