/** Fundamentos de diseño: cómo se muestra la evaluación de una planta (backend/assambl/fundamentos).
 *  No son estados ni errores: son observaciones «a favor» o «a considerar» para comparar alternativas y
 *  decidir con criterio. El razonamiento está en docs/fundamentos_diseno.md. */

import { useEffect, useState } from "react";
import { api } from "../../api/cliente";
import type { Evaluacion, Fundamento, NivelObservacion, Observacion } from "../../modelo/casa";

export const NIVEL: Record<NivelObservacion, { glifo: string; color: string; nombre: string }> = {
  a_favor: { glifo: "✓", color: "var(--resolved)", nombre: "A favor" },
  neutral: { glifo: "◐", color: "var(--rebar)", nombre: "Intermedio" },
  a_considerar: { glifo: "◑", color: "var(--warn)", nombre: "A considerar" },
  info: { glifo: "·", color: "var(--rebar)", nombre: "Para saber" },
};

/** Barras de los seis criterios. Sin números: sirven para comparar, no para calificar. */
export function Criterios({ evaluacion, compacto }: { evaluacion: Evaluacion; compacto?: boolean }) {
  return (
    <ul className={`grid ${compacto ? "grid-cols-2 gap-x-3 gap-y-1" : "grid-cols-1 gap-1.5"}`}>
      {evaluacion.criterios.map((c) => (
        <li key={c.id} title={c.pregunta} className="text-[10px] leading-tight">
          <div className="flex justify-between text-rebar">
            <span>{c.nombre}</span>
            {!compacto && c.puntaje !== null && <span>{Math.round(c.puntaje * 100)}</span>}
          </div>
          <div className="h-1.5 bg-concrete-3 mt-0.5">
            {c.puntaje !== null && (
              <div
                className="h-full"
                style={{
                  width: `${Math.max(4, c.puntaje * 100)}%`,
                  background: c.puntaje >= 0.75 ? "var(--resolved)" : c.puntaje < 0.5 ? "var(--warn)" : "var(--rebar)",
                }}
              />
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Lo más destacado de la evaluación: primero lo que juega a favor, después lo que conviene mirar. */
export function destacadas(e: Evaluacion, n = 2): { favor: Observacion[]; considerar: Observacion[] } {
  const con = e.observaciones.filter((o) => o.puntaje !== null);
  return {
    favor: con.filter((o) => o.nivel === "a_favor").sort((a, b) => (b.puntaje ?? 0) - (a.puntaje ?? 0)).slice(0, n),
    considerar: con.filter((o) => o.nivel === "a_considerar").sort((a, b) => (a.puntaje ?? 0) - (b.puntaje ?? 0)).slice(0, n),
  };
}

export function ItemObservacion({
  o,
  resaltar,
  alTocar,
}: {
  o: Observacion;
  resaltar?: (ids: string[]) => void;
  alTocar?: (o: Observacion) => void;
}) {
  const n = NIVEL[o.nivel];
  return (
    <li
      className={`flex gap-1.5 text-[11px] leading-snug ${alTocar && o.piezas.length ? "cursor-pointer hover:bg-concrete-2" : ""}`}
      onMouseEnter={() => resaltar?.(o.piezas)}
      onMouseLeave={() => resaltar?.([])}
      onClick={() => alTocar?.(o)}
    >
      <span className="font-bold w-3 shrink-0 text-center" style={{ color: n.color }} title={n.nombre}>
        {n.glifo}
      </span>
      <span>
        <b className="font-semibold">{o.titulo}.</b> {o.texto}
      </span>
    </li>
  );
}

/** Sección del panel del editor: se actualiza con cada cambio de la planta. */
export function PanelFundamentos({
  evaluacion,
  resaltar,
  alTocar,
  verTeoria,
}: {
  evaluacion: Evaluacion | null | undefined;
  resaltar: (ids: string[]) => void;
  alTocar: (o: Observacion) => void;
  verTeoria: () => void;
}) {
  const [todas, setTodas] = useState(false);
  if (!evaluacion) return <p className="text-xs text-rebar">Se evalúa cuando la planta tiene ambientes.</p>;
  const orden: NivelObservacion[] = ["a_considerar", "neutral", "a_favor", "info"];
  const obs = [...evaluacion.observaciones].sort((a, b) => orden.indexOf(a.nivel) - orden.indexOf(b.nivel));
  const visibles = todas ? obs : obs.filter((o) => o.nivel === "a_considerar" || o.nivel === "info").slice(0, 5);
  return (
    <div className="flex flex-col gap-2">
      <p className="text-[10px] text-rebar leading-snug">
        Buenas prácticas de diseño, no reglas: cada casa elige qué prioriza. Pasá el mouse para ver a qué ambientes se
        refiere.
      </p>
      <Criterios evaluacion={evaluacion} compacto />
      <ul className="flex flex-col gap-1.5 mt-1">
        {visibles.map((o, i) => (
          <ItemObservacion key={i} o={o} resaltar={resaltar} alTocar={alTocar} />
        ))}
        {!visibles.length && <li className="text-[11px] text-resolved">Nada para considerar: la planta sigue los fundamentos.</li>}
      </ul>
      <div className="flex gap-3 text-[10px]">
        <button className="text-rebar hover:text-ink underline underline-offset-2" onClick={() => setTodas((t) => !t)}>
          {todas ? "Ver solo lo que conviene mirar" : `Ver las ${obs.length} observaciones`}
        </button>
        <button className="text-rebar hover:text-ink underline underline-offset-2" onClick={verTeoria}>
          ¿Por qué Assambl piensa esto?
        </button>
      </div>
    </div>
  );
}

/** Los fundamentos completos: principio, por qué, qué mide Assambl y qué se resigna. */
export function Teoria() {
  const [datos, setDatos] = useState<{ criterios: { id: string; nombre: string; pregunta: string }[]; fundamentos: Fundamento[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.fundamentos().then(setDatos).catch((e) => setError((e as Error).message));
  }, []);
  if (error) return <p className="text-xs text-signal">No se pudieron cargar los fundamentos: {error}</p>;
  if (!datos) return <p className="text-xs text-rebar">Cargando…</p>;
  return (
    <div className="flex flex-col gap-6">
      {datos.criterios.map((c) => (
        <section key={c.id}>
          <h3 className="font-semibold">{c.nombre}</h3>
          <p className="text-xs text-rebar mb-2">{c.pregunta}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {datos.fundamentos
              .filter((f) => f.criterio === c.id)
              .map((f) => (
                <article key={f.id} className="border border-line bg-concrete-2 p-3 text-xs leading-relaxed">
                  <div className="flex justify-between items-baseline">
                    <h4 className="font-semibold text-sm">{f.titulo}</h4>
                    <span className="text-[10px] text-rebar">{f.id}</span>
                  </div>
                  <p className="mt-1">{f.principio}</p>
                  <p className="mt-1 text-rebar">
                    <b className="text-ink">Por qué.</b> {f.por_que}
                  </p>
                  <p className="mt-1 text-rebar">
                    <b className="text-ink">Qué mide Assambl.</b> {f.mide}
                  </p>
                  <p className="mt-1 text-rebar">
                    <b className="text-ink">Qué se resigna.</b> {f.tension}
                  </p>
                </article>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
