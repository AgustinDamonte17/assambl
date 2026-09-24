/** Espejo TypeScript del esquema casa.assambl.json (backend/assambl/modelo/proyecto.py). */

export const ESQUEMA_ACTUAL = "assambl/proyecto@0.2";

export type Estado =
  | "propuesto"
  | "comprobado_por_reglas"
  | "pendiente_datos"
  | "pendiente_calculo"
  | "pendiente_revision"
  | "revisado"
  | "desactualizado";

export type EstadoFuente = "ok" | "parcial" | "pendiente_datos";

/** De dónde sale un dato. Determina con qué reservas puede presentarse. */
export type Naturaleza = "medicion_satelital" | "reanalisis_regional" | "calculo_local" | "provisional";

export type Punto = [number, number];

export const MARGEN_MIN_M = 100;
export const MARGEN_MAX_M = 2000;
export const MARGEN_POR_DEFECTO_M = 500;

export interface Ubicacion {
  lat: number;
  lon: number;
  direccion?: string | null;
  fuente: string;
  fecha?: string | null;
}

export interface SistemaLocal {
  origen_lat: number;
  origen_lon: number;
  norte: "+Y";
  unidades: "m";
  proyeccion: string;
  cota_origen_msnm?: number | null;
}

export interface Lado {
  longitud_m: number;
  rumbo_deg: number;
}

export interface Lote {
  origen: Punto;
  lados: Lado[];
  vertices: Punto[];
  area_m2?: number | null;
  perimetro_m?: number | null;
  fuente: string;
}

export interface Retiros {
  frente_m: number;
  fondo_m: number;
  laterales_m: number;
}

export interface Pendiente {
  porcentaje: number;
  direccion_deg: number;
  paso_dem_m: number;
}

export interface Terreno {
  estado: Estado;
  ubicacion: Ubicacion | null;
  margen_m: number;
  sistema_local: SistemaLocal | null;
  escena_ref: string | null;
  lote: Lote;
  retiros: Retiros;
  pendiente: Pendiente | null;
  /** Fecha y hora con las que se estudia el asoleamiento. */
  fecha_sol: string;
  hora_sol: number;
  huso_h: number | null;
}

export interface Proyecto {
  esquema: string;
  id: string;
  nombre: string;
  mercado: string;
  creado: string;
  modificado: string;
  terreno: Terreno;
}

/* Datos del sitio (caché regenerable, backend/assambl/modelo/sitio.py) */

export interface Fuente {
  nombre: string;
  url: string;
  licencia: string;
  fecha: string;
  estado: EstadoFuente;
  resolucion: string;
  naturaleza: Naturaleza;
  detalle: string;
}

export interface Relieve {
  dem: { nx: number; ny: number; paso_deg: number; huecos: number; teselas: string[]; provisional: boolean } | null;
  cota_origen_msnm: number | null;
  paso_x_m: number;
  paso_y_m: number;
  z_min_m: number;
  z_max_m: number;
  provisional: boolean;
}

export interface RespuestaEscena {
  ref: string;
  relieve: Relieve;
  fuentes: Fuente[];
  advertencias: string[];
  area_m2: number;
  pendiente_pct: number;
  pendiente_azimut_deg: number;
  posts: [number, number];
  paso_m: [number, number];
  extension_m: [number, number];
  reglas: AnalisisLote;
  bytes_glb: number;
}

/* Sol: cálculo local, distinto de la radiación histórica y de la sombra del modelo */

export interface PosicionSolar {
  momento_utc: string;
  momento_local: string;
  minuto_local: number;
  azimut_deg: number;
  elevacion_deg: number;
  elevacion_aparente_deg: number;
  sobre_horizonte: boolean;
  direccion: [number, number, number];
}

export interface EventosSolares {
  fecha: string;
  amanecer_local: string | null;
  mediodia_solar_local: string;
  atardecer_local: string | null;
  duracion_dia_h: number;
  declinacion_deg: number;
  ecuacion_tiempo_min: number;
}

export interface Procedencia {
  fuente: string;
  algoritmo?: string;
  naturaleza: Naturaleza;
  resolucion: string;
  advertencia: string;
}

export interface Trayectoria {
  algoritmo: string;
  lat: number;
  lon: number;
  fecha: string;
  huso_horario_h: number;
  paso_min: number;
  muestras: PosicionSolar[];
  eventos: EventosSolares;
  fechas_clave: Record<string, string>;
  procedencia: Procedencia;
}

/* Clima: NASA POWER */

export interface ResumenMes {
  mes: number;
  t_media_c: number | null;
  t_max_c: number | null;
  t_min_c: number | null;
  t_max_abs_c: number | null;
  t_min_abs_c: number | null;
  radiacion_kwh_m2_dia: number | null;
  viento_medio_ms: number | null;
  viento_dir_predominante_deg: number | null;
  perfil_horario_c: number[];
}

export interface SectorViento {
  desde_deg: number;
  hasta_deg: number;
  centro_deg: number;
  frecuencia_pct: number;
  por_velocidad_pct: number[];
  velocidad_media_ms: number | null;
}

export interface Clima {
  lat: number;
  lon: number;
  elevacion_power_m: number | null;
  periodo_climatologia: string;
  periodo_horario: string;
  anios_horarios: number;
  horas: number;
  meses: ResumenMes[];
  rosa: SectorViento[];
  bins_velocidad_ms: number[];
  calma_pct: number;
  grados_dia_calefaccion: number | null;
  grados_dia_refrigeracion: number | null;
  base_grados_dia_c: number;
  altura_medicion_viento_m: number;
  parametros_climatologia: Record<string, { nombre: string; unidad: string }>;
  parametros_horarios: Record<string, { nombre: string; unidad: string }>;
}

export interface RespuestaClima {
  clima: Clima;
  fuente: Fuente;
  advertencias: string[];
}

/* Resultado de R01 (backend/assambl/reglas/r01_terreno.py) */

export interface Verificacion {
  id: string;
  version: string;
  descripcion: string;
  estado: Estado;
  detalle: string;
  origen: string;
  parametros: Record<string, number>;
}

export interface AnalisisLote {
  estado: Estado;
  area_m2: number;
  perimetro_m: number;
  centroide: Punto;
  lados: Lado[];
  pendiente: Pendiente | null;
  verificaciones: Verificacion[];
}

export function ahora(): string {
  return new Date().toISOString().slice(0, 19) + "Z";
}

export function hoy(): string {
  return new Date().toISOString().slice(0, 10);
}

export function proyectoNuevo(nombre = "Casa sin nombre"): Proyecto {
  const t = ahora();
  return {
    esquema: ESQUEMA_ACTUAL,
    id: crypto.randomUUID(),
    nombre,
    mercado: "AR",
    creado: t,
    modificado: t,
    terreno: {
      estado: "pendiente_datos",
      ubicacion: null,
      margen_m: MARGEN_POR_DEFECTO_M,
      sistema_local: null,
      escena_ref: null,
      lote: { origen: [0, 0], lados: [], vertices: [], area_m2: null, perimetro_m: null, fuente: "manual" },
      retiros: { frente_m: 3, fondo_m: 3, laterales_m: 0 },
      pendiente: null,
      fecha_sol: hoy(),
      hora_sol: 12,
      huso_h: null,
    },
  };
}

export const ETIQUETA_ESTADO: Record<Estado, string> = {
  propuesto: "propuesto",
  comprobado_por_reglas: "comprobado",
  pendiente_datos: "faltan datos",
  pendiente_calculo: "requiere cálculo",
  pendiente_revision: "requiere revisión",
  revisado: "revisado",
  desactualizado: "desactualizado",
};

export const ETIQUETA_NATURALEZA: Record<Naturaleza, string> = {
  medicion_satelital: "medición satelital",
  reanalisis_regional: "estimación regional",
  calculo_local: "cálculo local",
  provisional: "provisional",
};

export const MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

export const PUNTOS_CARDINALES = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO",
];

export function cardinal(grados: number): string {
  return PUNTOS_CARDINALES[Math.round(((grados % 360) + 360) % 360 / 22.5) % 16];
}
