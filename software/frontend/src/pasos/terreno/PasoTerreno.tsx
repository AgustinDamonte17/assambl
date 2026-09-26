import { useState } from "react";
import { Boton } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import type { SubPasoTerreno } from "../../modelo/proyecto";
import CierreTerreno from "./CierreTerreno";
import Mapa from "./Mapa";
import PanelClima from "./PanelClima";
import PanelLote from "./PanelLote";
import PanelModelo from "./PanelModelo";
import PanelUbicacion from "./PanelUbicacion";
import Visor3D from "./Visor3D";

type SubPaso = SubPasoTerreno;

const SUBPASOS: { id: SubPaso; n: string; nombre: string }[] = [
  { id: "ubicacion", n: "1", nombre: "Ubicación y relieve" },
  { id: "lote", n: "2", nombre: "Lote" },
  { id: "modelo", n: "3", nombre: "Modelo 3D y sol" },
  { id: "clima", n: "4", nombre: "Clima" },
];

export default function PasoTerreno({ apiOk, onAvanzar }: { apiOk: boolean | null; onAvanzar: () => void }) {
  const { proyecto, requisitos } = useProyecto();
  const [sub, setSub] = useState<SubPaso>("ubicacion");
  const t = proyecto.terreno;

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
        <div className="px-3 self-center">
          <Boton
            primario
            disabled={!requisitos?.listo}
            onClick={onAvanzar}
            title={requisitos?.listo ? "Pasar al diseño de la casa" : "Completá ubicación, relieve y lote para avanzar"}
          >
            Avanzar →
          </Boton>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_360px] min-h-0">
        <div className="relative min-h-0">
          {sub === "modelo" ? <Visor3D /> : <Mapa modo={sub === "lote" ? "lote" : "ubicacion"} />}
        </div>
        <aside className="border-l border-line bg-concrete overflow-y-auto p-4">
          {sub === "ubicacion" && <PanelUbicacion apiOk={apiOk} irALote={() => setSub("lote")} />}
          {sub === "lote" && <PanelLote irAModelo={() => setSub("modelo")} />}
          {sub === "modelo" && <PanelModelo irAClima={() => setSub("clima")} />}
          {sub === "clima" && (
            <>
              <PanelClima apiOk={apiOk} />
              <div className="mt-4">
                <CierreTerreno onAvanzar={onAvanzar} irAPaso={setSub} />
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
