/** Lumo en el editor: siempre a mano para pedirle un cambio con palabras o para que resuelva un problema.
 *
 *  Lumo no toca la planta en silencio: aplica el cambio, cuenta qué hizo y deja dos botones, «Dejar así» y
 *  «Volver atrás». Si al pedido le falta un dato, pregunta con opciones en vez de adivinar. */

import { useEffect, useRef, useState } from "react";
import { api } from "../../api/cliente";
import type { Casa, ItemCatalogo, Pieza, VerificacionPlanta } from "../../modelo/casa";
import { Lumo, type LumoState } from "../../componentes/lumo/Lumo";
import { contextoPara, ejecutar } from "./acciones";
import { resolver, type OpcionLumo, type TurnoLumo } from "./resolver";

interface Mensaje {
  de: "lumo" | "usuario";
  texto: string;
  opciones?: OpcionLumo[];
  /** Un cambio aplicado: la planta de antes, para volver, y la de después, para saber si sigue vigente. */
  antes?: Casa;
  despues?: Casa;
  cerrado?: "aceptado" | "deshecho";
  fallo?: boolean;
  /** Lo que decían las reglas antes del cambio, y los problemas que aparecieron con él. */
  verificacionesAntes?: VerificacionPlanta[];
  problemasNuevos?: string[];
}

const pendientes = (vs: VerificacionPlanta[]) =>
  vs.filter((v) => v.estado !== "comprobado_por_reglas" && v.gravedad !== "sugerencia").map((v) => v.detalle || v.descripcion);

export interface PedidoResolver {
  n: number;
  verificacion: VerificacionPlanta;
}

interface Props {
  casa: Casa;
  seleccion: Pieza | null;
  catalogo: ItemCatalogo[];
  apiOk: boolean | null;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
  /** Un problema de la lista que el usuario mandó a resolver. */
  pedido: PedidoResolver | null;
  /** Las verificaciones del momento: un problema a veces se resuelve con lo que señala otro. */
  verificaciones: VerificacionPlanta[];
}

const EJEMPLOS = ["Quiero ampliar este ambiente", "Cambiá la entrada de lugar", "Cocina abierta, integrada al estar"];

export default function LumoEditor({ casa, seleccion, catalogo, apiOk, aplicar, pedido, verificaciones }: Props) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [abierto, setAbierto] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [texto, setTexto] = useState("");
  const [gesto, setGesto] = useState<LumoState | null>(null);
  const fin = useRef<HTMLDivElement>(null);
  const reloj = useRef(0);
  // Los turnos son asíncronos: siempre se trabaja sobre la planta y la selección del momento.
  const actual = useRef({ casa, seleccion, catalogo, verificaciones });
  actual.current = { casa, seleccion, catalogo, verificaciones };

  useEffect(() => {
    fin.current?.scrollIntoView({ block: "end" });
  }, [mensajes.length, cargando, abierto]);

  const gesticular = (g: LumoState) => {
    setGesto(g);
    window.clearTimeout(reloj.current);
    reloj.current = window.setTimeout(() => setGesto(null), 2200);
  };

  const decir = (m: Mensaje) => setMensajes((ms) => [...ms, m]);

  /** Lo que devuelve un turno, venga del modelo o de las reglas de «Resolver». */
  const procesar = (t: TurnoLumo) => {
    if (t.acciones?.length) {
      const { casa: antes, catalogo: cat } = actual.current;
      const r = ejecutar(antes, t.acciones, cat);
      if (r.error) {
        decir({ de: "lumo", texto: `No pude hacerlo. ${r.error}`, fallo: true });
        gesticular("oops");
        return;
      }
      aplicar(r.casa, r.seleccion);
      decir({
        de: "lumo",
        texto: [t.mensaje, ...r.notas].filter(Boolean).join(" "),
        antes,
        despues: r.casa,
        verificacionesAntes: actual.current.verificaciones,
      });
      gesticular("success");
      return;
    }
    decir({ de: "lumo", texto: [t.mensaje, t.pregunta?.texto].filter(Boolean).join(" "), opciones: t.pregunta?.opciones });
  };

  const preguntarAlModelo = async (pedidoTexto: string, historial: Mensaje[]) => {
    if (apiOk === false) {
      decir({ de: "lumo", texto: "No tengo conexión con el servidor de Assambl: no puedo interpretar pedidos ahora.", fallo: true });
      gesticular("oops");
      return;
    }
    setCargando(true);
    try {
      const { casa: c, seleccion: s, catalogo: cat } = actual.current;
      const t = await api.lumoEditar(
        pedidoTexto,
        contextoPara(c, s, cat),
        historial.slice(-8).map((m) => ({ rol: m.de === "lumo" ? ("asistente" as const) : ("usuario" as const), texto: m.texto })),
      );
      procesar({
        mensaje: t.mensaje,
        acciones: t.acciones,
        pregunta: t.pregunta ? { texto: t.pregunta.texto, opciones: t.pregunta.opciones.map((o) => ({ etiqueta: o.etiqueta, detalle: o.detalle })) } : null,
      });
    } catch (e) {
      decir({ de: "lumo", texto: `No pude interpretar el pedido: ${(e as Error).message}`, fallo: true });
      gesticular("oops");
    } finally {
      setCargando(false);
    }
  };

  const enviar = (pedidoTexto: string) => {
    const limpio = pedidoTexto.trim();
    if (!limpio || cargando) return;
    setAbierto(true);
    const historial = mensajes;
    decir({ de: "usuario", texto: limpio });
    setTexto("");
    void preguntarAlModelo(limpio, historial);
  };

  // Cuando las reglas terminan de mirar un cambio de Lumo, se avisa si dejó problemas que antes no estaban.
  useEffect(() => {
    setMensajes((ms) => {
      const i = ms.length - 1;
      const m = ms[i];
      // Hasta que no llega un análisis nuevo, las verificaciones son todavía las de antes del cambio.
      if (!m?.despues || m.despues !== casa || m.cerrado || verificaciones === m.verificacionesAntes) return ms;
      const antes = pendientes(m.verificacionesAntes ?? []);
      const nuevos = pendientes(verificaciones).filter((p) => !antes.includes(p));
      if (nuevos.join("|") === (m.problemasNuevos ?? []).join("|")) return ms;
      return ms.map((x, k) => (k === i ? { ...x, problemasNuevos: nuevos } : x));
    });
  }, [verificaciones, casa]);

  // «Resolver» desde la lista de problemas.
  useEffect(() => {
    if (!pedido) return;
    const v = pedido.verificacion;
    const detalle = v.detalle || v.descripcion;
    setAbierto(true);
    decir({ de: "usuario", texto: `Resolvé esto: ${detalle}` });
    const t = resolver(actual.current.casa, v, actual.current.catalogo, actual.current.verificaciones);
    if (t) procesar(t);
    else void preguntarAlModelo(`Resolvé este problema de la planta: ${detalle} (regla ${v.id}; piezas: ${v.piezas.join(", ") || "ninguna"})`, mensajes);
    // Solo cuando llega un pedido nuevo.
  }, [pedido?.n]);

  const elegir = (o: OpcionLumo) => {
    if (cargando) return;
    if (o.acciones?.length) {
      decir({ de: "usuario", texto: o.etiqueta });
      procesar({ mensaje: o.mensaje ?? "", acciones: o.acciones });
    } else {
      enviar(o.etiqueta);
    }
  };

  const cerrar = (i: number, como: "aceptado" | "deshecho") => {
    const m = mensajes[i];
    if (como === "deshecho" && m.antes) {
      aplicar(m.antes, null);
      decir({ de: "lumo", texto: "Listo, lo dejé como estaba." });
    }
    setMensajes((ms) => ms.map((x, k) => (k === i ? { ...x, cerrado: como } : x)));
  };

  const estado: LumoState = cargando ? "think" : (gesto ?? (texto.trim() ? "listen" : apiOk === false ? "sleep" : "idle"));
  const ultimo = mensajes.length - 1;

  return (
    <div className="lumo-editor shrink-0 flex flex-col bg-concrete-2 border-b border-ink">
      {abierto && (
        <>
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-line">
            <span className="text-[11px] uppercase tracking-widest text-rebar">Lumo</span>
            <button className="text-xs text-rebar hover:text-ink px-1" onClick={() => setAbierto(false)} title="Achicar">
              —
            </button>
          </div>
          <div className="max-h-[42vh] overflow-y-auto px-3 py-2.5 flex flex-col gap-2">
            {!mensajes.length && (
              <div className="text-xs text-rebar leading-relaxed">
                Pedime un cambio con tus palabras. Si elegís algo en la planta, «este» es eso. Por ejemplo:
                <div className="flex flex-col gap-1 mt-2">
                  {EJEMPLOS.map((e) => (
                    <button key={e} className="text-left border border-line px-2 py-1 hover:border-ink text-ink" onClick={() => enviar(e)}>
                      {e}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {mensajes.map((m, i) =>
              m.de === "usuario" ? (
                <div key={i} className="self-end bg-ink text-concrete px-3 py-1.5 text-xs leading-relaxed max-w-[88%]">
                  {m.texto}
                </div>
              ) : (
                <div key={i} className={`border px-3 py-2 text-xs leading-relaxed max-w-[94%] ${m.fallo ? "border-warn bg-warn/5" : "border-line bg-concrete"}`}>
                  {m.texto}
                  {m.opciones && i === ultimo && (
                    <div className="flex flex-col gap-1 mt-2">
                      {m.opciones.map((o) => (
                        <button key={o.etiqueta} className="text-left border border-ink/30 bg-concrete-2 px-2 py-1.5 hover:border-signal" onClick={() => elegir(o)}>
                          <div>{o.etiqueta}</div>
                          {o.detalle && <div className="text-[10px] text-rebar mt-0.5">{o.detalle}</div>}
                        </button>
                      ))}
                    </div>
                  )}
                  {!!m.problemasNuevos?.length && !m.cerrado && (
                    <div className="border-l-2 border-warn pl-2 mt-2 text-[11px]">
                      Ojo: este cambio deja {m.problemasNuevos.length === 1 ? "un problema nuevo" : `${m.problemasNuevos.length} problemas nuevos`}:
                      <ul className="list-disc pl-4 text-rebar">
                        {m.problemasNuevos.slice(0, 3).map((p) => (
                          <li key={p}>{p}</li>
                        ))}
                      </ul>
                      Podés volver atrás o resolverlos desde «Para resolver».
                    </div>
                  )}
                  {m.despues &&
                    (m.cerrado ? (
                      <div className="text-[10px] text-rebar mt-1.5">{m.cerrado === "aceptado" ? "✓ Quedó así" : "↶ Deshecho"}</div>
                    ) : m.despues === casa ? (
                      <div className="flex gap-2 mt-2">
                        <button className="border border-signal bg-signal text-ink px-2.5 py-1 text-[11px] uppercase tracking-wide hover:bg-ink hover:text-concrete hover:border-ink" onClick={() => cerrar(i, "aceptado")}>
                          Dejar así
                        </button>
                        <button className="border border-ink/40 px-2.5 py-1 text-[11px] uppercase tracking-wide hover:border-ink" onClick={() => cerrar(i, "deshecho")}>
                          Volver atrás
                        </button>
                      </div>
                    ) : (
                      <div className="text-[10px] text-rebar mt-1.5">La planta siguió cambiando: para volver, usá deshacer (Ctrl+Z).</div>
                    ))}
                </div>
              ),
            )}
            {cargando && <div className="text-rebar text-xs">Lumo está pensando…</div>}
            <div ref={fin} />
          </div>
        </>
      )}
      <div className="flex items-center gap-2 px-2 py-1.5">
        <button onClick={() => setAbierto((a) => !a)} title={abierto ? "Achicar" : "Abrir la charla con Lumo"} className="shrink-0">
          <Lumo state={estado} size={44} />
        </button>
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onFocus={() => setAbierto(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter") enviar(texto);
            if (e.key === "Escape") (e.target as HTMLInputElement).blur();
          }}
          placeholder="Pedile un cambio a Lumo…"
          disabled={cargando}
          className="flex-1 min-w-0 bg-concrete border border-line px-2.5 py-1.5 text-xs focus:outline-none focus:border-signal"
        />
        <button
          onClick={() => enviar(texto)}
          disabled={!texto.trim() || cargando}
          className="border border-ink/40 px-2.5 py-1.5 text-xs hover:border-ink disabled:opacity-40"
          title="Enviar"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
