import { useEffect } from "react";
import { api } from "../api/cliente";
import { useProyecto } from "./ProyectoContext";

/**
 * Mantiene al día la trayectoria del sol, que comparten el modelo del sitio y el
 * diseño de la casa. Lo monta el Shell. El modelo 3D del sitio lo genera cada
 * etapa que lo muestra (useModeloSitio).
 */
export function useSitio(apiOk: boolean | null) {
  const { proyecto, trayectoria, setTrayectoria } = useProyecto();
  const t = proyecto.terreno;

  // Trayectoria solar del día elegido: se pide una vez y el visor interpola.
  useEffect(() => {
    if (!t.ubicacion || !apiOk) return;
    if (trayectoria && trayectoria.fecha === t.fecha_sol && trayectoria.lat === t.ubicacion.lat) return;
    api
      .sol(t.ubicacion.lat, t.ubicacion.lon, t.fecha_sol, t.huso_h)
      .then(setTrayectoria)
      .catch(() => setTrayectoria(null));
  }, [t.ubicacion, t.fecha_sol, t.huso_h, apiOk, trayectoria, setTrayectoria]);
}
