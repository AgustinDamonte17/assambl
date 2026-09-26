import { useEffect, useState } from "react";
import { api, type EstadoCredencial, type ResultadoGeo } from "../../api/cliente";
import { Aviso, Boton, Campo, Dato, FichaFuente, Seccion } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { MARGEN_MAX_M, MARGEN_MIN_M } from "../../modelo/proyecto";

export default function PanelUbicacion({ apiOk, irALote }: { apiOk: boolean | null; irALote: () => void }) {
  const { proyecto, operar, vincularEscena, escena } = useProyecto();
  const t = proyecto.terreno;
  const [busqueda, setBusqueda] = useState("");
  const [resultados, setResultados] = useState<ResultadoGeo[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [errorBusqueda, setErrorBusqueda] = useState<string | null>(null);
  const [generando, setGenerando] = useState(false);
  const [errorEscena, setErrorEscena] = useState<string | null>(null);
  const [credencial, setCredencial] = useState<EstadoCredencial | null>(null);
  const [lat, setLat] = useState(t.ubicacion?.lat.toFixed(6) ?? "");
  const [lon, setLon] = useState(t.ubicacion?.lon.toFixed(6) ?? "");
  // El deslizador se mueve localmente y la operación sale cuando se detiene.
  const [margen, setMargen] = useState(t.margen_m);

  useEffect(() => setMargen(t.margen_m), [t.margen_m]);

  useEffect(() => {
    if (margen === t.margen_m) return;
    const h = setTimeout(() => operar({ tipo: "definir_margen", margen_m: margen }), 300);
    return () => clearTimeout(h);
  }, [margen, t.margen_m, operar]);

  useEffect(() => {
    setLat(t.ubicacion?.lat.toFixed(6) ?? "");
    setLon(t.ubicacion?.lon.toFixed(6) ?? "");
  }, [t.ubicacion]);

  useEffect(() => {
    if (apiOk) api.credencial().then(setCredencial).catch(() => setCredencial(null));
  }, [apiOk]);

  // Dirección aproximada del origen cuando se fijó por clic en el mapa.
  useEffect(() => {
    if (t.ubicacion && !t.ubicacion.direccion && apiOk) {
      const { lat: la, lon: lo } = t.ubicacion;
      api
        .inverso(la, lo)
        .then((r) => {
          if (r.direccion)
            operar({ tipo: "definir_ubicacion", lat: la, lon: lo, direccion: r.direccion, fuente: t.ubicacion!.fuente }, "sistema");
        })
        .catch(() => undefined);
    }
  }, [t.ubicacion, apiOk, operar]);

  const buscar = async () => {
    if (busqueda.trim().length < 3) return;
    setBuscando(true);
    setErrorBusqueda(null);
    try {
      const r = await api.geocodificar(busqueda.trim());
      setResultados(r);
      if (!r.length) setErrorBusqueda("Sin resultados. Probá con calle, número y ciudad.");
    } catch (e) {
      setErrorBusqueda((e as Error).message);
    } finally {
      setBuscando(false);
    }
  };

  const aplicarCoordenadas = () => {
    const la = parseFloat(lat.replace(",", "."));
    const lo = parseFloat(lon.replace(",", "."));
    if (Number.isFinite(la) && Number.isFinite(lo) && Math.abs(la) <= 90 && Math.abs(lo) <= 180) {
      if (t.ubicacion?.lat === la && t.ubicacion?.lon === lo) return;
      operar({ tipo: "definir_ubicacion", lat: la, lon: lo, fuente: "coordenadas" });
    }
  };

  const generar = async () => {
    if (!t.ubicacion) return;
    setGenerando(true);
    setErrorEscena(null);
    try {
      const e = await api.generarEscena(t.ubicacion.lat, t.ubicacion.lon, t.margen_m, t.lote.vertices);
      await vincularEscena(e);
    } catch (e) {
      setErrorEscena((e as Error).message);
    } finally {
      setGenerando(false);
    }
  };

  const vigente = !!escena && t.escena_ref === escena.ref;

  return (
    <div className="text-xs">
      <Seccion titulo="1 · Ubicación">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            buscar();
          }}
          className="flex gap-1"
        >
          <input
            className="flex-1 bg-concrete-2 border border-line px-2 py-1 focus:outline-none focus:border-signal"
            placeholder="Dirección o lugar (Enter para buscar)"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <Boton type="submit" disabled={buscando || !apiOk}>
            {buscando ? "…" : "Buscar"}
          </Boton>
        </form>
        {errorBusqueda && <p className="text-warn mt-1">{errorBusqueda}</p>}
        {resultados.length > 0 && (
          <ul className="mt-2 border border-line divide-y divide-line max-h-44 overflow-y-auto">
            {resultados.map((r, i) => (
              <li key={i}>
                <button
                  className="w-full text-left px-2 py-1.5 hover:bg-concrete-2 leading-snug"
                  onClick={() => {
                    operar({ tipo: "definir_ubicacion", lat: r.lat, lon: r.lon, direccion: r.nombre, fuente: "nominatim" });
                    setResultados([]);
                  }}
                >
                  {r.nombre}
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <Campo etiqueta="Latitud" value={lat} onChange={(e) => setLat(e.target.value)} onBlur={aplicarCoordenadas} inputMode="decimal" />
          <Campo etiqueta="Longitud" value={lon} onChange={(e) => setLon(e.target.value)} onBlur={aplicarCoordenadas} inputMode="decimal" />
        </div>
        {t.ubicacion?.direccion && <p className="mt-2 text-rebar leading-snug">{t.ubicacion.direccion}</p>}
        {!t.ubicacion && <p className="mt-2 text-rebar">También podés hacer clic directamente en el mapa.</p>}
        <Aviso>
          La búsqueda y el mapa son solo para encontrar el lugar. Ningún dato del modelo sale de ahí.
        </Aviso>
      </Seccion>

      <Seccion titulo="Extensión del entorno">
        <div className="flex items-center gap-2">
          <input
            type="range"
            min={MARGEN_MIN_M}
            max={MARGEN_MAX_M}
            step={50}
            value={margen}
            onChange={(e) => setMargen(Number(e.target.value))}
            className="flex-1 accent-signal"
          />
          <input
            type="number"
            min={MARGEN_MIN_M}
            max={MARGEN_MAX_M}
            step={50}
            value={margen}
            onChange={(e) => setMargen(Math.min(MARGEN_MAX_M, Math.max(MARGEN_MIN_M, Number(e.target.value) || MARGEN_MIN_M)))}
            className="w-20 bg-concrete-2 border border-line px-2 py-1 text-right"
          />
          <span className="text-rebar">m</span>
        </div>
        <p className="text-rebar mt-1 leading-snug">
          Margen de relieve alrededor del origen, entre {MARGEN_MIN_M} y {MARGEN_MAX_M} m. Con 500 m la escena queda en
          algo más de 1 km de lado.
        </p>
      </Seccion>

      <Seccion titulo="Relieve del sitio">
        <Boton primario disabled={!t.ubicacion || generando || !apiOk} onClick={generar} className="w-full">
          {generando ? "Descargando NASADEM…" : vigente ? "Regenerar escena" : "Generar escena 3D"}
        </Boton>
        {generando && <p className="text-rebar mt-2">La primera descarga de un mosaico tarda: son unos 10 MB por grado.</p>}
        {errorEscena && <p className="text-signal mt-2">{errorEscena}</p>}

        {credencial && !credencial.earthdata && (
          <Aviso fuerte>
            Sin credencial de Earthdata ({credencial.mensaje}). La escena se genera plana y provisional. Generá un token
            en urs.earthdata.nasa.gov y guardalo como EARTHDATA_TOKEN en el archivo .env.
          </Aviso>
        )}

        {vigente && escena && (
          <div className="mt-3">
            <Dato etiqueta="Posts del relieve" valor={`${escena.posts[0]} × ${escena.posts[1]}`} />
            <Dato etiqueta="Separación entre posts" valor={`${escena.paso_m[0]} × ${escena.paso_m[1]}`} sufijo="m" />
            <Dato etiqueta="Extensión" valor={`${escena.extension_m[0]} × ${escena.extension_m[1]}`} sufijo="m" />
            <Dato etiqueta="Cota del origen" valor={escena.relieve.cota_origen_msnm ?? "—"} sufijo="m s.n.m." />
            <Dato
              etiqueta="Desnivel en el entorno"
              valor={`${escena.relieve.z_min_m} / +${escena.relieve.z_max_m}`}
              sufijo="m"
            />
            <ul className="mt-3 space-y-2">
              {escena.fuentes.map((f) => (
                <FichaFuente key={f.nombre} fuente={f} />
              ))}
            </ul>
            {escena.advertencias.map((a, i) => (
              <div key={i} className="mt-2">
                <Aviso fuerte={escena.relieve.provisional}>{a}</Aviso>
              </div>
            ))}
          </div>
        )}
      </Seccion>

      <div className="mt-5 flex justify-end">
        <Boton primario disabled={!t.ubicacion} onClick={irALote}>
          Siguiente: lote →
        </Boton>
      </div>
    </div>
  );
}
