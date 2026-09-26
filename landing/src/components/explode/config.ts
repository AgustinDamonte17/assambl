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

/**
 * Identificadores internos de capa, sin número: el número que se muestra sale del
 * orden de STEPS (orden del explode), así reordenar no obliga a renombrar el GLB.
 */
export type LayerId =
  | "techo"
  | "siding"
  | "terminaciones"
  | "aislante"
  | "estructura"
  | "electrico"
  | "interior"
  | "plomeria"
  | "cimientos"
  | "terreno";

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
const RISE_LIFT = 1.2;
const RISE: Motion = {
  range: [0.5, 0.62],
  lift: RISE_LIFT,
  ease: "inOutCubic",
};

/**
 * Tramos después de la estructura: desde el inicio de cada uno la capa pasa a ser
 * la nombrada y, dentro del tramo, se muestran o quitan las demás (LAYER_FADES).
 * El terreno queda siempre de fondo. Al subir se recorren al revés.
 */
const STAGE = {
  electrico: [0.62, 0.67],
  interior: [0.71, 0.76],
  plomeria: [0.78, 0.82],
  cimientos: [0.85, 0.89],
  terreno: [0.92, 0.96],
} as const satisfies Partial<Record<LayerId, readonly [number, number]>>;

/** Opacidad de los cimientos mientras se nombra la plomería: dejan ver las cañerías. */
const FOUNDATION_GHOST = 0.28;

/** Lo eléctrico que subió con los muros vuelve a su lugar al quedar solo. */
const SETTLE: Motion = {
  range: [STAGE.electrico[0], STAGE.electrico[1] + 0.02],
  lift: -RISE_LIFT,
  ease: "inOutCubic",
};

export const PART_RULES: readonly PartRule[] = [
  // Techo: la cubierta, el tablero y la estructura suben escalonados.
  {
    layer: "techo",
    part: "cubierta",
    motions: [{ range: [0.1, 0.24], lift: 3.1, ease: "inOutCubic" }],
  },
  {
    layer: "techo",
    part: "tablero",
    motions: [{ range: [0.12, 0.25], lift: 2.7, ease: "inOutCubic" }],
  },
  {
    layer: "techo",
    part: "estructura",
    motions: [{ range: [0.14, 0.26], lift: 2.25, ease: "inOutCubic" }],
  },

  // Siding: revestimiento y cámara de listones salen por fachada.
  {
    layer: "siding",
    part: "siding",
    motions: [{ range: [0.22, 0.34], out: 0.2, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "siding",
    part: "listones",
    motions: [{ range: [0.24, 0.35], out: 0.155, ease: "inOutCubic" }, RISE],
  },

  // Terminaciones: carpinterías, membrana y OSB por fachada; cielorraso arriba.
  {
    layer: "terminaciones",
    part: "carpinterias",
    motions: [{ range: [0.31, 0.42], out: 0.13, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "terminaciones",
    part: "wrb",
    motions: [{ range: [0.32, 0.43], out: 0.1, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "terminaciones",
    part: "osb",
    motions: [{ range: [0.34, 0.45], out: 0.065, ease: "inOutCubic" }, RISE],
  },
  {
    layer: "terminaciones",
    part: "cielorraso",
    motions: [{ range: [0.3, 0.44], lift: 1.85, ease: "inOutCubic" }],
  },
  {
    layer: "terminaciones",
    part: "revestimiento_interior",
    motions: [RISE],
  },

  // Aislante: la lana sale apenas de entre los montantes.
  {
    layer: "aislante",
    motions: [{ range: [0.42, 0.52], out: 0.032, ease: "inOutCubic" }, RISE],
  },

  // Estructura: el entramado sube con su envolvente y deja ver el interior.
  { layer: "estructura", motions: [RISE] },
  // Eléctrico: canalizaciones y luminarias viajan con los muros que las alojan
  // y bajan a su lugar cuando la estructura se va.
  { layer: "electrico", part: "redes", motions: [RISE, SETTLE] },
  { layer: "electrico", part: "luminarias", motions: [RISE, SETTLE] },
  // La acometida y la jabalina quedan en el terreno.
];

export type Fade = {
  /** Tramo de progreso en el que la opacidad va hacia `to`. */
  range: readonly [number, number];
  /** Opacidad final: 0 quita la capa, 1 la muestra, intermedio la transparenta. */
  to: number;
  ease?: EaseName;
};

/**
 * Visibilidad por capa: todas arrancan visibles y cada tramo lleva la opacidad a
 * `to`, en orden. Se evalúa desde el progreso: al subir vuelven igual.
 */
export type LayerFade = { layer: LayerId; fades: readonly Fade[] };

/** Al pasar el aislante se van el techo y toda la envolvente exterior. */
const CLEAR: Fade["range"] = [0.5, 0.57];
const EXTERIOR: readonly LayerId[] = [
  "techo",
  "siding",
  "terminaciones",
  "aislante",
];

/**
 * Mientras se despejan las capas exteriores y sube la estructura, la cámara se
 * acerca a lo que queda visible. Mismo tramo al subir, en sentido inverso.
 */
export const CAMERA_FOCUS: readonly [number, number] = [0.5, 0.62];

/** El eléctrico queda en gris un instante tras nombrarse el interior y recién ahí se va. */
const INTERIOR_CLEAR: Fade["range"] = [
  STAGE.interior[0] + 0.01,
  STAGE.interior[1],
];

export const LAYER_FADES: readonly LayerFade[] = [
  ...EXTERIOR.map((layer) => ({ layer, fades: [{ range: CLEAR, to: 0 }] })),
  // 07_Electrico: la estructura se va; el eléctrico baja sobre el interior,
  // la plomería, los cimientos y el terreno, en gris.
  { layer: "estructura", fades: [{ range: STAGE.electrico, to: 0 }] },
  // 08_Interior: se quitan el eléctrico y la plomería.
  { layer: "electrico", fades: [{ range: INTERIOR_CLEAR, to: 0 }] },
  // 09_Plomeria: vuelve la plomería, se quita el interior y los cimientos se
  // transparentan. 10_Cimientos: se va la plomería y los cimientos vuelven enteros.
  {
    layer: "plomeria",
    fades: [
      { range: INTERIOR_CLEAR, to: 0 },
      { range: STAGE.plomeria, to: 1 },
      { range: STAGE.cimientos, to: 0 },
    ],
  },
  { layer: "interior", fades: [{ range: STAGE.plomeria, to: 0 }] },
  {
    layer: "cimientos",
    fades: [
      { range: STAGE.plomeria, to: FOUNDATION_GHOST },
      { range: STAGE.cimientos, to: 1 },
      // 11_Terreno: solo queda el terreno.
      { range: STAGE.terreno, to: 0 },
    ],
  },
];

type StepDef = {
  layer: LayerId | "casa_y_terreno";
  /** Nombre sin número; el número sale de la posición en el explode. */
  name: string;
  /** View Layer de origen en angus_ranch_V11_11_capas.blend. */
  viewLayer: string;
  /** Descripción tomada de las View Layers de V11. */
  note: string;
  /** Desde qué progreso esta capa pasa a ser la nombrada. */
  from: number;
};

export type Step = StepDef & {
  /** Número de orden en el explode + nombre, p. ej. `02_Techo`. */
  label: string;
};

/** Orden en que se nombran las capas al bajar. Al subir se recorre al revés. */
const STEP_DEFS: readonly StepDef[] = [
  {
    layer: "casa_y_terreno",
    name: "Casa_y_terreno",
    viewLayer: "11_Casa_y_terreno",
    note: "Casa terminada completa sobre el terreno.",
    from: 0,
  },
  {
    layer: "techo",
    name: "Techo",
    viewLayer: "06_Techo",
    note: "Estructura, tablero y chapas de cubierta.",
    from: 0.09,
  },
  {
    layer: "siding",
    name: "Siding",
    viewLayer: "05_Siding",
    note: "Tablas, esquineros y cámara de listones, por fachada.",
    from: 0.21,
  },
  {
    layer: "terminaciones",
    name: "Terminaciones",
    viewLayer: "08_Terminaciones",
    note: "Carpinterías, membrana, OSB, cielorraso y galería.",
    from: 0.3,
  },
  {
    layer: "aislante",
    name: "Aislante",
    viewLayer: "04_Aislante",
    note: "Aislación de paredes entre montantes.",
    from: 0.42,
  },
  {
    layer: "estructura",
    name: "Estructura",
    viewLayer: "03_Estructura",
    note: "Entramado de madera: soleras, montantes y dinteles.",
    from: 0.5,
  },
  {
    layer: "electrico",
    name: "Electrico",
    viewLayer: "10_Electrico",
    note: "Instalación eléctrica y luminarias.",
    from: STAGE.electrico[0],
  },
  {
    layer: "interior",
    name: "Interior",
    viewLayer: "07_Interior",
    note: "Pisos, tabiques, puertas interiores y mobiliario.",
    from: STAGE.interior[0],
  },
  {
    layer: "plomeria",
    name: "Plomeria",
    viewLayer: "09_Plomeria",
    note: "Desagües, agua fría/caliente y pluviales con sus bajadas.",
    from: STAGE.plomeria[0],
  },
  {
    layer: "cimientos",
    name: "Cimientos",
    viewLayer: "02_Cimientos",
    note: "Platea, soleras, barrera capilar, pernos y bases.",
    from: STAGE.cimientos[0],
  },
  {
    layer: "terreno",
    name: "Terreno",
    viewLayer: "01_Terreno",
    note: "Lote de 2.500 m², alambrado y árboles.",
    from: STAGE.terreno[0],
  },
];

export const STEPS: readonly Step[] = STEP_DEFS.map((step, i) => ({
  ...step,
  label: `${String(i + 1).padStart(2, "0")}_${step.name}`,
}));

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
  { range: [0, 0.09], text: "Angus Ranch. 5.423 piezas modeladas." },
  { range: [0.5, 0.62], text: "Debajo de la envolvente, la estructura." },
  { range: [STAGE.terreno[0], 1.01], text: "Y todo empieza en el terreno." },
];

/** Resalte con --signal para la capa nombrada: sube y baja dentro de su tramo. */
export const HIGHLIGHT_FADE = 0.025;
/** Progreso en el que se apaga el último resalte (vista final estable). */
export const HIGHLIGHT_END = 0.98;
