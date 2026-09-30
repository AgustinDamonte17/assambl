/** Lienzo del editor de planta. Muros a 90° con imanes a extremos y alineaciones, aberturas del
 *  catálogo que se enganchan al muro, ambientes por rectángulo, y arrastre para mover muros y
 *  aberturas. Todo cambio pasa por `operaciones.ts` y se confirma con `aplicar` (una entrada de deshacer). */

import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import type { Punto } from "../../modelo/proyecto";
import {
  buscarAbertura,
  espesor,
  esHorizontal,
  extension,
  largo,
  proyectar,
  type AnalisisPlanta,
  type Casa,
  type ItemCatalogo,
  type Pieza,
} from "../../modelo/casa";
import DibujoPlanta, { aMetros, aPantalla, encuadrar, Tramas, type Vista } from "./DibujoPlanta";
import type { Calco } from "./ImportarImagen";
import { agregarAbertura, agregarAmbiente, agregarMuro, entraAbertura, modificarAbertura, moverMuro, redondear } from "./operaciones";

export type Herramienta = "seleccionar" | "muro" | "abertura" | "ambiente";

interface Props {
  casa: Casa;
  analisis: AnalisisPlanta | null;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
  seleccion: Pieza | null;
  setSeleccion: (p: Pieza | null) => void;
  herramienta: Herramienta;
  setHerramienta: (h: Herramienta) => void;
  item: ItemCatalogo | null;
  sistemaMuro: string;
  verEstados: boolean;
  calco: Calco | null;
  lote: Punto[] | null;
  resaltadas: Set<string>;
  /** Cambia cuando hay que volver a encuadrar la planta. */
  encuadre: number;
  avisar: (texto: string) => void;
}

type Arrastre =
  | { tipo: "pan"; x: number; y: number; ox: number; oy: number }
  | { tipo: "muro"; id: string; desde: Punto; original: Casa; delta: number }
  | { tipo: "abertura"; id: string; muro: string; agarre: number; original: Casa; pos: number }
  | { tipo: "ambiente"; desde: Punto; hasta: Punto };

const IMAN_PX = 10;

export default function EditorPlanta(p: Props) {
  const caja = useRef<HTMLDivElement>(null);
  const [tam, setTam] = useState({ w: 900, h: 600 });
  const [vista, setVista] = useState<Vista>({ escala: 40, ox: 80, oy: 500 });
  const [cursor, setCursor] = useState<Punto | null>(null);
  const [imanado, setImanado] = useState<Punto | null>(null);
  const [cadena, setCadena] = useState<Punto | null>(null);
  const [arrastre, setArrastre] = useState<Arrastre | null>(null);
  const [temporal, setTemporal] = useState<Casa | null>(null);
  const espacio = useRef(false);

  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setTam({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Encuadre inicial y cuando se pide (casa nueva, botón «encuadrar»).
  useEffect(() => {
    const ext = extension(p.casa) ?? (p.lote?.length ? extLote(p.lote) : { x0: -2, y0: -2, x1: 18, y1: 12 });
    setVista(encuadrar(ext, tam.w, tam.h, 60));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.encuadre, tam.w > 0 && tam.h > 0 ? Math.round(tam.w / 50) : 0]);

  useEffect(() => {
    if (p.herramienta !== "muro") setCadena(null);
  }, [p.herramienta]);

  useEffect(() => {
    const abajo = (e: KeyboardEvent) => {
      if (e.code === "Space" && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        espacio.current = true;
      }
      if (e.key === "Escape") setCadena(null);
    };
    const arriba = (e: KeyboardEvent) => {
      if (e.code === "Space") espacio.current = false;
    };
    window.addEventListener("keydown", abajo);
    window.addEventListener("keyup", arriba);
    return () => {
      window.removeEventListener("keydown", abajo);
      window.removeEventListener("keyup", arriba);
    };
  }, []);

  const casa = temporal ?? p.casa;

  /* ------------------------------------------------ imanes */

  const puntosIman = useMemo(() => {
    const pts: Punto[] = [];
    for (const m of p.casa.muros) pts.push(m.eje.desde_m, m.eje.hasta_m);
    return pts;
  }, [p.casa.muros]);

  const paso = vista.escala > 60 ? 0.05 : vista.escala > 25 ? 0.1 : 0.25;

  const imantar = useCallback(
    (raw: Punto, origen: Punto | null): { p: Punto; iman: boolean } => {
      const tol = IMAN_PX / vista.escala;
      let q: Punto = [raw[0], raw[1]];
      // Ortogonal respecto del punto anterior: gana el eje con más recorrido.
      if (origen) {
        if (Math.abs(q[0] - origen[0]) >= Math.abs(q[1] - origen[1])) q = [q[0], origen[1]];
        else q = [origen[0], q[1]];
      }
      // Imán a extremos de muros (solo si respeta la ortogonalidad).
      for (const e of [...puntosIman, ...(origen ? [origen] : [])]) {
        if (Math.hypot(e[0] - q[0], e[1] - q[1]) < tol * 1.3) {
          if (!origen || Math.abs(e[0] - origen[0]) < 1e-6 || Math.abs(e[1] - origen[1]) < 1e-6) return { p: e, iman: true };
        }
      }
      // Alineación con extremos existentes en la coordenada libre, y si no, grilla.
      let iman = false;
      const libre = origen ? (q[1] === origen[1] ? [0] : [1]) : [0, 1];
      for (const k of libre) {
        const cerca = puntosIman.find((e) => Math.abs(e[k] - q[k]) < tol);
        if (cerca) {
          q[k] = cerca[k];
          iman = true;
        } else q[k] = redondear(q[k], paso);
      }
      return { p: q, iman };
    },
    [puntosIman, vista.escala, paso],
  );

  /* ------------------------------------------------ utilidades de puntero */

  const metrosDe = (e: { clientX: number; clientY: number }): Punto => {
    const r = caja.current!.getBoundingClientRect();
    return aMetros(vista, e.clientX - r.left, e.clientY - r.top);
  };

  const muroCercano = (q: Punto) => {
    let mejor: { id: string; t: number; dist: number } | null = null;
    for (const m of casa.muros) {
      const { t, dist } = proyectar(m, q);
      if (t < 0 || t > largo(m)) continue;
      const lim = espesor(casa, m.sistema) / 2 + 8 / vista.escala;
      if (dist <= lim && (!mejor || dist < mejor.dist)) mejor = { id: m.id, t, dist };
    }
    return mejor;
  };

  /* ------------------------------------------------ eventos */

  const alBajar = (e: ReactPointerEvent<SVGSVGElement>) => {
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    const q = metrosDe(e);
    if (e.button === 1 || e.button === 2 || espacio.current) {
      setArrastre({ tipo: "pan", x: e.clientX, y: e.clientY, ox: vista.ox, oy: vista.oy });
      return;
    }
    if (p.herramienta === "muro") {
      const { p: punto } = imantar(q, cadena);
      if (!cadena) {
        setCadena(punto);
        return;
      }
      if (Math.hypot(punto[0] - cadena[0], punto[1] - cadena[1]) < 0.1) return;
      const r = agregarMuro(p.casa, cadena, punto, p.sistemaMuro);
      p.aplicar(r.casa, { tipo: "muro", id: r.id });
      // Si cerró sobre un extremo existente, termina la cadena.
      const cerro = puntosIman.some((x) => Math.hypot(x[0] - punto[0], x[1] - punto[1]) < 1e-6);
      setCadena(cerro ? null : punto);
      return;
    }
    if (p.herramienta === "ambiente") {
      const s = imantar(q, null).p;
      setArrastre({ tipo: "ambiente", desde: s, hasta: s });
      return;
    }
    if (p.herramienta === "abertura") {
      colocarAbertura(q);
      return;
    }
    // Seleccionar sobre el fondo: deselecciona y panea.
    p.setSeleccion(null);
    setArrastre({ tipo: "pan", x: e.clientX, y: e.clientY, ox: vista.ox, oy: vista.oy });
  };

  const colocarAbertura = (q: Punto) => {
    if (!p.item) {
      p.avisar("Elegí primero qué abertura poner en el panel de la derecha.");
      return;
    }
    const c = muroCercano(q);
    if (!c) {
      p.avisar("Las aberturas van sobre un muro: hacé clic encima de uno.");
      return;
    }
    const muro = casa.muros.find((m) => m.id === c.id)!;
    const pos = redondear(c.t - p.item.ancho_m / 2);
    if (!entraAbertura(muro, pos, p.item.ancho_m)) {
      p.avisar(`No entra una abertura de ${p.item.ancho_m.toFixed(2)} m ahí: pisa otra o se sale del muro.`);
      return;
    }
    const r = agregarAbertura(p.casa, c.id, p.item, pos);
    p.aplicar(r.casa, { tipo: "abertura", id: r.id, muro: c.id });
  };

  const alTocarPieza = (pieza: Pieza, e: ReactPointerEvent) => {
    if (e.button !== 0 || espacio.current) return;
    if (p.herramienta === "abertura" && pieza.tipo !== "ambiente") {
      e.stopPropagation();
      colocarAbertura(metrosDe(e));
      return;
    }
    if (p.herramienta !== "seleccionar") return;
    e.stopPropagation();
    (caja.current?.querySelector("svg") as SVGSVGElement | null)?.setPointerCapture(e.pointerId);
    p.setSeleccion(pieza);
    const q = metrosDe(e);
    if (pieza.tipo === "muro") {
      setArrastre({ tipo: "muro", id: pieza.id, desde: q, original: p.casa, delta: 0 });
    } else if (pieza.tipo === "abertura") {
      const hallada = buscarAbertura(p.casa, pieza.id);
      if (!hallada) return;
      const t = proyectar(hallada.muro, q).t;
      setArrastre({ tipo: "abertura", id: pieza.id, muro: pieza.muro, agarre: t - hallada.abertura.posicion_m, original: p.casa, pos: hallada.abertura.posicion_m });
    }
  };

  const alMover = (e: ReactPointerEvent<SVGSVGElement>) => {
    const q = metrosDe(e);
    setCursor(q);
    if (p.herramienta === "muro" && !arrastre) {
      const r = imantar(q, cadena);
      setImanado(r.iman ? r.p : null);
    }
    if (!arrastre) return;
    if (arrastre.tipo === "pan") {
      setVista((v) => ({ ...v, ox: arrastre.ox + e.clientX - arrastre.x, oy: arrastre.oy + e.clientY - arrastre.y }));
    } else if (arrastre.tipo === "muro") {
      const m = arrastre.original.muros.find((x) => x.id === arrastre.id);
      if (!m) return;
      const bruto = esHorizontal(m) ? q[1] - arrastre.desde[1] : q[0] - arrastre.desde[0];
      const delta = redondear(bruto, paso);
      if (delta !== arrastre.delta) {
        setArrastre({ ...arrastre, delta });
        setTemporal(delta ? moverMuro(arrastre.original, arrastre.id, delta) : null);
      }
    } else if (arrastre.tipo === "abertura") {
      const h = buscarAbertura(arrastre.original, arrastre.id);
      if (!h) return;
      const pos = redondear(proyectar(h.muro, q).t - arrastre.agarre, paso);
      if (pos !== arrastre.pos && entraAbertura(h.muro, pos, h.abertura.ancho_m, arrastre.id)) {
        setArrastre({ ...arrastre, pos });
        setTemporal(modificarAbertura(arrastre.original, arrastre.muro, arrastre.id, { posicion_m: pos }));
      }
    } else if (arrastre.tipo === "ambiente") {
      setArrastre({ ...arrastre, hasta: imantar(q, null).p });
    }
  };

  const alSoltar = () => {
    if (arrastre?.tipo === "muro" || arrastre?.tipo === "abertura") {
      if (temporal) p.aplicar(temporal);
    } else if (arrastre?.tipo === "ambiente") {
      const [a, b] = [arrastre.desde, arrastre.hasta];
      if (Math.abs(a[0] - b[0]) > 0.5 && Math.abs(a[1] - b[1]) > 0.5) {
        const [x0, x1] = [Math.min(a[0], b[0]), Math.max(a[0], b[0])];
        const [y0, y1] = [Math.min(a[1], b[1]), Math.max(a[1], b[1])];
        const n = p.casa.ambientes.length + 1;
        const r = agregarAmbiente(p.casa, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], `Ambiente ${n}`, "otro");
        p.aplicar(r.casa, { tipo: "ambiente", id: r.id });
        p.setHerramienta("seleccionar");
      }
    }
    setArrastre(null);
    setTemporal(null);
  };

  const alRueda = (e: React.WheelEvent) => {
    const r = caja.current!.getBoundingClientRect();
    const sx = e.clientX - r.left;
    const sy = e.clientY - r.top;
    const k = Math.exp(-e.deltaY * 0.0015);
    setVista((v) => {
      const escala = Math.min(Math.max(v.escala * k, 4), 400);
      const f = escala / v.escala;
      return { escala, ox: sx - (sx - v.ox) * f, oy: sy - (sy - v.oy) * f };
    });
  };

  /* ------------------------------------------------ dibujo auxiliar */

  const grilla = useMemo(() => {
    const [x0, y1] = aMetros(vista, 0, 0);
    const [x1, y0] = aMetros(vista, tam.w, tam.h);
    const lineas: { d: string; fuerte: boolean }[] = [];
    const pasoG = vista.escala < 12 ? 5 : 1;
    for (let x = Math.floor(x0 / pasoG) * pasoG; x <= x1; x += pasoG) {
      const [sx] = aPantalla(vista, [x, 0]);
      lineas.push({ d: `M${sx},0V${tam.h}`, fuerte: Math.round(x) % 5 === 0 });
    }
    for (let y = Math.floor(y0 / pasoG) * pasoG; y <= y1; y += pasoG) {
      const [, sy] = aPantalla(vista, [0, y]);
      lineas.push({ d: `M0,${sy}H${tam.w}`, fuerte: Math.round(y) % 5 === 0 });
    }
    return lineas;
  }, [vista, tam]);

  const previa = (() => {
    if (p.herramienta !== "muro" || !cadena || !cursor) return null;
    const fin = imantar(cursor, cadena).p;
    const [a, b] = [aPantalla(vista, cadena), aPantalla(vista, fin)];
    const l = Math.hypot(fin[0] - cadena[0], fin[1] - cadena[1]);
    const e = (espesor(p.casa, p.sistemaMuro) * vista.escala) || 6;
    return (
      <g pointerEvents="none">
        <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="var(--signal)" strokeWidth={e} strokeOpacity={0.35} strokeLinecap="square" />
        <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="var(--signal)" strokeWidth={1.5} />
        <rect x={(a[0] + b[0]) / 2 - 26} y={(a[1] + b[1]) / 2 - 22} width={52} height={16} fill="var(--ink)" />
        <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2 - 10} textAnchor="middle" fontSize={11} fill="var(--concrete)">
          {l.toFixed(2)} m
        </text>
      </g>
    );
  })();

  const fantasmaAbertura = (() => {
    if (p.herramienta !== "abertura" || !p.item || !cursor || arrastre) return null;
    const c = muroCercano(cursor);
    if (!c) return null;
    const m = casa.muros.find((x) => x.id === c.id)!;
    const pos = redondear(c.t - p.item.ancho_m / 2);
    const ok = entraAbertura(m, pos, p.item.ancho_m);
    const d: Punto = [(m.eje.hasta_m[0] - m.eje.desde_m[0]) / largo(m), (m.eje.hasta_m[1] - m.eje.desde_m[1]) / largo(m)];
    const a = aPantalla(vista, [m.eje.desde_m[0] + d[0] * pos, m.eje.desde_m[1] + d[1] * pos]);
    const b = aPantalla(vista, [m.eje.desde_m[0] + d[0] * (pos + p.item.ancho_m), m.eje.desde_m[1] + d[1] * (pos + p.item.ancho_m)]);
    return (
      <g pointerEvents="none">
        <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={ok ? "var(--signal)" : "var(--rebar)"} strokeWidth={espesor(casa, m.sistema) * vista.escala + 4} strokeOpacity={0.5} />
        <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2 - 12} textAnchor="middle" fontSize={10} fill={ok ? "var(--ink)" : "var(--rebar)"}>
          {ok ? p.item.nombre : "no entra"}
        </text>
      </g>
    );
  })();

  const rectAmbiente =
    arrastre?.tipo === "ambiente"
      ? (() => {
          const a = aPantalla(vista, arrastre.desde);
          const b = aPantalla(vista, arrastre.hasta);
          const w = Math.abs(arrastre.hasta[0] - arrastre.desde[0]);
          const h = Math.abs(arrastre.hasta[1] - arrastre.desde[1]);
          return (
            <g pointerEvents="none">
              <rect x={Math.min(a[0], b[0])} y={Math.min(a[1], b[1])} width={Math.abs(b[0] - a[0])} height={Math.abs(b[1] - a[1])} fill="var(--signal)" fillOpacity={0.12} stroke="var(--signal)" strokeDasharray="4 3" />
              <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2} textAnchor="middle" fontSize={11}>
                {w.toFixed(2)} × {h.toFixed(2)} m · {(w * h).toFixed(1)} m²
              </text>
            </g>
          );
        })()
      : null;

  const cotaArrastre =
    arrastre?.tipo === "muro" && arrastre.delta !== 0 && cursor ? (
      <g pointerEvents="none">
        <rect x={aPantalla(vista, cursor)[0] + 12} y={aPantalla(vista, cursor)[1] - 26} width={70} height={16} fill="var(--ink)" />
        <text x={aPantalla(vista, cursor)[0] + 47} y={aPantalla(vista, cursor)[1] - 14} textAnchor="middle" fontSize={11} fill="var(--concrete)">
          {arrastre.delta > 0 ? "+" : ""}
          {arrastre.delta.toFixed(2)} m
        </text>
      </g>
    ) : null;

  const cursorCss =
    arrastre?.tipo === "pan" ? "grabbing" : p.herramienta === "seleccionar" ? "default" : p.herramienta === "abertura" ? "copy" : "crosshair";

  const escalaBarra = [0.5, 1, 2, 5, 10].find((m) => m * vista.escala >= 60) ?? 10;

  return (
    <div ref={caja} className="absolute inset-0 editor-planta bg-concrete" onContextMenu={(e) => e.preventDefault()}>
      <svg
        width={tam.w}
        height={tam.h}
        style={{ cursor: cursorCss }}
        onPointerDown={alBajar}
        onPointerMove={alMover}
        onPointerUp={alSoltar}
        onPointerLeave={() => setCursor(null)}
        onDoubleClick={() => setCadena(null)}
        onWheel={alRueda}
      >
        <Tramas />
        {grilla.map((l, i) => (
          <path key={i} d={l.d} stroke="var(--ink)" strokeOpacity={l.fuerte ? 0.09 : 0.04} />
        ))}
        {p.calco && (
          <image
            href={p.calco.url}
            x={aPantalla(vista, [p.calco.x0, p.calco.y1])[0]}
            y={aPantalla(vista, [p.calco.x0, p.calco.y1])[1]}
            width={(p.calco.x1 - p.calco.x0) * vista.escala}
            height={(p.calco.y1 - p.calco.y0) * vista.escala}
            opacity={p.calco.opacidad}
            preserveAspectRatio="none"
            pointerEvents="none"
          />
        )}
        {p.lote && p.lote.length >= 3 && (
          <g pointerEvents="none">
            <polygon
              points={p.lote.map((q) => aPantalla(vista, q).join(",")).join(" ")}
              fill="none"
              stroke="var(--resolved)"
              strokeWidth={1.2}
              strokeDasharray="8 4"
            />
            <text x={aPantalla(vista, p.lote[0])[0] + 4} y={aPantalla(vista, p.lote[0])[1] - 4} fontSize={10} fill="var(--resolved)">
              lote
            </text>
          </g>
        )}
        <DibujoPlanta
          casa={casa}
          vista={vista}
          analisis={p.analisis}
          translucido={!!p.calco}
          verEstados={p.verEstados}
          seleccion={p.seleccion}
          resaltadas={p.resaltadas}
          onPieza={alTocarPieza}
          interactivo={p.herramienta === "seleccionar" || p.herramienta === "abertura"}
        />
        {previa}
        {fantasmaAbertura}
        {rectAmbiente}
        {cotaArrastre}
        {p.herramienta === "muro" && (cadena || imanado) && (
          <circle
            cx={aPantalla(vista, imanado ?? cadena!)[0]}
            cy={aPantalla(vista, imanado ?? cadena!)[1]}
            r={5}
            fill="none"
            stroke="var(--signal)"
            strokeWidth={2}
            pointerEvents="none"
          />
        )}

        {/* Norte y escala, fijos en pantalla */}
        <g transform={`translate(${tam.w - 40}, 44)`} pointerEvents="none">
          <circle r={18} fill="var(--concrete-2)" stroke="var(--line)" />
          <path d="M0,-14 L6,6 L0,2 L-6,6 Z" fill="var(--ink)" />
          <text y={-20} textAnchor="middle" fontSize={10} fontWeight={700}>
            N
          </text>
        </g>
        <g transform={`translate(16, ${tam.h - 18})`} pointerEvents="none">
          <rect width={escalaBarra * vista.escala} height={4} fill="var(--ink)" />
          <text y={-5} fontSize={10}>
            {escalaBarra} m
          </text>
        </g>
        {cursor && (
          <text x={tam.w - 12} y={tam.h - 10} textAnchor="end" fontSize={10} fill="var(--rebar)" pointerEvents="none">
            x {cursor[0].toFixed(2)} · y {cursor[1].toFixed(2)} m
          </text>
        )}
      </svg>
    </div>
  );
}

function extLote(l: Punto[]) {
  return {
    x0: Math.min(...l.map((p) => p[0])),
    y0: Math.min(...l.map((p) => p[1])),
    x1: Math.max(...l.map((p) => p[0])),
    y1: Math.max(...l.map((p) => p[1])),
  };
}
