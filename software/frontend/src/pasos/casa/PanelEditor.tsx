/** Panel del editor: herramientas, propiedades de lo seleccionado, lo que falta resolver y la leyenda de estados. */

import type { ReactNode } from "react";
import type { Estado } from "../../modelo/proyecto";
import {
  areaPoligono,
  buscarAbertura,
  largo,
  superficieCubierta,
  USOS,
  type AnalisisPlanta,
  type Casa,
  type ItemCatalogo,
  type Pieza,
  type Uso,
} from "../../modelo/casa";
import { Boton, Dato, Etiqueta, Seccion } from "../../componentes/ui";
import type { Herramienta } from "./EditorPlanta";
import { ASPECTO, contarDeclaradas, contarEstados, estadoDe, ORDEN_ESTADOS } from "./estados";
import {
  borrarAbertura,
  borrarAmbiente,
  borrarMuro,
  entraAbertura,
  marcarRevisado,
  modificarAbertura,
  modificarAmbiente,
  modificarMuro,
  redondear,
} from "./operaciones";

const HERRAMIENTAS: { id: Herramienta; nombre: string; tecla: string; ayuda: string }[] = [
  { id: "seleccionar", nombre: "Elegir y mover", tecla: "V", ayuda: "Clic para elegir. Arrastrá un muro para correrlo o una abertura para deslizarla. Espacio + arrastrar o botón derecho para desplazarte; rueda para acercar." },
  { id: "muro", nombre: "Muro", tecla: "M", ayuda: "Clic para empezar y clic en cada quiebre. Los muros salen a 90° y se enganchan a los extremos existentes. Doble clic o Esc para terminar." },
  { id: "abertura", nombre: "Puerta / ventana", tecla: "A", ayuda: "Elegí una abertura del catálogo y hacé clic sobre un muro." },
  { id: "ambiente", nombre: "Ambiente", tecla: "R", ayuda: "Arrastrá un rectángulo para marcar un ambiente y después ponele nombre." },
];

const SISTEMAS = [
  { id: "exterior", nombre: "Exterior 45 × 140" },
  { id: "interior_portante", nombre: "Interior portante" },
  { id: "tabique", nombre: "Tabique 45 × 90" },
];

interface Props {
  casa: Casa;
  analisis: AnalisisPlanta | null;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
  seleccion: Pieza | null;
  setSeleccion: (p: Pieza | null) => void;
  herramienta: Herramienta;
  setHerramienta: (h: Herramienta) => void;
  catalogo: ItemCatalogo[];
  item: ItemCatalogo | null;
  setItem: (i: ItemCatalogo) => void;
  sistemaMuro: string;
  setSistemaMuro: (s: string) => void;
  verEstados: boolean;
  setVerEstados: (v: boolean) => void;
  opacidadCalco: number | null;
  setOpacidadCalco: (v: number) => void;
  quitarCalco: () => void;
  encuadrar: () => void;
  deshacer: (() => void) | null;
  rehacer: (() => void) | null;
  resaltar: (ids: string[]) => void;
  empezarDeNuevo: () => void;
}

export function piezaDeId(casa: Casa, id: string): Pieza | null {
  if (casa.muros.some((m) => m.id === id)) return { tipo: "muro", id };
  const a = buscarAbertura(casa, id);
  if (a) return { tipo: "abertura", id, muro: a.muro.id };
  if (casa.ambientes.some((x) => x.id === id)) return { tipo: "ambiente", id };
  return null;
}

export default function PanelEditor(p: Props) {
  const { casa, analisis } = p;
  const cuenta = contarEstados(casa, analisis);
  const pendientes = (analisis?.verificaciones ?? []).filter((v) => v.estado !== "comprobado_por_reglas");
  const aRevisar = contarDeclaradas(casa);
  const sup = superficieCubierta(casa);
  const ayuda = HERRAMIENTAS.find((h) => h.id === p.herramienta)?.ayuda;

  return (
    <div className="flex flex-col gap-0">
      <Seccion
        titulo="Herramientas"
        accion={
          <span className="flex gap-1">
            <Boton className="px-2 py-0.5" disabled={!p.deshacer} onClick={() => p.deshacer?.()} title="Deshacer (Ctrl+Z)">
              ↶
            </Boton>
            <Boton className="px-2 py-0.5" disabled={!p.rehacer} onClick={() => p.rehacer?.()} title="Rehacer (Ctrl+Shift+Z)">
              ↷
            </Boton>
          </span>
        }
      >
        <div className="grid grid-cols-2 gap-1">
          {HERRAMIENTAS.map((h) => (
            <button
              key={h.id}
              onClick={() => p.setHerramienta(h.id)}
              className={`border px-2 py-1.5 text-left text-xs flex justify-between ${
                p.herramienta === h.id ? "border-signal bg-signal/10" : "border-line hover:border-ink"
              }`}
            >
              {h.nombre}
              <kbd className="text-[10px] text-rebar">{h.tecla}</kbd>
            </button>
          ))}
        </div>
        {ayuda && <p className="text-[10px] text-rebar leading-snug mt-2">{ayuda}</p>}
        {p.herramienta === "muro" && (
          <div className="flex gap-1 mt-2">
            {SISTEMAS.map((s) => (
              <button
                key={s.id}
                onClick={() => p.setSistemaMuro(s.id)}
                className={`flex-1 border px-1 py-1 text-[10px] ${p.sistemaMuro === s.id ? "border-signal bg-signal/10" : "border-line"}`}
              >
                {s.nombre}
              </button>
            ))}
          </div>
        )}
        {p.herramienta === "abertura" && (
          <ul className="mt-2 max-h-56 overflow-y-auto border border-line">
            {p.catalogo.map((it) => (
              <li key={it.codigo}>
                <button
                  onClick={() => p.setItem(it)}
                  className={`w-full text-left px-2 py-1 text-xs flex justify-between border-b border-line/60 ${
                    p.item?.codigo === it.codigo ? "bg-signal/10" : "hover:bg-concrete-2"
                  }`}
                >
                  <span>{it.nombre}</span>
                  <span className="text-rebar text-[10px]">{it.uso}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Seccion>

      <Seccion titulo="Seleccionado">
        {p.seleccion ? (
          <Propiedades {...p} />
        ) : (
          <p className="text-xs text-rebar">Nada. Tocá un muro, una abertura o un ambiente para ver y cambiar sus datos.</p>
        )}
      </Seccion>

      <Seccion titulo={`Para resolver (${pendientes.length})`}>
        {aRevisar > 0 && (
          <div className="border border-warn bg-warn/5 p-2 mb-2">
            <p className="text-[11px] leading-snug">
              {aRevisar} pieza{aRevisar === 1 ? "" : "s"} para revisar: las propuso la IA o cambiaron después de revisarlas.
              Compará con tu dibujo y confirmá.
            </p>
            <Boton className="mt-1.5" onClick={() => p.aplicar(marcarRevisado(casa))}>
              Ya revisé todo
            </Boton>
          </div>
        )}
        {!analisis ? (
          <p className="text-xs text-rebar">Verificando…</p>
        ) : !pendientes.length ? (
          <p className="text-xs text-resolved">Todas las reglas de la planta se cumplen.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {pendientes.map((v, i) => (
              <li key={i}>
                <button
                  className="w-full text-left border-l-2 pl-2 py-0.5 hover:bg-concrete-2"
                  style={{ borderColor: ASPECTO[v.estado].acento }}
                  onMouseEnter={() => p.resaltar(v.piezas)}
                  onMouseLeave={() => p.resaltar([])}
                  onClick={() => {
                    const pieza = v.piezas[0] ? piezaDeId(casa, v.piezas[0]) : null;
                    if (pieza) p.setSeleccion(pieza);
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[11px]" style={{ color: ASPECTO[v.estado].acento }}>
                      {ASPECTO[v.estado].glifo}
                    </span>
                    <span className="text-[11px]">{v.detalle || v.descripcion}</span>
                  </div>
                  <div className="text-[9px] text-rebar">
                    {v.id} · {v.descripcion}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Seccion>

      <Seccion
        titulo="Estados"
        accion={
          <label className="text-[10px] flex items-center gap-1 text-rebar">
            <input type="checkbox" checked={p.verEstados} onChange={(e) => p.setVerEstados(e.target.checked)} />
            ver sobre la planta
          </label>
        }
      >
        <ul className="flex flex-col gap-1">
          {ORDEN_ESTADOS.map((e) => (
            <li key={e} className="flex items-start gap-2" title={ASPECTO[e].explicacion}>
              <Muestra estado={e} />
              <span className="flex-1 text-[11px] leading-tight">
                {ASPECTO[e].nombre}
                <span className="block text-[9px] text-rebar">{ASPECTO[e].explicacion}</span>
              </span>
              <span className="text-[11px] text-rebar">{cuenta[e] ?? 0}</span>
            </li>
          ))}
        </ul>
      </Seccion>

      <Seccion titulo="Vista">
        <div className="flex gap-2 flex-wrap">
          <Boton onClick={p.encuadrar}>Encuadrar</Boton>
          {p.opacidadCalco !== null && <Boton onClick={p.quitarCalco}>Quitar dibujo de fondo</Boton>}
        </div>
        {p.opacidadCalco !== null && (
          <label className="flex items-center gap-2 mt-2 text-[11px] text-rebar">
            Dibujo de fondo
            <input type="range" min={0} max={1} step={0.05} value={p.opacidadCalco} onChange={(e) => p.setOpacidadCalco(parseFloat(e.target.value))} className="flex-1" />
          </label>
        )}
      </Seccion>

      <Seccion titulo="Resumen">
        <div className="text-xs">
          <Dato etiqueta="Superficie cubierta" valor={sup ? sup.toFixed(1) : "—"} sufijo="m²" />
          <Dato
            etiqueta="Muro exterior"
            valor={casa.muros.filter((m) => m.sistema === "exterior").reduce((s, m) => s + largo(m), 0).toFixed(1)}
            sufijo="m"
          />
          <Dato etiqueta="Muros · aberturas" valor={`${casa.muros.length} · ${casa.muros.reduce((s, m) => s + m.aberturas.length, 0)}`} />
          <Dato etiqueta="Ambientes" valor={casa.ambientes.length} />
        </div>
        <button className="text-[11px] text-rebar hover:text-signal mt-3 underline underline-offset-2" onClick={p.empezarDeNuevo}>
          Empezar la planta de nuevo
        </button>
      </Seccion>
    </div>
  );
}

function Muestra({ estado }: { estado: Estado }) {
  const a = ASPECTO[estado];
  return (
    <svg width={30} height={14} className="shrink-0 mt-0.5">
      <rect
        x={1}
        y={3}
        width={20}
        height={8}
        fill={a.trama === "rayado" ? "url(#trama-rayado)" : a.trama === "punteado" ? "url(#trama-punteado)" : a.muro}
        stroke={a.borde ?? "none"}
        strokeDasharray={a.borde ? "3 2" : undefined}
      />
      {a.glifo && (
        <text x={26} y={11} fontSize={10} fontWeight={700} textAnchor="middle" fill={a.acento}>
          {a.glifo}
        </text>
      )}
    </svg>
  );
}

function Fila({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <label className="grid grid-cols-[92px_1fr] items-center gap-2 py-0.5">
      <span className="text-[11px] text-rebar">{etiqueta}</span>
      {children}
    </label>
  );
}

function Numero({ valor, onCambio, paso = 0.05, min, max }: { valor: number; onCambio: (v: number) => void; paso?: number; min?: number; max?: number }) {
  return (
    <span className="flex items-baseline gap-1">
      <input
        key={valor}
        type="number"
        step={paso}
        min={min}
        max={max}
        defaultValue={Number(valor.toFixed(3))}
        onBlur={(e) => {
          const v = parseFloat(e.target.value);
          if (Number.isFinite(v) && Math.abs(v - valor) > 1e-6) onCambio(v);
        }}
        onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
        className="w-full bg-concrete-2 border border-line px-1.5 py-0.5 text-xs focus:outline-none focus:border-signal"
      />
      <span className="text-[10px] text-rebar">m</span>
    </span>
  );
}

function Propiedades(p: Props) {
  const { casa, analisis, seleccion } = p;
  if (!seleccion) return null;
  const estado = estadoDe(casa, seleccion, analisis);
  const reglas = (analisis?.verificaciones ?? []).filter((v) => v.piezas.includes(seleccion.id) && v.estado !== "comprobado_por_reglas");
  const revisar = () => p.aplicar(marcarRevisado(casa, new Set([seleccion.id])), seleccion);
  const encabezado = (titulo: string) => (
    <div className="flex items-start justify-between gap-2 mb-1.5">
      <div>
        <div className="text-sm font-semibold">{titulo}</div>
        <div className="text-[10px] text-rebar">{seleccion.id}</div>
      </div>
      <Etiqueta estado={estado} />
    </div>
  );
  const pie = (borrar: () => void) => (
    <>
      {reglas.map((v, i) => (
        <p key={i} className="text-[10px] leading-snug border-l-2 pl-2 mt-1" style={{ borderColor: ASPECTO[v.estado].acento }}>
          {v.detalle || v.descripcion}
        </p>
      ))}
      <div className="flex gap-2 mt-2">
        <Boton onClick={revisar} disabled={estado === "revisado"} title="Confirmás que esta pieza está bien">
          ✓ Revisado
        </Boton>
        <Boton onClick={borrar}>Borrar</Boton>
      </div>
    </>
  );

  if (seleccion.tipo === "muro") {
    const m = casa.muros.find((x) => x.id === seleccion.id);
    if (!m) return null;
    const L = largo(m);
    return (
      <div>
        {encabezado(`Muro ${m.lado_exterior ? `· ${m.lado_exterior}` : ""}`)}
        <Fila etiqueta="Sistema">
          <select
            value={m.sistema}
            onChange={(e) => p.aplicar(modificarMuro(casa, m.id, { sistema: e.target.value }), seleccion)}
            className="bg-concrete-2 border border-line px-1 py-0.5 text-xs"
          >
            {SISTEMAS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
            {!SISTEMAS.some((s) => s.id === m.sistema) && <option value={m.sistema}>{m.sistema}</option>}
          </select>
        </Fila>
        <Fila etiqueta="Largo">
          <Numero
            valor={L}
            min={0.3}
            onCambio={(v) => {
              const d = [(m.eje.hasta_m[0] - m.eje.desde_m[0]) / L, (m.eje.hasta_m[1] - m.eje.desde_m[1]) / L];
              const hasta: [number, number] = [redondear(m.eje.desde_m[0] + d[0] * v, 0.005), redondear(m.eje.desde_m[1] + d[1] * v, 0.005)];
              p.aplicar(modificarMuro(casa, m.id, { eje: { desde_m: m.eje.desde_m, hasta_m: hasta } }), seleccion);
            }}
          />
        </Fila>
        <div className="text-[10px] text-rebar">
          eje ({m.eje.desde_m.map((v) => v.toFixed(2)).join(", ")}) → ({m.eje.hasta_m.map((v) => v.toFixed(2)).join(", ")}) ·{" "}
          {m.aberturas.length} abertura{m.aberturas.length === 1 ? "" : "s"}
        </div>
        {pie(() => p.aplicar(borrarMuro(casa, m.id), null))}
      </div>
    );
  }

  if (seleccion.tipo === "abertura") {
    const h = buscarAbertura(casa, seleccion.id);
    if (!h) return null;
    const { muro, abertura: o } = h;
    const cambiar = (c: Partial<typeof o>) => p.aplicar(modificarAbertura(casa, muro.id, o.id, c), seleccion);
    const item = p.catalogo.find((i) => i.codigo === o.catalogo);
    return (
      <div>
        {encabezado(item?.nombre ?? o.tipo)}
        <Fila etiqueta="Catálogo">
          <select
            value={o.catalogo ?? ""}
            onChange={(e) => {
              const it = p.catalogo.find((i) => i.codigo === e.target.value);
              if (!it) return;
              if (!entraAbertura(muro, o.posicion_m, it.ancho_m, o.id)) {
                alert(`No entra una abertura de ${it.ancho_m} m en esa posición.`);
                return;
              }
              cambiar({
                catalogo: it.codigo,
                tipo: it.tipo,
                ancho_m: it.ancho_m,
                antepecho_m: it.antepecho_m,
                dintel_m: Math.round((it.antepecho_m + it.alto_m) * 1000) / 1000,
                ...(it.tipo === "puerta" && !o.hoja ? { hoja: { bisagra: "inicio" as const, apertura_deg: 70 } } : {}),
              });
            }}
            className="bg-concrete-2 border border-line px-1 py-0.5 text-xs"
          >
            {!item && <option value="">a medida ({o.tipo})</option>}
            {p.catalogo.map((i) => (
              <option key={i.codigo} value={i.codigo}>
                {i.nombre}
              </option>
            ))}
          </select>
        </Fila>
        <Fila etiqueta="Desde el inicio">
          <Numero valor={o.posicion_m} onCambio={(v) => entraAbertura(muro, v, o.ancho_m, o.id) && cambiar({ posicion_m: redondear(v, 0.005) })} />
        </Fila>
        <Fila etiqueta="Ancho">
          <Numero valor={o.ancho_m} min={0.3} onCambio={(v) => entraAbertura(muro, o.posicion_m, v, o.id) && cambiar({ ancho_m: v, catalogo: null })} />
        </Fila>
        <Fila etiqueta="Antepecho">
          <Numero valor={o.antepecho_m} min={0} onCambio={(v) => cambiar({ antepecho_m: v })} />
        </Fila>
        <Fila etiqueta="Dintel">
          <Numero valor={o.dintel_m} min={0.5} onCambio={(v) => cambiar({ dintel_m: v })} />
        </Fila>
        {o.tipo === "puerta" && (
          <div className="flex gap-2 mt-1">
            <Boton onClick={() => cambiar({ hoja: { bisagra: o.hoja?.bisagra === "fin" ? "inicio" : "fin", apertura_deg: o.hoja?.apertura_deg ?? 70 } })}>
              Cambiar bisagra
            </Boton>
            <Boton onClick={() => cambiar({ hoja: { bisagra: o.hoja?.bisagra ?? "inicio", apertura_deg: -(o.hoja?.apertura_deg ?? 70) } })}>
              Abrir hacia el otro lado
            </Boton>
          </div>
        )}
        <div className="text-[10px] text-rebar mt-1">en {muro.id} ({largo(muro).toFixed(2)} m)</div>
        {pie(() => p.aplicar(borrarAbertura(casa, muro.id, o.id), null))}
      </div>
    );
  }

  const a = casa.ambientes.find((x) => x.id === seleccion.id);
  if (!a) return null;
  return (
    <div>
      {encabezado(a.nombre)}
      <Fila etiqueta="Nombre">
        <input
          key={a.id + a.nombre}
          autoFocus={/^Ambiente \d+$/.test(a.nombre)}
          defaultValue={a.nombre}
          onFocus={(e) => e.target.select()}
          onBlur={(e) => e.target.value.trim() && e.target.value !== a.nombre && p.aplicar(modificarAmbiente(casa, a.id, { nombre: e.target.value.trim() }), seleccion)}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
          className="bg-concrete-2 border border-line px-1.5 py-0.5 text-xs focus:outline-none focus:border-signal"
        />
      </Fila>
      <Fila etiqueta="Uso">
        <select
          value={a.uso}
          onChange={(e) => p.aplicar(modificarAmbiente(casa, a.id, { uso: e.target.value as Uso }), seleccion)}
          className="bg-concrete-2 border border-line px-1 py-0.5 text-xs"
        >
          {USOS.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nombre}
            </option>
          ))}
        </select>
      </Fila>
      <div className="text-xs mt-1">
        <Dato etiqueta="Superficie" valor={a.contorno_m ? areaPoligono(a.contorno_m).toFixed(1) : "sin contorno"} sufijo={a.contorno_m ? "m²" : undefined} />
      </div>
      {pie(() => p.aplicar(borrarAmbiente(casa, a.id), null))}
    </div>
  );
}
