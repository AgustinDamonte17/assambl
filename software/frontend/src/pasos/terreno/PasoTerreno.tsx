import { useEffect, useState } from "react";
import { api } from "../../api/cliente";
import { useProyecto } from "../../estado/ProyectoContext";
import Mapa from "./Mapa";
import PanelClima from "./PanelClima";
import PanelLote from "./PanelLote";
import PanelModelo from "./PanelModelo";
import PanelUbicacion from "./PanelUbicacion";
import Visor3D from "./Visor3D";

export type SubPaso = "ubicacion" | "lote" | "modelo" | "clima";

const SUBPASOS: { id: SubPaso; n: string; nombre: string }[] = [
  { id: "ubicacion", n: "1", nombre: "Ubicación y relieve" },
  { id: "lote", n: "2", nombre: "Lote" },
  { id: "modelo", n: "3", nombre: "Modelo 3D y sol" },
  { id: "clima", n: "4", nombre: "Clima" },
];

export default function PasoTerreno({ apiOk }: { apiOk: boolean | null }) {
  const { proyecto, despachar, escena, setEscena, trayectoria, setTrayectoria } = useProyecto();
  const [sub, setSub] = useState<SubPaso>("ubicacion");
  const t = proyecto.terreno;

  // Una vez generada la escena, se mantiene en sincronía con el lote, el margen y
  // el origen. La primera generación es explícita porque puede bajar mosaicos de
  // varios MB; las siguientes salen de la caché y son inmediatas.
  useEffect(() => {
    if (!escena || !t.ubicacion || !apiOk) return;
    const h = setTimeout(() => {
      api
        .generarEscena(t.ubicacion!.lat, t.ubicacion!.lon, t.margen_m, t.lote.vertices)
        .then((e) => {
          if (e.ref === escena.ref) return;
          setEscena(e);
          despachar({ tipo: "escena", escena: e });
        })
        .catch(() => undefined);
    }, 500);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t.ubicacion?.lat, t.ubicacion?.lon, t.margen_m, t.lote.vertices, apiOk, escena?.ref]);

  // Trayectoria solar del día elegido: se pide una vez y el visor interpola.
  useEffect(() => {
    if (!t.ubicacion || !apiOk) return;
    if (trayectoria && trayectoria.fecha === t.fecha_sol && trayectoria.lat === t.ubicacion.lat) return;
    api
      .sol(t.ubicacion.lat, t.ubicacion.lon, t.fecha_sol, t.huso_h)
      .then(setTrayectoria)
      .catch(() => setTrayectoria(null));
  }, [t.ubicacion, t.fecha_sol, t.huso_h, apiOk, trayectoria, setTrayectoria]);

  const habilitado: Record<SubPaso, boolean> = {
    ubicacion: true,
    lote: !!t.ubicacion,
    modelo: !!t.ubicacion && !!t.escena_ref,
    clima: !!t.ubicacion,
  };

  return (
    <div className="h-full grid grid-rows-[40px_1fr]">
      <div className="flex items-stretch border-b border-line bg-concrete">
        {SUBPASOS.map((s) => {
          const activo = s.id === sub;
          return (
            <button
              key={s.id}
              disabled={!habilitado[s.id]}
              onClick={() => setSub(s.id)}
              className={`px-5 text-xs uppercase tracking-wide border-b-2 -mb-px disabled:opacity-40 ${
                activo ? "border-signal text-ink" : "border-transparent text-rebar hover:text-ink"
              }`}
            >
              <span className="text-signal mr-2">{s.n}</span>
              {s.nombre}
            </button>
          );
        })}
        <div className="flex-1" />
        <div className="px-4 self-center text-[11px] text-rebar">
          {t.ubicacion
            ? `${t.ubicacion.lat.toFixed(5)}, ${t.ubicacion.lon.toFixed(5)} · margen ${t.margen_m} m · +Y norte`
            : "Sin ubicación"}
        </div>
      </div>

      <div className="grid grid-cols-[1fr_360px] min-h-0">
        <div className="relative min-h-0">
          {sub === "modelo" ? <Visor3D /> : <Mapa modo={sub === "lote" ? "lote" : "ubicacion"} />}
        </div>
        <aside className="border-l border-line bg-concrete overflow-y-auto p-4">
          {sub === "ubicacion" && <PanelUbicacion apiOk={apiOk} irALote={() => setSub("lote")} />}
          {sub === "lote" && <PanelLote irAModelo={() => setSub("modelo")} />}
          {sub === "modelo" && <PanelModelo />}
          {sub === "clima" && <PanelClima apiOk={apiOk} />}
        </aside>
      </div>
    </div>
  );
}
