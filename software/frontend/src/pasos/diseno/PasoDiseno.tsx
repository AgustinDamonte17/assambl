/**
 * Etapa de diseño de la casa. Arranca sobre el terreno reconstruido en la capa 01:
 * el visor muestra ese relieve con el lote apoyado, y el panel reúne los datos de
 * partida. Las herramientas para dibujar la casa se construyen sobre esta base.
 */

import { Aviso, Boton, Dato, Etiqueta, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { fmt } from "../../modelo/geometria";
import { cardinal } from "../../modelo/proyecto";
import Visor3D from "../terreno/Visor3D";

export default function PasoDiseno({ onVolver }: { onVolver: () => void }) {
  const { proyecto, requisitos, clima } = useProyecto();
  const t = proyecto.terreno;
  const avisos = requisitos?.requisitos.filter((r) => !r.bloquea && !r.cumple) ?? [];
  const bloqueado = requisitos !== null && !requisitos.listo;

  const viento = clima?.clima.rosa.length
    ? clima.clima.rosa.reduce((a, b) => (b.frecuencia_pct > a.frecuencia_pct ? b : a))
    : null;

  return (
    <div className="h-full grid grid-rows-[40px_1fr]">
      <div className="flex items-center gap-4 border-b border-line bg-concrete px-4">
        <button className="text-xs text-rebar hover:text-ink" onClick={onVolver}>
          ← Terreno
        </button>
        <span className="text-xs uppercase tracking-wide">
          <span className="text-signal mr-2">·</span>Diseño de la casa
        </span>
        <div className="flex-1" />
        <span className="text-[11px] text-rebar">
          {t.ubicacion ? `${t.ubicacion.lat.toFixed(5)}, ${t.ubicacion.lon.toFixed(5)} · +Y norte` : ""}
        </span>
      </div>

      <div className="grid grid-cols-[1fr_360px] min-h-0">
        <div className="relative min-h-0">
          <Visor3D />
        </div>
        <aside className="border-l border-line bg-concrete overflow-y-auto p-4 text-xs">
          {bloqueado ? (
            <Seccion titulo="El terreno cambió">
              <p className="text-rebar leading-snug mb-3">
                Para diseñar hace falta el terreno completo. Falta resolver:
              </p>
              <ul className="space-y-1 mb-3">
                {requisitos!.requisitos
                  .filter((r) => r.bloquea && !r.cumple)
                  .map((r) => (
                    <li key={r.id} className="border-l-2 border-signal pl-2">
                      {r.descripcion}
                    </li>
                  ))}
              </ul>
              <Boton primario onClick={onVolver}>
                Volver al terreno
              </Boton>
            </Seccion>
          ) : (
            <>
              <Seccion titulo="Diseño de la casa">
                <p className="text-rebar leading-snug">
                  La casa se diseña sobre el terreno que reconstruiste: el relieve, el lote y el norte del visor son los del
                  proyecto. El primer paso es ubicar la huella de la casa dentro del lote.
                </p>
                <div className="mt-3">
                  <Aviso>
                    Las herramientas de diseño (huella, ambientes, muros y aberturas) son el próximo desarrollo. Por ahora
                    esta etapa muestra el punto de partida.
                  </Aviso>
                </div>
              </Seccion>

              <Seccion titulo="Datos de partida" accion={<Etiqueta estado={t.estado} />}>
                <Dato etiqueta="Superficie del lote" valor={fmt(t.lote.area_m2 ?? 0)} sufijo="m²" />
                <Dato etiqueta="Perímetro" valor={fmt(t.lote.perimetro_m ?? 0)} sufijo="m" />
                <Dato etiqueta="Lados" valor={t.lote.lados.length} />
                <Dato
                  etiqueta="Pendiente"
                  valor={
                    t.pendiente ? (
                      `${fmt(t.pendiente.porcentaje, 1)} % hacia ${cardinal(t.pendiente.direccion_deg)}`
                    ) : (
                      <span className="text-rebar">sin relieve medido</span>
                    )
                  }
                />
                <Dato etiqueta="Cota del origen" valor={t.sistema_local?.cota_origen_msnm ?? "—"} sufijo="m s.n.m." />
                {clima && (
                  <>
                    <Dato
                      etiqueta="Grados-día"
                      valor={`${clima.clima.grados_dia_calefaccion ?? "—"} calef. · ${clima.clima.grados_dia_refrigeracion ?? "—"} refrig.`}
                    />
                    {viento && <Dato etiqueta="Viento predominante" valor={`del ${cardinal(viento.centro_deg)}`} />}
                  </>
                )}
              </Seccion>

              {avisos.length > 0 && (
                <Seccion titulo="Pendientes del terreno">
                  <div className="space-y-1">
                    {avisos.map((r) => (
                      <Aviso key={r.id}>
                        <span className="text-ink">{r.descripcion}.</span> {r.detalle}
                      </Aviso>
                    ))}
                  </div>
                  <p className="text-[10px] text-rebar mt-2 leading-snug">
                    No impiden diseñar. Siguen marcados en el proyecto hasta que se resuelvan.
                  </p>
                </Seccion>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
