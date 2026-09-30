/** Momento de decisión: el mismo programa resuelto en tres partidos de planta, cada uno con su «por qué»
 *  (fundamentos de diseño) y, si sale de una planta de referencia, qué se le adaptó. */

import type { Alternativa, AnalisisPlanta, Casa } from "../../modelo/casa";
import { extension } from "../../modelo/casa";
import { Aviso, Boton, Etiqueta } from "../../componentes/ui";
import DibujoPlanta, { encuadrar, Tramas } from "./DibujoPlanta";
import { Criterios, destacadas, ItemObservacion } from "./Fundamentos";
import Monti from "./Monti";

export function MiniPlanta({ casa, analisis, ancho = 340, alto = 220 }: { casa: Casa; analisis: AnalisisPlanta | null; ancho?: number; alto?: number }) {
  const ext = extension(casa);
  if (!ext) return null;
  const vista = encuadrar(ext, ancho, alto, 16);
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} width="100%" className="block bg-concrete">
      <Tramas />
      <DibujoPlanta casa={casa} vista={vista} analisis={analisis} etiquetas={vista.escala > 22} verEstados />
    </svg>
  );
}

interface Props {
  alternativas: Alternativa[] | null;
  cargando: boolean;
  error: string | null;
  elegir: (a: Alternativa) => void;
  volver: () => void;
  verReferencias: () => void;
}

export default function Alternativas({ alternativas, cargando, error, elegir, volver, verReferencias }: Props) {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <button className="text-xs text-rebar hover:text-ink" onClick={volver}>
          ← Volver a la charla
        </button>
        <div className="flex items-center gap-4 mt-3 mb-5">
          <Monti animo={cargando ? "pensando" : "contento"} tamano={52} />
          <div>
            <h1 className="font-display text-2xl">Elegí un punto de partida</h1>
            <p className="text-rebar text-sm mt-1 max-w-2xl">
              Son el mismo pedido resuelto de distintas maneras. No busques la perfecta: elegí la que más se parece a lo
              que imaginás y la ajustás en el editor (mover muros, cambiar ventanas, renombrar ambientes). Cada una
              te cuenta qué gana y qué resigna según{" "}
              <button className="underline underline-offset-2 hover:text-ink" onClick={verReferencias}>
                fundamentos de diseño
              </button>
              : ninguno es obligatorio, vos decidís qué te importa más.
            </p>
          </div>
        </div>
        {error && <Aviso fuerte>{error}</Aviso>}
        {cargando && <p className="text-rebar">Armando plantas…</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {alternativas?.map((a) => (
            <article key={a.id} className="border border-line bg-concrete-2 flex flex-col">
              <div className="border-b border-line flex justify-center">
                <MiniPlanta casa={a.casa} analisis={a.analisis} />
              </div>
              <div className="p-4 flex flex-col gap-2 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-semibold">{a.nombre}</h2>
                  <Etiqueta estado={a.analisis.estado} />
                </div>
                {a.origen?.tipo === "referencia" && (
                  <p className="text-[10px] uppercase tracking-wide text-signal">
                    Basada en una planta de referencia de {a.origen.superficie_m2} m²
                  </p>
                )}
                <p className="text-xs text-rebar leading-relaxed">{a.descripcion}</p>
                {a.evaluacion && <PorQue alternativa={a} />}
                <dl className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs mt-1">
                  <dt className="text-rebar">Superficie cubierta</dt>
                  <dd className="text-right">{a.resumen.superficie_cubierta_m2.toFixed(0)} m²</dd>
                  <dt className="text-rebar">Frente × fondo</dt>
                  <dd className="text-right">
                    {a.resumen.ancho_m.toFixed(1)} × {a.resumen.profundidad_m.toFixed(1)} m
                  </dd>
                  <dt className="text-rebar" title="Más muro exterior es más material y más superficie que pierde calor">
                    Muro exterior
                  </dt>
                  <dd className="text-right">{a.resumen.muro_exterior_m.toFixed(0)} m</dd>
                </dl>
                {a.advertencias.map((w, i) => (
                  <Aviso key={i}>{w}</Aviso>
                ))}
                <div className="mt-auto pt-2">
                  <Boton primario className="w-full" onClick={() => elegir(a)}>
                    Elegir esta y editarla →
                  </Boton>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

function PorQue({ alternativa: a }: { alternativa: Alternativa }) {
  const e = a.evaluacion!;
  const d = destacadas(e, 2);
  return (
    <div className="flex flex-col gap-2 border-t border-line pt-2 mt-1">
      <Criterios evaluacion={e} compacto />
      <ul className="flex flex-col gap-1">
        {[...d.favor, ...d.considerar].map((o, i) => (
          <ItemObservacion key={i} o={o} />
        ))}
      </ul>
      {!!a.adaptacion?.length && (
        <details className="text-[11px] text-rebar">
          <summary className="cursor-pointer hover:text-ink">Qué se adaptó de la planta original ({a.adaptacion.length})</summary>
          <ul className="list-disc pl-4 mt-1 flex flex-col gap-0.5">
            {a.adaptacion.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </details>
      )}
      <details className="text-[11px] text-rebar">
        <summary className="cursor-pointer hover:text-ink">Todas las observaciones ({e.observaciones.length})</summary>
        <ul className="flex flex-col gap-1 mt-1">
          {e.observaciones.map((o, i) => (
            <ItemObservacion key={i} o={o} />
          ))}
        </ul>
      </details>
    </div>
  );
}
