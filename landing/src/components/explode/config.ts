/**
 * Coreografía del explode de Angus Ranch.
 *
 * Los nodos del GLB se llaman `<capa>__<parte>[__<fachada>]` y traen en userData
 * `layer`, `part`, `size` y, si son de envolvente, `dir` (normal de fachada en XZ).
 * Ver scripts/angus/export_glb.py.
 *
 * Cada transformación se calcula desde la posición de reposo:
 *   pos = reposo + Σ ease(tramo) · (lift·alto·Y + out·ancho·dir)
 * `lift` se expresa en alturas de muro y `out` en anchos de casa, así las distancias
 * escalan con el modelo. Nada se acumula entre frames.
 */

export const MODEL_URL = "/models/angus-ranch.glb";

export type LayerId =
  | "L01_Terreno"
  | "L02_Cimientos"
  | "L03_Estructura"
  | "L04_Aislante"
  | "L05_Siding"
  | "L06_Techo"
  | "L07_Interior"
  | "L08_Terminaciones"
  | "L09_Plomeria"
  | "L10_Electrico";

export type EaseName = "linear" | "inOutCubic" | "outCubic" | "inOutSine";

export const EASE: Record<EaseName, (t: number) => number> = {
  linear: (t) => t,
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2),
  outCubic: (t) => 1 - (1 - t) ** 3,
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
};

export type Motion = {
  /** Tramo de progreso [inicio, fin] entre 0 y 1. */
  range: readonly [number, number];
  /** Elevación, en alturas del entramado de muros. */
  lift?: number;
  /** Desplazamiento hacia afuera según la fachada del nodo, en anchos de la casa. */
  out?: number;
  /** Rotación opcional en radianes (x, y, z), sobre el pivote del nodo. */
  rotate?: readonly [number, number, number];
  ease?: EaseName;
};

export type PartRule = {
  layer: LayerId;
  /** Sin `part`, la regla aplica a todas las partes de la capa. */
  part?: string;
  motions: readonly Motion[];
};

/** Momento en que el muro con toda su envolvente sube y deja ver el interior. */
const RISE: Motion = { range: [0.5, 0.64], lift: 1.2, ease: "inOutCubic" };

export const PART_RULES: readonly PartRule[] = [
  // 06_Techo: la cubierta, el tablero y la estructura suben escalonados.
  {
    layer: "L06_Techo",
    part: "cubierta",
    motions: [{ range: [0.1, 0.24], lift: 3.1, ease: "inOutCubic" }],
  },
  {
    layer: "L06_Techo",
    part: "tablero",
    motions: [{ range: [0.12, 0.25], lift: 2.7, ease: "inOutCubic" }],
  },
  {
    layer: "L06_Techo",
    part: "estructura",
    motions: [{ range: [0.14, 0.26], lift: 2.25, ease: "inOutCubic" }],
  },

  // 05_Siding: revestimiento y cámara de listones salen por fachada.
  {
    layer: "L05_Siding",
    part: "siding",
    motions: [{ range: [0.22, 0.34], out: 0.2, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "L05_Siding",
    part: "listones",
    motions: [{ range: [0.24, 0.35], out: 0.155, ease: "inOutCubic" }, RISE],
  },

  // 08_Terminaciones: carpinterías, membrana y OSB por fachada; cielorraso arriba.
  {
    layer: "L08_Terminaciones",
    part: "carpinterias",
    motions: [{ range: [0.31, 0.42], out: 0.13, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "L08_Terminaciones",
    part: "wrb",
    motions: [{ range: [0.32, 0.43], out: 0.1, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "L08_Terminaciones",
    part: "osb",
    motions: [{ range: [0.34, 0.45], out: 0.065, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "L08_Terminaciones",
    part: "cielorraso",
    motions: [{ range: [0.3, 0.44], lift: 1.85, ease: "inOutCubic" }],
  },
  {
    layer: "L08_Terminaciones",
    part: "revestimiento_interior",
    motions: [RISE],
  },

  // 04_Aislante: la lana sale apenas de entre los montantes.
  {
    layer: "L04_Aislante",
    motions: [{ range: [0.42, 0.52], out: 0.032, ease: "inOutCubic" }, RISE],
  },

  // 03_Estructura: el entramado sube con su envolvente y deja ver el interior.
  { layer: "L03_Estructura", motions: [RISE] },
  // 10_Electrico: canalizaciones y luminarias viajan con los muros que las alojan.
  { layer: "L10_Electrico", part: "redes", motions: [RISE] },
  { layer: "L10_Electrico", part: "luminarias", motions: [RISE] },
  // La acometida y la jabalina quedan en el terreno.
];

export type Step = {
  layer: LayerId | "L11_Casa_y_terreno";
  /** Nombre de la View Layer en angus_ranch_V09_11_capas.blend. */
  label: string;
  /** Descripción tomada de las View Layers de V09. */
  note: string;
  /** Desde qué progreso esta capa pasa a ser la nombrada. */
  from: number;
};

/** Orden en que se nombran las capas al bajar. Al subir se recorre al revés. */
export const STEPS: readonly Step[] = [
  {
    layer: "L11_Casa_y_terreno",
    label: "11_Casa_y_terreno",
    note: "Casa terminada completa sobre el terreno.",
    from: 0,
  },
  {
    layer: "L06_Techo",
    label: "06_Techo",
    note: "Estructura, tablero y chapas de cubierta.",
    from: 0.09,
  },
  {
    layer: "L05_Siding",
    label: "05_Siding",
    note: "Tablas, esquineros y cámara de listones, por fachada.",
    from: 0.21,
  },
  {
    layer: "L08_Terminaciones",
    label: "08_Terminaciones",
    note: "Carpinterías, membrana, OSB y cielorraso.",
    from: 0.3,
  },
  {
    layer: "L04_Aislante",
    label: "04_Aislante",
    note: "Aislación de paredes entre montantes.",
    from: 0.42,
  },
  {
    layer: "L03_Estructura",
    label: "03_Estructura",
    note: "Entramado de madera: soleras, montantes y dinteles.",
    from: 0.5,
  },
  {
    layer: "L10_Electrico",
    label: "10_Electrico",
    note: "Instalación eléctrica y luminarias.",
    from: 0.62,
  },
  {
    layer: "L07_Interior",
    label: "07_Interior",
    note: "Pisos, tabiques, puertas interiores y mobiliario.",
    from: 0.7,
  },
  {
    layer: "L09_Plomeria",
    label: "09_Plomeria",
    note: "Desagües y agua fría/caliente.",
    from: 0.77,
  },
  {
    layer: "L02_Cimientos",
    label: "02_Cimientos",
    note: "Platea, soleras, barrera capilar, pernos y bases.",
    from: 0.84,
  },
  {
    layer: "L01_Terreno",
    label: "01_Terreno",
    note: "Lote de 2.500 m², alambrado y árboles.",
    from: 0.91,
  },
];

/** Orden de la lista visible: numeración de V09. */
export const LAYER_INDEX: readonly Step[] = [...STEPS].sort((a, b) =>
  a.label.localeCompare(b.label),
);

export function stepAt(progress: number): number {
  let index = 0;
  for (let i = 0; i < STEPS.length; i++)
    if (progress >= STEPS[i].from) index = i;
  return index;
}

/** Textos breves ligados a los momentos principales (máximo tres). */
export const CAPTIONS: readonly {
  range: readonly [number, number];
  text: string;
}[] = [
  { range: [0, 0.09], text: "Angus Ranch. 5.393 piezas modeladas." },
  { range: [0.5, 0.7], text: "Debajo de la envolvente, la estructura." },
  { range: [0.91, 1.01], text: "Todas las capas, a la vista." },
];

/** Resalte con --signal para la capa nombrada: sube y baja dentro de su tramo. */
export const HIGHLIGHT_FADE = 0.025;
/** Progreso en el que se apaga el último resalte (vista explotada estable). */
export const HIGHLIGHT_END = 0.97;
