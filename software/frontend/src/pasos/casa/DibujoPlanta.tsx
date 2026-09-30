/** Dibuja una planta en SVG con convenciones de plano: muros con su espesor, aberturas con su símbolo,
 *  ambientes con nombre y superficie, y el estado de cada pieza. Lo usan el editor y las miniaturas. */

import type { PointerEvent as ReactPointerEvent, ReactNode } from "react";
import type { Estado, Punto } from "../../modelo/proyecto";
import {
  areaPoligono,
  centroide,
  direccion,
  espesor,
  largo,
  proyectar,
  type Abertura,
  type AnalisisPlanta,
  type Casa,
  type Muro,
  type Pieza,
} from "../../modelo/casa";
import { ASPECTO, estadoPieza } from "./estados";

export interface Vista {
  /** Píxeles por metro. */
  escala: number;
  /** Posición en pantalla del origen de la casa. */
  ox: number;
  oy: number;
}

export const aPantalla = (v: Vista, p: Punto): Punto => [v.ox + p[0] * v.escala, v.oy - p[1] * v.escala];
export const aMetros = (v: Vista, x: number, y: number): Punto => [(x - v.ox) / v.escala, (v.oy - y) / v.escala];

export function encuadrar(ext: { x0: number; y0: number; x1: number; y1: number }, ancho: number, alto: number, margen = 40): Vista {
  const w = Math.max(ext.x1 - ext.x0, 1);
  const h = Math.max(ext.y1 - ext.y0, 1);
  const escala = Math.min((ancho - 2 * margen) / w, (alto - 2 * margen) / h);
  return {
    escala,
    ox: (ancho - w * escala) / 2 - ext.x0 * escala,
    oy: (alto + h * escala) / 2 + ext.y0 * escala,
  };
}

export function Tramas() {
  return (
    <defs>
      <pattern id="trama-rayado" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="6" height="6" fill="var(--warn)" />
        <line x1="0" y1="0" x2="0" y2="6" stroke="var(--concrete-2)" strokeWidth="2.2" />
      </pattern>
      <pattern id="trama-punteado" width="5" height="5" patternUnits="userSpaceOnUse">
        <rect width="5" height="5" fill="var(--concrete-2)" />
        <circle cx="2.5" cy="2.5" r="0.8" fill="var(--rebar)" />
      </pattern>
      <pattern id="trama-ambiente-datos" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="8" height="8" fill="var(--concrete-3)" />
        <line x1="0" y1="0" x2="0" y2="8" stroke="var(--concrete-2)" strokeWidth="3" />
      </pattern>
    </defs>
  );
}

function rellenoMuro(e: Estado, verEstados: boolean): string {
  if (!verEstados) return "var(--ink)";
  const a = ASPECTO[e];
  if (a.trama === "rayado") return "url(#trama-rayado)";
  if (a.trama === "punteado") return "url(#trama-punteado)";
  return a.muro;
}

/** Polígono de pantalla de un tramo de muro entre t0 y t1 (metros a lo largo del eje). */
function tramo(v: Vista, m: Muro, t0: number, t1: number, e: number): string {
  const d = direccion(m);
  const n: Punto = [-d[1], d[0]];
  const p = (t: number, s: number): Punto =>
    aPantalla(v, [m.eje.desde_m[0] + d[0] * t + n[0] * s, m.eje.desde_m[1] + d[1] * t + n[1] * s]);
  return [p(t0, -e / 2), p(t1, -e / 2), p(t1, e / 2), p(t0, e / 2)].map((q) => q.join(",")).join(" ");
}

/** Un extremo se prolonga medio espesor si llega a otro muro, para que las esquinas cierren. */
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

interface Props {
  casa: Casa;
  vista: Vista;
  analisis: AnalisisPlanta | null;
  verEstados?: boolean;
  seleccion?: Pieza | null;
  resaltadas?: Set<string>;
  etiquetas?: boolean;
  onPieza?: (p: Pieza, e: ReactPointerEvent) => void;
  interactivo?: boolean;
  /** Ambientes translúcidos, para ver un dibujo de fondo. */
  translucido?: boolean;
}

export default function DibujoPlanta({
  casa,
  vista: v,
  analisis,
  verEstados = true,
  seleccion,
  resaltadas,
  etiquetas = true,
  onPieza,
  interactivo = false,
  translucido = false,
}: Props) {
  const cursor = interactivo ? "pointer" : undefined;
  const seleccionado = (id: string) => seleccion?.id === id;
  const insignias: ReactNode[] = [];

  const insignia = (id: string, e: Estado, p: Punto, esAmbiente = false) => {
    const a = ASPECTO[e];
    if (!verEstados || !a.glifo) return;
    // «Revisar» suele abarcar toda una planta leída por IA: en muros y aberturas lo dice la trama,
    // y la insignia queda solo en los ambientes para no llenar el plano de signos.
    if (e === "pendiente_revision" && !esAmbiente) return;
    insignias.push(
      <g key={`i-${id}`} transform={`translate(${p[0]},${p[1]})`} pointerEvents="none">
        <circle r={7} fill="var(--concrete-2)" stroke={a.acento} strokeWidth={1.5} />
        <text textAnchor="middle" dy="3.5" fontSize="10" fontWeight="700" fill={a.acento}>
          {a.glifo}
        </text>
      </g>,
    );
  };

  return (
    <g>
      {/* Ambientes */}
      {casa.ambientes.map((amb) => {
        if (!amb.contorno_m || amb.contorno_m.length < 3) return null;
        const e = estadoPieza(amb.estado, amb.id, analisis);
        const pts = amb.contorno_m.map((p) => aPantalla(v, p).join(",")).join(" ");
        const relleno = !verEstados
          ? "var(--concrete-2)"
          : e === "pendiente_datos"
            ? "url(#trama-ambiente-datos)"
            : ASPECTO[e].ambiente;
        return (
          <polygon
            key={amb.id}
            data-pieza={amb.id}
            points={pts}
            fill={relleno}
            fillOpacity={translucido ? 0.3 : 1}
            stroke={seleccionado(amb.id) ? "var(--signal)" : resaltadas?.has(amb.id) ? "var(--warn)" : "none"}
            strokeWidth={seleccionado(amb.id) ? 2.5 : 2}
            strokeDasharray={seleccionado(amb.id) ? undefined : "4 3"}
            style={{ cursor }}
            onPointerDown={onPieza ? (ev) => onPieza({ tipo: "ambiente", id: amb.id }, ev) : undefined}
          />
        );
      })}

      {/* Muros, cortados donde hay aberturas */}
      {casa.muros.map((m) => {
        const L = largo(m);
        const e = espesor(casa, m.sistema);
        const est = estadoPieza(m.estado, m.id, analisis);
        const [pi, pf] = prolongaciones(casa, m);
        const huecos = [...m.aberturas].sort((a, b) => a.posicion_m - b.posicion_m);
        const llenos: [number, number][] = [];
        let t = -pi;
        for (const o of huecos) {
          if (o.posicion_m > t) llenos.push([t, o.posicion_m]);
          t = Math.max(t, o.posicion_m + o.ancho_m);
        }
        if (L + pf > t) llenos.push([t, L + pf]);
        const sel = seleccionado(m.id) || resaltadas?.has(m.id);
        const a = ASPECTO[est];
        const d = direccion(m);
        const medio = aPantalla(v, [m.eje.desde_m[0] + (d[0] * L) / 2, m.eje.desde_m[1] + (d[1] * L) / 2]);
        insignia(m.id, est, medio);
        return (
          <g
            key={m.id}
            data-pieza={m.id}
            style={{ cursor }}
            onPointerDown={onPieza ? (ev) => onPieza({ tipo: "muro", id: m.id }, ev) : undefined}
          >
            {/* Zona de toque más ancha que el muro, para poder elegirlo con el mouse. */}
            {interactivo && <polygon points={tramo(v, m, -pi, L + pf, e + 12 / v.escala)} fill="transparent" />}
            {llenos.map(([t0, t1], i) => (
              <polygon
                key={i}
                points={tramo(v, m, t0, t1, e)}
                fill={rellenoMuro(est, verEstados)}
                stroke={sel ? "var(--signal)" : verEstados && a.borde ? a.borde : "none"}
                strokeWidth={sel ? 2 : 1}
                strokeDasharray={verEstados && a.borde && !sel ? "3 2" : undefined}
              />
            ))}
            {huecos.map((o) => (
              <SimboloAbertura
                key={o.id}
                v={v}
                muro={m}
                o={o}
                espesorMuro={e}
                estado={estadoPieza(o.estado, o.id, analisis)}
                verEstados={verEstados}
                seleccionada={seleccionado(o.id) || !!resaltadas?.has(o.id)}
                cursor={cursor}
                onPointerDown={onPieza ? (ev) => {
                  ev.stopPropagation();
                  onPieza({ tipo: "abertura", id: o.id, muro: m.id }, ev);
                } : undefined}
                insignia={insignia}
              />
            ))}
          </g>
        );
      })}

      {/* Nombres y superficies */}
      {etiquetas &&
        casa.ambientes.map((amb) => {
          if (!amb.contorno_m || amb.contorno_m.length < 3) return null;
          const c = aPantalla(v, centroide(amb.contorno_m));
          const area = areaPoligono(amb.contorno_m);
          const e = estadoPieza(amb.estado, amb.id, analisis);
          const xs = amb.contorno_m.map((p) => p[0]);
          const anchoPx = (Math.max(...xs) - Math.min(...xs)) * v.escala;
          const chico = anchoPx < 70;
          insignia(amb.id, e, [c[0] + (chico ? 14 : Math.min(anchoPx / 2 - 12, 48)), c[1] - 16], true);
          return (
            <g key={`t-${amb.id}`} pointerEvents="none" textAnchor="middle">
              <text x={c[0]} y={c[1]} fontSize={chico ? 9 : 11} fill="var(--ink)" fontWeight={600}>
                {chico ? amb.nombre.split(" ")[0] : amb.nombre}
              </text>
              <text x={c[0]} y={c[1] + 13} fontSize={9} fill="var(--rebar)">
                {area.toFixed(1)} m²
              </text>
            </g>
          );
        })}
      {insignias}
    </g>
  );
}

function SimboloAbertura({
  v,
  muro: m,
  o,
  espesorMuro: e,
  estado,
  verEstados,
  seleccionada,
  cursor,
  onPointerDown,
  insignia,
}: {
  v: Vista;
  muro: Muro;
  o: Abertura;
  espesorMuro: number;
  estado: Estado;
  verEstados: boolean;
  seleccionada: boolean;
  cursor?: string;
  onPointerDown?: (e: ReactPointerEvent) => void;
  insignia: (id: string, e: Estado, p: Punto, esAmbiente?: boolean) => void;
}) {
  const d = direccion(m);
  const n: Punto = [-d[1], d[0]];
  const P = (t: number, s = 0): Punto =>
    aPantalla(v, [m.eje.desde_m[0] + d[0] * t + n[0] * s, m.eje.desde_m[1] + d[1] * t + n[1] * s]);
  const color = seleccionada ? "var(--signal)" : verEstados ? ASPECTO[estado].acento : "var(--ink)";
  const t0 = o.posicion_m;
  const t1 = o.posicion_m + o.ancho_m;
  const linea = (a: Punto, b: Punto, w = 1, dash?: string, k?: string) => (
    <line key={k} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color} strokeWidth={w} strokeDasharray={dash} />
  );
  const partes: ReactNode[] = [];
  // Zona de toque: el vano entero.
  const zona = [P(t0, -e / 2 - 4 / v.escala), P(t1, -e / 2 - 4 / v.escala), P(t1, e / 2 + 4 / v.escala), P(t0, e / 2 + 4 / v.escala)];
  partes.push(<polygon key="z" points={zona.map((q) => q.join(",")).join(" ")} fill={seleccionada ? "color-mix(in srgb, var(--signal) 15%, transparent)" : "transparent"} />);
  // Jambas
  partes.push(linea(P(t0, -e / 2), P(t0, e / 2), 1, undefined, "j0"), linea(P(t1, -e / 2), P(t1, e / 2), 1, undefined, "j1"));

  if (o.tipo === "ventana") {
    partes.push(linea(P(t0, -e / 2), P(t1, -e / 2), 1, undefined, "a"), linea(P(t0, e / 2), P(t1, e / 2), 1, undefined, "b"));
    partes.push(linea(P(t0, 0), P(t1, 0), 2, undefined, "v"));
  } else if (o.tipo === "ventana_corrediza") {
    partes.push(linea(P(t0, -e / 2), P(t1, -e / 2), 1, undefined, "a"), linea(P(t0, e / 2), P(t1, e / 2), 1, undefined, "b"));
    const m1 = t0 + o.ancho_m * 0.55;
    const m2 = t0 + o.ancho_m * 0.45;
    partes.push(linea(P(t0, -e / 8), P(m1, -e / 8), 2, undefined, "h1"), linea(P(m2, e / 8), P(t1, e / 8), 2, undefined, "h2"));
  } else if (o.tipo === "porton") {
    // Portón de garage: la hoja sube y se dibuja proyectada, en trazo cortado hacia adentro.
    partes.push(linea(P(t0, 0), P(t1, 0), 1.5, undefined, "p"));
    partes.push(linea(P(t0, e / 2 + 0.6), P(t1, e / 2 + 0.6), 0.8, "4 3", "proy"));
  } else if (o.tipo === "puerta") {
    const lado = (o.hoja?.apertura_deg ?? 70) >= 0 ? 1 : -1;
    const bisagraFin = o.hoja?.bisagra === "fin";
    const tb = bisagraFin ? t1 : t0;
    const tl = bisagraFin ? t0 : t1;
    const s0 = (lado * e) / 2;
    const bis = P(tb, s0);
    const punta = P(tb, s0 + lado * o.ancho_m);
    const libre = P(tl, s0);
    const r = o.ancho_m * v.escala;
    // Barrido de 90°: de la punta de la hoja abierta al marco libre.
    const barrido = (bisagraFin ? 1 : -1) * lado > 0 ? 1 : 0;
    partes.push(linea(bis, punta, 1.5, undefined, "hoja"));
    partes.push(
      <path
        key="arco"
        d={`M ${punta[0]} ${punta[1]} A ${r} ${r} 0 0 ${barrido} ${libre[0]} ${libre[1]}`}
        fill="none"
        stroke={color}
        strokeWidth={0.8}
        strokeDasharray="3 2"
      />,
    );
  }
  insignia(o.id, estado, P((t0 + t1) / 2, (e / 2) + 10 / v.escala));
  return (
    <g data-pieza={o.id} style={{ cursor }} onPointerDown={onPointerDown}>
      {partes}
    </g>
  );
}
