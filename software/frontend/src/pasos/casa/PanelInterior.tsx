/** Panel de la vista 3D: cámara y corte, lo seleccionado, catálogo de muebles, galería, amoblado y Lumo. */

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/cliente";
import Lumo, { type LumoState } from "../../componentes/lumo/Lumo";
import { Boton, Dato, Etiqueta, Seccion } from "../../componentes/ui";
import type { Punto } from "../../modelo/proyecto";
import {
  alturaMuros,
  areaPoligono,
  superficieCubierta,
  superficieGaleria,
  USOS,
  USOS_EXTERIORES,
  type AnalisisPlanta,
  type Casa,
  type MensajeChat,
  type Pieza,
} from "../../modelo/casa";
import { CATALOGO_MUEBLES, CATEGORIAS, piezasInterior, type ItemMueble } from "../../modelo/muebles";
import { estadoDe } from "./estados";
import { agregarPieza, borrarAmbiente, moverMuro } from "./operaciones";
import { PropiedadesMueble } from "./PropiedadesMueble";
import type { Camara3D } from "./VistaCasa3D";

export interface Propuesta {
  casa: Casa;
  mensaje: string;
  nuevas: Set<string>;
}

interface Props {
  casa: Casa;
  analisis: AnalisisPlanta | null;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
  seleccion: Pieza | null;
  setSeleccion: (p: Pieza | null) => void;
  apiOk: boolean | null;
  lat: number | null;
  camara: Camara3D;
  setCamara: (c: Camara3D) => void;
  corte: number;
  setCorte: (v: number) => void;
  verMuebles: boolean;
  setVerMuebles: (v: boolean) => void;
  exportar: () => void;
  irAPlanta: (p: Pieza | null) => void;
  resaltar: (ids: string[]) => void;
  avisar: (t: string) => void;
  propuesta: Propuesta | null;
  setPropuesta: (p: Propuesta | null) => void;
  historial: MensajeChat[];
  setHistorial: (h: MensajeChat[]) => void;
}

const CAMARAS: { id: Camara3D; nombre: string }[] = [
  { id: "suroeste", nombre: "SO" },
  { id: "sureste", nombre: "SE" },
  { id: "noreste", nombre: "NE" },
  { id: "noroeste", nombre: "NO" },
  { id: "planta", nombre: "Planta" },
  { id: "recorrido", nombre: "Recorrer" },
];

export default function PanelInterior(p: Props) {
  const { casa, analisis } = p;
  const H = alturaMuros(casa);
  const [categoria, setCategoria] = useState("estar");
  const [ocupado, setOcupado] = useState<string | null>(null);
  const galeria = casa.ambientes.find((a) => USOS_EXTERIORES.includes(a.uso));
  const conApi = p.apiOk !== false;

  const destino = (): string | null => {
    const s = p.seleccion;
    if (s?.tipo === "ambiente") return s.id;
    if (s?.tipo === "mueble") return piezasInterior(casa).find((x) => x.id === s.id)?.ambiente ?? null;
    return null;
  };

  const agregar = async (it: ItemMueble) => {
    const elegido = destino();
    const sugerido = casa.ambientes.find(
      (a) => a.contorno_m && ((it.sugerido_para ?? it.usos ?? []).includes(a.uso) || (!it.interior && USOS_EXTERIORES.includes(a.uso))),
    );
    const amb = casa.ambientes.find((a) => a.id === elegido) ?? sugerido ?? casa.ambientes.find((a) => a.contorno_m);
    if (!amb?.contorno_m) {
      p.avisar("Elegí primero un ambiente (tocá su piso) para saber dónde ponerlo.");
      return;
    }
    if (conApi) {
      setOcupado(it.codigo);
      try {
        const r = await api.colocar(casa, it.codigo, amb.id);
        if (r.pieza) p.aplicar(r.casa, { tipo: "mueble", id: r.pieza.id });
        else p.avisar(r.motivo);
      } catch (e) {
        p.avisar(`No pude ubicarlo: ${(e as Error).message}`);
      } finally {
        setOcupado(null);
      }
      return;
    }
    const c = centro(amb.contorno_m);
    const r = agregarPieza(casa, it.codigo, c, 0, amb.id);
    p.aplicar(r.casa, { tipo: "mueble", id: r.id });
  };

  const amoblar = async (ambientes: string[] | null, reemplazar: boolean) => {
    setOcupado("amoblar");
    try {
      const r = await api.amoblar(casa, ambientes, reemplazar);
      p.aplicar(r.casa, null);
      if (r.notas.length) p.avisar(r.notas.join(" "));
    } catch (e) {
      p.avisar(`No pude amoblar: ${(e as Error).message}`);
    } finally {
      setOcupado(null);
    }
  };

  const items = CATALOGO_MUEBLES.filter((i) => i.categoria === categoria);
  const interior = (analisis?.verificaciones ?? []).filter((v) => v.id.startsWith("RI") && v.estado !== "comprobado_por_reglas");
  const sup = superficieCubierta(casa);
  const supGaleria = superficieGaleria(casa);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        <Seccion titulo="Vista">
          <div className="grid grid-cols-6 gap-1">
            {CAMARAS.map((c) => (
              <button
                key={c.id}
                onClick={() => p.setCamara(c.id)}
                title={c.id === "recorrido" ? "A la altura de los ojos, dentro del ambiente elegido" : `Vista ${c.nombre}`}
                className={`border py-1 text-[11px] ${c.id === "planta" || c.id === "recorrido" ? "col-span-3" : "col-span-3 sm:col-span-1"} ${
                  p.camara === c.id ? "border-signal bg-signal/10" : "border-line hover:border-ink"
                }`}
              >
                {c.nombre}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-2 mt-3 text-xs">
            <span className="text-rebar w-14">Muros</span>
            <input type="range" min={0.3} max={H} step={0.05} value={p.corte} onChange={(e) => p.setCorte(parseFloat(e.target.value))} className="flex-1 min-w-0" />
            <span className="font-label text-[11px] w-16 text-right whitespace-nowrap">{p.corte >= H - 0.01 ? "enteros" : `${p.corte.toFixed(2)} m`}</span>
          </label>
          <div className="flex items-center justify-between mt-2">
            <label className="text-xs flex items-center gap-1.5 text-rebar">
              <input type="checkbox" checked={p.verMuebles} onChange={(e) => p.setVerMuebles(e.target.checked)} />
              Muebles
            </label>
            <Boton onClick={p.exportar}>Exportar imagen</Boton>
          </div>
          <p className="text-[11px] text-rebar leading-snug mt-2">
            Arrastrá el fondo para girar, rueda para acercar, botón derecho para desplazar. Tocá un mueble para elegirlo y
            arrastralo para moverlo; <span className="font-label">R</span> lo gira.
          </p>
        </Seccion>

        <Seccion titulo="Seleccionado">
          <Seleccionado {...p} amoblar={amoblar} ocupado={ocupado} />
        </Seccion>

        <Seccion titulo="Agregar">
          <div className="flex flex-wrap gap-1 mb-2">
            {CATEGORIAS.map((c) => (
              <button
                key={c.id}
                onClick={() => setCategoria(c.id)}
                className={`border px-2 py-0.5 text-[11px] ${categoria === c.id ? "border-signal bg-signal/10" : "border-line hover:border-ink"}`}
              >
                {c.nombre}
              </button>
            ))}
          </div>
          <ul className="border border-line max-h-56 overflow-y-auto">
            {items.map((it) => (
              <li key={it.codigo}>
                <button
                  disabled={!!ocupado}
                  onClick={() => agregar(it)}
                  title={it.nota ?? `Se ubica donde entre, con ${Math.round(it.frente_libre_m * 100)} cm libres delante`}
                  className="w-full text-left px-2 py-1 text-xs flex justify-between items-baseline gap-2 border-b border-line/60 hover:bg-concrete-2 disabled:opacity-50"
                >
                  <span className="truncate">{ocupado === it.codigo ? "Ubicando…" : it.nombre}</span>
                  <span className="font-label text-[10px] text-rebar shrink-0">
                    {it.medidas_m[0].toFixed(2)} × {it.medidas_m[1].toFixed(2)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <p className="text-[11px] text-rebar mt-1.5 leading-snug">
            Va al ambiente elegido{destino() ? ` («${casa.ambientes.find((a) => a.id === destino())?.nombre}»)` : " o al que le corresponde"}, contra un
            muro y con su espacio de uso libre.
          </p>
        </Seccion>

        <Seccion titulo="Galería">
          {galeria ? (
            <>
              <div className="text-xs">
                <Dato etiqueta={galeria.nombre} valor={areaPoligono(galeria.contorno_m ?? []).toFixed(1)} sufijo="m²" />
              </div>
              <div className="flex gap-2 mt-2 flex-wrap">
                <Boton disabled={!conApi || !!ocupado} onClick={() => amoblar([galeria.id], true)}>
                  Amoblarla de nuevo
                </Boton>
                <Boton
                  onClick={() => {
                    const sin = borrarAmbiente(casa, galeria.id);
                    const fuera = (l?: typeof casa.mobiliario) => l?.filter((x) => x.ambiente !== galeria.id);
                    p.aplicar({ ...sin, mobiliario: fuera(sin.mobiliario), artefactos: fuera(sin.artefactos) }, null);
                  }}
                >
                  Quitar
                </Boton>
              </div>
            </>
          ) : (
            <NuevaGaleria {...p} conApi={conApi} />
          )}
        </Seccion>

        <Seccion titulo="Amoblado">
          <div className="flex gap-2 flex-wrap">
            <Boton disabled={!conApi || !!ocupado} onClick={() => amoblar(null, false)}>
              Amoblar lo vacío
            </Boton>
            <Boton
              disabled={!conApi || !!ocupado}
              onClick={() => {
                if (piezasInterior(casa).length && !confirm("Se reemplazan todos los muebles por una propuesta nueva (podés deshacerlo). ¿Seguir?")) return;
                amoblar(casa.ambientes.map((a) => a.id), true);
              }}
            >
              Proponer todo de nuevo
            </Boton>
          </div>
          {!conApi && <p className="text-[11px] text-rebar mt-2">Sin conexión con la API: agregá muebles a mano desde el catálogo.</p>}
        </Seccion>

        <Seccion titulo={`Interior · para resolver (${interior.length})`}>
          {!interior.length ? (
            <p className="text-xs text-resolved">{analisis ? "Los muebles tienen su espacio y no tapan puertas." : "Verificando…"}</p>
          ) : (
            <ul className="flex flex-col gap-1">
              {interior.map((v, i) => (
                <li key={i}>
                  <button
                    className="w-full text-left border-l-2 border-warn pl-2 py-0.5 hover:bg-concrete-2"
                    onMouseEnter={() => p.resaltar(v.piezas)}
                    onMouseLeave={() => p.resaltar([])}
                    onClick={() => v.piezas[0] && p.setSeleccion(piezaDe(casa, v.piezas[0]))}
                  >
                    <div className="text-xs leading-snug">{v.detalle || v.descripcion}</div>
                    <div className="text-[10px] text-rebar">
                      <span className="font-label">{v.id}</span> · {v.descripcion}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Seccion>

        <Seccion titulo="Resumen">
          <div className="text-xs">
            <Dato etiqueta="Superficie cubierta" valor={sup ? sup.toFixed(1) : "—"} sufijo="m²" />
            {supGaleria > 0 && <Dato etiqueta="Galería" valor={supGaleria.toFixed(1)} sufijo="m²" />}
            <Dato etiqueta="Muebles y artefactos" valor={piezasInterior(casa).length} />
          </div>
        </Seccion>
      </div>
      <LumoInterior {...p} />
    </div>
  );
}

function piezaDe(casa: Casa, id: string): Pieza | null {
  if (piezasInterior(casa).some((x) => x.id === id)) return { tipo: "mueble", id };
  if (casa.ambientes.some((a) => a.id === id)) return { tipo: "ambiente", id };
  if (casa.muros.some((m) => m.id === id)) return { tipo: "muro", id };
  return null;
}

function centro(c: Punto[]): Punto {
  return [c.reduce((s, v) => s + v[0], 0) / c.length, c.reduce((s, v) => s + v[1], 0) / c.length];
}

function Seleccionado(p: Props & { amoblar: (a: string[] | null, r: boolean) => void; ocupado: string | null }) {
  const { casa, seleccion: s, analisis } = p;
  if (!s) return <p className="text-xs text-rebar">Nada. Tocá un mueble, un piso o un muro.</p>;
  if (s.tipo === "mueble") return <PropiedadesMueble casa={casa} id={s.id} analisis={analisis} aplicar={p.aplicar} />;
  if (s.tipo === "ambiente") {
    const a = casa.ambientes.find((x) => x.id === s.id);
    if (!a) return null;
    const n = piezasInterior(casa).filter((x) => x.ambiente === a.id).length;
    return (
      <div>
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="font-head text-sm font-bold leading-snug">{a.nombre}</div>
          <Etiqueta estado={estadoDe(casa, s, analisis)} />
        </div>
        <div className="text-xs">
          <Dato etiqueta="Uso" valor={<span className="font-body">{USOS.find((u) => u.id === a.uso)?.nombre ?? a.uso}</span>} />
          {a.contorno_m && <Dato etiqueta="Superficie" valor={areaPoligono(a.contorno_m).toFixed(1)} sufijo="m²" />}
          <Dato etiqueta="Piezas" valor={n} />
        </div>
        <div className="flex gap-2 mt-2 flex-wrap">
          <Boton disabled={p.apiOk === false || !!p.ocupado} onClick={() => p.amoblar([a.id], true)}>
            {n ? "Amoblar de nuevo" : "Amoblar"}
          </Boton>
          <Boton onClick={() => p.irAPlanta(s)}>Editar en planta →</Boton>
        </div>
      </div>
    );
  }
  const etiqueta = s.tipo === "muro" ? `Muro ${s.id}` : `Abertura ${s.id}`;
  return (
    <div>
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="font-head text-sm font-bold leading-snug">{etiqueta}</div>
        <Etiqueta estado={estadoDe(casa, s, analisis)} />
      </div>
      <p className="text-xs text-rebar leading-snug mb-2">Muros y aberturas se editan en la planta: el cambio se ve acá enseguida.</p>
      <Boton onClick={() => p.irAPlanta(s)}>Editar en planta →</Boton>
    </div>
  );
}

function NuevaGaleria(p: Props & { conApi: boolean }) {
  const soleado = p.lat !== null && p.lat > 0 ? "sur" : "norte";
  const [lado, setLado] = useState<string>(soleado);
  const [fondo, setFondo] = useState(3);
  const [ocupado, setOcupado] = useState(false);
  const crear = async () => {
    setOcupado(true);
    try {
      const r = await api.galeria(p.casa, lado, fondo, p.lat);
      p.aplicar(r.casa, { tipo: "ambiente", id: r.galeria });
      if (r.notas.length) p.avisar(r.notas.join(" "));
    } catch (e) {
      p.avisar(`No pude armar la galería: ${(e as Error).message}`);
    } finally {
      setOcupado(false);
    }
  };
  return (
    <div>
      <p className="text-xs text-rebar leading-snug mb-2">
        Un espacio techado afuera, pegado a un muro exterior. Del lado {soleado} recibe el sol de invierno.
      </p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <label className="flex flex-col gap-1">
          <span className="font-label text-[11px] uppercase tracking-wide text-rebar">Lado</span>
          <select value={lado} onChange={(e) => setLado(e.target.value)} className="bg-concrete-2 border border-line px-1 py-0.5">
            {["norte", "sur", "este", "oeste"].map((l) => (
              <option key={l} value={l}>
                {l[0].toUpperCase() + l.slice(1)}
                {l === soleado ? " (sol)" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="font-label text-[11px] uppercase tracking-wide text-rebar">Fondo</span>
          <select value={fondo} onChange={(e) => setFondo(parseFloat(e.target.value))} className="bg-concrete-2 border border-line px-1 py-0.5 font-label">
            {[2, 2.5, 3, 3.5, 4].map((f) => (
              <option key={f} value={f}>
                {f.toFixed(1)} m
              </option>
            ))}
          </select>
        </label>
      </div>
      <Boton primario className="mt-2" disabled={!p.conApi || ocupado} onClick={crear}>
        {ocupado ? "Armando…" : "Agregar galería"}
      </Boton>
    </div>
  );
}

/* ---------------------------------------------------------------- Lumo */

function LumoInterior(p: Props) {
  const [texto, setTexto] = useState("");
  const [estado, setEstado] = useState<LumoState>("idle");
  const fin = useRef<HTMLDivElement>(null);
  const sinApi = p.apiOk === false;

  useEffect(() => {
    fin.current?.scrollIntoView({ block: "end" });
  }, [p.historial.length]);

  const enviar = async () => {
    const t = texto.trim();
    if (!t || estado === "think") return;
    const h: MensajeChat[] = [...p.historial, { rol: "usuario", texto: t }];
    p.setHistorial(h);
    setTexto("");
    setEstado("think");
    try {
      const r = await api.conversarInterior(p.casa, h, p.lat);
      let casa = r.casa;
      for (const pend of r.pendientes) casa = moverMuro(casa, pend.muro, pend.delta_m);
      const antes = new Set(piezasInterior(p.casa).map((x) => x.id));
      const nuevas = new Set(piezasInterior(casa).filter((x) => !antes.has(x.id)).map((x) => x.id));
      const notas = r.notas.length ? ` ${r.notas.join(" ")}` : "";
      p.setHistorial([...h, { rol: "asistente", texto: r.mensaje + notas }]);
      const cambia = JSON.stringify(casa) !== JSON.stringify(p.casa);
      p.setPropuesta(cambia ? { casa, mensaje: r.mensaje, nuevas } : null);
      setEstado(cambia ? "success" : "reply");
    } catch (e) {
      p.setHistorial([...h, { rol: "asistente", texto: `Ups, no pude: ${(e as Error).message}` }]);
      setEstado("oops");
    }
  };

  const ultimo = useMemo(() => p.historial.slice(-6), [p.historial]);
  const lumoEstado: LumoState = sinApi ? "sleep" : texto ? "listen" : estado;

  return (
    <div className="border-t border-line bg-concrete-2 p-3 flex flex-col gap-2 max-h-[46%] min-h-[150px]">
      <div className="flex items-center gap-2">
        <Lumo state={lumoEstado} size={34} />
        <div className="font-head text-sm font-bold">Lumo</div>
        <span className="font-label text-[10px] uppercase tracking-wide text-rebar ml-auto">muebles y espacios</span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-1.5 text-xs leading-snug">
        {!ultimo.length && (
          <p className="text-rebar">
            Pedime cosas como «sumá un escritorio en la oficina», «cambiá la cama por una queen», «armá una galería al
            norte» o «agrandá el baño».
          </p>
        )}
        {ultimo.map((m, i) => (
          <div key={i} className={m.rol === "usuario" ? "self-end bg-ink text-concrete px-2 py-1 max-w-[85%]" : "bg-concrete border border-line px-2 py-1 max-w-[92%]"}>
            {m.texto}
          </div>
        ))}
        {estado === "think" && <div className="text-rebar">Lumo está pensando…</div>}
        <div ref={fin} />
      </div>
      {p.propuesta && (
        <div className="border border-[#6c4dff] bg-[#6c4dff]/10 px-2 py-1.5 text-xs flex items-center gap-2">
          <span className="flex-1 leading-snug">Vista previa de la propuesta.</span>
          <Boton
            primario
            onClick={() => {
              p.aplicar(p.propuesta!.casa, null);
              p.setPropuesta(null);
              setEstado("success");
            }}
          >
            Aplicar
          </Boton>
          <Boton onClick={() => p.setPropuesta(null)}>Descartar</Boton>
        </div>
      )}
      <div className="flex gap-1.5">
        <input
          value={texto}
          disabled={sinApi}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && enviar()}
          placeholder={sinApi ? "Lumo necesita la API" : "Pedile algo a Lumo…"}
          className="flex-1 min-w-0 bg-concrete border border-line px-2 py-1.5 text-xs focus:outline-none focus:border-signal"
        />
        <Boton primario disabled={sinApi || !texto.trim() || estado === "think"} onClick={enviar}>
          Enviar
        </Boton>
      </div>
    </div>
  );
}

