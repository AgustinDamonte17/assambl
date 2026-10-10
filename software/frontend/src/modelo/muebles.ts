/** Muebles y artefactos: catálogo, geometría de la huella y forma de cada pieza.
 *
 *  El catálogo es el mismo `backend/assambl/catalogo/ar.json` que usan las reglas y el amoblado
 *  automático, importado tal cual: no hay una segunda lista que pueda desincronizarse.
 *
 *  Cada pieza se dibuja con pocas cajas y cilindros (`primitivas`). La planta 2D las proyecta desde
 *  arriba y la vista 3D las levanta: las dos muestran exactamente el mismo mueble. */

import catalogoAr from "assambl-software/backend/assambl/catalogo/ar.json";
import type { Punto } from "./proyecto";
import type { Casa, PiezaInterior, Uso } from "./casa";

export interface ItemMueble {
  codigo: string;
  nombre: string;
  categoria: string;
  familia: "mueble" | "artefacto";
  medidas_m: [number, number, number];
  forma: string;
  apoyo: "muro" | "esquina" | "libre";
  frente_libre_m: number;
  exterior: boolean;
  interior: boolean;
  usos?: Uso[];
  sugerido_para?: Uso[];
  grupo?: string;
  elevacion_m?: number;
  sillas?: number;
  nota?: string;
}

export const CATALOGO_MUEBLES: ItemMueble[] = (catalogoAr as unknown as { familias: { mobiliario: { items: ItemMueble[] } } })
  .familias.mobiliario.items;

const POR_CODIGO = new Map(CATALOGO_MUEBLES.map((i) => [i.codigo, i]));

export function itemMueble(codigo: string): ItemMueble | null {
  return POR_CODIGO.get(codigo) ?? null;
}

export const CATEGORIAS: { id: string; nombre: string }[] = [
  { id: "estar", nombre: "Estar" },
  { id: "comedor", nombre: "Comedor" },
  { id: "cocina", nombre: "Cocina" },
  { id: "dormitorio", nombre: "Dormitorio" },
  { id: "bano", nombre: "Baño" },
  { id: "lavadero", nombre: "Lavadero" },
  { id: "oficina", nombre: "Oficina" },
  { id: "galeria", nombre: "Galería" },
  { id: "deco", nombre: "Deco" },
];

export function nombrePieza(p: PiezaInterior): string {
  return itemMueble(p.tipo)?.nombre ?? p.tipo.replace(/_/g, " ");
}

export function listaDe(codigo: string): "mobiliario" | "artefactos" {
  return itemMueble(codigo)?.familia === "artefacto" ? "artefactos" : "mobiliario";
}

/** Todas las piezas de la casa, muebles y artefactos. */
export function piezasInterior(casa: Casa): PiezaInterior[] {
  return [...(casa.mobiliario ?? []), ...(casa.artefactos ?? [])];
}

export function buscarPieza(casa: Casa, id: string): PiezaInterior | null {
  return piezasInterior(casa).find((p) => p.id === id) ?? null;
}

export function medidas(p: PiezaInterior): [number, number, number] {
  const it = itemMueble(p.tipo);
  const m = (p.medidas_m && p.medidas_m.length >= 2 ? p.medidas_m : it?.medidas_m) ?? [0.6, 0.6, 0.9];
  return [m[0], m[1], m[2] ?? it?.medidas_m[2] ?? 0.9];
}

/** Rectángulo que ocupa en planta: [x0, y0, x1, y1]. */
export function huella(p: PiezaInterior): [number, number, number, number] {
  const [a, f] = medidas(p);
  const g = ((p.giro_deg ?? 0) * Math.PI) / 180;
  const c = Math.abs(Math.cos(g));
  const s = Math.abs(Math.sin(g));
  const w = a * c + f * s;
  const d = a * s + f * c;
  return [p.centro_m[0] - w / 2, p.centro_m[1] - d / 2, p.centro_m[0] + w / 2, p.centro_m[1] + d / 2];
}

/** De coordenadas de la pieza (x a lo ancho, y hacia el frente) a la planta. */
export function aPlanta(p: PiezaInterior, x: number, y: number): Punto {
  const g = ((p.giro_deg ?? 0) * Math.PI) / 180;
  const c = Math.cos(g);
  const s = Math.sin(g);
  return [p.centro_m[0] + x * c - y * s, p.centro_m[1] + x * s + y * c];
}

/** Espacio de uso delante de la pieza, como polígono en planta. */
export function zonaFrente(p: PiezaInterior): Punto[] | null {
  const it = itemMueble(p.tipo);
  if (!it || !it.frente_libre_m || it.apoyo === "libre") return null;
  const [a, f] = medidas(p);
  const d = it.frente_libre_m;
  return [aPlanta(p, -a / 2, f / 2), aPlanta(p, a / 2, f / 2), aPlanta(p, a / 2, f / 2 + d), aPlanta(p, -a / 2, f / 2 + d)];
}

/* ---------------------------------------------------------------- materiales */

export const COLORES = {
  madera: "#ad7950",
  maderaClara: "#c9a477",
  tela: "#6b7a55",
  telaClara: "#8c9873",
  lino: "#d9cdb3",
  blanco: "#efede6",
  ceramica: "#f6f4ef",
  piedra: "#e3ded2",
  acero: "#b6bbbe",
  negro: "#25292c",
  follaje: "#587049",
  terracota: "#b4643f",
  vidrio: "#bcd6d9",
  agua: "#9ec0c6",
  ladrillo: "#9a5a3d",
  gris: "#8e8a80",
} as const;

export type Color = keyof typeof COLORES;

/** Caja o cilindro en coordenadas de la pieza: x a lo ancho, y hacia el frente, z desde el piso. */
export type Primitiva =
  | { f: "caja"; x: number; y: number; z: number; a: number; p: number; h: number; c: Color; transparente?: boolean }
  | { f: "cil"; x: number; y: number; z: number; r: number; h: number; c: Color };

const caja = (x: number, y: number, z: number, a: number, p: number, h: number, c: Color, transparente = false): Primitiva =>
  ({ f: "caja", x, y, z, a, p, h, c, transparente });
const cil = (x: number, y: number, z: number, r: number, h: number, c: Color): Primitiva => ({ f: "cil", x, y, z, r, h, c });

function patas(a: number, p: number, h: number, g = 0.05, c: Color = "madera"): Primitiva[] {
  const dx = a / 2 - g;
  const dy = p / 2 - g;
  return [
    caja(-dx, -dy, 0, g, g, h, c),
    caja(dx, -dy, 0, g, g, h, c),
    caja(-dx, dy, 0, g, g, h, c),
    caja(dx, dy, 0, g, g, h, c),
  ];
}

/** Forma de la pieza a partir de su tipo y medidas. Lo desconocido se dibuja como una caja. */
export function primitivas(pz: PiezaInterior): Primitiva[] {
  const it = itemMueble(pz.tipo);
  const [a, p, h] = medidas(pz);
  const forma = it?.forma ?? "caja";
  const atras = -p / 2;
  switch (forma) {
    case "sofa":
    case "sillon": {
      const brazo = Math.min(0.18, a * 0.15);
      return [
        caja(0, 0.04, 0, a, p - 0.08, 0.42, "tela"),
        caja(0, atras + 0.11, 0.42, a - 2 * brazo, 0.22, h - 0.42, "tela"),
        caja(-a / 2 + brazo / 2, 0, 0, brazo, p, 0.62, "tela"),
        caja(a / 2 - brazo / 2, 0, 0, brazo, p, 0.62, "tela"),
        caja(0, 0.08, 0.42, a - 2 * brazo - 0.04, p - 0.36, 0.08, "telaClara"),
      ];
    }
    case "sofa_l": {
      const prof = 0.92;
      return [
        caja(0, atras + prof / 2, 0, a, prof, 0.42, "tela"),
        caja(a / 2 - prof / 2, atras + prof + (p - prof) / 2, 0, prof, p - prof, 0.42, "tela"),
        caja(0, atras + 0.11, 0.42, a, 0.22, h - 0.42, "tela"),
        caja(-a / 2 + 0.09, atras + prof / 2, 0, 0.18, prof, 0.62, "tela"),
        caja(-0.05, atras + prof / 2 + 0.1, 0.42, a - 0.4, prof - 0.36, 0.08, "telaClara"),
      ];
    }
    case "mesa_baja":
      return [caja(0, 0, h - 0.05, a, p, 0.05, "maderaClara"), ...patas(a, p, h - 0.05)];
    case "mueble_tv":
      return [
        caja(0, 0, 0, a, p, 0.5, "madera"),
        caja(0, atras + 0.06, 0.55, a * 0.72, 0.05, Math.max(h - 0.6, 0.3), "negro"),
        caja(0, atras + 0.08, 0.5, 0.25, 0.12, 0.05, "negro"),
      ];
    case "estanteria":
      return [
        caja(0, atras + 0.02, 0, a, 0.04, h, "madera"),
        caja(-a / 2 + 0.02, 0, 0, 0.04, p, h, "madera"),
        caja(a / 2 - 0.02, 0, 0, 0.04, p, h, "madera"),
        ...[0, 1, 2, 3, 4].map((i) => caja(0, 0, (h - 0.04) * (i / 4), a - 0.08, p, 0.04, "madera")),
        ...[0, 1, 2, 3].map((i) =>
          caja(((i % 2) - 0.5) * a * 0.3, 0, (h - 0.04) * (i / 4) + 0.04, a * 0.45, p * 0.75, (h / 4) * 0.7,
            (["terracota", "tela", "lino", "gris"] as Color[])[i]),
        ),
      ];
    case "alfombra":
      return [caja(0, 0, 0, a, p, 0.015, "lino")];
    case "planta":
      return [cil(0, 0, 0, a * 0.32, 0.4, "terracota"), cil(0, 0, 0.4, a * 0.5, h - 0.4, "follaje")];
    case "lampara":
      return [cil(0, 0, 0, 0.14, 0.03, "negro"), cil(0, 0, 0.03, 0.015, h - 0.3, "negro"), cil(0, 0, h - 0.3, a * 0.5, 0.3, "lino")];
    case "mesa":
      return [caja(0, 0, h - 0.04, a, p, 0.04, "maderaClara"), ...patas(a, p, h - 0.04, 0.06)];
    case "mesa_redonda":
      return [cil(0, 0, h - 0.04, a / 2, 0.04, "maderaClara"), cil(0, 0, 0, 0.05, h - 0.04, "madera"), cil(0, 0, 0, 0.25, 0.03, "madera")];
    case "silla": {
      const asiento = 0.45;
      return [
        caja(0, 0.02, asiento - 0.04, a, p - 0.04, 0.04, "madera"),
        ...patas(a, p - 0.04, asiento - 0.04, 0.035),
        caja(0, atras + 0.03, asiento, a, 0.04, h - asiento, "madera"),
      ];
    }
    case "banqueta":
      return [cil(0, 0, h - 0.04, a / 2, 0.04, "madera"), cil(0, 0, 0, 0.025, h - 0.04, "negro"), cil(0, 0, 0, a * 0.4, 0.02, "negro")];
    case "aparador":
    case "comoda":
    case "mesa_luz":
      return [caja(0, 0, 0.08, a, p, h - 0.08, "madera"), caja(0, 0, 0, a - 0.06, p - 0.06, 0.08, "negro"), caja(0, p / 2 - 0.005, h * 0.55, a - 0.04, 0.01, 0.01, "negro")];
    case "bajo_mesada":
    case "isla":
      return [
        caja(0, -0.01, 0.1, a, p - 0.04, h - 0.14, forma === "isla" ? "madera" : "blanco"),
        caja(0, 0, 0, a - 0.04, p - 0.1, 0.1, "negro"),
        caja(0, 0, h - 0.04, a, p, 0.04, "piedra"),
      ];
    case "mesada_bacha":
      return [
        caja(0, -0.01, 0.1, a, p - 0.04, h - 0.14, "blanco"),
        caja(0, 0, 0, a - 0.04, p - 0.1, 0.1, "negro"),
        caja(0, 0, h - 0.04, a, p, 0.04, "piedra"),
        caja(0, 0.03, h - 0.02, Math.min(0.55, a - 0.2), p * 0.62, 0.025, "acero"),
        cil(0, atras + 0.08, h, 0.02, 0.28, "acero"),
      ];
    case "cocina_anafe":
      return [
        caja(0, -0.01, 0.1, a, p - 0.04, h - 0.14, "blanco"),
        caja(0, 0, 0, a - 0.04, p - 0.1, 0.1, "negro"),
        caja(0, 0, h - 0.04, a, p, 0.04, "piedra"),
        caja(0, 0, h - 0.01, a * 0.9, p * 0.85, 0.015, "negro"),
        caja(0, p / 2 - 0.02, 0.18, a * 0.85, 0.02, 0.5, "negro"),
      ];
    case "electro_bajo":
      return [caja(0, 0, 0, a, p, h, "blanco"), caja(0, p / 2 - 0.005, h * 0.42, a * 0.55, 0.01, a * 0.55, "acero")];
    case "heladera":
      return [caja(0, 0, 0, a, p, h, "acero"), caja(0, p / 2 - 0.005, h * 0.62, a - 0.04, 0.01, 0.01, "negro"), caja(a / 2 - 0.08, p / 2, h * 0.4, 0.02, 0.03, 0.4, "negro")];
    case "alacena": {
      const z = it?.elevacion_m ?? 1.5;
      return [caja(0, 0, z, a, p, h, "blanco"), caja(0, p / 2 - 0.005, z + 0.04, 0.01, 0.01, h - 0.08, "gris")];
    }
    case "cama": {
      const colchon = 0.3;
      const almohada = Math.min(0.5, a / 2 - 0.08);
      const partes: Primitiva[] = [
        caja(0, 0.03, 0, a, p - 0.06, colchon, "madera"),
        caja(0, 0.04, colchon, a - 0.04, p - 0.1, 0.2, "blanco"),
        caja(0, 0.04 + (p - 0.1) * 0.18, colchon + 0.2, a - 0.02, (p - 0.1) * 0.6, 0.05, "tela"),
        caja(0, atras + 0.03, 0, a + 0.04, 0.06, h, "madera"),
      ];
      const n = a > 1.2 ? 2 : 1;
      for (let i = 0; i < n; i++) {
        const x = n === 1 ? 0 : (i === 0 ? -1 : 1) * (a / 4);
        partes.push(caja(x, atras + 0.3, colchon + 0.2, almohada * (n === 1 ? 1.2 : 1), 0.32, 0.1, "lino"));
      }
      return partes;
    }
    case "placard": {
      const hojas = Math.max(2, Math.round(a / 0.6));
      return [
        caja(0, 0, 0, a, p, h, "maderaClara"),
        ...Array.from({ length: hojas - 1 }, (_, i) => caja(-a / 2 + (a * (i + 1)) / hojas, p / 2 - 0.004, 0.05, 0.008, 0.008, h - 0.1, "madera")),
      ];
    }
    case "cuna":
      return [
        caja(0, 0, 0.3, a, p, 0.12, "blanco"),
        caja(0, atras + 0.02, 0, a, 0.04, h, "blanco"),
        caja(0, p / 2 - 0.02, 0, a, 0.04, h, "blanco"),
        caja(-a / 2 + 0.02, 0, 0.42, 0.04, p, h - 0.42, "blanco"),
        caja(a / 2 - 0.02, 0, 0.42, 0.04, p, h - 0.42, "blanco"),
      ];
    case "inodoro":
      return [caja(0, atras + 0.09, 0, a, 0.18, h, "ceramica"), cil(0, 0.08, 0, a * 0.42, 0.4, "ceramica"), caja(0, atras + 0.25, 0.35, a * 0.6, 0.18, 0.06, "ceramica")];
    case "bidet":
      return [cil(0, 0.04, 0, a * 0.45, h, "ceramica"), caja(0, atras + 0.08, 0, a * 0.6, 0.16, h, "ceramica")];
    case "vanitory":
      return [
        caja(0, 0, 0.12, a, p, h - 0.17, "madera"),
        caja(0, 0, h - 0.05, a, p, 0.05, "ceramica"),
        cil(0, 0.04, h - 0.03, Math.min(a, p) * 0.32, 0.04, "agua"),
        cil(0, atras + 0.06, h, 0.02, 0.22, "acero"),
      ];
    case "ducha":
      return [
        caja(0, 0, 0, a, p, 0.05, "ceramica"),
        caja(0, p / 2 - 0.01, 0.05, a, 0.015, Math.min(h, 2.0) - 0.05, "vidrio", true),
        caja(a / 2 - 0.01, 0, 0.05, 0.015, p, Math.min(h, 2.0) - 0.05, "vidrio", true),
        cil(-a / 2 + 0.12, atras + 0.12, 1.8, 0.1, 0.02, "acero"),
      ];
    case "banera":
      return [caja(0, 0, 0, a, p, h, "ceramica"), caja(0, 0, h - 0.01, a - 0.12, p - 0.12, 0.015, "agua")];
    case "pileta":
      return [caja(0, 0, 0, a, p, h - 0.25, "blanco"), caja(0, 0, h - 0.25, a, p, 0.25, "ceramica"), caja(0, 0.03, h - 0.02, a - 0.12, p - 0.16, 0.025, "agua")];
    case "termotanque":
      return [cil(0, 0, 0.1, a / 2, h - 0.1, "blanco"), cil(0, 0, 0, a * 0.3, 0.1, "gris")];
    case "escritorio":
      return [
        caja(0, 0, h - 0.04, a, p, 0.04, "maderaClara"),
        caja(-a / 2 + 0.03, 0, 0, 0.04, p - 0.04, h - 0.04, "maderaClara"),
        caja(a / 2 - 0.03, 0, 0, 0.04, p - 0.04, h - 0.04, "maderaClara"),
        caja(0, atras + 0.12, h, 0.55, 0.04, 0.34, "negro"),
      ];
    case "silla_escritorio":
      return [cil(0, 0, 0, a * 0.4, 0.05, "negro"), cil(0, 0, 0.05, 0.03, 0.38, "negro"), caja(0, 0.03, 0.43, a * 0.8, p * 0.75, 0.07, "gris"), caja(0, atras + 0.08, 0.5, a * 0.75, 0.06, h - 0.5, "gris")];
    case "reposera":
      return [caja(0, 0.15, 0.18, a, p - 0.3, 0.08, "lino"), ...patas(a, p - 0.3, 0.18, 0.04), caja(0, atras + 0.2, 0.18, a, 0.4, h * 1.4, "lino")];
    case "banco":
      return [caja(0, 0, h - 0.05, a, p, 0.05, "madera"), caja(-a / 2 + 0.15, 0, 0, 0.06, p - 0.06, h - 0.05, "madera"), caja(a / 2 - 0.15, 0, 0, 0.06, p - 0.06, h - 0.05, "madera")];
    case "parrilla":
      return [
        caja(0, 0, 0, a, p, 0.9, "ladrillo"),
        caja(0, 0.05, 0.9, a - 0.1, p - 0.15, 0.05, "negro"),
        caja(-a / 2 + 0.06, 0, 0.95, 0.12, p, 0.7, "ladrillo"),
        caja(a / 2 - 0.06, 0, 0.95, 0.12, p, 0.7, "ladrillo"),
        caja(0, -0.05, 1.65, a, p - 0.1, 0.45, "ladrillo"),
        caja(0, atras + 0.25, 2.1, 0.4, 0.4, Math.max(h - 2.1, 0.3), "ladrillo"),
      ];
    default:
      return [caja(0, 0, 0, a, p, h, "gris")];
  }
}
