/** Charla con Monti: arma el programa de la casa (qué ambientes, qué tamaño) antes de proponer plantas.
 *  Las decisiones importantes llegan como opciones con su consecuencia; siempre se puede escribir. */

import { useEffect, useRef, useState } from "react";
import { USOS, type MensajeChat, type Programa, type RespuestaAsistente } from "../../modelo/casa";
import { Aviso, Boton } from "../../componentes/ui";
import Monti from "./Monti";

interface Props {
  modo: "libre" | "orientador";
  historial: MensajeChat[];
  respuesta: RespuestaAsistente | null;
  cargando: boolean;
  error: string | null;
  enviar: (texto: string, opciones: string[]) => void;
  verPlantas: () => void;
  volver: () => void;
}

export default function Charla({ modo, historial, respuesta, cargando, error, enviar, verPlantas, volver }: Props) {
  const [texto, setTexto] = useState("");
  const [marcadas, setMarcadas] = useState<string[]>([]);
  const fin = useRef<HTMLDivElement>(null);
  const pregunta = respuesta?.pregunta ?? null;

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    setMarcadas([]);
  }, [historial.length, cargando]);

  const mandar = () => {
    if (!texto.trim() || cargando) return;
    enviar(texto.trim(), []);
    setTexto("");
  };

  return (
    <div className="h-full grid grid-cols-[1fr_320px] min-h-0">
      <div className="flex flex-col min-h-0">
        <div className="flex items-center justify-between px-6 py-3 border-b border-line">
          <button className="text-xs text-rebar hover:text-ink" onClick={volver}>
            ← Otras formas de empezar
          </button>
          <span className="text-[11px] uppercase tracking-widest text-rebar">
            {modo === "orientador" ? "Paso a paso con Monti" : "Contala con tus palabras"}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          <div className="max-w-2xl mx-auto flex flex-col gap-4">
            {historial.map((m, i) =>
              m.rol === "asistente" ? (
                <div key={i} className="flex gap-3 items-end">
                  <div className="shrink-0 w-10">
                    <Monti animo={i === historial.length - 1 && !cargando ? "hablando" : "quieto"} tamano={38} />
                  </div>
                  <div className="bg-concrete-2 border border-line px-4 py-2.5 leading-relaxed max-w-[85%]">{m.texto}</div>
                </div>
              ) : (
                <div key={i} className="self-end bg-ink text-concrete px-4 py-2.5 leading-relaxed max-w-[80%]">
                  {m.texto}
                </div>
              ),
            )}
            {cargando && (
              <div className="flex gap-3 items-end">
                <div className="shrink-0 w-10">
                  <Monti animo="pensando" tamano={38} />
                </div>
                <div className="text-rebar text-xs pb-2">Monti está pensando…</div>
              </div>
            )}

            {!cargando && pregunta && (
              <div className="pl-[52px]">
                <div className="text-sm font-semibold mb-2">{pregunta.texto}</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {pregunta.opciones.map((o) => {
                    const marcada = marcadas.includes(o.id);
                    return (
                      <button
                        key={o.id}
                        onClick={() => {
                          if (pregunta.multiple) {
                            setMarcadas((ms) => (marcada ? ms.filter((x) => x !== o.id) : [...ms, o.id]));
                          } else {
                            enviar(o.etiqueta, [o.id]);
                          }
                        }}
                        className={`text-left border px-3 py-2 hover:border-signal ${
                          marcada ? "border-signal bg-signal/10" : "border-ink/30 bg-concrete-2"
                        }`}
                      >
                        <div className="text-sm">{o.etiqueta}</div>
                        {o.detalle && <div className="text-[11px] text-rebar mt-0.5">{o.detalle}</div>}
                      </button>
                    );
                  })}
                </div>
                {pregunta.multiple && (
                  <div className="mt-2 flex justify-end">
                    <Boton
                      primario
                      onClick={() => {
                        const elegidas = pregunta.opciones.filter((o) => marcadas.includes(o.id));
                        enviar(elegidas.map((o) => o.etiqueta).join(", ") || "Nada más", marcadas.length ? marcadas : ["nada"]);
                      }}
                    >
                      Listo
                    </Boton>
                  </div>
                )}
              </div>
            )}

            {!cargando && respuesta?.listo && (
              <div className="pl-[52px]">
                <Boton primario onClick={verPlantas} className="text-sm px-4 py-2">
                  Ver plantas posibles →
                </Boton>
                <span className="text-[11px] text-rebar ml-3">o seguí charlando para ajustar el pedido</span>
              </div>
            )}
            {error && <Aviso fuerte>{error}</Aviso>}
            <div ref={fin} />
          </div>
        </div>

        <div className="border-t border-line px-6 py-3">
          <div className="max-w-2xl mx-auto flex gap-2">
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && mandar()}
              placeholder={pregunta ? "O escribí tu respuesta…" : "Escribí para ajustar: «que el baño sea más grande», «sumá un lavadero»…"}
              className="flex-1 bg-concrete-2 border border-line px-3 py-2 focus:outline-none focus:border-signal"
              disabled={cargando}
            />
            <Boton primario onClick={mandar} disabled={!texto.trim() || cargando}>
              Enviar
            </Boton>
          </div>
        </div>
      </div>

      <aside className="border-l border-line bg-concrete overflow-y-auto p-4">
        <ResumenPrograma programa={respuesta?.programa ?? null} />
      </aside>
    </div>
  );
}

export function ResumenPrograma({ programa }: { programa: Programa | null }) {
  const nombreUso = (u: string) => USOS.find((x) => x.id === u)?.nombre ?? u;
  const ambs = programa?.ambientes ?? [];
  const total = ambs.reduce((s, a) => s + (a.area_m2 ?? 0), 0);
  return (
    <div>
      <h3 className="text-[11px] uppercase tracking-widest text-rebar mb-2">Lo que va anotando Monti</h3>
      {!ambs.length ? (
        <p className="text-xs text-rebar leading-relaxed">
          Acá aparece el programa de tu casa: los ambientes que necesitás y su tamaño aproximado. Es lo que después
          se convierte en plantas.
        </p>
      ) : (
        <>
          {programa?.superficie_objetivo_m2 ? (
            <div className="flex justify-between py-1 border-b border-line mb-2">
              <span className="text-rebar">Superficie buscada</span>
              <span>{programa.superficie_objetivo_m2.toFixed(0)} m²</span>
            </div>
          ) : null}
          <ul className="text-xs">
            {ambs.map((a) => (
              <li key={a.id} className="flex justify-between py-1 border-b border-line/60">
                <span>
                  {a.nombre}
                  <span className="text-rebar text-[10px] ml-1">{nombreUso(a.uso)}</span>
                </span>
                <span className="text-rebar">{a.area_m2 ? `${a.area_m2.toFixed(1)} m²` : "—"}</span>
              </li>
            ))}
          </ul>
          <div className="flex justify-between py-1 text-xs mt-1">
            <span className="text-rebar">Ambientes</span>
            <span>{total.toFixed(0)} m²</span>
          </div>
          <p className="text-[10px] text-rebar mt-2 leading-snug">
            A la superficie de los ambientes se suman muros y pasillos. Las medidas son orientativas: se ajustan en el
            editor.
          </p>
          {programa?.notas?.length ? (
            <div className="mt-3">
              <h4 className="text-[10px] uppercase tracking-wide text-rebar mb-1">Notas</h4>
              <ul className="text-[11px] list-disc pl-4">
                {programa.notas.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
