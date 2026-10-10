/** Acciones de Lumo sobre la planta: «ampliar este ambiente», «integrar la cocina», «mover la entrada».
 *
 *  Cada acción es una decisión de diseño expresada con las operaciones de `operaciones.ts`. Lumo las elige
 *  (a partir de lo que escribe el usuario, o para resolver un problema de la lista) y acá se ejecutan: nadie
 *  escribe geometría por su cuenta. Son todo o nada: si una acción no se puede hacer, la planta no cambia y
 *  el motivo se le cuenta al usuario. */

import type { Punto } from "../../modelo/proyecto";
import {
  areaPoligono,
  buscarAbertura,
  esHorizontal,
  esVertical,
  espesor,
  largo,
  superficieCubierta,
  type Ambiente,
  type Casa,
  type ItemCatalogo,
  type Muro,
  type Pieza,
  type Uso,
} from "../../modelo/casa";
import {
  agregarAbertura,
  agregarAmbiente,
  borrarAbertura,
  borrarAmbiente,
  borrarMuro,
  entraAbertura,
  modificarAbertura,
  modificarAmbiente,
  moverMuro,
  redondear,
} from "./operaciones";

export type Lado = "norte" | "sur" | "este" | "oeste";
export const LADOS: Lado[] = ["norte", "sur", "este", "oeste"];

export interface Accion {
  tipo:
    | "ampliar"
    | "mover_muro"
    | "quitar_muro"
    | "integrar"
    | "renombrar"
    | "quitar_ambiente"
    | "crear_ambiente"
    | "agregar_abertura"
    | "quitar_abertura"
    | "cambiar_abertura"
    | "acomodar_abertura"
    | "mover_entrada";
  ambiente?: string | null;
  destino?: string | null;
  lado?: Lado | null;
  metros?: number | null;
  muro?: string | null;
  abertura?: string | null;
  catalogo?: string | null;
  clase?: "ventana" | "puerta" | "puerta_ventana" | null;
  nombre?: string | null;
  uso?: Uso | null;
  contorno?: Punto[] | null;
}

/** Lo que no se puede hacer se dice con un mensaje para el usuario. */
class NoSePuede extends Error {}

const TOLERANCIA = 0.16; // un contorno está a medio muro del eje: hasta 10 cm en un exterior

/* ---------------------------------------------------------------- lectura de la planta */

interface Borde {
  lado: Lado;
  fijo: number;
  a: number;
  b: number;
}

function areaConSigno(p: Punto[]): number {
  let s = 0;
  for (let i = 0; i < p.length; i++) s += p[i][0] * p[(i + 1) % p.length][1] - p[(i + 1) % p.length][0] * p[i][1];
  return s / 2;
}

/** Lados del contorno con hacia dónde miran. Solo los tramos a 90°. */
function bordes(contorno: Punto[]): Borde[] {
  const antihorario = areaConSigno(contorno) >= 0;
  const salida: Borde[] = [];
  for (let i = 0; i < contorno.length; i++) {
    const p = contorno[i];
    const q = contorno[(i + 1) % contorno.length];
    const dx = q[0] - p[0];
    const dy = q[1] - p[1];
    if (Math.abs(dx) < 1e-6 && Math.abs(dy) > 1e-6) {
      // Subiendo con el interior a la izquierda, este tramo es el borde este.
      const lado: Lado = dy > 0 === antihorario ? "este" : "oeste";
      salida.push({ lado, fijo: p[0], a: Math.min(p[1], q[1]), b: Math.max(p[1], q[1]) });
    } else if (Math.abs(dy) < 1e-6 && Math.abs(dx) > 1e-6) {
      const lado: Lado = dx > 0 === antihorario ? "sur" : "norte";
      salida.push({ lado, fijo: p[1], a: Math.min(p[0], q[0]), b: Math.max(p[0], q[0]) });
    }
  }
  return salida;
}

/** Un muro que corre junto a un lado del ambiente, y qué tramo de su eje (desde el inicio) lo acompaña. */
export interface Toque {
  muro: Muro;
  lado: Lado;
  t0: number;
  t1: number;
}

export function murosDe(casa: Casa, amb: Ambiente): Toque[] {
  if (!amb.contorno_m || amb.contorno_m.length < 3) return [];
  const salida: Toque[] = [];
  for (const b of bordes(amb.contorno_m)) {
    const vertical = b.lado === "este" || b.lado === "oeste";
    for (const m of casa.muros) {
      if (vertical ? !esVertical(m) : !esHorizontal(m)) continue;
      const fijo = vertical ? m.eje.desde_m[0] : m.eje.desde_m[1];
      if (Math.abs(fijo - b.fijo) > TOLERANCIA) continue;
      const ini = vertical ? m.eje.desde_m[1] : m.eje.desde_m[0];
      const fin = vertical ? m.eje.hasta_m[1] : m.eje.hasta_m[0];
      const lo = Math.max(b.a, Math.min(ini, fin));
      const hi = Math.min(b.b, Math.max(ini, fin));
      if (hi - lo <= 0.3) continue;
      const [t0, t1] = ini <= fin ? [lo - ini, hi - ini] : [ini - hi, ini - lo];
      salida.push({ muro: m, lado: b.lado, t0, t1 });
    }
  }
  return salida;
}

export interface Vecino {
  ambiente: Ambiente;
  muro: Muro;
  lado: Lado;
  /** Tramo del muro que comparten los dos ambientes. */
  t0: number;
  t1: number;
}

export function vecinosDe(casa: Casa, amb: Ambiente): Vecino[] {
  const propios = murosDe(casa, amb);
  const salida: Vecino[] = [];
  for (const otro of casa.ambientes) {
    if (otro.id === amb.id) continue;
    for (const o of murosDe(casa, otro)) {
      for (const p of propios) {
        if (p.muro.id !== o.muro.id) continue;
        const t0 = Math.max(p.t0, o.t0);
        const t1 = Math.min(p.t1, o.t1);
        if (t1 - t0 > 0.3) salida.push({ ambiente: otro, muro: p.muro, lado: p.lado, t0, t1 });
      }
    }
  }
  return salida;
}

function caja(contorno: Punto[]) {
  const xs = contorno.map((p) => p[0]);
  const ys = contorno.map((p) => p[1]);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}

function ambienteDe(casa: Casa, id: string | null | undefined): Ambiente {
  const a = casa.ambientes.find((x) => x.id === id);
  if (!a) throw new NoSePuede(id ? `No encuentro el ambiente «${id}».` : "No sé de qué ambiente me hablás: elegilo en la planta.");
  if (!a.contorno_m || a.contorno_m.length < 3) throw new NoSePuede(`«${a.nombre}» todavía no tiene contorno dibujado.`);
  return a;
}

function muroDe(casa: Casa, id: string | null | undefined): Muro {
  const m = casa.muros.find((x) => x.id === id);
  if (!m) throw new NoSePuede(`No encuentro el muro «${id ?? ""}».`);
  return m;
}

const metros = (v: number) => `${Math.abs(v).toFixed(2).replace(/\.?0+$/, "").replace(".", ",")} m`;

/* ---------------------------------------------------------------- ambientes */

function ampliar(casa: Casa, a: Accion): Paso {
  const amb = ambienteDe(casa, a.ambiente);
  const lado = a.lado;
  if (!lado) throw new NoSePuede("Me falta saber hacia qué lado.");
  const cuanto = a.metros ?? 1;
  const c = caja(amb.contorno_m!);
  const medida = lado === "norte" || lado === "sur" ? c.y1 - c.y0 : c.x1 - c.x0;
  if (medida + cuanto < 0.8) throw new NoSePuede(`«${amb.nombre}» mide ${metros(medida)} en ese sentido: no lo puedo achicar tanto.`);
  const deEseLado = murosDe(casa, amb).filter((t) => t.lado === lado);
  if (!deEseLado.length) throw new NoSePuede(`«${amb.nombre}» no tiene un muro del lado ${lado}: de ese lado está abierto a otro ambiente.`);
  // Si el ambiente tiene varios tramos mirando a ese lado, se corre el de más afuera.
  const coord = (m: Muro) => (lado === "norte" || lado === "sur" ? m.eje.desde_m[1] : m.eje.desde_m[0]);
  const afuera = lado === "norte" || lado === "este" ? Math.max(...deEseLado.map((t) => coord(t.muro))) : Math.min(...deEseLado.map((t) => coord(t.muro)));
  const ids = [...new Set(deEseLado.filter((t) => Math.abs(coord(t.muro) - afuera) < 0.2).map((t) => t.muro.id))];
  const delta = (lado === "norte" || lado === "este" ? 1 : -1) * cuanto;
  let nueva = casa;
  for (const id of ids) nueva = moverMuro(nueva, id, delta);
  const antes = areaPoligono(amb.contorno_m!);
  const despues = areaPoligono(nueva.ambientes.find((x) => x.id === amb.id)!.contorno_m!);
  const otros = casa.ambientes.filter((o) => {
    if (o.id === amb.id || !o.contorno_m) return false;
    const n = nueva.ambientes.find((x) => x.id === o.id);
    return !!n?.contorno_m && Math.abs(areaPoligono(n.contorno_m) - areaPoligono(o.contorno_m)) > 0.05;
  });
  return {
    casa: nueva,
    seleccion: { tipo: "ambiente", id: amb.id },
    nota:
      `«${amb.nombre}» pasa de ${antes.toFixed(1)} a ${despues.toFixed(1)} m².` +
      (otros.length ? ` También cambia${otros.length > 1 ? "n" : ""} ${otros.map((o) => `«${o.nombre}»`).join(", ")}.` : ""),
  };
}

/** Deja de un muro solo lo que queda fuera del tramo [t0, t1]. */
function abrirTramo(casa: Casa, m: Muro, t0: number, t1: number): Casa {
  const L = largo(m);
  if (t0 <= 0.3 && L - t1 <= 0.3) return borrarMuro(casa, m.id);
  const d: Punto = [(m.eje.hasta_m[0] - m.eje.desde_m[0]) / L, (m.eje.hasta_m[1] - m.eje.desde_m[1]) / L];
  const en = (t: number): Punto => [redondear(m.eje.desde_m[0] + d[0] * t, 0.005), redondear(m.eje.desde_m[1] + d[1] * t, 0.005)];
  const partes: Muro[] = [];
  if (t0 > 0.3) {
    partes.push({ ...m, eje: { desde_m: m.eje.desde_m, hasta_m: en(t0) }, aberturas: m.aberturas.filter((o) => o.posicion_m + o.ancho_m <= t0), estado: "propuesto" });
  }
  if (L - t1 > 0.3) {
    const usados = new Set(casa.muros.map((x) => x.id));
    let id = partes.length ? `${m.id}_b` : m.id;
    while (partes.length && usados.has(id)) id += "b";
    partes.push({
      ...m,
      id,
      eje: { desde_m: en(t1), hasta_m: m.eje.hasta_m },
      aberturas: m.aberturas.filter((o) => o.posicion_m >= t1).map((o) => ({ ...o, id: o.id.replace(m.id, id), posicion_m: redondear(o.posicion_m - t1, 0.005) })),
      estado: "propuesto",
    });
  }
  return { ...casa, muros: casa.muros.flatMap((x) => (x.id === m.id ? partes : [x])) };
}

/** Contorno de la unión de varios polígonos a 90° (y rectángulos de relleno), recorriendo el borde de las
 *  celdas ocupadas sobre la grilla que forman sus coordenadas. */
export function unirContornos(poligonos: Punto[][]): Punto[] | null {
  const juntar = (vs: number[]) => {
    const orden = [...vs].sort((a, b) => a - b);
    const salida: number[] = [];
    for (const v of orden) if (!salida.length || v - salida[salida.length - 1] > 0.02) salida.push(v);
    return salida;
  };
  const xs = juntar(poligonos.flatMap((p) => p.map((v) => v[0])));
  const ys = juntar(poligonos.flatMap((p) => p.map((v) => v[1])));
  const dentroDe = (p: Punto[], x: number, y: number) => {
    let d = false;
    for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
      if (p[i][1] > y !== p[j][1] > y && x < ((p[j][0] - p[i][0]) * (y - p[i][1])) / (p[j][1] - p[i][1]) + p[i][0]) d = !d;
    }
    return d;
  };
  const ocupada = (i: number, j: number) => {
    if (i < 0 || j < 0 || i >= xs.length - 1 || j >= ys.length - 1) return false;
    const cx = (xs[i] + xs[i + 1]) / 2;
    const cy = (ys[j] + ys[j + 1]) / 2;
    return poligonos.some((p) => dentroDe(p, cx, cy));
  };
  const clave = (p: Punto) => `${p[0]},${p[1]}`;
  const siguiente = new Map<string, [Punto, Punto]>();
  for (let i = 0; i < xs.length; i++) {
    for (let j = 0; j < ys.length - 1; j++) {
      const izq = ocupada(i - 1, j);
      const der = ocupada(i, j);
      if (izq === der) continue;
      const [p, q]: [Punto, Punto] = der ? [[xs[i], ys[j + 1]], [xs[i], ys[j]]] : [[xs[i], ys[j]], [xs[i], ys[j + 1]]];
      siguiente.set(clave(p), [p, q]);
    }
  }
  for (let j = 0; j < ys.length; j++) {
    for (let i = 0; i < xs.length - 1; i++) {
      const abajo = ocupada(i, j - 1);
      const arriba = ocupada(i, j);
      if (abajo === arriba) continue;
      const [p, q]: [Punto, Punto] = arriba ? [[xs[i], ys[j]], [xs[i + 1], ys[j]]] : [[xs[i + 1], ys[j]], [xs[i], ys[j]]];
      siguiente.set(clave(p), [p, q]);
    }
  }
  let mejor: Punto[] | null = null;
  while (siguiente.size) {
    const [k0, [p0, q0]] = siguiente.entries().next().value as [string, [Punto, Punto]];
    siguiente.delete(k0);
    const lazo: Punto[] = [p0];
    let q = q0;
    while (clave(q) !== k0 && siguiente.has(clave(q))) {
      lazo.push(q);
      const [, s] = siguiente.get(clave(q))!;
      siguiente.delete(clave(q));
      q = s;
    }
    if (!mejor || Math.abs(areaConSigno(lazo)) > Math.abs(areaConSigno(mejor))) mejor = lazo;
  }
  if (!mejor) return null;
  const lazo = mejor;
  const limpio = lazo.filter((b, i) => {
    const a = lazo[(i - 1 + lazo.length) % lazo.length];
    const c = lazo[(i + 1) % lazo.length];
    return Math.abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9;
  });
  return limpio.length >= 4 ? limpio.map((p) => [redondear(p[0], 0.005), redondear(p[1], 0.005)] as Punto) : null;
}

function integrar(casa: Casa, a: Accion): Paso {
  let origen = ambienteDe(casa, a.ambiente);
  let destino = ambienteDe(casa, a.destino);
  if (origen.id === destino.id) throw new NoSePuede("Necesito dos ambientes distintos para integrarlos.");
  // El estar absorbe a la cocina, no al revés.
  if (destino.uso === "cocina" && origen.uso === "social") [origen, destino] = [destino, origen];
  const compartidos = vecinosDe(casa, origen).filter((v) => v.ambiente.id === destino.id);
  if (!compartidos.length) throw new NoSePuede(`«${origen.nombre}» y «${destino.nombre}» no comparten ningún muro: no son vecinos.`);
  let nueva = casa;
  const relleno: Punto[][] = [];
  // De atrás hacia adelante en cada muro, para que abrir un tramo no corra los que faltan.
  for (const v of [...compartidos].sort((p, q) => q.t0 - p.t0)) {
    const m = nueva.muros.find((x) => x.id === v.muro.id);
    if (!m) continue;
    // El hueco que deja el muro pasa a ser parte del ambiente.
    const e = espesor(casa, m.sistema) / 2 + 0.03;
    const L = largo(v.muro);
    const d: Punto = [(v.muro.eje.hasta_m[0] - v.muro.eje.desde_m[0]) / L, (v.muro.eje.hasta_m[1] - v.muro.eje.desde_m[1]) / L];
    const en = (t: number, s: number): Punto => [v.muro.eje.desde_m[0] + d[0] * t - d[1] * s, v.muro.eje.desde_m[1] + d[1] * t + d[0] * s];
    relleno.push([en(v.t0, -e), en(v.t1, -e), en(v.t1, e), en(v.t0, e)]);
    nueva = abrirTramo(nueva, m, v.t0, v.t1);
  }
  const contorno = unirContornos([destino.contorno_m!, origen.contorno_m!, ...relleno]);
  if (!contorno) throw new NoSePuede("No pude unir los dos contornos; probá borrando el muro a mano.");
  const sumaCocina = origen.uso === "cocina" && destino.uso === "social" && !/cocina/i.test(destino.nombre);
  // «Estar y comedor» + cocina = «Estar, comedor y cocina».
  const nombre = a.nombre?.trim() || (sumaCocina ? `${destino.nombre.replace(/ y (?!.* y )/, ", ")} y cocina` : destino.nombre);
  nueva = borrarAmbiente(nueva, origen.id);
  nueva = modificarAmbiente(nueva, destino.id, { contorno_m: contorno, nombre });
  return {
    casa: nueva,
    seleccion: { tipo: "ambiente", id: destino.id },
    nota: `Saqué el muro entre «${origen.nombre}» y «${destino.nombre}»: ahora son un solo ambiente de ${areaPoligono(contorno).toFixed(1)} m².`,
  };
}

/* ---------------------------------------------------------------- aberturas */

const VENTANAS: Partial<Record<Uso, string[]>> = {
  social: ["ventana_200_110", "ventana_150_110", "ventana_100_110"],
  dormitorio: ["ventana_150_110", "ventana_100_110"],
  oficina: ["ventana_150_110", "ventana_100_110"],
  bano: ["ventiluz_060_040"],
};
const VENTANA_GENERICA = ["ventana_100_110", "ventiluz_060_040"];
const PREFERENCIA_PUERTA: Partial<Record<Uso, number>> = { circulacion: 0, social: 1, cocina: 2 };

/** Posición libre más cercana a la deseada dentro de un tramo del muro, o null si no entra. */
function ubicar(muro: Muro, ancho: number, t0: number, t1: number, deseada: number, ignorar?: string): number | null {
  const lo = Math.max(t0 + 0.05, 0.1);
  const hi = Math.min(t1 - 0.05, largo(muro) - 0.1) - ancho;
  if (hi < lo - 1e-6) return null;
  const centro = Math.min(Math.max(deseada, lo), hi);
  for (let d = 0; d <= hi - lo + 0.05; d += 0.05) {
    for (const pos of d === 0 ? [centro] : [centro - d, centro + d]) {
      if (pos >= lo - 1e-6 && pos <= hi + 1e-6 && entraAbertura(muro, redondear(pos), ancho, ignorar)) return redondear(pos);
    }
  }
  return null;
}

function items(catalogo: ItemCatalogo[], codigos: string[]): ItemCatalogo[] {
  return codigos.map((c) => catalogo.find((i) => i.codigo === c)).filter((i): i is ItemCatalogo => !!i);
}

function agregarAberturaEn(casa: Casa, a: Accion, catalogo: ItemCatalogo[]): Paso {
  const amb = ambienteDe(casa, a.ambiente);
  const clase = a.clase ?? "ventana";
  if (clase === "puerta") {
    let candidatos = vecinosDe(casa, amb).filter((v) => v.muro.sistema !== "exterior");
    if (a.destino) {
      candidatos = candidatos.filter((v) => v.ambiente.id === a.destino);
      if (!candidatos.length) throw new NoSePuede(`«${amb.nombre}» no comparte un muro con ese ambiente.`);
    } else {
      const sinBano = candidatos.filter((v) => v.ambiente.uso !== "bano");
      candidatos = (sinBano.length ? sinBano : candidatos).sort(
        (p, q) => (PREFERENCIA_PUERTA[p.ambiente.uso] ?? 3) - (PREFERENCIA_PUERTA[q.ambiente.uso] ?? 3) || q.t1 - q.t0 - (p.t1 - p.t0),
      );
    }
    if (a.lado) candidatos = candidatos.filter((v) => v.lado === a.lado);
    if (!candidatos.length) throw new NoSePuede(`«${amb.nombre}» no linda con otro ambiente por donde entrar.`);
    const opciones = items(catalogo, amb.uso === "bano" || amb.uso === "deposito" ? ["puerta_070", "puerta_080"] : ["puerta_080", "puerta_070"]);
    for (const v of candidatos) {
      for (const it of opciones) {
        const pos = ubicar(v.muro, it.ancho_m, v.t0, v.t1, v.t0 + 0.15);
        if (pos === null) continue;
        const r = agregarAbertura(casa, v.muro.id, it, pos);
        return { casa: r.casa, seleccion: { tipo: "abertura", id: r.id, muro: v.muro.id }, nota: `Puse una ${it.nombre.toLowerCase()} entre «${amb.nombre}» y «${v.ambiente.nombre}».` };
      }
    }
    throw new NoSePuede(`No encontré lugar para una puerta en los muros de «${amb.nombre}».`);
  }

  let tramos = murosDe(casa, amb).filter((t) => t.muro.sistema === "exterior");
  if (!tramos.length) throw new NoSePuede(`«${amb.nombre}» no tiene ningún muro exterior: no le puedo poner una ventana. Podés ampliarlo hasta el borde de la casa o integrarlo a un ambiente que sí tenga.`);
  if (a.lado) {
    tramos = tramos.filter((t) => t.lado === a.lado);
    if (!tramos.length) throw new NoSePuede(`«${amb.nombre}» no tiene muro exterior del lado ${a.lado}.`);
  }
  tramos.sort((p, q) => q.t1 - q.t0 - (p.t1 - p.t0));
  const codigos = a.catalogo ? [a.catalogo] : clase === "puerta_ventana" ? ["corrediza_200_205"] : [...(VENTANAS[amb.uso] ?? []), ...VENTANA_GENERICA];
  for (const t of tramos) {
    for (const it of items(catalogo, codigos)) {
      const pos = ubicar(t.muro, it.ancho_m, t.t0, t.t1, (t.t0 + t.t1 - it.ancho_m) / 2);
      if (pos === null) continue;
      const r = agregarAbertura(casa, t.muro.id, it, pos);
      return { casa: r.casa, seleccion: { tipo: "abertura", id: r.id, muro: t.muro.id }, nota: `Puse una ${it.nombre.toLowerCase()} en el muro ${t.lado} de «${amb.nombre}».` };
    }
  }
  throw new NoSePuede(`No encontré lugar para una ventana en los muros exteriores de «${amb.nombre}».`);
}

function cambiarAbertura(casa: Casa, a: Accion, catalogo: ItemCatalogo[]): Paso {
  const h = a.abertura ? buscarAbertura(casa, a.abertura) : null;
  if (!h) throw new NoSePuede(`No encuentro la abertura «${a.abertura ?? ""}».`);
  const it = catalogo.find((i) => i.codigo === a.catalogo);
  if (!it) throw new NoSePuede(`«${a.catalogo ?? ""}» no está en el catálogo.`);
  const { muro, abertura: o } = h;
  const pos = ubicar(muro, it.ancho_m, 0, largo(muro), o.posicion_m + (o.ancho_m - it.ancho_m) / 2, o.id);
  if (pos === null) throw new NoSePuede(`No entra una ${it.nombre.toLowerCase()} en ese muro.`);
  const nueva = modificarAbertura(casa, muro.id, o.id, {
    catalogo: it.codigo,
    tipo: it.tipo,
    posicion_m: pos,
    ancho_m: it.ancho_m,
    antepecho_m: it.antepecho_m,
    dintel_m: Math.round((it.antepecho_m + it.alto_m) * 1000) / 1000,
    ...(it.tipo === "puerta" && !o.hoja ? { hoja: { bisagra: "inicio" as const, apertura_deg: 70 } } : {}),
  });
  return { casa: nueva, seleccion: { tipo: "abertura", id: o.id, muro: muro.id }, nota: `Ahora es una ${it.nombre.toLowerCase()}.` };
}

function acomodarAbertura(casa: Casa, a: Accion): Paso {
  const h = a.abertura ? buscarAbertura(casa, a.abertura) : null;
  if (!h) throw new NoSePuede(`No encuentro la abertura «${a.abertura ?? ""}».`);
  const { muro, abertura: o } = h;
  const pos = ubicar(muro, o.ancho_m, 0, largo(muro), o.posicion_m, o.id);
  if (pos === null) throw new NoSePuede(`Esa abertura mide ${metros(o.ancho_m)} y no entra en su muro (${metros(largo(muro))}) junto a las demás. Hay que achicarla o sacarla.`);
  return { casa: modificarAbertura(casa, muro.id, o.id, { posicion_m: pos }), seleccion: { tipo: "abertura", id: o.id, muro: muro.id }, nota: "La corrí hasta donde entra en su muro." };
}

function moverEntrada(casa: Casa, a: Accion, catalogo: ItemCatalogo[]): Paso {
  const amb = a.ambiente ? ambienteDe(casa, a.ambiente) : casa.ambientes.find((x) => x.uso === "social" && x.contorno_m);
  if (!amb) throw new NoSePuede("No encuentro el estar para ponerle la entrada: decime en qué ambiente va.");
  const exteriores = murosDe(casa, amb).filter((t) => t.muro.sistema === "exterior");
  const lados = [...new Set(exteriores.map((t) => t.lado))];
  if (!a.lado) throw new NoSePuede(`Me falta saber de qué lado va la entrada. «${amb.nombre}» da al exterior por: ${lados.join(", ") || "ningún lado"}.`);
  const tramos = exteriores.filter((t) => t.lado === a.lado).sort((p, q) => q.t1 - q.t0 - (p.t1 - p.t0));
  if (!tramos.length) throw new NoSePuede(`«${amb.nombre}» no tiene muro exterior del lado ${a.lado}. Da al exterior por: ${lados.join(", ") || "ningún lado"}.`);
  const it = items(catalogo, ["puerta_090", "puerta_080"])[0];
  if (!it) throw new NoSePuede("El catálogo no tiene una puerta de entrada.");
  // Primero salen las entradas que había: pueden estar ocupando el lugar.
  let nueva = casa;
  let quitadas = 0;
  for (const m of casa.muros) {
    if (m.sistema !== "exterior") continue;
    for (const o of m.aberturas) {
      if (o.tipo === "puerta") {
        nueva = borrarAbertura(nueva, m.id, o.id);
        quitadas++;
      }
    }
  }
  for (const t of tramos) {
    const muro = nueva.muros.find((x) => x.id === t.muro.id)!;
    const pos = ubicar(muro, it.ancho_m, t.t0, t.t1, (t.t0 + t.t1 - it.ancho_m) / 2);
    if (pos === null) continue;
    const r = agregarAbertura(nueva, muro.id, it, pos);
    // La hoja abre hacia adentro: a la izquierda del eje en los muros sur y este.
    const hoja = { bisagra: "inicio" as const, apertura_deg: a.lado === "sur" || a.lado === "este" ? 80 : -80 };
    return {
      casa: modificarAbertura(r.casa, muro.id, r.id, { hoja, estado: "propuesto" }),
      seleccion: { tipo: "abertura", id: r.id, muro: muro.id },
      nota: `${quitadas ? "Saqué la entrada de donde estaba y la puse" : "Puse la entrada"} en el muro ${a.lado} de «${amb.nombre}».`,
    };
  }
  throw new NoSePuede(`No hay lugar para una puerta en el muro ${a.lado} de «${amb.nombre}»: está ocupado por ventanas.`);
}

/* ---------------------------------------------------------------- ejecución */

interface Paso {
  casa: Casa;
  nota: string;
  seleccion?: Pieza | null;
}

function paso(casa: Casa, a: Accion, catalogo: ItemCatalogo[]): Paso {
  switch (a.tipo) {
    case "ampliar":
      return ampliar(casa, a);
    case "mover_muro": {
      const m = muroDe(casa, a.muro);
      if (!a.metros) throw new NoSePuede("Me falta saber cuánto correr el muro.");
      return { casa: moverMuro(casa, m.id, a.metros), seleccion: { tipo: "muro", id: m.id }, nota: `Corrí el muro ${metros(a.metros)}.` };
    }
    case "quitar_muro": {
      const m = muroDe(casa, a.muro);
      return { casa: borrarMuro(casa, m.id), seleccion: null, nota: "Saqué el muro." };
    }
    case "integrar":
      return integrar(casa, a);
    case "renombrar": {
      const amb = casa.ambientes.find((x) => x.id === a.ambiente);
      if (!amb) throw new NoSePuede(`No encuentro el ambiente «${a.ambiente ?? ""}».`);
      const nombre = a.nombre?.trim() || amb.nombre;
      return {
        casa: modificarAmbiente(casa, amb.id, { nombre, ...(a.uso ? { uso: a.uso } : {}) }),
        seleccion: { tipo: "ambiente", id: amb.id },
        nota: nombre !== amb.nombre ? `«${amb.nombre}» ahora se llama «${nombre}».` : `«${amb.nombre}» cambió de uso.`,
      };
    }
    case "quitar_ambiente": {
      const amb = casa.ambientes.find((x) => x.id === a.ambiente);
      if (!amb) throw new NoSePuede(`No encuentro el ambiente «${a.ambiente ?? ""}».`);
      return { casa: borrarAmbiente(casa, amb.id), seleccion: null, nota: `Le saqué el nombre a «${amb.nombre}»: el espacio y sus muros siguen ahí.` };
    }
    case "crear_ambiente": {
      if (!a.contorno || a.contorno.length < 3) throw new NoSePuede("Me falta el contorno del ambiente.");
      const r = agregarAmbiente(casa, a.contorno, a.nombre?.trim() || "Ambiente nuevo", a.uso ?? "otro");
      const sinNombre = !a.nombre?.trim() || a.nombre === "Ambiente nuevo";
      return { casa: r.casa, seleccion: { tipo: "ambiente", id: r.id }, nota: sinNombre ? "Ya es un ambiente: ponele nombre y elegí su uso." : "" };
    }
    case "agregar_abertura":
      return agregarAberturaEn(casa, a, catalogo);
    case "quitar_abertura": {
      const h = a.abertura ? buscarAbertura(casa, a.abertura) : null;
      if (!h) throw new NoSePuede(`No encuentro la abertura «${a.abertura ?? ""}».`);
      return { casa: borrarAbertura(casa, h.muro.id, h.abertura.id), seleccion: null, nota: "Saqué la abertura." };
    }
    case "cambiar_abertura":
      return cambiarAbertura(casa, a, catalogo);
    case "acomodar_abertura":
      return acomodarAbertura(casa, a);
    case "mover_entrada":
      return moverEntrada(casa, a, catalogo);
  }
}

export interface Resultado {
  casa: Casa;
  /** Qué se hizo, acción por acción. */
  notas: string[];
  /** Si no se pudo, por qué; la casa vuelve sin cambios. */
  error: string | null;
  seleccion: Pieza | null | undefined;
}

export function ejecutar(casa: Casa, acciones: Accion[], catalogo: ItemCatalogo[]): Resultado {
  let actual = casa;
  const notas: string[] = [];
  let seleccion: Pieza | null | undefined;
  try {
    for (const a of acciones) {
      const r = paso(actual, a, catalogo);
      actual = r.casa;
      notas.push(r.nota);
      if (r.seleccion !== undefined) seleccion = r.seleccion;
    }
  } catch (e) {
    if (!(e instanceof NoSePuede)) throw e;
    return { casa, notas: [], error: e.message, seleccion: undefined };
  }
  return { casa: actual, notas, error: null, seleccion };
}

/* ---------------------------------------------------------------- contexto para el modelo */

/** Resumen de la planta para que el modelo elija acciones: qué hay, cómo se llama y qué tiene al lado. */
export function contextoPara(casa: Casa, seleccion: Pieza | null, catalogo: ItemCatalogo[]) {
  const ambientes = casa.ambientes.map((amb) => {
    if (!amb.contorno_m) return { id: amb.id, nombre: amb.nombre, uso: amb.uso, sin_contorno: true };
    const c = caja(amb.contorno_m);
    const toques = murosDe(casa, amb);
    const vecinos = vecinosDe(casa, amb);
    const lados = Object.fromEntries(
      LADOS.map((lado) => {
        const que = new Set<string>();
        for (const t of toques.filter((x) => x.lado === lado)) {
          if (t.muro.sistema === "exterior") que.add("exterior");
          for (const v of vecinos) if (v.muro.id === t.muro.id) que.add(v.ambiente.id);
        }
        return [lado, que.size ? [...que] : ["abierto"]];
      }),
    );
    return {
      id: amb.id,
      nombre: amb.nombre,
      uso: amb.uso,
      superficie_m2: Math.round(areaPoligono(amb.contorno_m) * 10) / 10,
      de_este_a_oeste_m: Math.round((c.x1 - c.x0) * 100) / 100,
      de_norte_a_sur_m: Math.round((c.y1 - c.y0) * 100) / 100,
      que_tiene_a_cada_lado: lados,
    };
  });
  const aberturas = casa.muros.flatMap((m) =>
    m.aberturas.map((o) => {
      const centro = o.posicion_m + o.ancho_m / 2;
      const de = casa.ambientes.filter((amb) => murosDe(casa, amb).some((t) => t.muro.id === m.id && centro >= t.t0 && centro <= t.t1));
      return { id: o.id, tipo: o.tipo, catalogo: o.catalogo ?? null, ancho_m: o.ancho_m, exterior: m.sistema === "exterior", lado: m.lado_exterior ?? null, ambientes: de.map((x) => x.id) };
    }),
  );
  const pieza = seleccion
    ? { tipo: seleccion.tipo, id: seleccion.id, nombre: seleccion.tipo === "ambiente" ? casa.ambientes.find((x) => x.id === seleccion.id)?.nombre : undefined }
    : null;
  return {
    seleccion: pieza,
    superficie_cubierta_m2: Math.round((superficieCubierta(casa) ?? 0) * 10) / 10,
    ambientes,
    aberturas,
    muros: casa.muros.map((m) => ({ id: m.id, sistema: m.sistema, lado_exterior: m.lado_exterior ?? null, orientacion: esHorizontal(m) ? "este-oeste" : "norte-sur", largo_m: Math.round(largo(m) * 100) / 100 })),
    catalogo: catalogo.map((i) => ({ codigo: i.codigo, nombre: i.nombre, tipo: i.tipo })),
  };
}
