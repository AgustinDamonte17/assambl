/**
 * Cierre de la capa 01: lo que falta para confirmar el terreno y lo que queda
 * pendiente sin impedir el diseño. Los requisitos los decide el backend
 * (assambl/guia/terreno.py); acá solo se muestran. El botón Confirmar está en la
 * barra fija del paso 3.
 */

import { Aviso, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import type { SubPasoTerreno } from "../../modelo/proyecto";

const NOMBRE_PASO: Record<SubPasoTerreno, string> = {
  ubicacion: "Ubicación",
  lote: "Lote",
  modelo: "Modelo 3D",
};

export default function CierreTerreno({ irAPaso }: { irAPaso: (p: SubPasoTerreno) => void }) {
  const { requisitos } = useProyecto();
  const faltan = requisitos?.requisitos.filter((r) => r.bloquea && !r.cumple) ?? [];
  const avisos = requisitos?.requisitos.filter((r) => !r.bloquea && !r.cumple) ?? [];

  return (
    <Seccion titulo="Confirmar el terreno">
      {!requisitos && <p className="text-rebar">Verificando el terreno…</p>}

      {requisitos && faltan.length > 0 && (
        <>
          <p className="text-rebar leading-snug mb-2">Para confirmar falta:</p>
          <ul className="space-y-2">
            {faltan.map((r) => (
              <li key={r.id} className="leading-snug border-l-2 border-signal pl-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-ink">{r.descripcion}</span>
                  {r.paso && r.paso !== "modelo" && (
                    <button
                      className="text-signal text-[10px] uppercase tracking-wide shrink-0"
                      onClick={() => irAPaso(r.paso as SubPasoTerreno)}
                    >
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
          Ubicación, lote y modelo del sitio listos. Al confirmar empieza el diseño de la casa sobre este terreno.
        </p>
      )}

      {avisos.length > 0 && (
        <div className="mt-3 space-y-1">
          <p className="text-[10px] uppercase tracking-wide text-rebar">Queda pendiente, no impide confirmar</p>
          {avisos.map((r) => (
            <Aviso key={r.id}>
              <span className="text-ink">{r.descripcion}.</span> {r.detalle}
            </Aviso>
          ))}
        </div>
      )}
    </Seccion>
  );
}
