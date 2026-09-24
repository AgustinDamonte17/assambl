/**
 * Panel del modelo 3D: procedencia de cada capa, control de fecha y hora, y las
 * salidas de la fase de terreno (.glb y script de Blender).
 */

import { api } from "../../api/cliente";
import { Aviso, Boton, Campo, Dato, EtiquetaNaturaleza, FichaFuente, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { cardinal } from "../../modelo/proyecto";
import { horaTexto, solALaHora } from "./sol";

export default function PanelModelo() {
  const { proyecto, escena, trayectoria, despachar } = useProyecto();
  const t = proyecto.terreno;

  if (!escena) return <p className="text-rebar text-xs">Generá la escena desde el panel de ubicación.</p>;

  const sol = trayectoria ? solALaHora(trayectoria, t.hora_sol) : null;
  const provisional = escena.relieve.provisional;

  return (
    <div className="text-xs">
      <Seccion titulo="3 · Modelo del sitio">
        <Dato etiqueta="Relieve" valor={`${escena.posts[0]} × ${escena.posts[1]} posts`} />
        <Dato etiqueta="Separación" valor={`${escena.paso_m[0]} × ${escena.paso_m[1]}`} sufijo="m" />
        <Dato etiqueta="Extensión" valor={`${escena.extension_m[0]} × ${escena.extension_m[1]}`} sufijo="m" />
        <Dato etiqueta="Cota del origen" valor={escena.relieve.cota_origen_msnm ?? "—"} sufijo="m s.n.m." />
        <Dato etiqueta="Lote" valor={escena.area_m2 || "—"} sufijo="m²" />
        <Dato
          etiqueta="Pendiente estimada"
          valor={provisional ? "—" : `${escena.pendiente_pct} % hacia ${cardinal(escena.pendiente_azimut_deg)}`}
        />
        <Dato etiqueta="Tamaño del .glb" valor={(escena.bytes_glb / 1024).toFixed(0)} sufijo="kB" />
      </Seccion>

      <Seccion titulo="Fecha y hora del sol">
        <div className="grid grid-cols-2 gap-2">
          <Campo
            etiqueta="Fecha"
            type="date"
            value={t.fecha_sol}
            onChange={(e) => despachar({ tipo: "sol_fecha", fecha: e.target.value })}
          />
          <Campo
            etiqueta="Huso horario"
            type="number"
            step={0.5}
            value={t.huso_h ?? ""}
            placeholder="automático"
            onChange={(e) => despachar({ tipo: "sol_huso", huso_h: e.target.value === "" ? null : Number(e.target.value) })}
            sufijo="h UTC"
          />
        </div>

        {trayectoria && (
          <>
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

      <Seccion titulo="Salida de la fase de terreno">
        <p className="text-rebar leading-snug mb-2">
          La misma geometría en dos formas: la malla resuelta y el código que la compone. Las dos salen del mismo
          generador.
        </p>
        <div className="flex flex-col gap-2">
          <a href={api.urlGlb(escena.ref)} download={`assambl_terreno_${escena.ref}.glb`}>
            <Boton className="w-full">Descargar escena .glb</Boton>
          </a>
          <a href={api.urlScriptBlender(escena.ref, t.fecha_sol, t.hora_sol, t.huso_h)}>
            <Boton className="w-full">Descargar script de Blender .py</Boton>
          </a>
        </div>
        <p className="text-[10px] text-rebar mt-2 leading-snug">
          El script trae el relieve como rejilla de posts, el contorno del lote apoyado y el sol orientado a la fecha y
          hora elegidas.
        </p>
      </Seccion>

      <p className="text-[10px] text-rebar mt-4 leading-snug">
        Arrastrá para orbitar, rueda para acercar, botón derecho para desplazar.
      </p>
    </div>
  );
}
