/** Galería de plantas de referencia (docs/interior_fundamentals) y los fundamentos de diseño.
 *  Otra manera de empezar: elegir una casa que ya funciona y adaptarla. Cada planta se muestra
 *  como el dibujo original y como la arma Assambl, orientada al sol y evaluada. */

import { useEffect, useState } from "react";
import { api } from "../../api/cliente";
import type { AnalisisPlanta, Casa, Evaluacion, PlantaReferencia } from "../../modelo/casa";
import { Aviso, Boton } from "../../componentes/ui";
import { MiniPlanta } from "./Alternativas";
import { Criterios, destacadas, ItemObservacion, Teoria } from "./Fundamentos";
import Monti from "./Monti";

// Los dibujos originales viven en software/docs; Vite los copia al construir.
const ORIGINALES = import.meta.glob("../../../../docs/interior_fundamentals/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

function original(archivo: string): string | undefined {
  return Object.entries(ORIGINALES).find(([ruta]) => ruta.endsWith("/" + archivo))?.[1];
}

interface Armada {
  casa: Casa;
  evaluacion: Evaluacion;
  analisis: AnalisisPlanta;
  adaptacion: string[];
}

interface Props {
  lat: number | null;
  pestana: "plantas" | "teoria";
  setPestana: (p: "plantas" | "teoria") => void;
  elegir: (casa: Casa) => void;
  volver: () => void;
}

export default function Referencias({ lat, pestana, setPestana, elegir, volver }: Props) {
  const [plantas, setPlantas] = useState<PlantaReferencia[] | null>(null);
  const [armadas, setArmadas] = useState<Record<string, Armada>>({});
  const [error, setError] = useState<string | null>(null);
  const [verOriginal, setVerOriginal] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api
      .referencias()
      .then((ps) => {
        setPlantas(ps);
        for (const p of ps)
          api
            .partirDeReferencia(p.id, lat)
            .then((r) => setArmadas((a) => ({ ...a, [p.id]: r })))
            .catch(() => undefined);
      })
      .catch((e) => setError(`No se pudieron cargar las plantas: ${(e as Error).message}`));
  }, [lat]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <button className="text-xs text-rebar hover:text-ink" onClick={volver}>
          ← Formas de empezar
        </button>
        <div className="flex items-center gap-4 mt-3 mb-4">
          <Monti animo="contento" tamano={52} />
          <div>
            <h1 className="font-display text-2xl">Casas que funcionan, y por qué</h1>
            <p className="text-rebar text-sm mt-1 max-w-3xl">
              Diez plantas de 60 a 204 m² resueltas con criterios distintos. Monti las usa como base de sus propuestas;
              acá podés recorrerlas, ver qué gana y qué resigna cada una, y empezar tu casa desde la que más te guste.
            </p>
          </div>
        </div>
        <div className="flex gap-1 mb-5 border-b border-line">
          {(
            [
              ["plantas", "Plantas de referencia"],
              ["teoria", "Fundamentos de diseño"],
            ] as const
          ).map(([id, nombre]) => (
            <button
              key={id}
              onClick={() => setPestana(id)}
              className={`px-3 py-1.5 text-xs -mb-px border-b-2 ${pestana === id ? "border-signal text-ink" : "border-transparent text-rebar hover:text-ink"}`}
            >
              {nombre}
            </button>
          ))}
        </div>

        {pestana === "teoria" ? (
          <Teoria />
        ) : (
          <>
            {error && <Aviso fuerte>{error}</Aviso>}
            {!plantas && !error && <p className="text-rebar">Cargando…</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {plantas?.map((p) => {
                const a = armadas[p.id];
                const img = original(p.archivo);
                const d = a ? destacadas(a.evaluacion, 2) : null;
                return (
                  <article key={p.id} className="border border-line bg-concrete-2 flex flex-col">
                    <div className="border-b border-line relative">
                      {verOriginal[p.id] && img ? (
                        <img src={img} alt={`Planta original de ${p.nombre}`} className="block w-full h-[220px] object-contain bg-white" />
                      ) : a ? (
                        <MiniPlanta casa={a.casa} analisis={null} />
                      ) : (
                        <div className="h-[220px] flex items-center justify-center text-xs text-rebar">Armando…</div>
                      )}
                      {img && (
                        <button
                          className="absolute top-2 right-2 text-[10px] bg-concrete/90 border border-line px-1.5 py-0.5 hover:border-ink"
                          onClick={() => setVerOriginal((v) => ({ ...v, [p.id]: !v[p.id] }))}
                        >
                          {verOriginal[p.id] ? "Ver en Assambl" : "Ver dibujo original"}
                        </button>
                      )}
                    </div>
                    <div className="p-4 flex flex-col gap-2 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <h2 className="font-semibold">{p.nombre}</h2>
                        <span className="text-[11px] text-rebar whitespace-nowrap">{p.superficie_m2} m²</span>
                      </div>
                      <p className="text-[11px] text-rebar">
                        {p.dormitorios} dormitorios · {p.banos} baño{p.banos > 1 ? "s" : ""}
                        {p.garage ? " · garage" : ""}
                      </p>
                      <p className="text-xs leading-relaxed">{p.lectura}</p>
                      <ul className="flex flex-wrap gap-1">
                        {p.rasgos_texto.map((r) => (
                          <li key={r} className="text-[10px] border border-line px-1.5 py-0.5 text-rebar">
                            {r}
                          </li>
                        ))}
                      </ul>
                      {a && d && (
                        <>
                          <div className="mt-1">
                            <Criterios evaluacion={a.evaluacion} compacto />
                          </div>
                          <ul className="flex flex-col gap-1 mt-1">
                            {[...d.favor, ...d.considerar].map((o, i) => (
                              <ItemObservacion key={i} o={o} />
                            ))}
                          </ul>
                        </>
                      )}
                      <div className="mt-auto pt-2">
                        <Boton primario className="w-full" disabled={!a} onClick={() => a && elegir(a.casa)}>
                          Empezar desde esta →
                        </Boton>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
