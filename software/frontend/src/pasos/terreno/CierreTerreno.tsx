/**
 * Cierre de la capa 01: lo que falta para empezar a diseñar la casa y el botón
 * para avanzar. Los requisitos los decide el backend (assambl/guia/terreno.py);
 * acá solo se muestran.
 */

import { Aviso, Boton, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import type { SubPasoTerreno } from "../../modelo/proyecto";

const NOMBRE_PASO: Record<SubPasoTerreno, string> = {
  ubicacion: "Ubicación",
  lote: "Lote",
  modelo: "Modelo 3D",
  clima: "Clima",
};

export default function CierreTerreno({
  onAvanzar,
  irAPaso,
}: {
  onAvanzar: () => void;
  irAPaso: (p: SubPasoTerreno) => void;
}) {
  const { requisitos } = useProyecto();
  const faltan = requisitos?.requisitos.filter((r) => r.bloquea && !r.cumple) ?? [];
  const avisos = requisitos?.requisitos.filter((r) => !r.bloquea && !r.cumple) ?? [];

  return (
    <Seccion titulo="Terreno listo para diseñar">
      {!requisitos && <p className="text-rebar">Verificando el terreno…</p>}

      {requisitos && faltan.length > 0 && (
        <>
          <p className="text-rebar leading-snug mb-2">Para avanzar falta resolver:</p>
          <ul className="space-y-2">
            {faltan.map((r) => (
              <li key={r.id} className="leading-snug border-l-2 border-signal pl-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-ink">{r.descripcion}</span>
                  {r.paso && (
                    <button className="text-signal text-[10px] uppercase tracking-wide shrink-0" onClick={() => irAPaso(r.paso as SubPasoTerreno)}>
                      Ir a {NOMBRE_PASO[r.paso as SubPasoTerreno]}
                    </button>
                  )}
                </div>
                {r.detalle && <div className="text-[10px] text-rebar mt-0.5">{r.detalle}</div>}
              </li>
            ))}
          </ul>
        </>
      )}

      {requisitos?.listo && (
        <p className="text-resolved leading-snug">
          Ubicación, relieve y lote resueltos. El diseño de la casa arranca sobre este terreno.
        </p>
      )}

      {avisos.length > 0 && (
        <div className="mt-3 space-y-1">
          <p className="text-[10px] uppercase tracking-wide text-rebar">Queda pendiente, no impide avanzar</p>
          {avisos.map((r) => (
            <Aviso key={r.id}>
              <span className="text-ink">{r.descripcion}.</span> {r.detalle}
            </Aviso>
          ))}
        </div>
      )}

      <Boton primario disabled={!requisitos?.listo} onClick={onAvanzar} className="w-full mt-4 !py-3 !text-sm">
        Avanzar al diseño de la casa →
      </Boton>
    </Seccion>
  );
}
