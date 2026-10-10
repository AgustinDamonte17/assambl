/** El lienzo en blanco: tres maneras de empezar la casa, ordenadas de la más guiada a la más libre. */

import { useState } from "react";
import type { EstadoIA } from "../../modelo/casa";
import { Boton } from "../../componentes/ui";
import Monti from "./Monti";

const EJEMPLOS = [
  "Una casa de 90 m² con dos dormitorios, un baño y la cocina integrada al living.",
  "Somos una familia de cuatro: tres dormitorios, dos baños, lavadero y un rincón para trabajar. Unos 130 m².",
  "Una cabaña chica para fines de semana, un dormitorio, mucha luz y una galería.",
];

interface Props {
  ia: EstadoIA | null;
  apiOk: boolean | null;
  hayCasa: boolean;
  empezarLibre: (texto: string) => void;
  empezarOrientador: () => void;
  empezarImagen: (archivo?: File) => void;
  empezarDibujo: () => void;
  abrirEjemplo: () => void;
  volverAlEditor: () => void;
}

export default function Inicio(p: Props) {
  const [texto, setTexto] = useState("");
  const [arrastrando, setArrastrando] = useState(false);
  const sinApi = p.apiOk === false;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-start justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-rebar mb-2">Capa 03 · Casa</div>
            <h1 className="font-display text-3xl leading-tight">¿Cómo querés empezar tu casa?</h1>
            <p className="text-rebar mt-2 max-w-xl leading-relaxed">
              No hace falta saber dibujar planos. Elegí una manera de arrancar: lo que salga es un punto de partida, y
              después lo ajustás en el editor. Assambl verifica cada muro y cada abertura a medida que avanzás.
            </p>
          </div>
          <EstadoAsistente ia={p.ia} apiOk={p.apiOk} />
        </div>

        {p.hayCasa && (
          <div className="mb-4 border border-line bg-concrete-2 px-4 py-3 flex items-center justify-between">
            <span>Ya tenés una planta en este proyecto. Si empezás de nuevo, la reemplazás (podés deshacerlo desde el editor).</span>
            <Boton onClick={p.volverAlEditor}>Volver a mi planta</Boton>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* 1a · Prompt libre */}
          <section className="border border-line bg-concrete-2 p-5 flex flex-col">
            <Encabezado n="1" titulo="Contala con tus palabras" etiqueta="IA · texto libre" />
            <p className="text-rebar text-xs mb-3">
              Escribí cómo la imaginás. Si falta algo importante, te preguntamos; si no, te mostramos plantas posibles.
            </p>
            <textarea
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && texto.trim()) p.empezarLibre(texto.trim());
              }}
              rows={4}
              placeholder="Ej.: una casa de 100 m² con dos dormitorios, un baño, cocina integrada y lavadero…"
              className="w-full bg-concrete border border-line px-3 py-2 text-sm leading-relaxed focus:outline-none focus:border-signal resize-none"
            />
            <div className="flex flex-wrap gap-1.5 mt-2">
              {EJEMPLOS.map((e) => (
                <button
                  key={e}
                  onClick={() => setTexto(e)}
                  className="text-[10px] text-left border border-line px-2 py-1 hover:border-ink text-rebar hover:text-ink"
                >
                  {e.length > 52 ? e.slice(0, 50) + "…" : e}
                </button>
              ))}
            </div>
            <div className="mt-auto pt-4 flex justify-end">
              <Boton primario disabled={!texto.trim() || sinApi} onClick={() => p.empezarLibre(texto.trim())}>
                Proponer plantas →
              </Boton>
            </div>
          </section>

          {/* 1b · Orientador */}
          <section className="border border-line bg-concrete-2 p-5 flex flex-col">
            <Encabezado n="2" titulo="Armala con Monti" etiqueta="IA · paso a paso" />
            <div className="flex gap-4 items-center">
              <Monti animo="contento" tamano={80} />
              <p className="text-sm leading-relaxed">
                «Hola, soy Monti. Te hago unas pocas preguntas —dormitorios, tamaño, cocina— con opciones para elegir, y
                te explico qué cambia con cada una. <span className="text-rebar">Ideal si no sabés por dónde empezar.</span>»
              </p>
            </div>
            <div className="mt-auto pt-4 flex justify-end">
              <Boton primario disabled={sinApi} onClick={p.empezarOrientador}>
                Empezar con Monti →
              </Boton>
            </div>
          </section>

          {/* 2 · Imagen */}
          <section
            className={`border bg-concrete-2 p-5 flex flex-col lg:col-span-2 ${arrastrando ? "border-signal" : "border-line"}`}
            onDragOver={(e) => {
              e.preventDefault();
              setArrastrando(true);
            }}
            onDragLeave={() => setArrastrando(false)}
            onDrop={(e) => {
              e.preventDefault();
              setArrastrando(false);
              const f = e.dataTransfer.files?.[0];
              if (f) p.empezarImagen(f);
            }}
          >
            <Encabezado n="3" titulo="Subí un bosquejo o un plano" etiqueta="IA · imagen" />
            <div className="grid grid-cols-[1fr_auto] gap-6 items-center">
              <p className="text-rebar text-xs leading-relaxed">
                Arrastrá acá una foto de un dibujo a mano, una captura o un plano en PNG o JPG. La IA reconoce los
                ambientes y sus medidas, y reconstruye la planta sobre tu dibujo para que la compares. Todo lo que
                interpreta queda marcado <b className="text-warn">para revisar</b> hasta que lo confirmes.
              </p>
              <Boton disabled={sinApi} onClick={() => p.empezarImagen()}>
                Elegir imagen…
              </Boton>
            </div>
          </section>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-rebar">
          <button className="hover:text-ink underline underline-offset-2" onClick={p.empezarDibujo}>
            Dibujar desde cero (editor libre, básico)
          </button>
          <button className="hover:text-ink underline underline-offset-2" onClick={p.abrirEjemplo}>
            Ver un ejemplo: Angus Ranch (164 m²)
          </button>
        </div>
      </div>
    </div>
  );
}

function Encabezado({ n, titulo, etiqueta }: { n: string; titulo: string; etiqueta: string }) {
  return (
    <div className="flex items-baseline justify-between mb-3">
      <h2 className="text-base font-semibold">
        <span className="text-signal mr-2">{n}</span>
        {titulo}
      </h2>
      <span className="text-[10px] uppercase tracking-wide text-rebar">{etiqueta}</span>
    </div>
  );
}

export function EstadoAsistente({ ia, apiOk, compacto }: { ia: EstadoIA | null; apiOk: boolean | null; compacto?: boolean }) {
  if (compacto) {
    if (apiOk === false || !ia) return null;
    return (
      <span className={`text-[10px] uppercase tracking-wide ${ia.simulado ? "text-warn" : "text-rebar"}`} title={ia.motivo ?? `${ia.proveedor} · ${ia.modelo}`}>
        {ia.simulado ? "IA en demostración" : `IA · ${ia.modelo}`}
      </span>
    );
  }
  if (apiOk === false)
    return (
      <div className="text-[11px] border border-signal text-signal px-2 py-1 max-w-56">
        Sin conexión con la API: las opciones con IA no están disponibles. Podés abrir el ejemplo o dibujar.
      </div>
    );
  if (!ia) return null;
  return (
    <div
      className={`text-[11px] border px-2 py-1 max-w-64 leading-snug ${ia.simulado ? "border-warn text-warn" : "border-line text-rebar"}`}
      title={ia.motivo ?? ""}
    >
      {ia.simulado ? (
        <>
          <b>IA en modo demostración.</b> {ia.motivo}. Las respuestas siguen un guion fijo.
        </>
      ) : (
        <>
          IA: {ia.proveedor} · {ia.modelo}
        </>
      )}
    </div>
  );
}
