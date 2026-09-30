/** Operaciones de la planta (MVP_01 §4.4: crear_muro, mover_muro, agregar_abertura, modificar_abertura,
 *  definir_ambiente…). Son funciones puras: reciben la casa y devuelven otra. La interfaz y el asistente
 *  usan las mismas; ninguno escribe geometría por su cuenta.
 *
 *  Regla de estados al editar: una pieza que se toca pasa a `propuesto` (es una propuesta nueva del
 *  usuario y las reglas la vuelven a verificar); si estaba `revisado`, pasa a `desactualizado`. */

import type { Estado, Punto } from "../../modelo/proyecto";
import {
  espesor,
  esHorizontal,
  largo,
  proyectar,
  type Abertura,
  type Ambiente,
  type Casa,
  type ItemCatalogo,
  type Muro,
  type Uso,
} from "../../modelo/casa";

const EPS = 0.02;

export const redondear = (v: number, paso = 0.05) => {
  const r = Math.round(v / paso) * paso;
  return Math.round(r * 1000) / 1000 || 0;
};

function tocado(e: Estado | null | undefined): Estado {
  return e === "revisado" || e === "desactualizado" ? "desactualizado" : "propuesto";
}

function idUnico(base: string, usados: Set<string>): string {
  let id = base;
  let n = 2;
  while (usados.has(id)) id = `${base}_${n++}`;
  return id;
}

export function slug(t: string): string {
  return (
    t
      .normalize("NFKD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, "_")
      .replace(/^_|_$/g, "")
      .toLowerCase() || "ambiente"
  );
}

function conMuros(casa: Casa, muros: Muro[]): Casa {
  return recalcularHuella({ ...casa, muros });
}

/* ---------------------------------------------------------------- muros */

export function agregarMuro(casa: Casa, desde: Punto, hasta: Punto, sistema: string): { casa: Casa; id: string } {
  const usados = new Set(casa.muros.map((m) => m.id));
  const n = casa.muros.length + 1;
  const id = idUnico(sistema === "exterior" ? `Ext_${n}` : `M${n}`, usados);
  // Horizontales de oeste a este, verticales de sur a norte (convención de Angus Ranch).
  const [a, b] = desde[0] > hasta[0] || (desde[0] === hasta[0] && desde[1] > hasta[1]) ? [hasta, desde] : [desde, hasta];
  const muro: Muro = {
    id,
    sistema,
    eje: { desde_m: [redondear(a[0]), redondear(a[1])], hasta_m: [redondear(b[0]), redondear(b[1])] },
    altura: sistema === "tabique" ? { tipo: "tabique" } : { tipo: "hasta_cubierta", cubierta: "principal" },
    aberturas: [],
    estado: "propuesto",
  };
  return { casa: conMuros(casa, [...casa.muros, muro]), id };
}

export function borrarMuro(casa: Casa, id: string): Casa {
  return conMuros(
    casa,
    casa.muros.filter((m) => m.id !== id),
  );
}

export function modificarMuro(casa: Casa, id: string, cambios: Partial<Muro>): Casa {
  return conMuros(
    casa,
    casa.muros.map((m) => (m.id === id ? { ...m, ...cambios, estado: tocado(m.estado) } : m)),
  );
}

/** Desplaza un muro en forma perpendicular a su eje y arrastra lo que está conectado:
 *  los extremos de los muros que apoyan contra él y los bordes de los ambientes que lo tocan. */
export function moverMuro(casa: Casa, id: string, delta: number): Casa {
  const muro = casa.muros.find((m) => m.id === id);
  if (!muro || Math.abs(delta) < 1e-9) return casa;
  const horizontal = esHorizontal(muro);
  const eje = horizontal ? 1 : 0; // coordenada que cambia
  const fijo = muro.eje.desde_m[eje];
  const otro = 1 - eje;
  const lo = Math.min(muro.eje.desde_m[otro], muro.eje.hasta_m[otro]) - EPS;
  const hi = Math.max(muro.eje.desde_m[otro], muro.eje.hasta_m[otro]) + EPS;
  const t = espesor(casa, muro.sistema) / 2;
  const mover = (p: Punto): Punto => {
    const q: Punto = [p[0], p[1]];
    q[eje] = redondear(q[eje] + delta, 0.005);
    return q;
  };
  const enLinea = (p: Punto) => Math.abs(p[eje] - fijo) < EPS && p[otro] >= lo && p[otro] <= hi;

  const muros = casa.muros.map((m) => {
    if (m.id === id) {
      return { ...m, eje: { desde_m: mover(m.eje.desde_m), hasta_m: mover(m.eje.hasta_m) }, estado: tocado(m.estado) };
    }
    const d = enLinea(m.eje.desde_m);
    const h = enLinea(m.eje.hasta_m);
    if (!d && !h) return m;
    const perpendicular = horizontal ? !esHorizontal(m) : esHorizontal(m);
    if (!perpendicular) return m;
    const nuevo: Muro = {
      ...m,
      eje: { desde_m: d ? mover(m.eje.desde_m) : m.eje.desde_m, hasta_m: h ? mover(m.eje.hasta_m) : m.eje.hasta_m },
      estado: tocado(m.estado),
    };
    // Las aberturas se miden desde el inicio del eje: si el inicio se mueve, se compensa
    // para que queden en el mismo lugar del espacio.
    if (d) {
      const corrimiento = proyectar(nuevo, m.eje.desde_m).t;
      nuevo.aberturas = m.aberturas.map((o) => ({ ...o, posicion_m: redondear(o.posicion_m + corrimiento, 0.005) }));
    }
    return nuevo;
  });

  const ambientes = casa.ambientes.map((a) => {
    if (!a.contorno_m) return a;
    let cambio = false;
    const contorno = a.contorno_m.map((p) => {
      const cerca = [fijo - t, fijo, fijo + t].some((v) => Math.abs(p[eje] - v) < EPS + 0.03);
      if (cerca && p[otro] >= lo - t && p[otro] <= hi + t) {
        cambio = true;
        return mover(p);
      }
      return p;
    });
    return cambio ? { ...a, contorno_m: contorno, estado: tocado(a.estado) } : a;
  });
  return recalcularHuella({ ...casa, muros, ambientes });
}

/* ---------------------------------------------------------------- aberturas */

export function agregarAbertura(casa: Casa, muroId: string, item: ItemCatalogo, posicion: number): { casa: Casa; id: string } {
  let id = "";
  const muros = casa.muros.map((m) => {
    if (m.id !== muroId) return m;
    const usados = new Set(m.aberturas.map((o) => o.id));
    let n = m.aberturas.length;
    do id = `${m.id}/O${n++}`;
    while (usados.has(id));
    const ab: Abertura = {
      id,
      tipo: item.tipo,
      posicion_m: redondear(posicion),
      ancho_m: item.ancho_m,
      antepecho_m: item.antepecho_m,
      dintel_m: Math.round((item.antepecho_m + item.alto_m) * 1000) / 1000,
      catalogo: item.codigo,
      estado: "propuesto",
      ...(item.tipo === "puerta" ? { hoja: { bisagra: "inicio" as const, apertura_deg: 70 } } : {}),
    };
    return { ...m, aberturas: [...m.aberturas, ab].sort((a, b) => a.posicion_m - b.posicion_m) };
  });
  return { casa: { ...casa, muros }, id };
}

export function modificarAbertura(casa: Casa, muroId: string, id: string, cambios: Partial<Abertura>): Casa {
  return {
    ...casa,
    muros: casa.muros.map((m) =>
      m.id !== muroId
        ? m
        : {
            ...m,
            aberturas: m.aberturas
              .map((o) => (o.id === id ? { ...o, ...cambios, estado: tocado(o.estado) } : o))
              .sort((a, b) => a.posicion_m - b.posicion_m),
          },
    ),
  };
}

export function borrarAbertura(casa: Casa, muroId: string, id: string): Casa {
  return {
    ...casa,
    muros: casa.muros.map((m) => (m.id !== muroId ? m : { ...m, aberturas: m.aberturas.filter((o) => o.id !== id) })),
  };
}

/** ¿Entra una abertura de este ancho en esta posición, sin pisar otras? */
export function entraAbertura(muro: Muro, posicion: number, ancho: number, ignorar?: string): boolean {
  if (posicion < 0.1 - 1e-6 || posicion + ancho > largo(muro) - 0.1 + 1e-6) return false;
  return muro.aberturas.every(
    (o) => o.id === ignorar || posicion + ancho + 0.1 <= o.posicion_m + 1e-6 || o.posicion_m + o.ancho_m + 0.1 <= posicion + 1e-6,
  );
}

/* ---------------------------------------------------------------- ambientes */

export function agregarAmbiente(casa: Casa, contorno: Punto[], nombre: string, uso: Uso): { casa: Casa; id: string } {
  const id = idUnico(slug(nombre), new Set(casa.ambientes.map((a) => a.id)));
  const amb: Ambiente = {
    id,
    nombre,
    uso,
    contorno_m: contorno.map((p) => [redondear(p[0], 0.005), redondear(p[1], 0.005)] as Punto),
    estado: "propuesto",
  };
  return { casa: { ...casa, ambientes: [...casa.ambientes, amb] }, id };
}

export function modificarAmbiente(casa: Casa, id: string, cambios: Partial<Ambiente>): Casa {
  return {
    ...casa,
    ambientes: casa.ambientes.map((a) => (a.id === id ? { ...a, ...cambios, estado: tocado(a.estado) } : a)),
  };
}

export function borrarAmbiente(casa: Casa, id: string): Casa {
  return { ...casa, ambientes: casa.ambientes.filter((a) => a.id !== id) };
}

/* ---------------------------------------------------------------- revisión */

/** Marca piezas como revisadas por el usuario. Sin ids, marca todas las que estaban a revisar. */
export function marcarRevisado(casa: Casa, ids?: Set<string>): Casa {
  const fecha = new Date().toISOString().slice(0, 19) + "Z";
  const toca = (id: string, e: Estado | null | undefined) =>
    ids ? ids.has(id) : e === "pendiente_revision" || e === "desactualizado";
  const marcar = <T extends { id: string; estado?: Estado | null }>(p: T): T =>
    toca(p.id, p.estado) ? { ...p, estado: "revisado", revision: { fecha } } : p;
  return {
    ...casa,
    muros: casa.muros.map((m) => ({ ...marcar(m), aberturas: m.aberturas.map(marcar) })),
    ambientes: casa.ambientes.map(marcar),
  };
}

/* ---------------------------------------------------------------- huella */

/** Rehace la huella (contorno exterior de la planta) encadenando los ejes de los muros
 *  exteriores y desplazándolos medio espesor hacia afuera. Si no cierran, deja la anterior. */
export function recalcularHuella(casa: Casa): Casa {
  const ext = casa.muros.filter((m) => m.sistema === "exterior" && largo(m) > 0.01);
  if (ext.length < 3) return casa;
  const clave = (p: Punto) => `${p[0].toFixed(2)},${p[1].toFixed(2)}`;
  const vecinos = new Map<string, { p: Punto; muros: number[] }>();
  ext.forEach((m, i) => {
    for (const p of [m.eje.desde_m, m.eje.hasta_m]) {
      const k = clave(p);
      if (!vecinos.has(k)) vecinos.set(k, { p, muros: [] });
      vecinos.get(k)!.muros.push(i);
    }
  });
  if ([...vecinos.values()].some((v) => v.muros.length !== 2)) return casa;
  const lazo: Punto[] = [];
  let actual = ext[0].eje.desde_m;
  let muro = 0;
  const usados = new Set<number>();
  while (!usados.has(muro)) {
    usados.add(muro);
    lazo.push(actual);
    const m = ext[muro];
    const siguiente = clave(m.eje.desde_m) === clave(actual) ? m.eje.hasta_m : m.eje.desde_m;
    const v = vecinos.get(clave(siguiente))!;
    muro = v.muros[0] === muro ? v.muros[1] : v.muros[0];
    actual = siguiente;
  }
  if (usados.size !== ext.length || lazo.length < 3) return casa;
  // Sentido antihorario: el exterior queda a la derecha.
  let s = 0;
  for (let i = 0; i < lazo.length; i++) {
    const [x1, y1] = lazo[i];
    const [x2, y2] = lazo[(i + 1) % lazo.length];
    s += x1 * y2 - x2 * y1;
  }
  if (s < 0) lazo.reverse();
  const limpio = lazo.filter((b, i) => {
    const a = lazo[(i - 1 + lazo.length) % lazo.length];
    const c = lazo[(i + 1) % lazo.length];
    return Math.abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9;
  });
  const d = espesor(casa, "exterior") / 2;
  const normal = (a: Punto, b: Punto): Punto => {
    const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [(b[1] - a[1]) / l, -(b[0] - a[0]) / l];
  };
  const huella = limpio.map((b, i) => {
    const a = limpio[(i - 1 + limpio.length) % limpio.length];
    const c = limpio[(i + 1) % limpio.length];
    const n1 = normal(a, b);
    const n2 = normal(b, c);
    return [redondear(b[0] + d * (n1[0] + n2[0]), 0.005), redondear(b[1] + d * (n1[1] + n2[1]), 0.005)] as Punto;
  });
  return { ...casa, huella_m: huella };
}
