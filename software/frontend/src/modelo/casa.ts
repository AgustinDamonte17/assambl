/**
 * Espejo TypeScript de la sección `casa` de casa.assambl.json
 * (backend/assambl/modelo/casa.py, que es la referencia y valida las referencias cruzadas).
 * Qué significa cada campo: docs/modelo_de_la_casa.md. Caso de ejemplo: casos/angus_ranch.assambl.json.
 *
 * Metros; X este, Y norte, Z arriba; origen en la esquina suroeste de la planta
 * principal con Z = 0 en el piso terminado. Rectángulos: [x0, y0, x1, y1].
 */

import type { Estado, Punto } from "./proyecto";

export const ESQUEMA_CASA = "assambl/casa@0.1";

export type Punto3 = [number, number, number];
export type Rectangulo = [number, number, number, number];
/** [ancho en X, fondo en Y, alto], antes de aplicar el giro. */
export type Medidas = [number, number, number];
export type Paralela = "x" | "y";
export type Cardinal = "norte" | "sur" | "este" | "oeste";

/* Generales */

export interface Origen {
  fuente: string;
  version: string;
  regresion?: { piezas_madera: number; pernos_solera: number; soleras_con_anclaje_especial: number } | null;
  nota?: string;
}

export interface Implantacion {
  /** Dónde cae el origen de la casa en el sistema local del terreno. */
  origen_en_lote_m: Punto;
  giro_deg: number;
  cota_piso_sobre_terreno_m: number;
}

/* Sistemas de muro */

export type NombreCapa =
  | "terminacion_interior"
  | "entramado"
  | "aislante"
  | "osb"
  | "wrb"
  | "camara_ventilada"
  | "siding";

export interface Capa {
  capa: NombreCapa;
  material?: string | null;
  espesor_mm?: number | null;
  /** [ancho, fondo] de la escuadría, p. ej. [45, 140]. */
  seccion_mm?: [number, number] | null;
  modulo_mm?: number | null;
  placa_mm?: [number, number] | null;
  junta_mm?: number | null;
  solape_mm?: number | null;
  retorno_esquina_mm?: number | null;
  liston_mm?: [number, number] | null;
  paso_mm?: number | null;
  esquinero_mm?: number | null;
  junta_esquinero_mm?: number | null;
}

export interface Sistema {
  descripcion: string;
  espesor_arquitectonico_m: number;
  capas: Capa[];
  terminacion?: string | null;
}

export interface Parametros {
  altura_tabiques_m: number;
  esquinas: string;
  zocalo: { desde_m: number; hasta_m: number; espesor_mm: number; material: string };
  cielorraso: { cara_inferior_m: number; espesor_m: number; material: string; zonas_m: Rectangulo[] };
  solado_general: string;
}

/* Muros y aberturas */

export interface Eje {
  desde_m: Punto;
  hasta_m: Punto;
}

export type Altura = { tipo: "tabique"; cubierta?: null } | { tipo: "hasta_cubierta"; cubierta: string };

export type TipoAbertura = "ventana" | "ventana_corrediza" | "puerta" | "paso";

export interface Abertura {
  /** "<muro>/O<n>", en orden a lo largo del eje. */
  id: string;
  tipo: TipoAbertura;
  /** Desde eje.desde_m hasta la primera jamba del vano libre, medido sobre el eje. */
  posicion_m: number;
  ancho_m: number;
  antepecho_m: number;
  dintel_m: number;
  /** Solo puertas. */
  hoja?: { bisagra: "inicio" | "fin"; apertura_deg: number } | null;
}

export interface Muro {
  id: string;
  /** Clave en Casa.sistemas: "exterior", "interior_portante" o "tabique". */
  sistema: string;
  eje: Eje;
  /** Solo muros exteriores. */
  lado_exterior?: Cardinal | null;
  altura: Altura;
  aberturas: Abertura[];
}

/* Ambientes */

export type Uso = "dormitorio" | "vestidor" | "bano" | "lavadero" | "oficina" | "social" | "cocina" | "circulacion";

export interface Ambiente {
  id: string;
  nombre: string;
  uso: Uso;
  /** null mientras falte dibujarlo (estado pendiente_datos). */
  contorno_m: Punto[] | null;
  solado: string;
  estado: Estado;
  nota?: string;
}

/* Cubiertas */

export interface PlanoApoyo {
  cota_m: number;
  en_m: Punto;
  pendiente_pct: number;
  /** Azimut hacia donde sube: 0 norte, 90 este. */
  sube_hacia_deg: number;
}

export interface ApoyoIntermedio {
  tipo: "viga" | "viga_alta";
  eje_y_m: number;
  seccion_mm: [number, number];
  largo_m?: number | null;
  postes_x_m: number[];
  seccion_poste_mm: [number, number];
  estado: Estado;
  nota?: string;
}

export interface Cubierta {
  id: string;
  tipo: "un_agua" | "dos_aguas";
  material: string;
  plano_apoyo: PlanoApoyo;
  contorno_chapa_m: Rectangulo;
  chapa: { espesor_mm: number; junta_alzada_paso_m?: number | null };
  tablero?: { espesor_mm: number; contorno_m: Rectangulo; material: string } | null;
  cabios: {
    seccion_mm: [number, number];
    cantidad: number;
    desde_x_m: number;
    hasta_x_m: number;
    desde_y_m: number;
    hasta_y_m: number;
  };
  apoyos_intermedios: ApoyoIntermedio[];
  fascias?: { altura_m: number; espesor_mm: number; material: string } | null;
  nota?: string;
}

/* Cimientos y carpinterías */

export interface Cimientos {
  tipo: "platea";
  /** La platea sigue Casa.huella_m. */
  contorno: "huella";
  espesor_m: number;
  junta_bajo_solera_mm: number;
  solera_inferior: { material: string; barrera_capilar: boolean };
  pernos: {
    diametro_mm: number;
    empotramiento_mm: number;
    separacion_max_m: number;
    distancia_extremo_objetivo_m: number;
    forma: "L" | "J";
  };
  bases_postes: { dado_m: Medidas; elevacion_mm: number; tipo: string };
  estado: Estado;
  nota?: string;
}

export interface Carpinterias {
  marco: { seccion_mm: [number, number]; material: string };
  hojas_ventana: string;
  puerta: { hoja_mm: number; material: string; apertura_deg_por_defecto: number };
  alfeizar: { vuelo_m: number; material: string };
  dintel: {
    tipo: string;
    altura_m: { hasta_2_6_m: number; mayor: number };
    separadores: string;
    estado: Estado;
  };
}

/* Equipamiento */

/** Mueble o equipo: caja de medidas_m centrada en centro_m, girada giro_deg. */
export interface Elemento {
  id: string;
  tipo: string;
  ambiente?: string | null;
  centro_m: Punto;
  medidas_m: Medidas;
  giro_deg: number;
  estado?: Estado;
  nota?: string;
}

export type TipoArtefacto =
  | "inodoro"
  | "bidet"
  | "ducha"
  | "vanitory"
  | "bacha_cocina"
  | "pileta_lavadero"
  | "lavarropas";

export interface Artefacto {
  id: string;
  tipo: TipoArtefacto;
  ambiente: string;
  centro_m: Punto;
  giro_deg: number;
  /** Planta [ancho, fondo] cuando el tipo no la fija. */
  medidas_m?: [number, number] | null;
  desague: { salida_m: Punto3; dn_mm: number; grupo: string };
  agua: { fria: boolean; caliente: boolean };
}

export interface Volumen {
  centro_m: Punto;
  medidas_m: number[];
  material: string;
}

export interface Exteriores {
  galeria?: {
    cubierta: string;
    deck: { contorno_m: Rectangulo; tabla_mm: [number, number]; paso_mm: number; bastidor_alto_m: number; material: string };
    escalon: Volumen;
    equipamiento: Elemento[];
  } | null;
  sendero_entrada?: Volumen | null;
}

/* Instalaciones */

/** Algo que el proyecto todavía no decidió. */
export interface Pendiente {
  estado: Estado;
  nota?: string;
}

export interface Toma {
  id: string;
  ambiente: string;
  posicion_m: Punto3;
  circuito: string;
  /** Plano de la caja: paralelo al eje X o al eje Y. */
  paralela_a: Paralela;
}

export interface BocaLuz {
  id: string;
  ambiente: string;
  posicion_m: Punto3;
  circuito: string;
  luminaria: "plafon" | "colgante" | null;
  llave: string;
}

export interface Llave {
  id: string;
  ambiente: string;
  posicion_m: Punto3;
  paralela_a: Paralela;
}

export interface Electrica {
  tablero: { posicion_m: Punto3; medidas_m: Medidas; protecciones: string };
  acometida: { desde_m: Punto3; estado: Estado; nota?: string };
  puesta_a_tierra: { jabalina_m: Punto; hasta_cota_m: number; estado: Estado };
  altura_distribucion_m: number;
  circuitos: { id: string; uso: string; seccion_mm2: number }[];
  tomas: Toma[];
  bocas_luz: BocaLuz[];
  llaves: Llave[];
}

export interface Sanitaria {
  desague: {
    pendiente: number;
    colector_y_m: number;
    cota_eje_inicio_m: number;
    columnas: { grupo: string; x_m: number }[];
    camaras_inspeccion: { id: string; x_m: number }[];
    salida: { x_m: number; estado: Estado; nota?: string };
    ventilacion: Pendiente;
  };
  agua: {
    entrada_m: Punto3;
    colector_m: Punto;
    altura_distribucion_m: number;
    llave_general_m: Punto3;
    abastecimiento: Pendiente;
    termotanque: {
      tipo: "electrico" | "gas" | "solar";
      capacidad_l: number;
      centro_m: Punto3;
      medidas_m: Medidas;
      circuito?: string | null;
    };
  };
}

export interface Pluvial {
  canaletas: { cubierta: string; borde: Cardinal; bajada: Cardinal }[];
  seccion_mm: [number, number];
  pendiente: number;
  bajada_dn_mm: number;
  material: string;
  destino: Pendiente;
}

export interface Material {
  nombre: string;
  /** "#rrggbb" */
  color: string;
  rugosidad: number;
  metalico: number;
}

/* Casa */

export interface Casa {
  esquema: typeof ESQUEMA_CASA;
  nombre: string;
  origen?: Origen | null;
  unidades: "m";
  ejes: { x: "este"; y: "norte"; z: "arriba"; origen: string };
  implantacion: Implantacion;
  /** Contorno exterior de la planta; también es el de la platea. */
  huella_m: Punto[];
  sistemas: Record<string, Sistema>;
  parametros: Parametros;
  muros: Muro[];
  ambientes: Ambiente[];
  cubiertas: Cubierta[];
  cimientos: Cimientos;
  carpinterias: Carpinterias;
  exteriores: Exteriores;
  artefactos: Artefacto[];
  mobiliario: Elemento[];
  instalaciones: { electrica: Electrica; sanitaria: Sanitaria; pluvial: Pluvial };
  materiales: Record<string, Material>;
}

/* Utilidades de lectura: la misma geometría que usa backend/assambl/modelo/casa.py */

export function largoEje(e: Eje): number {
  return Math.hypot(e.hasta_m[0] - e.desde_m[0], e.hasta_m[1] - e.desde_m[1]);
}

/** Cota del plano de apoyo de una cubierta en (x, y). */
export function cotaPlano(p: PlanoApoyo, x: number, y: number): number {
  const az = (p.sube_hacia_deg * Math.PI) / 180;
  const avance = (x - p.en_m[0]) * Math.sin(az) + (y - p.en_m[1]) * Math.cos(az);
  return p.cota_m + (p.pendiente_pct / 100) * avance;
}

/** Tope de un muro en un punto de su eje. */
export function alturaMuro(casa: Casa, muro: Muro, x: number, y: number): number {
  if (muro.altura.tipo === "tabique") return casa.parametros.altura_tabiques_m;
  const nombre = muro.altura.cubierta;
  const cubierta = casa.cubiertas.find((c) => c.id === nombre);
  if (!cubierta) throw new Error(`El muro ${muro.id} apunta a una cubierta inexistente: ${nombre}`);
  return cotaPlano(cubierta.plano_apoyo, x, y);
}

/** Extremos de una abertura en planta, sobre el eje del muro. */
export function extremosAbertura(muro: Muro, a: Abertura): [Punto, Punto] {
  const largo = largoEje(muro.eje);
  const [x0, y0] = muro.eje.desde_m;
  const ux = (muro.eje.hasta_m[0] - x0) / largo;
  const uy = (muro.eje.hasta_m[1] - y0) / largo;
  return [
    [x0 + ux * a.posicion_m, y0 + uy * a.posicion_m],
    [x0 + ux * (a.posicion_m + a.ancho_m), y0 + uy * (a.posicion_m + a.ancho_m)],
  ];
}
