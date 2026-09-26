/**
 * Panel del modelo 3D: muestra el resultado de la reconstrucción del terreno. No
 * pide decisiones; el sol se puede recorrer para mirar, sin cambiar el proyecto.
 */

import { Aviso, Boton, Dato, EtiquetaNaturaleza, FichaFuente, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { cardinal } from "../../modelo/proyecto";
import { horaTexto, solALaHora } from "./sol";

export default function PanelModelo({ irAClima }: { irAClima: () => void }) {
  const { proyecto, escena, trayectoria, despachar } = useProyecto();
  const t = proyecto.terreno;

  if (!escena) return <p className="text-rebar text-xs">Generá la escena desde el panel de ubicación.</p>;

  const sol = trayectoria ? solALaHora(trayectoria, t.hora_sol) : null;
  const provisional = escena.relieve.provisional;

  return (
    <div className="text-xs">
      <Seccion titulo="3 · Terreno reconstruido">
        <p className="text-rebar leading-snug mb-2">
          Este es el terreno sobre el que vas a diseñar la casa. No hay nada que decidir acá: revisá que el relieve y el
          lote se vean como esperás.
        </p>
        <Dato etiqueta="Relieve" valor={`${escena.posts[0]} × ${escena.posts[1]} posts`} />
        <Dato etiqueta="Separación" valor={`${escena.paso_m[0]} × ${escena.paso_m[1]}`} sufijo="m" />
        <Dato etiqueta="Extensión" valor={`${escena.extension_m[0]} × ${escena.extension_m[1]}`} sufijo="m" />
        <Dato etiqueta="Cota del origen" valor={escena.relieve.cota_origen_msnm ?? "—"} sufijo="m s.n.m." />
        <Dato etiqueta="Lote" valor={escena.area_m2 || "—"} sufijo="m²" />
        <Dato
          etiqueta="Pendiente estimada"
          valor={provisional ? "—" : `${escena.pendiente_pct} % hacia ${cardinal(escena.pendiente_azimut_deg)}`}
        />
        {provisional && (
          <div className="mt-2">
            <Aviso fuerte>
              El relieve es plano porque no hubo datos de elevación para este punto. Podés seguir: el diseño avanza y la
              pendiente queda marcada como pendiente.
            </Aviso>
          </div>
        )}
      </Seccion>

      <Seccion titulo="Recorrido del sol">
        <p className="text-rebar leading-snug">
          Elegí un día clave y mové la hora en el visor para ver luz y sombras. Es solo para mirar: no cambia el
          proyecto.
        </p>
        {trayectoria && (
          <>
            <div className="mt-2">
              <Dato etiqueta="Día" valor={t.fecha_sol} />
            </div>
            <div className="flex flex-wrap gap-1 mt-2">
              {Object.entries(trayectoria.fechas_clave).map(([clave, fecha]) => (
                <Boton key={clave} onClick={() => despachar({ tipo: "sol_fecha", fecha })} className="!px-2 !py-1 !text-[10px]">
                  {clave.replace(/_/g, " ")}
                </Boton>
              ))}
            </div>
            <div className="mt-3">
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
            <div className="mt-2">
              <Aviso>{trayectoria.procedencia.advertencia}</Aviso>
            </div>
          </>
        )}
      </Seccion>

      <Seccion titulo="Procedencia por capa">
        <ul className="space-y-3">
          {escena.fuentes.map((f) => (
            <FichaFuente key={f.nombre} fuente={f} />
          ))}
          <li className="leading-snug border-t border-line pt-2">
            <div className="flex items-start justify-between gap-2">
              <span className="flex-1">Contorno del lote</span>
              <EtiquetaNaturaleza naturaleza="calculo_local" />
            </div>
            <div className="text-[10px] text-rebar mt-0.5">
              Resolución: exacta. La forma la definís vos; la altura sale de apoyar el contorno sobre la malla del
              relieve, no de medir el terreno.
            </div>
          </li>
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
          <li className="leading-snug border-t border-line pt-2">
            <div className="flex items-start justify-between gap-2">
              <span className="flex-1">Sombras</span>
              <EtiquetaNaturaleza naturaleza="calculo_local" />
            </div>
            <div className="text-[10px] text-rebar mt-0.5">
              Calculadas a partir del modelo 3D. Heredan la resolución del relieve: con posts cada{" "}
              {escena.paso_m[1]} m no representan el sombreado de un árbol ni de una medianera.
            </div>
          </li>
        </ul>
        <div className="mt-3 space-y-1">
          <Aviso fuerte={provisional}>
            {provisional
              ? "Escena provisional: el relieve es plano porque no hubo datos. No representa el terreno."
              : "El relieve es un modelo de elevación de unos 30 m de resolución. No es una mensura y no sirve para definir fundaciones."}
          </Aviso>
        </div>
      </Seccion>

      <p className="text-[10px] text-rebar mt-4 leading-snug">
        Arrastrá para orbitar, rueda para acercar, botón derecho para desplazar.
      </p>

      <div className="mt-5 flex justify-end">
        <Boton primario onClick={irAClima}>
          Siguiente: clima →
        </Boton>
      </div>
    </div>
  );
}
