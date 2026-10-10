/** Construye la casa en 3D a partir de la planta, sin pasar por el backend: muros con sus aberturas,
 *  pisos por ambiente, galería con su deck y los muebles del catálogo.
 *
 *  Ejes: la planta usa X al este e Y al norte; three.js usa Y hacia arriba. Un punto (x, y) de la planta a
 *  altura z queda en (x, z, −y). Los muros se cortan a la altura `corte` para ver adentro, como una maqueta
 *  seccionada; arriba del corte se pinta la «cara cortada» del muro.
 *
 *  Cada malla lleva en `userData.pieza` la pieza de la planta que representa, para elegirla con el mouse. */

import * as THREE from "three";
import type { Punto } from "../../modelo/proyecto";
import {
  alturaMuros,
  contiene,
  direccion,
  espesor,
  largo,
  proyectar,
  USOS_EXTERIORES,
  type AnalisisPlanta,
  type Casa,
  type Muro,
  type Pieza,
  type PiezaInterior,
} from "../../modelo/casa";
import { COLORES, piezasInterior, primitivas } from "../../modelo/muebles";
import { estadoPieza } from "./estados";

export interface OpcionesEscena {
  /** Altura hasta la que se muestran los muros (m). */
  corte: number;
  analisis: AnalisisPlanta | null;
  seleccion: Pieza | null;
  resaltadas: Set<string>;
  /** Piezas nuevas de una propuesta de Lumo: se marcan en su color. */
  nuevas: Set<string>;
  verEstados: boolean;
  verMuebles: boolean;
}

export const COLOR_ESCENA = {
  fondo: "#e8e6e1",
  revoque: "#ebe6dc",
  siding: "#363c3f",
  corteExterior: "#c9b27a",
  corteInterior: "#d8d1c3",
  platea: "#bdb7aa",
  vidrio: "#a9c9ce",
  marco: "#2f3437",
  seleccion: "#ff4f1f",
  lumo: "#6c4dff",
  aviso: "#b45309",
  deck: "#8c6c4d",
  poste: "#6f5640",
};

const SOLADOS: Record<string, string> = {
  piso_madera: "#b98d63",
  madera: "#b98d63",
  porcelanato: "#a8b7b4",
  ceramica: "#b3bdb9",
  piso_piedra: "#cfc8b9",
  madera_exterior: COLOR_ESCENA.deck,
};

const SOLADO_POR_USO: Record<string, string> = {
  dormitorio: "piso_madera",
  oficina: "piso_madera",
  vestidor: "piso_madera",
  bano: "porcelanato",
  lavadero: "porcelanato",
  cocina: "ceramica",
  galeria: "madera_exterior",
};

export const a3 = (p: Punto, z = 0) => new THREE.Vector3(p[0], z, -p[1]);

/* ---------------------------------------------------------------- materiales */

const cache = new Map<string, THREE.Material>();

function mat(color: string, opciones: { transparente?: boolean; opacidad?: number } = {}): THREE.Material {
  const clave = `${color}|${opciones.transparente ? opciones.opacidad ?? 0.35 : 1}`;
  let m = cache.get(clave);
  if (!m) {
    m = new THREE.MeshLambertMaterial({
      color,
      transparent: !!opciones.transparente,
      opacity: opciones.transparente ? opciones.opacidad ?? 0.35 : 1,
      depthWrite: !opciones.transparente,
    });
    cache.set(clave, m);
  }
  return m;
}

let texturaDeck: THREE.CanvasTexture | null = null;

function deck(): THREE.Material {
  if (!texturaDeck) {
    const c = document.createElement("canvas");
    c.width = 64;
    c.height = 64;
    const g = c.getContext("2d")!;
    g.fillStyle = COLOR_ESCENA.deck;
    g.fillRect(0, 0, 64, 64);
    g.fillStyle = "#6f5238";
    for (let y = 0; y < 64; y += 16) g.fillRect(0, y, 64, 2);
    texturaDeck = new THREE.CanvasTexture(c);
    texturaDeck.wrapS = texturaDeck.wrapT = THREE.RepeatWrapping;
    texturaDeck.colorSpace = THREE.SRGBColorSpace;
  }
  return new THREE.MeshLambertMaterial({ map: texturaDeck });
}

/* ---------------------------------------------------------------- muros */

function prolongaciones(casa: Casa, m: Muro): [number, number] {
  const toca = (p: Punto) =>
    casa.muros.some((o) => {
      if (o.id === m.id) return false;
      const { t, dist } = proyectar(o, p);
      return dist < 0.02 && t > -0.02 && t < largo(o) + 0.02;
    });
  const e = espesor(casa, m.sistema) / 2;
  return [toca(m.eje.desde_m) ? e : 0, toca(m.eje.hasta_m) ? e : 0];
}

/** Lado derecho del eje (según su sentido) hacia afuera de la casa. */
function exteriorALaDerecha(casa: Casa, m: Muro): boolean | null {
  const huella = casa.huella_m;
  if (m.sistema !== "exterior" || !huella || huella.length < 3) return null;
  const d = direccion(m);
  const L = largo(m);
  const e = espesor(casa, m.sistema) / 2 + 0.05;
  const medio: Punto = [m.eje.desde_m[0] + (d[0] * L) / 2, m.eje.desde_m[1] + (d[1] * L) / 2];
  return !contiene(huella, medio[0] + d[1] * e, medio[1] - d[0] * e);
}

function bloque(
  m: Muro,
  t0: number,
  t1: number,
  z0: number,
  z1: number,
  e: number,
  materiales: THREE.Material | THREE.Material[],
): THREE.Mesh | null {
  if (t1 - t0 < 0.005 || z1 - z0 < 0.005) return null;
  const d = direccion(m);
  const geo = new THREE.BoxGeometry(t1 - t0, z1 - z0, e);
  const malla = new THREE.Mesh(geo, materiales);
  const tm = (t0 + t1) / 2;
  malla.position.copy(a3([m.eje.desde_m[0] + d[0] * tm, m.eje.desde_m[1] + d[1] * tm], (z0 + z1) / 2));
  malla.rotation.y = Math.atan2(d[1], d[0]);
  return malla;
}

function muro3d(casa: Casa, m: Muro, o: OpcionesEscena, H: number): THREE.Group {
  const g = new THREE.Group();
  const e = espesor(casa, m.sistema);
  const L = largo(m);
  const [pi, pf] = prolongaciones(casa, m);
  const tope = Math.min(o.corte, H);
  const derechaExt = exteriorALaDerecha(casa, m);
  const sel = o.seleccion?.id === m.id || o.resaltadas.has(m.id);
  const est = estadoPieza(m.estado, m.id, o.analisis);
  const aviso = o.verEstados && (est === "pendiente_calculo" || est === "pendiente_revision" || est === "desactualizado");
  const interior = mat(sel ? "#ffd7c9" : COLOR_ESCENA.revoque);
  const exterior = mat(sel ? "#ff8a66" : COLOR_ESCENA.siding);
  const corteColor = sel ? COLOR_ESCENA.seleccion : aviso ? "#e0a35a" : m.sistema === "exterior" ? COLOR_ESCENA.corteExterior : COLOR_ESCENA.corteInterior;
  // Caras de BoxGeometry: +x, −x, +y (arriba), −y, +z (derecha del eje), −z (izquierda).
  const caras = (cortado: boolean): THREE.Material[] => [
    interior,
    interior,
    cortado ? mat(corteColor) : interior,
    interior,
    derechaExt === true ? exterior : interior,
    derechaExt === false ? exterior : interior,
  ];

  const huecos = [...m.aberturas].sort((a, b) => a.posicion_m - b.posicion_m);
  let t = -pi;
  const agregar = (x: THREE.Object3D | null) => x && g.add(x);
  for (const ab of huecos) {
    if (ab.posicion_m > t) agregar(bloque(m, t, ab.posicion_m, 0, tope, e, caras(tope < H + 1e-6)));
    const a0 = ab.posicion_m;
    const a1 = ab.posicion_m + ab.ancho_m;
    const antepecho = ab.tipo === "ventana" ? ab.antepecho_m : 0;
    const dintel = Math.min(ab.dintel_m, H);
    // Antepecho y dintel macizos.
    if (antepecho > 0) agregar(bloque(m, a0, a1, 0, Math.min(antepecho, tope), e, caras(tope <= antepecho)));
    if (tope > dintel) agregar(bloque(m, a0, a1, dintel, tope, e, caras(true)));
    // Vidrio de ventanas y corredizas, hasta el corte.
    if (ab.tipo === "ventana" || ab.tipo === "ventana_corrediza") {
      const v = bloque(m, a0 + 0.03, a1 - 0.03, antepecho, Math.min(dintel, tope), 0.02, mat(COLOR_ESCENA.vidrio, { transparente: true, opacidad: 0.4 }));
      agregar(v);
      if (v) v.userData.pieza = { tipo: "abertura", id: ab.id, muro: m.id } satisfies Pieza;
    }
    // Hoja de la puerta, abierta a 90° como en la planta.
    if (ab.tipo === "puerta") {
      const d = direccion(m);
      const n: Punto = [-d[1], d[0]];
      const lado = (ab.hoja?.apertura_deg ?? 70) >= 0 ? 1 : -1;
      const tb = ab.hoja?.bisagra === "fin" ? a1 : a0;
      const s0 = (lado * e) / 2;
      const base: Punto = [m.eje.desde_m[0] + d[0] * tb + n[0] * s0, m.eje.desde_m[1] + d[1] * tb + n[1] * s0];
      const h = Math.min(dintel, tope) - 0.01;
      if (h > 0.05) {
        const hoja = new THREE.Mesh(new THREE.BoxGeometry(0.04, h, ab.ancho_m), mat(COLORES.madera));
        const c: Punto = [base[0] + n[0] * lado * (ab.ancho_m / 2), base[1] + n[1] * lado * (ab.ancho_m / 2)];
        hoja.position.copy(a3(c, h / 2));
        hoja.rotation.y = Math.atan2(d[1], d[0]);
        hoja.userData.pieza = { tipo: "abertura", id: ab.id, muro: m.id } satisfies Pieza;
        g.add(hoja);
      }
    }
    t = Math.max(t, a1);
  }
  if (L + pf > t) agregar(bloque(m, t, L + pf, 0, tope, e, caras(tope < H + 1e-6)));
  g.traverse((x) => {
    if (!x.userData.pieza) x.userData.pieza = { tipo: "muro", id: m.id } satisfies Pieza;
  });
  return g;
}

/* ---------------------------------------------------------------- pisos */

function forma(contorno: Punto[]): THREE.Shape {
  // La forma se dibuja en (x, y) y se acuesta con rotateX(−90°): (x, y, 0) → (x, 0, −y).
  return new THREE.Shape(contorno.map((p) => new THREE.Vector2(p[0], p[1])));
}

function losa(contorno: Punto[], z0: number, z1: number, material: THREE.Material): THREE.Mesh {
  const geo = new THREE.ExtrudeGeometry(forma(contorno), { depth: z1 - z0, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, z0, 0);
  return new THREE.Mesh(geo, material);
}

function pisos(casa: Casa, o: OpcionesEscena): THREE.Group {
  const g = new THREE.Group();
  if (casa.huella_m && casa.huella_m.length >= 3) {
    const platea = losa(casa.huella_m, -0.25, 0, mat(COLOR_ESCENA.platea));
    g.add(platea);
  }
  for (const amb of casa.ambientes) {
    if (!amb.contorno_m || amb.contorno_m.length < 3) continue;
    const exterior = USOS_EXTERIORES.includes(amb.uso);
    const sel = o.seleccion?.id === amb.id;
    let malla: THREE.Mesh;
    if (exterior) {
      const m = deck() as THREE.MeshLambertMaterial;
      malla = losa(amb.contorno_m, -0.18, -0.01, m);
      // El deck repite la textura cada 60 cm.
      const uv = malla.geometry.getAttribute("uv");
      for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / 0.6, uv.getY(i) / 0.6);
      if (sel) m.color.set("#ffb39c");
      g.add(malla);
      g.add(postes(casa, amb.contorno_m, Math.min(o.corte, alturaMuros(casa))));
    } else {
      const solado = (amb.solado as string | undefined) ?? SOLADO_POR_USO[amb.uso] ?? "piso_piedra";
      const color = sel ? "#ffc4b0" : SOLADOS[solado] ?? SOLADOS.piso_piedra;
      const geo = new THREE.ShapeGeometry(forma(amb.contorno_m));
      geo.rotateX(-Math.PI / 2);
      malla = new THREE.Mesh(geo, mat(color));
      malla.position.y = 0.004;
      g.add(malla);
    }
    malla.userData.pieza = { tipo: "ambiente", id: amb.id } satisfies Pieza;
  }
  return g;
}

/** Postes de la galería en las esquinas que no apoyan en la casa. */
function postes(casa: Casa, contorno: Punto[], alto: number): THREE.Group {
  const g = new THREE.Group();
  const huella = casa.huella_m ?? [];
  const xs = contorno.map((p) => p[0]);
  const ys = contorno.map((p) => p[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const r = 0.07;
  for (const [x, y] of [[x0 + r, y0 + r], [x1 - r, y0 + r], [x1 - r, y1 - r], [x0 + r, y1 - r]] as Punto[]) {
    const cerca = huella.length >= 3 && [[0.3, 0], [-0.3, 0], [0, 0.3], [0, -0.3]].some(([dx, dy]) => contiene(huella, x + dx, y + dy));
    if (cerca) continue;
    const poste = new THREE.Mesh(new THREE.BoxGeometry(0.14, alto, 0.14), mat(COLOR_ESCENA.poste));
    poste.position.copy(a3([x, y], alto / 2));
    g.add(poste);
  }
  return g;
}

/* ---------------------------------------------------------------- muebles */

export function mueble3d(p: PiezaInterior): THREE.Group {
  const g = new THREE.Group();
  for (const q of primitivas(p)) {
    let malla: THREE.Mesh;
    if (q.f === "caja") {
      malla = new THREE.Mesh(
        new THREE.BoxGeometry(Math.max(q.a, 0.005), Math.max(q.h, 0.005), Math.max(q.p, 0.005)),
        mat(COLORES[q.c], { transparente: q.transparente, opacidad: 0.3 }),
      );
    } else {
      malla = new THREE.Mesh(new THREE.CylinderGeometry(q.r, q.r, Math.max(q.h, 0.005), 20), mat(COLORES[q.c]));
    }
    // En la pieza: x a lo ancho, y hacia el frente. En three, el frente (+y) va hacia −Z.
    malla.position.set(q.x, q.z + q.h / 2, -q.y);
    g.add(malla);
  }
  g.position.copy(a3(p.centro_m));
  g.rotation.y = ((p.giro_deg ?? 0) * Math.PI) / 180;
  g.traverse((x) => (x.userData.pieza = { tipo: "mueble", id: p.id } satisfies Pieza));
  g.userData.raiz = p.id;
  return g;
}

function marco(objeto: THREE.Object3D, color: string): THREE.Box3Helper {
  const caja = new THREE.Box3().setFromObject(objeto).expandByScalar(0.03);
  const h = new THREE.Box3Helper(caja, new THREE.Color(color));
  (h.material as THREE.LineBasicMaterial).depthTest = false;
  h.renderOrder = 10;
  return h;
}

/* ---------------------------------------------------------------- escena */

export function construirCasa(casa: Casa, o: OpcionesEscena): THREE.Group {
  const raiz = new THREE.Group();
  const H = alturaMuros(casa);
  raiz.add(pisos(casa, o));
  for (const m of casa.muros) raiz.add(muro3d(casa, m, o, H));
  if (o.verMuebles) {
    for (const p of piezasInterior(casa)) {
      const g = mueble3d(p);
      raiz.add(g);
      // Lo que falta resolver se lista en el panel y se resalta al pasar el mouse: marcarlo siempre ensucia la vista.
      if (o.seleccion?.id === p.id || o.resaltadas.has(p.id)) raiz.add(marco(g, COLOR_ESCENA.seleccion));
      else if (o.nuevas.has(p.id)) raiz.add(marco(g, COLOR_ESCENA.lumo));
    }
  }
  return raiz;
}

export function liberar(objeto: THREE.Object3D): void {
  objeto.traverse((x) => {
    const m = x as THREE.Mesh;
    if (m.geometry) m.geometry.dispose();
  });
}

/** Centro y tamaño de la casa (incluida la galería), para encuadrar. */
export function extension3d(casa: Casa): { centro: THREE.Vector3; radio: number } {
  const pts: Punto[] = [...(casa.huella_m ?? [])];
  for (const a of casa.ambientes) if (a.contorno_m) pts.push(...a.contorno_m);
  for (const m of casa.muros) pts.push(m.eje.desde_m, m.eje.hasta_m);
  if (!pts.length) return { centro: new THREE.Vector3(), radio: 10 };
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const c: Punto = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  const radio = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) / 2;
  return { centro: a3(c, 1), radio: Math.max(radio, 3) };
}

/** Muestra la pieza movida sin reconstruir la escena (durante el arrastre). */
export function moverEnEscena(raiz: THREE.Object3D, id: string, centro: Punto): void {
  raiz.traverse((x) => {
    if (x.userData.raiz === id) x.position.copy(a3(centro));
  });
}
