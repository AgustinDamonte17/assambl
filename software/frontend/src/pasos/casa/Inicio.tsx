/** El lienzo en blanco. Un camino principal, Lumo, y debajo las otras maneras de llegar a una primera planta. */

import { useState } from "react";
import type { EstadoIA } from "../../modelo/casa";
import { Boton } from "../../componentes/ui";
import { numeroCapa } from "../../componentes/capas";
import Lumo from "../../componentes/lumo/Lumo";

interface Props {
  ia: EstadoIA | null;
  apiOk: boolean | null;
  hayCasa: boolean;
  empezarConLumo: () => void;
  empezarImagen: (archivo?: File) => void;
  empezarDibujo: () => void;
  abrirEjemplo: () => void;
  volverAlEditor: () => void;
}

export default function Inicio(p: Props) {
  const [arrastrando, setArrastrando] = useState(false);
  const sinApi = p.apiOk === false;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-6">
          <div className="font-label text-[11px] uppercase tracking-widest text-rebar mb-2">Capa {numeroCapa("casa")} · Casa</div>
          <h1 className="font-head font-extrabold text-3xl leading-tight tracking-tight">Empecemos tu casa</h1>
          <p className="text-rebar text-[15px] mt-2 max-w-xl leading-relaxed">
            No hace falta saber dibujar planos. Lumo te arma una planta ordenada y después la ajustás en el editor:
            Assambl verifica cada muro y cada abertura a medida que avanzás.
          </p>
        </div>

        {sinApi && (
          <div className="mb-4 text-[11px] border border-signal text-signal px-3 py-2">
            Sin conexión con la API: Lumo y la lectura de imágenes no están disponibles. Podés abrir el ejemplo o
            dibujar desde cero.
          </div>
        )}

        {p.hayCasa && (
          <div className="mb-4 border border-line bg-concrete-2 px-4 py-3 flex items-center justify-between gap-4">
            <span>Ya tenés una planta en este proyecto. Si empezás de nuevo, la reemplazás (podés deshacerlo desde el editor).</span>
            <Boton onClick={p.volverAlEditor}>Volver a mi planta</Boton>
          </div>
        )}

        {/* Camino principal */}
        <section className="border border-ink bg-concrete-2 p-6 flex flex-col sm:flex-row gap-6 items-center">
          <Lumo state={sinApi ? "sleep" : "wave"} size={140} className="shrink-0" />
          <div className="flex-1">
            <h2 className="font-head font-bold text-2xl leading-tight">Diseñá con Lumo</h2>
            <p className="leading-relaxed mt-2 max-w-lg">
              «Hola, soy Lumo. Con tres decisiones —dormitorios, cocina y tamaño— te armo una casa ordenada y te cuento
              por qué quedó así. Vas viendo la planta mientras elegís.»
            </p>
            <div className="mt-4 flex items-center gap-4 flex-wrap">
              <Boton primario className="text-sm px-5 py-2.5" disabled={sinApi} onClick={p.empezarConLumo}>
                Empezar →
              </Boton>
              <span className="text-[11px] text-rebar">Menos de un minuto · siempre podés cambiar todo después</span>
            </div>
          </div>
        </section>

        {/* Otras maneras */}
        <h3 className="font-label text-[11px] uppercase tracking-widest text-rebar mt-8 mb-2">O si ya tenés algo</h3>
        <section
          className={`border bg-concrete-2 px-5 py-4 grid grid-cols-[1fr_auto] gap-6 items-center ${arrastrando ? "border-signal" : "border-line"}`}
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
          <div>
            <div className="flex items-baseline gap-3">
              <h2 className="font-head text-sm font-bold">Subí un bosquejo o un plano</h2>
              <EstadoAsistente ia={p.ia} apiOk={p.apiOk} compacto />
            </div>
            <p className="text-rebar text-[13px] leading-relaxed mt-1">
              Arrastrá acá una foto de un dibujo a mano o un plano en PNG o JPG. La IA reconoce los ambientes y
              reconstruye la planta; todo lo que interpreta queda marcado <b className="text-warn">para revisar</b>.
            </p>
          </div>
          <Boton disabled={sinApi} onClick={() => p.empezarImagen()}>
            Elegir imagen…
          </Boton>
        </section>

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-rebar">
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

export function EstadoAsistente({ ia, apiOk, compacto }: { ia: EstadoIA | null; apiOk: boolean | null; compacto?: boolean }) {
  if (compacto) {
    if (apiOk === false || !ia) return null;
    return (
      <span className={`font-label text-[10px] uppercase tracking-wide ${ia.simulado ? "text-warn" : "text-rebar"}`} title={ia.motivo ?? `${ia.proveedor} · ${ia.modelo}`}>
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
          <b>IA en modo demostración.</b> {ia.motivo}. La lectura de imágenes devuelve una planta de ejemplo.
        </>
      ) : (
        <span className="font-label">
          IA: {ia.proveedor} · {ia.modelo}
        </span>
      )}
    </div>
  );
}
