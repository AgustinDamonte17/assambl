import { createContext, useContext, useEffect, useMemo, useReducer, useState, type ReactNode } from "react";
import { area, lados as calcularLados, perimetro } from "../modelo/geometria";
import {
  ahora,
  ESQUEMA_ACTUAL,
  proyectoNuevo,
  type Estado,
  type Pendiente,
  type Proyecto,
  type Punto,
  type RespuestaClima,
  type RespuestaEscena,
  type Retiros,
  type Trayectoria,
} from "../modelo/proyecto";

const CLAVE_LOCAL = "assambl.proyecto";

type Accion =
  | { tipo: "cargar"; proyecto: Proyecto }
  | { tipo: "nuevo" }
  | { tipo: "nombre"; nombre: string }
  | { tipo: "ubicacion"; lat: number; lon: number; direccion?: string | null; fuente: string }
  | { tipo: "margen"; margen_m: number }
  | { tipo: "escena"; escena: RespuestaEscena | null }
  | { tipo: "lote_vertices"; vertices: Punto[] }
  | { tipo: "lote_estado"; estado: Estado; pendiente: Pendiente | null; area_m2: number; perimetro_m: number }
  | { tipo: "retiros"; retiros: Retiros }
  | { tipo: "sol_fecha"; fecha: string }
  | { tipo: "sol_hora"; hora: number }
  | { tipo: "sol_huso"; huso_h: number | null };

function tocar(p: Proyecto): Proyecto {
  return { ...p, modificado: ahora() };
}

function reducir(p: Proyecto, a: Accion): Proyecto {
  switch (a.tipo) {
    case "cargar":
      return a.proyecto;
    case "nuevo":
      return proyectoNuevo();
    case "nombre":
      return tocar({ ...p, nombre: a.nombre });
    case "ubicacion": {
      const cambioOrigen = !p.terreno.ubicacion || p.terreno.ubicacion.lat !== a.lat || p.terreno.ubicacion.lon !== a.lon;
      return tocar({
        ...p,
        terreno: {
          ...p.terreno,
          ubicacion: { lat: a.lat, lon: a.lon, direccion: a.direccion ?? null, fuente: a.fuente, fecha: ahora() },
          sistema_local: {
            origen_lat: a.lat,
            origen_lon: a.lon,
            norte: "+Y",
            unidades: "m",
            proyeccion: "equirrectangular local",
            cota_origen_msnm: cambioOrigen ? null : p.terreno.sistema_local?.cota_origen_msnm ?? null,
          },
          // El lote está en coordenadas locales del origen: si cambia, queda desactualizado.
          pendiente: cambioOrigen ? null : p.terreno.pendiente,
          estado: cambioOrigen && p.terreno.lote.vertices.length ? "desactualizado" : p.terreno.estado,
        },
      });
    }
    case "margen":
      return tocar({ ...p, terreno: { ...p.terreno, margen_m: a.margen_m } });
    case "escena": {
      if (!a.escena) return tocar({ ...p, terreno: { ...p.terreno, escena_ref: null } });
      const e = a.escena;
      return tocar({
        ...p,
        terreno: {
          ...p.terreno,
          escena_ref: e.ref,
          pendiente: e.reglas.pendiente,
          estado: e.reglas.estado,
          sistema_local: p.terreno.sistema_local
            ? { ...p.terreno.sistema_local, cota_origen_msnm: e.relieve.cota_origen_msnm }
            : null,
        },
      });
    }
    case "lote_vertices": {
      const v = a.vertices;
      return tocar({
        ...p,
        terreno: {
          ...p.terreno,
          lote: {
            ...p.terreno.lote,
            origen: v[0] ?? [0, 0],
            vertices: v,
            lados: v.length >= 2 ? calcularLados(v) : [],
            area_m2: v.length >= 3 ? area(v) : null,
            perimetro_m: v.length >= 2 ? perimetro(v) : null,
          },
          estado: v.length >= 3 ? "propuesto" : "pendiente_datos",
          pendiente: null,
        },
      });
    }
    case "lote_estado":
      return tocar({
        ...p,
        terreno: {
          ...p.terreno,
          estado: a.estado,
          pendiente: a.pendiente,
          lote: { ...p.terreno.lote, area_m2: a.area_m2, perimetro_m: a.perimetro_m },
        },
      });
    case "retiros":
      return tocar({ ...p, terreno: { ...p.terreno, retiros: a.retiros } });
    case "sol_fecha":
      return tocar({ ...p, terreno: { ...p.terreno, fecha_sol: a.fecha } });
    case "sol_hora":
      return tocar({ ...p, terreno: { ...p.terreno, hora_sol: a.hora } });
    case "sol_huso":
      return tocar({ ...p, terreno: { ...p.terreno, huso_h: a.huso_h } });
  }
}

function leerLocal(): Proyecto {
  try {
    const crudo = localStorage.getItem(CLAVE_LOCAL);
    if (crudo) {
      const p = JSON.parse(crudo) as Proyecto;
      if (p.esquema === ESQUEMA_ACTUAL) return p;
    }
  } catch {
    /* almacenamiento corrupto: se arranca de cero */
  }
  return proyectoNuevo();
}

interface Valor {
  proyecto: Proyecto;
  despachar: (a: Accion) => void;
  escena: RespuestaEscena | null;
  setEscena: (e: RespuestaEscena | null) => void;
  trayectoria: Trayectoria | null;
  setTrayectoria: (t: Trayectoria | null) => void;
  clima: RespuestaClima | null;
  setClima: (c: RespuestaClima | null) => void;
}

const Ctx = createContext<Valor | null>(null);

export function ProyectoProvider({ children }: { children: ReactNode }) {
  const [proyecto, despachar] = useReducer(reducir, undefined, leerLocal);
  const [escena, setEscena] = useState<RespuestaEscena | null>(null);
  const [trayectoria, setTrayectoria] = useState<Trayectoria | null>(null);
  const [clima, setClima] = useState<RespuestaClima | null>(null);

  useEffect(() => {
    localStorage.setItem(CLAVE_LOCAL, JSON.stringify(proyecto));
  }, [proyecto]);

  // La escena en memoria debe corresponder a la referencia del proyecto.
  useEffect(() => {
    if (escena && proyecto.terreno.escena_ref !== escena.ref) setEscena(null);
  }, [proyecto.terreno.escena_ref, escena]);

  const valor = useMemo(
    () => ({ proyecto, despachar, escena, setEscena, trayectoria, setTrayectoria, clima, setClima }),
    [proyecto, escena, trayectoria, clima],
  );
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}

export function useProyecto(): Valor {
  const v = useContext(Ctx);
  if (!v) throw new Error("useProyecto fuera de ProyectoProvider");
  return v;
}

export function descargarProyecto(p: Proyecto) {
  const blob = new Blob([JSON.stringify(p, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${p.nombre.replace(/[^\w\-]+/g, "_") || "casa"}.assambl.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function leerArchivoProyecto(archivo: File): Promise<Proyecto> {
  const p = JSON.parse(await archivo.text()) as Proyecto;
  if (p.esquema !== ESQUEMA_ACTUAL) throw new Error(`Esquema no compatible: ${p.esquema}`);
  return p;
}
