/**
 * Panel de clima. Todo lo que muestra viene de NASA POWER, que es un reanálisis
 * global: describe la región, no el lote. Los avisos que acompañan cada bloque no
 * son decorativos.
 */

import { useEffect, useState } from "react";
import { api } from "../../api/cliente";
import { Aviso, Boton, Dato, FichaFuente, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { cardinal, MESES_CORTOS, type Clima, type SectorViento } from "../../modelo/proyecto";

export default function PanelClima({ apiOk }: { apiOk: boolean | null }) {
  const { proyecto, clima, setClima } = useProyecto();
  const t = proyecto.terreno;
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mesElegido, setMesElegido] = useState(0);

  const ubicacion = t.ubicacion;
  const vigente = !!clima && !!ubicacion && Math.abs(clima.clima.lat - ubicacion.lat) < 1e-6;

  useEffect(() => {
    if (!ubicacion || !apiOk || vigente || cargando) return;
    setCargando(true);
    setError(null);
    api
      .clima(ubicacion.lat, ubicacion.lon)
      .then(setClima)
      .catch((e) => setError((e as Error).message))
      .finally(() => setCargando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ubicacion?.lat, ubicacion?.lon, apiOk]);

  if (!ubicacion) return <p className="text-rebar text-xs">Definí primero la ubicación.</p>;
  if (cargando) return <p className="text-rebar text-xs">Descargando series de NASA POWER… la primera vez tarda.</p>;
  if (error) return <p className="text-signal text-xs">{error}</p>;
  if (!clima) return <p className="text-rebar text-xs">Sin datos de clima.</p>;

  const c = clima.clima;
  const mes = c.meses[mesElegido];

  return (
    <div className="text-xs">
      <Seccion titulo="4 · Clima del sitio">
        <Dato etiqueta="Período de climatología" valor={<span className="text-[10px]">{c.periodo_climatologia}</span>} />
        <Dato etiqueta="Series horarias" valor={`${c.periodo_horario} · ${c.horas.toLocaleString("es-AR")} horas`} />
        <Dato etiqueta="Elevación de la celda" valor={c.elevacion_power_m ?? "—"} sufijo="m s.n.m." />
        <Dato
          etiqueta={`Grados-día (base ${c.base_grados_dia_c} °C)`}
          valor={`${c.grados_dia_calefaccion ?? "—"} calef. · ${c.grados_dia_refrigeracion ?? "—"} refrig.`}
        />
        <div className="mt-2">
          <Aviso fuerte>
            La celda de POWER mide decenas de kilómetros y su elevación es {c.elevacion_power_m ?? "—"} m, que puede no
            coincidir con la del lote. Es una estimación regional.
          </Aviso>
        </div>
      </Seccion>

      <Seccion titulo="Temperatura por mes">
        <TablaMeses clima={c} mesElegido={mesElegido} onMes={setMesElegido} />
        <p className="text-[10px] text-rebar mt-2 leading-snug">
          Media del período de climatología; máxima y mínima son los extremos registrados, no promedios de máximas.
        </p>
      </Seccion>

      <Seccion titulo={`Día medio de ${MESES_CORTOS[mesElegido]}`}>
        {mes.perfil_horario_c.length === 24 ? (
          <PerfilHorario valores={mes.perfil_horario_c} />
        ) : (
          <p className="text-rebar">Sin series horarias para este mes.</p>
        )}
        <p className="text-[10px] text-rebar mt-1">
          Media de cada hora solar local en las series horarias. Amplitud diaria de{" "}
          {(Math.max(...mes.perfil_horario_c) - Math.min(...mes.perfil_horario_c)).toFixed(1)} °C.
        </p>
      </Seccion>

      <Seccion titulo="Radiación solar por mes">
        <BarrasRadiacion clima={c} />
        <p className="text-[10px] text-rebar mt-1">
          Irradiancia global horizontal media diaria, en kWh/m² por día. Es radiación histórica medida por satélite: no
          es lo mismo que la posición del sol ni que la sombra del modelo 3D.
        </p>
      </Seccion>

      <Seccion titulo="Rosa de vientos">
        <RosaDeVientos rosa={c.rosa} bins={c.bins_velocidad_ms} />
        <div className="mt-2">
          <Dato etiqueta="Calmas" valor={c.calma_pct.toFixed(1)} sufijo="%" />
          <Dato
            etiqueta="Dirección dominante"
            valor={(() => {
              const d = c.rosa.reduce((a, b) => (b.frecuencia_pct > a.frecuencia_pct ? b : a));
              return `${cardinal(d.centro_deg)} (${d.centro_deg}°) · ${d.frecuencia_pct.toFixed(1)} %`;
            })()}
          />
          <Dato etiqueta="Altura de medición" valor={c.altura_medicion_viento_m} sufijo="m" />
        </div>
        <div className="mt-2">
          <Aviso fuerte>
            Velocidades a {c.altura_medicion_viento_m} m sobre terreno abierto de la celda. No es la velocidad que habrá
            junto a una ventana del proyecto: el entorno construido, la vegetación y la propia casa la cambian por
            completo.
          </Aviso>
        </div>
      </Seccion>

      <Seccion titulo="Procedencia">
        <ul className="space-y-2">
          <FichaFuente fuente={clima.fuente} />
        </ul>
        <div className="mt-2 space-y-1">
          {clima.advertencias.map((a, i) => (
            <Aviso key={i}>{a}</Aviso>
          ))}
        </div>
        <details className="mt-3">
          <summary className="cursor-pointer text-rebar text-[11px]">Parámetros y unidades informados por la fuente</summary>
          <div className="mt-2 space-y-2">
            {(
              [
                ["Climatología", c.parametros_climatologia],
                ["Series horarias", c.parametros_horarios],
              ] as const
            ).map(([titulo, bloque]) => (
              <div key={titulo}>
                <div className="text-[10px] uppercase tracking-widest text-rebar">{titulo}</div>
                <ul className="text-[10px] text-rebar">
                  {Object.entries(bloque).map(([clave, info]) => (
                    <li key={clave} className="flex justify-between gap-2">
                      <span className="font-mono">{clave}</span>
                      <span className="text-right flex-1">{info.nombre}</span>
                      <span>{info.unidad}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
        <div className="mt-3">
          <Boton
            className="w-full"
            onClick={() => {
              setClima(null);
              setError(null);
            }}
          >
            Volver a consultar
          </Boton>
        </div>
      </Seccion>
    </div>
  );
}

function TablaMeses({ clima, mesElegido, onMes }: { clima: Clima; mesElegido: number; onMes: (m: number) => void }) {
  const valores = clima.meses.flatMap((m) => [m.t_min_c, m.t_max_c].filter((v): v is number => v !== null));
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const escala = (v: number) => ((v - min) / (max - min || 1)) * 100;

  return (
    <table className="w-full tabular-nums">
      <thead>
        <tr className="text-[10px] uppercase tracking-wide text-rebar">
          <th className="text-left font-normal">mes</th>
          <th className="text-right font-normal">mín</th>
          <th className="text-right font-normal">media</th>
          <th className="text-right font-normal">máx</th>
          <th className="w-20"></th>
        </tr>
      </thead>
      <tbody>
        {clima.meses.map((m, i) => (
          <tr
            key={m.mes}
            onClick={() => onMes(i)}
            className={`cursor-pointer hover:bg-concrete-2 ${i === mesElegido ? "bg-concrete-2" : ""}`}
          >
            <td className={i === mesElegido ? "text-ink" : "text-rebar"}>{MESES_CORTOS[i]}</td>
            <td className="text-right">{m.t_min_c?.toFixed(1) ?? "—"}</td>
            <td className="text-right text-ink">{m.t_media_c?.toFixed(1) ?? "—"}</td>
            <td className="text-right">{m.t_max_c?.toFixed(1) ?? "—"}</td>
            <td className="pl-2">
              {m.t_min_c !== null && m.t_max_c !== null && (
                <svg viewBox="0 0 100 8" className="w-full h-2">
                  <rect x={escala(m.t_min_c)} y={2} width={Math.max(escala(m.t_max_c) - escala(m.t_min_c), 1)} height={4} fill="#8a857a" />
                  {m.t_media_c !== null && <rect x={escala(m.t_media_c) - 0.8} y={0} width={1.6} height={8} fill="#ff4f1f" />}
                </svg>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PerfilHorario({ valores }: { valores: number[] }) {
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const y = (v: number) => 40 - ((v - min) / (max - min || 1)) * 34;
  const d = valores.map((v, i) => `${i === 0 ? "M" : "L"}${(i / 23) * 100},${y(v)}`).join(" ");
  return (
    <div>
      <svg viewBox="0 0 100 44" className="w-full h-16" preserveAspectRatio="none">
        <path d={d} fill="none" stroke="#ff4f1f" strokeWidth={1.2} vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="flex justify-between text-[10px] text-rebar">
        <span>00 h</span>
        <span>{max.toFixed(1)} °C máx</span>
        <span>{min.toFixed(1)} °C mín</span>
        <span>23 h</span>
      </div>
    </div>
  );
}

function BarrasRadiacion({ clima }: { clima: Clima }) {
  const valores = clima.meses.map((m) => m.radiacion_kwh_m2_dia ?? 0);
  const max = Math.max(...valores, 1);
  return (
    <div>
      <div className="flex items-end gap-0.5 h-20">
        {valores.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end items-center" title={`${MESES_CORTOS[i]}: ${v} kWh/m²/día`}>
            <div className="w-full bg-signal" style={{ height: `${(v / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="flex gap-0.5 text-[9px] text-rebar">
        {MESES_CORTOS.map((m, i) => (
          <span key={i} className="flex-1 text-center">
            {m[0]}
          </span>
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-rebar mt-1">
        <span>mín {Math.min(...valores).toFixed(1)}</span>
        <span>máx {max.toFixed(1)} kWh/m²/día</span>
      </div>
    </div>
  );
}

const GRISES = ["#d8d4cc", "#b9b3a8", "#9a9387", "#7b7468", "#5c574e", "#ff4f1f"];

function RosaDeVientos({ rosa, bins }: { rosa: SectorViento[]; bins: number[] }) {
  if (!rosa.length) return <p className="text-rebar">Sin series horarias de viento.</p>;
  const maximo = Math.max(...rosa.map((s) => s.frecuencia_pct));
  const R = 46;
  const centro = 50;
  const ancho = (360 / rosa.length) * 0.82;

  // Cada sector es una pila de arcos: uno por intervalo de velocidad.
  const arco = (desde: number, hasta: number, r0: number, r1: number) => {
    const p = (a: number, r: number) => {
      const rad = ((a - 90) * Math.PI) / 180;
      return [centro + r * Math.cos(rad), centro + r * Math.sin(rad)];
    };
    const [x1, y1] = p(desde, r0);
    const [x2, y2] = p(hasta, r0);
    const [x3, y3] = p(hasta, r1);
    const [x4, y4] = p(desde, r1);
    return `M${x1},${y1} A${r0},${r0} 0 0 1 ${x2},${y2} L${x3},${y3} A${r1},${r1} 0 0 0 ${x4},${y4} Z`;
  };

  return (
    <div>
      <svg viewBox="0 0 100 100" className="w-full max-w-[220px] mx-auto">
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <circle key={f} cx={centro} cy={centro} r={R * f} fill="none" stroke="#d8d4cc" strokeWidth={0.4} />
        ))}
        {rosa.map((s) => {
          let acumulado = 0;
          return s.por_velocidad_pct.map((v, k) => {
            const r0 = (acumulado / maximo) * R;
            acumulado += v;
            const r1 = (acumulado / maximo) * R;
            if (r1 - r0 < 0.05) return null;
            return (
              <path
                key={`${s.centro_deg}-${k}`}
                d={arco(s.centro_deg - ancho / 2, s.centro_deg + ancho / 2, r0, r1)}
                fill={GRISES[k] ?? GRISES[GRISES.length - 1]}
              />
            );
          });
        })}
        <text x={centro} y={7} textAnchor="middle" fontSize={6} fill="#111111">N</text>
        <text x={97} y={centro + 2} textAnchor="end" fontSize={6} fill="#8a857a">E</text>
        <text x={centro} y={98} textAnchor="middle" fontSize={6} fill="#8a857a">S</text>
        <text x={3} y={centro + 2} fontSize={6} fill="#8a857a">O</text>
      </svg>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-rebar justify-center mt-1">
        {bins.map((b, k) => (
          <span key={k} className="flex items-center gap-1">
            <span className="inline-block w-2.5 h-2.5" style={{ background: GRISES[k] ?? GRISES[GRISES.length - 1] }} />
            {k === bins.length - 1 ? `≥ ${b}` : `${b}–${bins[k + 1]}`} m/s
          </span>
        ))}
      </div>
      <p className="text-[10px] text-rebar text-center mt-1">
        Frecuencia por dirección de procedencia; el círculo exterior es {maximo.toFixed(1)} %.
      </p>
    </div>
  );
}
