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
  type PiezaInterior,
  USOS_EXTERIORES,
} from "../../modelo/casa";
import { aPlanta, COLORES, huella, piezasInterior, primitivas } from "../../modelo/muebles";
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
      <pattern id="trama-deck" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" fill="#cdb79b" />
        <line x1="0" y1="5.5" x2="6" y2="5.5" stroke="#a88b69" strokeWidth="0.8" />
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
  /** Muebles y artefactos. */
  verMuebles?: boolean;
  /** Medidas exteriores de la casa y medidas de cada ambiente. */
  cotas?: boolean;
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
  verMuebles = true,
  cotas = false,
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
    // Las aberturas piden su insignia al dibujarse; si se dibujan de nuevo, no se repite.
    if (insignias.some((n) => (n as { key?: string } | null)?.key === `i-${id}`)) return;
    insignias.push(
      <g key={`i-${id}`} transform={`translate(${p[0]},${p[1]})`} pointerEvents="none">
        <circle r={7} fill="var(--concrete-2)" stroke={a.acento} strokeWidth={1.5} />
        <text textAnchor="middle" dy="3.5" fontSize="10" fontWeight="500" fill={a.acento} className="font-label">
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
        const exterior = USOS_EXTERIORES.includes(amb.uso);
        const relleno = exterior
          ? "url(#trama-deck)"
          : !verEstados
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

      {/* Muebles y artefactos, vistos desde arriba */}
      {verMuebles &&
        piezasInterior(casa).map((pz) => (
          <PiezaEnPlanta
            key={pz.id}
            v={v}
            pieza={pz}
            estado={estadoPieza(pz.estado, pz.id, analisis)}
            verEstados={verEstados}
            seleccionada={seleccionado(pz.id) || !!resaltadas?.has(pz.id)}
            cursor={cursor}
            onPointerDown={onPieza ? (ev) => {
              ev.stopPropagation();
              onPieza({ tipo: "mueble", id: pz.id }, ev);
            } : undefined}
          />
        ))}

      {/* Nombres y superficies */}
      {etiquetas &&
        casa.ambientes.map((amb) => {
          if (!amb.contorno_m || amb.contorno_m.length < 3) return null;
          const c = aPantalla(v, centroide(amb.contorno_m));
          const area = areaPoligono(amb.contorno_m);
          const e = estadoPieza(amb.estado, amb.id, analisis);
          const xs = amb.contorno_m.map((p) => p[0]);
          const ys = amb.contorno_m.map((p) => p[1]);
          const ancho = Math.max(...xs) - Math.min(...xs);
          const fondo = Math.max(...ys) - Math.min(...ys);
          const anchoPx = ancho * v.escala;
          const chico = anchoPx < 70;
          insignia(amb.id, e, [c[0] + (chico ? 14 : Math.min(anchoPx / 2 - 12, 48)), c[1] - 16], true);
          return (
            <g key={`t-${amb.id}`} pointerEvents="none" textAnchor="middle">
              <text x={c[0]} y={c[1]} fontSize={chico ? 9 : 11} fill="var(--ink)" fontWeight={700}>
                {chico ? amb.nombre.split(" ")[0] : amb.nombre}
              </text>
              <text x={c[0]} y={c[1] + 13} fontSize={9} fill="var(--rebar)" className="font-label">
                {area.toFixed(1)} m²
              </text>
              {cotas && !chico && (
                <text x={c[0]} y={c[1] + 25} fontSize={9} fill="var(--signal)" className="font-label">
                  {medida(ancho)} × {medida(fondo)}
                </text>
              )}
            </g>
          );
        })}
      {cotas && <CotasExteriores casa={casa} v={v} />}
      {insignias}
    </g>
  );
}

const medida = (m: number) => m.toFixed(2).replace(".", ",");

/** Una línea de cota por cada lado de la huella, del lado de afuera: es la medida exterior de la casa. */
function CotasExteriores({ casa, v }: { casa: Casa; v: Vista }) {
  const h = casa.huella_m ?? [];
  if (h.length < 3) return null;
  let s = 0;
  for (let i = 0; i < h.length; i++) s += h[i][0] * h[(i + 1) % h.length][1] - h[(i + 1) % h.length][0] * h[i][1];
  const sentido = s >= 0 ? 1 : -1; // con la huella en sentido antihorario, afuera queda a la derecha
  const separacion = 18 / v.escala;
  return (
    <g pointerEvents="none">
      {h.map((a, i) => {
        const b = h[(i + 1) % h.length];
        const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (L * v.escala < 34) return null;
        const n: Punto = [(sentido * (b[1] - a[1])) / L, (sentido * -(b[0] - a[0])) / L];
        const p = aPantalla(v, [a[0] + n[0] * separacion, a[1] + n[1] * separacion]);
        const q = aPantalla(v, [b[0] + n[0] * separacion, b[1] + n[1] * separacion]);
        const medio: Punto = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
        const vertical = Math.abs(p[0] - q[0]) < 1;
        // El texto se aparta de la línea hacia afuera (en pantalla, la Y crece hacia abajo).
        const tx = medio[0] + n[0] * 11;
        const ty = medio[1] - n[1] * 11;
        return (
          <g key={i} stroke="var(--signal)" strokeWidth={1}>
            <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} />
            {[p, q].map((e, k) => (
              <line key={k} x1={e[0] - (vertical ? 4 : 0)} y1={e[1] - (vertical ? 0 : 4)} x2={e[0] + (vertical ? 4 : 0)} y2={e[1] + (vertical ? 0 : 4)} />
            ))}
            <text
              x={tx}
              y={ty}
              stroke="none"
              fill="var(--signal)"
              fontSize={10}
              fontWeight={500}
              className="font-label"
              textAnchor="middle"
              dominantBaseline="middle"
              transform={vertical ? `rotate(-90 ${tx} ${ty})` : undefined}
            >
              {medida(L)}
            </text>
          </g>
        );
      })}
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

function PiezaEnPlanta({
  v,
  pieza,
  estado,
  verEstados,
  seleccionada,
  cursor,
  onPointerDown,
}: {
  v: Vista;
  pieza: PiezaInterior;
  estado: Estado;
  verEstados: boolean;
  seleccionada: boolean;
  cursor?: string;
  onPointerDown?: (e: ReactPointerEvent) => void;
}) {
  const prims = [...primitivas(pieza)].sort((a, b) => a.z + a.h - (b.z + b.h));
  const P = (x: number, y: number) => aPantalla(v, aPlanta(pieza, x, y)).join(",");
  const [x0, y0, x1, y1] = huella(pieza);
  const contorno = [aPantalla(v, [x0, y0]), aPantalla(v, [x1, y0]), aPantalla(v, [x1, y1]), aPantalla(v, [x0, y1])]
    .map((q) => q.join(","))
    .join(" ");
  const aviso = verEstados && (estado === "pendiente_revision" || estado === "desactualizado");
  return (
    <g data-pieza={pieza.id} style={{ cursor }} onPointerDown={onPointerDown}>
      <polygon points={contorno} fill="transparent" />
      {prims.map((q, i) =>
        q.f === "caja" ? (
          <polygon
            key={i}
            points={[P(q.x - q.a / 2, q.y - q.p / 2), P(q.x + q.a / 2, q.y - q.p / 2), P(q.x + q.a / 2, q.y + q.p / 2), P(q.x - q.a / 2, q.y + q.p / 2)].join(" ")}
            fill={q.transparente ? "none" : COLORES[q.c]}
            stroke="var(--ink)"
            strokeOpacity={0.55}
            strokeWidth={0.6}
          />
        ) : (
          <circle
            key={i}
            cx={aPantalla(v, aPlanta(pieza, q.x, q.y))[0]}
            cy={aPantalla(v, aPlanta(pieza, q.x, q.y))[1]}
            r={q.r * v.escala}
            fill={COLORES[q.c]}
            stroke="var(--ink)"
            strokeOpacity={0.55}
            strokeWidth={0.6}
          />
        ),
      )}
      {(seleccionada || aviso) && (
        <polygon
          points={contorno}
          fill="none"
          stroke={seleccionada ? "var(--signal)" : ASPECTO[estado].acento}
          strokeWidth={seleccionada ? 2 : 1.5}
          strokeDasharray={seleccionada ? undefined : "4 3"}
        />
      )}
    </g>
  );
}
