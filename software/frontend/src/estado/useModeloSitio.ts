import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/cliente";
import { escenaVigente } from "../modelo/proyecto";
import { useProyecto } from "./ProyectoContext";

/**
 * Genera el modelo 3D del sitio para la ubicación, el entorno y el lote actuales
 * cuando `activo` y el que hay en memoria no corresponde. Se usa en el paso Modelo
 * 3D y en el diseño de la casa. La primera vez descarga imagen y puede tardar;
 * después sale de la caché del backend.
 */
export function useModeloSitio(activo: boolean) {
  const { proyecto, escena, vincularEscena } = useProyecto();
  const t = proyecto.terreno;
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intentada = useRef<string | null>(null);
  const [intento, setIntento] = useState(0);

  const vigente = escenaVigente(escena, t);
  const listo = !!t.ubicacion && t.lote.vertices.length >= 3;
  const clave = t.ubicacion
    ? `${t.ubicacion.lat}_${t.ubicacion.lon}_${t.margen_m}_${JSON.stringify(t.lote.vertices)}_${intento}`
    : "";

  useEffect(() => {
    if (!activo || !listo || vigente || intentada.current === clave) return;
    intentada.current = clave;
    // Si los datos cambian o se sale del paso antes de terminar, el resultado se
    // descarta y la próxima vez se vuelve a pedir (sale de la caché del backend).
    let vivo = true;
    let terminado = false;
    setGenerando(true);
    setError(null);
    api
      .generarEscena(t.ubicacion!.lat, t.ubicacion!.lon, t.margen_m, t.lote.vertices)
      .then((e) => (vivo ? vincularEscena(e) : null))
      .catch((e) => vivo && setError((e as Error).message))
      .finally(() => {
        terminado = true;
        if (vivo) setGenerando(false);
      });
    return () => {
      vivo = false;
      if (!terminado) {
        intentada.current = null;
        setGenerando(false);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activo, listo, vigente, clave]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);
  return { generando: generando && !vigente, error: vigente ? null : error, vigente, reintentar };
}
