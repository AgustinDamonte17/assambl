/** Datos y acciones de un mueble o artefacto elegido. Lo usan el panel de la planta y el de la vista 3D. */

import { Boton, Dato, Etiqueta } from "../../componentes/ui";
import { USOS, type AnalisisPlanta, type Casa, type Pieza } from "../../modelo/casa";
import { buscarPieza, CATALOGO_MUEBLES, itemMueble, medidas, nombrePieza } from "../../modelo/muebles";
import { ASPECTO, estadoDe } from "./estados";
import { borrarPieza, cambiarModelo, duplicarPieza, girarPieza, marcarRevisado } from "./operaciones";

export function PropiedadesMueble({
  casa,
  id,
  analisis,
  aplicar,
}: {
  casa: Casa;
  id: string;
  analisis: AnalisisPlanta | null;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
}) {
  const p = buscarPieza(casa, id);
  if (!p) return null;
  const sel: Pieza = { tipo: "mueble", id };
  const it = itemMueble(p.tipo);
  const variantes = it?.grupo ? CATALOGO_MUEBLES.filter((x) => x.grupo === it.grupo) : [];
  const [a, f, h] = medidas(p);
  const amb = casa.ambientes.find((x) => x.id === p.ambiente);
  const estado = estadoDe(casa, sel, analisis);
  const reglas = (analisis?.verificaciones ?? []).filter((v) => v.piezas.includes(id) && v.estado !== "comprobado_por_reglas");
  return (
    <div>
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div>
          <div className="font-head text-sm font-bold leading-snug">{nombrePieza(p)}</div>
          <div className="font-label text-[10px] text-rebar">{p.id}</div>
        </div>
        <Etiqueta estado={estado} />
      </div>
      <div className="text-xs">
        <Dato
          etiqueta="Ambiente"
          valor={<span className="font-body">{amb ? `${amb.nombre}` : "fuera de un ambiente"}</span>}
        />
        <Dato etiqueta="Medidas" valor={`${a.toFixed(2)} × ${f.toFixed(2)} × ${h.toFixed(2)}`} sufijo="m" />
        {it && it.frente_libre_m > 0 && it.apoyo !== "libre" && <Dato etiqueta="Libre delante" valor={(it.frente_libre_m * 100).toFixed(0)} sufijo="cm" />}
      </div>
      {variantes.length > 1 && (
        <label className="grid grid-cols-[92px_1fr] items-center gap-2 py-0.5 mt-1">
          <span className="text-xs text-rebar">Modelo</span>
          <select
            value={p.tipo}
            onChange={(e) => aplicar(cambiarModelo(casa, id, e.target.value), sel)}
            className="bg-concrete-2 border border-line px-1 py-0.5 text-xs"
          >
            {variantes.map((v) => (
              <option key={v.codigo} value={v.codigo}>
                {v.nombre}
              </option>
            ))}
          </select>
        </label>
      )}
      {it?.usos && amb && !it.usos.includes(amb.uso) && (
        <p className="text-[11px] text-warn mt-1 leading-snug">
          Va en {it.usos.map((u) => USOS.find((x) => x.id === u)?.nombre.toLowerCase() ?? u).join(", ")}.
        </p>
      )}
      {it?.nota && <p className="text-[11px] text-rebar mt-1 leading-snug">{it.nota}</p>}
      {reglas.map((v, i) => (
        <p key={i} className="text-[11px] leading-snug border-l-2 pl-2 mt-1" style={{ borderColor: ASPECTO[v.estado].acento }}>
          {v.detalle || v.descripcion}
        </p>
      ))}
      <div className="flex gap-1.5 mt-2 flex-wrap">
        <Boton onClick={() => aplicar(girarPieza(casa, id, 1), sel)} title="Girar 90° (R)">
          ↺ Girar
        </Boton>
        <Boton
          onClick={() => {
            const r = duplicarPieza(casa, id);
            if (r) aplicar(r.casa, { tipo: "mueble", id: r.id });
          }}
          title="Duplicar (Ctrl+D)"
        >
          Duplicar
        </Boton>
        <Boton onClick={() => aplicar(marcarRevisado(casa, new Set([id])), sel)} disabled={estado === "revisado"}>
          ✓ Revisado
        </Boton>
        <Boton onClick={() => aplicar(borrarPieza(casa, id), null)} title="Borrar (Supr)">
          Borrar
        </Boton>
      </div>
    </div>
  );
}
