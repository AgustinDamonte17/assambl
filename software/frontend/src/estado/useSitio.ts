import { useEffect, useRef } from "react";
import { api } from "../api/cliente";
import { useProyecto } from "./ProyectoContext";

/**
 * Mantiene al día lo que se deriva del sitio y comparten todas las etapas: la
 * escena 3D del terreno y la trayectoria del sol. Lo monta el Shell, así el
 * visor del diseño tiene el terreno aunque no se haya pasado por el paso 01.
 */
export function useSitio(apiOk: boolean | null) {
  const { proyecto, vincularEscena, escena, trayectoria, setTrayectoria } = useProyecto();
  const t = proyecto.terreno;

  // Al abrir un proyecto que ya tenía escena (recarga, archivo importado) se
  // reconstruye desde la caché del backend. Un intento por combinación, para no
  // insistir si el backend no puede.
  const intentada = useRef<string | null>(null);
  useEffect(() => {
    if (escena || !t.ubicacion || !t.escena_ref || !apiOk) return;
    const clave = `${t.ubicacion.lat}_${t.ubicacion.lon}_${t.margen_m}_${t.escena_ref}`;
    if (intentada.current === clave) return;
    intentada.current = clave;
    api
      .generarEscena(t.ubicacion.lat, t.ubicacion.lon, t.margen_m, t.lote.vertices)
      .then((e) => vincularEscena(e))
      .catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [escena, t.ubicacion?.lat, t.ubicacion?.lon, t.margen_m, t.escena_ref, apiOk]);

  // Una vez generada la escena, se mantiene en sincronía con el lote, el margen y
  // el origen. La primera generación es explícita porque puede bajar mosaicos de
  // varios MB; las siguientes salen de la caché y son inmediatas.
  useEffect(() => {
    if (!escena || !t.ubicacion || !apiOk) return;
    const h = setTimeout(() => {
      api
        .generarEscena(t.ubicacion!.lat, t.ubicacion!.lon, t.margen_m, t.lote.vertices)
        .then((e) => {
          if (e.ref === escena.ref) return;
          vincularEscena(e);
        })
        .catch(() => undefined);
    }, 500);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t.ubicacion?.lat, t.ubicacion?.lon, t.margen_m, t.lote.vertices, apiOk, escena?.ref]);

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
