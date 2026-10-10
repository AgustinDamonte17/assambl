/** Diseñá con Lumo: tres decisiones y una planta base que se arma a la vista.
 *  A la izquierda, Lumo pregunta de a una; a la derecha, la casa cambia con cada respuesta y explica su orden.
 *  Cualquier decisión se puede cambiar después desde los controles: la charla es la guía, no una traba. */

import { useEffect, useRef, useState } from "react";
import { api } from "../../api/cliente";
import type { Casa, Decisiones, RespuestaLumo } from "../../modelo/casa";
import { Aviso, Boton, Etiqueta } from "../../componentes/ui";
import { Lumo, type LumoState } from "../../componentes/lumo/Lumo";
import MiniPlanta from "./MiniPlanta";

interface Mensaje {
  de: "lumo" | "usuario";
  texto: string;
}

type Fase = "pensando" | "armando" | "festejo" | "quieto" | "error";

const ORDEN = ["dormitorios", "cocina", "tamano"] as const;
type Clave = (typeof ORDEN)[number];

const CONTROLES: Record<Clave, { titulo: string; opciones: { valor: number | string; etiqueta: string }[] }> = {
  dormitorios: {
    titulo: "Dormitorios",
    opciones: [1, 2, 3, 4].map((n) => ({ valor: n, etiqueta: String(n) })),
  },
  cocina: {
    titulo: "Cocina",
    opciones: [
      { valor: "abierta", etiqueta: "Abierta" },
      { valor: "cerrada", etiqueta: "Cerrada" },
    ],
  },
  tamano: {
    titulo: "Tamaño",
    opciones: [
      { valor: "compacta", etiqueta: "Compacta" },
      { valor: "comoda", etiqueta: "Cómoda" },
      { valor: "amplia", etiqueta: "Amplia" },
    ],
  },
};

const ESTADO_LUMO: Record<Fase, LumoState> = {
  pensando: "think",
  armando: "build",
  festejo: "success",
  quieto: "idle",
  error: "oops",
};

interface Props {
  lat: number | null;
  inicial: Decisiones;
  elegir: (casa: Casa) => void;
  volver: () => void;
}

export default function DisenarConLumo({ lat, inicial, elegir, volver }: Props) {
  const [decisiones, setDecisiones] = useState<Decisiones>(inicial);
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [respuesta, setRespuesta] = useState<RespuestaLumo | null>(null);
  const [fase, setFase] = useState<Fase>("pensando");
  const [error, setError] = useState<string | null>(null);
  const [texto, setTexto] = useState("");
  const turno = useRef(0);
  const reloj = useRef<number[]>([]);
  const fin = useRef<HTMLDivElement>(null);

  const pedir = async (d: Decisiones, escrito = "", dicho?: string, cambio: Clave | null = null) => {
    const n = ++turno.current;
    reloj.current.forEach((t) => window.clearTimeout(t));
    reloj.current = [];
    if (dicho) setMensajes((m) => [...m, { de: "usuario", texto: dicho }]);
    setFase("pensando");
    setError(null);
    try {
      const r = await api.lumo(d, escrito, lat, cambio);
      if (n !== turno.current) return;
      setDecisiones(r.decisiones);
      setRespuesta(r);
      setMensajes((m) => [...m, { de: "lumo", texto: r.mensaje }]);
      if (!r.propuesta) {
        setFase("quieto");
        return;
      }
      // Lumo «ensambla» un momento y, si ya no falta nada, festeja.
      setFase("armando");
      const despues = (ms: number, f: Fase) =>
        reloj.current.push(window.setTimeout(() => n === turno.current && setFase(f), ms));
      if (r.listo) {
        despues(1300, "festejo");
        despues(3600, "quieto");
      } else {
        despues(1300, "quieto");
      }
    } catch (e) {
      if (n !== turno.current) return;
      setError(`No pude armar la planta: ${(e as Error).message}`);
      setFase("error");
    }
  };

  useEffect(() => {
    void pedir(inicial);
    return () => {
      turno.current++;
      reloj.current.forEach((t) => window.clearTimeout(t));
    };
    // Solo al entrar: después cada turno lo dispara el usuario.
  }, []);

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes.length, fase]);

  const pendiente = ORDEN.find((k) => decisiones[k] === null) ?? null;
  const pregunta = fase === "pensando" ? null : (respuesta?.pregunta ?? null);
  const propuesta = respuesta?.propuesta ?? null;
  const ocupado = fase === "pensando";

  /** Responder la pregunta pendiente es seguir la charla; tocar otra decisión es un cambio, y Lumo lo cuenta. */
  const decidir = (clave: Clave, valor: number | string, dicho: string) =>
    void pedir({ ...decisiones, [clave]: valor } as Decisiones, "", dicho, clave === pendiente ? null : clave);

  const mandar = () => {
    if (!texto.trim() || ocupado || !pendiente) return;
    void pedir(decisiones, texto.trim(), texto.trim());
    setTexto("");
  };

  const estadoLumo: LumoState = texto.trim() && fase === "quieto" ? "listen" : ESTADO_LUMO[fase];

  return (
    <div className="h-full grid grid-cols-[minmax(340px,420px)_1fr] min-h-0">
      {/* Charla */}
      <div className="flex flex-col min-h-0 border-r border-line">
        <div className="flex items-center gap-3 px-5 py-3 border-b border-line">
          <Lumo state={estadoLumo} size={64} />
          <div className="flex-1 min-w-0">
            <div className="font-head font-bold text-lg leading-none">Diseñá con Lumo</div>
            <div className="text-[11px] text-rebar mt-1">Tres decisiones y una casa ordenada para editar</div>
          </div>
          <button className="text-xs text-rebar hover:text-ink whitespace-nowrap" onClick={volver}>
            ← Volver
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="flex flex-col gap-3">
            {mensajes.map((m, i) =>
              m.de === "lumo" ? (
                <div key={i} className="bg-concrete-2 border border-line px-3.5 py-2.5 leading-relaxed max-w-[92%]">
                  {m.texto}
                </div>
              ) : (
                <div key={i} className="self-end bg-ink text-concrete px-3.5 py-2 leading-relaxed max-w-[85%]">
                  {m.texto}
                </div>
              ),
            )}
            {ocupado && <div className="text-rebar text-xs">Lumo está pensando…</div>}

            {pregunta && pendiente && (
              <div className="mt-1">
                <div className="text-sm font-medium mb-2">{pregunta.texto}</div>
                <div className="grid grid-cols-1 gap-2">
                  {pregunta.opciones.map((o) => (
                    <button
                      key={o.id}
                      onClick={() => decidir(pendiente, pendiente === "dormitorios" ? Number(o.id) : o.id, o.etiqueta)}
                      className="text-left border border-ink/30 bg-concrete-2 px-3 py-2 hover:border-signal"
                    >
                      <div className="text-sm">{o.etiqueta}</div>
                      {o.detalle && <div className="text-[11px] text-rebar mt-0.5">{o.detalle}</div>}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {error && <Aviso fuerte>{error}</Aviso>}
            <div ref={fin} />
          </div>
        </div>

        {pendiente && (
          <div className="border-t border-line px-5 py-3 flex gap-2">
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && mandar()}
              placeholder="O escribí tu respuesta…"
              className="flex-1 min-w-0 bg-concrete-2 border border-line px-3 py-2 focus:outline-none focus:border-signal"
              disabled={ocupado}
            />
            <Boton onClick={mandar} disabled={!texto.trim() || ocupado}>
              Enviar
            </Boton>
          </div>
        )}
      </div>

      {/* La casa */}
      <div className="flex flex-col min-h-0 overflow-y-auto bg-concrete">
        {!propuesta ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center px-8">
            <Lumo state="curious" size={150} />
            <p className="text-rebar max-w-sm leading-relaxed">
              Acá va a aparecer tu casa. Con la primera respuesta ya tenés una planta completa; las otras dos la
              afinan.
            </p>
          </div>
        ) : (
          <div className="max-w-5xl w-full mx-auto px-6 py-5 flex flex-col gap-4">
            <div className="flex items-end justify-between gap-4 flex-wrap">
              <div>
                <div className="font-label text-[11px] uppercase tracking-widest text-rebar mb-1">
                  {respuesta?.listo ? "Tu planta base" : "Así va quedando"}
                </div>
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className="font-label font-medium text-3xl leading-none">
                    {propuesta.resumen.superficie_cubierta_m2.toFixed(0)} m²
                  </span>
                  <span className="font-label text-rebar text-xs">
                    {propuesta.resumen.ancho_m.toFixed(1)} × {propuesta.resumen.profundidad_m.toFixed(1)} m ·{" "}
                    {propuesta.resumen.ambientes} ambientes
                  </span>
                  <Etiqueta estado={propuesta.analisis.estado} />
                </div>
              </div>
              <Boton primario className="text-sm px-4 py-2" onClick={() => elegir(propuesta.casa)}>
                Abrir en el editor →
              </Boton>
            </div>

            <div className="border border-line bg-concrete-2 p-2">
              <MiniPlanta
                key={JSON.stringify(propuesta.decisiones)}
                casa={propuesta.casa}
                analisis={propuesta.analisis}
                ancho={880}
                alto={500}
                verEstados={false}
                className="planta-aparece"
              />
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-2">
              {ORDEN.map((clave) => (
                <div key={clave} className="flex items-center gap-2">
                  <span className="font-label text-[11px] uppercase tracking-wide text-rebar whitespace-nowrap">{CONTROLES[clave].titulo}</span>
                  <div className="flex">
                    {CONTROLES[clave].opciones.map((o) => {
                      const activa = propuesta.decisiones[clave] === o.valor;
                      const elegida = decisiones[clave] === o.valor;
                      return (
                        <button
                          key={o.valor}
                          disabled={ocupado}
                          onClick={() => !elegida && decidir(clave, o.valor, `${CONTROLES[clave].titulo}: ${o.etiqueta}`)}
                          title={activa && !elegida ? "Valor de partida: todavía no lo elegiste" : undefined}
                          className={`px-2.5 py-1 text-xs border -ml-px first:ml-0 ${
                            elegida
                              ? "bg-ink text-concrete border-ink"
                              : activa
                                ? "border-ink/40 border-dashed text-ink"
                                : "border-ink/25 text-rebar hover:text-ink hover:border-ink"
                          }`}
                        >
                          {o.etiqueta}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div>
              <h3 className="font-label text-[11px] uppercase tracking-widest text-rebar mb-2">Por qué está ordenada así</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
                {propuesta.razones.map((r) => (
                  <div key={r.titulo} className="border-l-2 border-[#6C4DFF] pl-3">
                    <div className="font-head text-sm font-bold">{r.titulo}</div>
                    <p className="text-xs text-rebar leading-relaxed mt-0.5">{r.texto}</p>
                  </div>
                ))}
              </div>
            </div>

            {propuesta.advertencias.map((a, i) => (
              <Aviso key={i}>{a}</Aviso>
            ))}
            <p className="text-[11px] text-rebar leading-snug">
              Es un punto de partida: en el editor podés mover muros, cambiar puertas y ventanas, y renombrar ambientes.
              Assambl verifica cada pieza a medida que la tocás.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
