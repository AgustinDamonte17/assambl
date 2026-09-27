/**
 * Paso 3 · Modelo 3D. El software reconstruye el lote y su entorno a partir de la
 * imagen satelital; el usuario no decide nada acá. Explora el modelo, el sol y el
 * clima, y confirma para empezar a diseñar la casa o vuelve a un paso anterior.
 */

import { Aviso, Boton, Dato, EtiquetaNaturaleza, FichaFuente, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { fmt } from "../../modelo/geometria";
import { cardinal, escenaVigente, type SubPasoTerreno } from "../../modelo/proyecto";
import CierreTerreno from "./CierreTerreno";
import PanelClima from "./PanelClima";
import { horaTexto, solALaHora } from "./sol";

export interface EstadoGeneracion {
  generando: boolean;
  error: string | null;
  reintentar: () => void;
}

export default function PanelModelo({
  generacion,
  apiOk,
  irAPaso,
  onConfirmar,
}: {
  generacion: EstadoGeneracion;
  apiOk: boolean | null;
  irAPaso: (p: SubPasoTerreno) => void;
  onConfirmar: () => void;
}) {
  const { proyecto, escena, trayectoria, despachar, requisitos } = useProyecto();
  const t = proyecto.terreno;
  const vigente = escenaVigente(escena, t);
  const sol = trayectoria ? solALaHora(trayectoria, t.hora_sol) : null;
  const r = vigente ? escena!.resumen : null;

  return (
    <div className="text-xs flex flex-col min-h-full">
      <div className="flex-1">
        <Seccion titulo="3 · Modelo 3D del sitio">
          <p className="text-rebar leading-snug">
            El lote y su entorno reconstruidos a partir de la imagen satelital. No hay nada que decidir: recorré el
            modelo, el sol y el clima, y confirmá para empezar a diseñar la casa.
          </p>
          {generacion.generando && (
            <p className="mt-3 text-ink leading-snug">
              Reconstruyendo el sitio: imagen satelital, calles, construcciones y árboles… La primera vez puede tardar
              un minuto.
            </p>
          )}
          {generacion.error && (
            <div className="mt-3">
              <p className="text-signal leading-snug">No se pudo reconstruir el sitio: {generacion.error}</p>
              <Boton onClick={generacion.reintentar} className="mt-2">
                Reintentar
              </Boton>
            </div>
          )}
          {r && escena && (
            <div className="mt-3">
              <Dato
                etiqueta="Árboles en el lote"
                valor={`${r.arboles_lote}${r.interpretacion === "ia" ? " · con IA" : ""}`}
              />
              <Dato etiqueta="Árboles en el borde del lote" valor={r.arboles_borde} />
              <Dato etiqueta="Árboles en el entorno" valor={r.arboles_entorno} />
              <Dato etiqueta="Construcciones" valor={r.construcciones} />
              <Dato etiqueta="Calles y caminos" valor={r.vias} />
              <Dato
                etiqueta="Imagen"
                valor={`lote ${r.m_px_lote ?? "—"} · entorno ${r.m_px_entorno}`}
                sufijo="m/píxel"
              />
              <div className="mt-2 space-y-1">
                {escena.advertencias.map((a, i) => (
                  <Aviso key={i} fuerte={r.sintetica && a.startsWith("IMAGEN SINTÉTICA")}>
                    {a}
                  </Aviso>
                ))}
              </div>
            </div>
          )}
        </Seccion>

        {r && escena && escena.arboles_lote.length > 0 && (
          <Seccion titulo="Árboles del lote">
            <table className="w-full">
              <thead className="text-[10px] uppercase tracking-wide text-rebar">
                <tr>
                  <th className="text-left font-normal py-1">Id</th>
                  <th className="text-right font-normal">Copa Ø m</th>
                  <th className="text-right font-normal">Altura m</th>
                  <th className="text-right font-normal">Dónde</th>
                </tr>
              </thead>
              <tbody>
                {escena.arboles_lote.map((a) => (
                  <tr key={a.id} className="border-t border-line">
                    <td className="py-1 text-rebar">{a.id}</td>
                    <td className="text-right">{fmt(a.radio_m * 2, 1)}</td>
                    <td className="text-right">
                      {fmt(a.altura_m, 1)}
                      {a.altura_supuesta && <span className="text-rebar">*</span>}
                    </td>
                    <td className="text-right text-rebar">{a.dentro_del_lote ? "lote" : "borde"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-[10px] text-rebar mt-2 leading-snug">
              Posición y copa medidas en la imagen. * Altura supuesta a partir del tamaño de la copa: desde arriba no se
              puede medir.
            </p>
          </Seccion>
        )}

        <Seccion titulo="Recorrido del sol">
          <p className="text-rebar leading-snug">
            Elegí un día clave y mové la hora en el visor para ver luz y sombras. Es solo para mirar: no cambia el
            proyecto.
          </p>
          {trayectoria && (
            <>
              <div className="flex flex-wrap gap-1 mt-2">
                {Object.entries(trayectoria.fechas_clave).map(([clave, fecha]) => (
                  <Boton
                    key={clave}
                    onClick={() => despachar({ tipo: "sol_fecha", fecha })}
                    className={`!px-2 !py-1 !text-[10px] ${fecha === t.fecha_sol ? "!border-signal" : ""}`}
                  >
                    {clave.replace(/_/g, " ")}
                  </Boton>
                ))}
              </div>
              <div className="mt-3">
                <Dato etiqueta="Día" valor={t.fecha_sol} />
                <Dato etiqueta="Hora" valor={horaTexto(t.hora_sol)} />
                <Dato etiqueta="Amanece" valor={trayectoria.eventos.amanecer_local ?? "—"} />
                <Dato etiqueta="Mediodía solar" valor={trayectoria.eventos.mediodia_solar_local} />
                <Dato etiqueta="Atardece" valor={trayectoria.eventos.atardecer_local ?? "—"} />
                <Dato etiqueta="Duración del día" valor={trayectoria.eventos.duracion_dia_h.toFixed(2)} sufijo="h" />
                {sol && (
                  <>
                    <Dato etiqueta="Azimut" valor={`${sol.azimut_deg.toFixed(1)}° (${cardinal(sol.azimut_deg)})`} />
                    <Dato etiqueta="Altura sobre el horizonte" valor={sol.elevacion_deg.toFixed(1)} sufijo="°" />
                  </>
                )}
              </div>
            </>
          )}
        </Seccion>

        <PanelClima apiOk={apiOk} />

        {vigente && escena && (
          <Seccion titulo="Procedencia">
            <ul className="space-y-3">
              {escena.fuentes.map((f) => (
                <FichaFuente key={f.nombre} fuente={f} />
              ))}
              {trayectoria && (
                <li className="leading-snug border-t border-line pt-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="flex-1">Posición del sol</span>
                    <EtiquetaNaturaleza naturaleza="calculo_local" />
                  </div>
                  <div className="text-[10px] text-rebar mt-0.5">
                    Resolución: {trayectoria.procedencia.resolucion}. {trayectoria.algoritmo}.
                  </div>
                </li>
              )}
            </ul>
          </Seccion>
        )}

        <CierreTerreno irAPaso={irAPaso} />
      </div>

      <div className="sticky -bottom-4 -mx-4 -mb-4 mt-4 px-4 py-3 bg-concrete border-t border-line flex items-center gap-2">
        <Boton onClick={() => irAPaso("ubicacion")}>← Ubicación</Boton>
        <Boton onClick={() => irAPaso("lote")}>← Lote</Boton>
        <div className="flex-1" />
        <Boton
          primario
          disabled={!requisitos?.listo}
          onClick={onConfirmar}
          title={requisitos?.listo ? "Empezar a diseñar la casa sobre este terreno" : "Falta completar el terreno"}
          className="!px-4"
        >
          Confirmar →
        </Boton>
      </div>
    </div>
  );
}
