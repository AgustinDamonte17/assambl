import { useEffect, useState } from "react";
import { api } from "../../api/cliente";
import { Boton, Campo, Dato, Etiqueta, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { desdeLados, fmt, lados as calcularLados, rectangulo } from "../../modelo/geometria";
import { cardinal, type AnalisisLote, type Punto } from "../../modelo/proyecto";

export default function PanelLote({ irAModelo }: { irAModelo: () => void }) {
  const { proyecto, despachar, escena } = useProyecto();
  const t = proyecto.terreno;
  const v = t.lote.vertices;
  const [frente, setFrente] = useState("12");
  const [fondo, setFondo] = useState("30");
  const [rumboFrente, setRumboFrente] = useState("90");
  const [analisis, setAnalisis] = useState<AnalisisLote | null>(null);
  const [errorAnalisis, setErrorAnalisis] = useState<string | null>(null);

  // Análisis R01 con retardo para no golpear la API en cada arrastre.
  useEffect(() => {
    if (v.length < 3) {
      setAnalisis(null);
      return;
    }
    const h = setTimeout(() => {
      api.analizarLote(v, escena?.ref ?? null, t.margen_m)
        .then((a) => {
          setAnalisis(a);
          setErrorAnalisis(null);
          despachar({
            tipo: "lote_estado",
            estado: a.estado,
            pendiente: a.pendiente,
            area_m2: a.area_m2,
            perimetro_m: a.perimetro_m,
          });
        })
        .catch((e) => setErrorAnalisis((e as Error).message));
    }, 400);
    return () => clearTimeout(h);
  }, [v, escena?.ref, t.margen_m, despachar]);

  const setVertices = (nuevos: Punto[]) => despachar({ tipo: "lote_vertices", vertices: nuevos.map(([x, y]) => [r2(x), r2(y)]) });

  const crearRectangulo = () => {
    const f = num(frente);
    const d = num(fondo);
    const r = num(rumboFrente);
    if (f > 0 && d > 0) setVertices(rectangulo(f, d, Number.isFinite(r) ? r : 90));
  };

  const lados = v.length >= 2 ? calcularLados(v) : [];

  const editarLado = (i: number, campo: "longitud_m" | "rumbo_deg", valor: string) => {
    const n = num(valor);
    if (!Number.isFinite(n) || (campo === "longitud_m" && n <= 0)) return;
    const nuevos = lados.map((l, k) => (k === i ? { ...l, [campo]: campo === "rumbo_deg" ? ((n % 360) + 360) % 360 : n } : l));
    setVertices(desdeLados(v[0], nuevos));
  };

  const editarVertice = (i: number, eje: 0 | 1, valor: string) => {
    const n = num(valor);
    if (!Number.isFinite(n)) return;
    setVertices(v.map((p, k) => (k === i ? ((eje === 0 ? [n, p[1]] : [p[0], n]) as Punto) : p)));
  };

  return (
    <div className="text-xs">
      <Seccion titulo="2 · Lote">
        <p className="text-rebar leading-snug">
          Dibujá los vértices sobre el mapa o cargá el lote por lados. Coordenadas locales en metros: +X este, +Y norte; el origen es el
          punto fijado en el paso 1.
        </p>
      </Seccion>

      <Seccion titulo="Rectángulo rápido">
        <div className="grid grid-cols-3 gap-2">
          <Campo etiqueta="Frente" sufijo="m" value={frente} onChange={(e) => setFrente(e.target.value)} inputMode="decimal" />
          <Campo etiqueta="Fondo" sufijo="m" value={fondo} onChange={(e) => setFondo(e.target.value)} inputMode="decimal" />
          <Campo etiqueta="Rumbo frente" sufijo="°" value={rumboFrente} onChange={(e) => setRumboFrente(e.target.value)} inputMode="decimal" />
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className="text-[10px] text-rebar">Centrado en el origen. Rumbo 90° = frente sobre el lado sur, mirando al este.</span>
          <Boton onClick={crearRectangulo}>Crear</Boton>
        </div>
      </Seccion>

      <Seccion
        titulo={`Lados (${lados.length})`}
        accion={
          <div className="flex gap-1">
            <Boton disabled={!v.length} onClick={() => setVertices(v.slice(0, -1))} title="Quitar último vértice">
              Deshacer
            </Boton>
            <Boton disabled={!v.length} onClick={() => setVertices([])}>
              Limpiar
            </Boton>
          </div>
        }
      >
        {lados.length === 0 ? (
          <p className="text-rebar">Sin lados todavía.</p>
        ) : (
          <table className="w-full">
            <thead className="text-[10px] uppercase tracking-wide text-rebar">
              <tr>
                <th className="text-left font-normal py-1">#</th>
                <th className="text-right font-normal">Longitud m</th>
                <th className="text-right font-normal">Rumbo °</th>
              </tr>
            </thead>
            <tbody>
              {lados.map((l, i) => {
                const cierre = v.length >= 3 && i === lados.length - 1;
                return (
                  <tr key={i} className="border-t border-line">
                    <td className="py-1 text-rebar">
                      {i + 1}→{((i + 1) % v.length) + 1}
                      {cierre && <span className="ml-1 text-[9px] uppercase">cierre</span>}
                    </td>
                    <td className="text-right">
                      <CeldaNumero valor={l.longitud_m} dec={2} soloLectura={cierre} onCommit={(s) => editarLado(i, "longitud_m", s)} />
                    </td>
                    <td className="text-right">
                      <CeldaNumero valor={l.rumbo_deg} dec={1} soloLectura={cierre} onCommit={(s) => editarLado(i, "rumbo_deg", s)} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        <p className="text-[10px] text-rebar mt-2 leading-snug">
          Al editar un lado se recalculan los vértices siguientes; el último lado cierra el polígono y se deriva.
        </p>
      </Seccion>

      {v.length > 0 && (
        <Seccion titulo={`Vértices (${v.length})`}>
          <table className="w-full">
            <thead className="text-[10px] uppercase tracking-wide text-rebar">
              <tr>
                <th className="text-left font-normal py-1">#</th>
                <th className="text-right font-normal">X este m</th>
                <th className="text-right font-normal">Y norte m</th>
              </tr>
            </thead>
            <tbody>
              {v.map((p, i) => (
                <tr key={i} className="border-t border-line">
                  <td className="py-1 text-rebar">{i + 1}</td>
                  <td className="text-right">
                    <CeldaNumero valor={p[0]} dec={2} onCommit={(s) => editarVertice(i, 0, s)} />
                  </td>
                  <td className="text-right">
                    <CeldaNumero valor={p[1]} dec={2} onCommit={(s) => editarVertice(i, 1, s)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Seccion>
      )}

      <Seccion titulo="Resultado" accion={<Etiqueta estado={t.estado} />}>
        {v.length < 3 ? (
          <p className="text-rebar">Se necesitan al menos 3 vértices.</p>
        ) : (
          <>
            <Dato etiqueta="Superficie" valor={fmt(t.lote.area_m2 ?? 0)} sufijo="m²" />
            <Dato etiqueta="Perímetro" valor={fmt(t.lote.perimetro_m ?? 0)} sufijo="m" />
            {analisis?.pendiente ? (
              <>
                <Dato
                  etiqueta="Pendiente estimada"
                  valor={`${fmt(analisis.pendiente.porcentaje, 1)} % hacia ${cardinal(analisis.pendiente.direccion_deg)}`}
                />
                <Dato etiqueta="Posts del relieve cada" valor={fmt(analisis.pendiente.paso_dem_m, 0)} sufijo="m" />
              </>
            ) : (
              <Dato
                etiqueta="Pendiente"
                valor={<span className="text-rebar">{escena ? "sin relieve disponible" : "generá la escena (paso 1)"}</span>}
              />
            )}
            {errorAnalisis && <p className="text-signal mt-1">{errorAnalisis}</p>}
            {analisis && (
              <ul className="mt-3 space-y-2">
                {analisis.verificaciones.map((ver) => (
                  <li key={ver.id} className="leading-snug">
                    <div className="flex items-start justify-between gap-2">
                      <span>
                        <span className="text-rebar mr-1">{ver.id}</span>
                        {ver.descripcion}
                      </span>
                      <Etiqueta estado={ver.estado} />
                    </div>
                    {ver.detalle && <div className="text-[10px] text-rebar mt-0.5">{ver.detalle}</div>}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </Seccion>

      <div className="mt-5 flex justify-end">
        <Boton primario disabled={!escena} onClick={irAModelo} title={escena ? "" : "Generá la escena en el paso 1"}>
          Siguiente: modelo 3D →
        </Boton>
      </div>
    </div>
  );
}

function CeldaNumero({
  valor,
  dec,
  soloLectura,
  onCommit,
}: {
  valor: number;
  dec: number;
  soloLectura?: boolean;
  onCommit: (s: string) => void;
}) {
  const [texto, setTexto] = useState(valor.toFixed(dec));
  const [editando, setEditando] = useState(false);
  useEffect(() => {
    if (!editando) setTexto(valor.toFixed(dec));
  }, [valor, dec, editando]);
  if (soloLectura) return <span className="text-rebar">{valor.toFixed(dec)}</span>;
  return (
    <input
      className="w-20 bg-transparent text-right border-b border-transparent hover:border-line focus:border-signal focus:outline-none"
      value={texto}
      inputMode="decimal"
      onFocus={(e) => {
        setEditando(true);
        e.target.select();
      }}
      onChange={(e) => setTexto(e.target.value)}
      onBlur={() => {
        setEditando(false);
        if (texto !== valor.toFixed(dec)) onCommit(texto);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
      }}
    />
  );
}

const num = (s: string) => parseFloat(s.replace(",", "."));
const r2 = (n: number) => Math.round(n * 100) / 100;
