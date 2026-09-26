import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef, useState, type ReactNode } from "react";
import { api } from "../api/cliente";
import type { Autor, Operacion, RegistroOperacion } from "../modelo/operaciones";
import {
  ahora,
  ESQUEMA_ACTUAL,
  proyectoNuevo,
  type Proyecto,
  type RespuestaClima,
  type RespuestaEscena,
  type Trayectoria,
} from "../modelo/proyecto";

const CLAVE_LOCAL = "assambl.proyecto";
const CLAVE_HISTORIAL = "assambl.historial";
const MAX_HISTORIAL = 200;
const MAX_DESHACER = 50;
// Operaciones seguidas del mismo tipo dentro de esta ventana se deshacen juntas
// (tipear un nombre, mover el deslizador del margen).
const VENTANA_AGRUPAR_MS = 1500;

/** Cambios locales que no son operaciones del dominio. Todo lo que modifica el
 *  diseño pasa por `operar` (docs/decisiones/0002_operaciones_e_historial.md). */
type Accion =
  | { tipo: "cargar"; proyecto: Proyecto }
  | { tipo: "nuevo" }
  | { tipo: "reemplazar"; proyecto: Proyecto }
  // Preferencias de estudio del asoleamiento: no cambian el diseño.
  | { tipo: "sol_fecha"; fecha: string }
  | { tipo: "sol_hora"; hora: number }
  | { tipo: "sol_huso"; huso_h: number | null };

function reducir(p: Proyecto, a: Accion): Proyecto {
  switch (a.tipo) {
    case "cargar":
    case "reemplazar":
      return a.proyecto;
    case "nuevo":
      return proyectoNuevo();
    case "sol_fecha":
      return { ...p, terreno: { ...p.terreno, fecha_sol: a.fecha } };
    case "sol_hora":
      return { ...p, terreno: { ...p.terreno, hora_sol: a.hora } };
    case "sol_huso":
      return { ...p, terreno: { ...p.terreno, huso_h: a.huso_h } };
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

/** El historial se guarda aparte del proyecto para que casa.assambl.json siga liviano. */
function leerHistorial(proyectoId: string): RegistroOperacion[] {
  try {
    const crudo = localStorage.getItem(CLAVE_HISTORIAL);
    if (crudo) {
      const h = JSON.parse(crudo) as { proyecto_id: string; registros: RegistroOperacion[] };
      if (h.proyecto_id === proyectoId) return h.registros;
    }
  } catch {
    /* sin historial legible */
  }
  return [];
}

interface PasoDeshacer {
  antes: Proyecto;
  registro: RegistroOperacion;
  momento: number;
}

interface Valor {
  proyecto: Proyecto;
  /** Solo para cambios locales: cargar, nuevo y preferencias de vista. */
  despachar: (a: Exclude<Accion, { tipo: "reemplazar" }>) => void;
  /** Aplica una operación del dominio en el backend. Devuelve el registro, o null si falló. */
  operar: (op: Operacion, autor?: Autor) => Promise<RegistroOperacion | null>;
  /** Vincula una escena recién generada; la escena en memoria cambia junto con el proyecto. */
  vincularEscena: (e: RespuestaEscena) => Promise<RegistroOperacion | null>;
  deshacer: () => void;
  puedeDeshacer: boolean;
  historial: RegistroOperacion[];
  errorOperacion: string | null;
  limpiarError: () => void;
  escena: RespuestaEscena | null;
  setEscena: (e: RespuestaEscena | null) => void;
  trayectoria: Trayectoria | null;
  setTrayectoria: (t: Trayectoria | null) => void;
  clima: RespuestaClima | null;
  setClima: (c: RespuestaClima | null) => void;
}

const Ctx = createContext<Valor | null>(null);

export function ProyectoProvider({ children }: { children: ReactNode }) {
  const [proyecto, despacharInterno] = useReducer(reducir, undefined, leerLocal);
  const [escena, setEscena] = useState<RespuestaEscena | null>(null);
  const [trayectoria, setTrayectoria] = useState<Trayectoria | null>(null);
  const [clima, setClima] = useState<RespuestaClima | null>(null);
  const [historial, setHistorial] = useState<RegistroOperacion[]>(() => leerHistorial(proyecto.id));
  // La pila de deshacer vive en una ref (se lee y se modifica fuera del render);
  // el estado solo avisa si hay algo para deshacer.
  const pila = useRef<PasoDeshacer[]>([]);
  const [puedeDeshacer, setPuedeDeshacer] = useState(false);
  const [errorOperacion, setErrorOperacion] = useState<string | null>(null);

  // Las operaciones se aplican de a una, siempre sobre el último proyecto. Cargar,
  // crear o deshacer cambia la generación: las respuestas que llegan después de
  // eso corresponden a otro estado y se descartan.
  const proyectoRef = useRef(proyecto);
  proyectoRef.current = proyecto;
  const cola = useRef<Promise<unknown>>(Promise.resolve());
  const generacion = useRef(0);

  useEffect(() => {
    localStorage.setItem(CLAVE_LOCAL, JSON.stringify(proyecto));
  }, [proyecto]);

  useEffect(() => {
    localStorage.setItem(CLAVE_HISTORIAL, JSON.stringify({ proyecto_id: proyecto.id, registros: historial }));
  }, [proyecto.id, historial]);

  // La escena en memoria debe corresponder a la referencia del proyecto.
  useEffect(() => {
    if (escena && proyecto.terreno.escena_ref !== escena.ref) setEscena(null);
  }, [proyecto.terreno.escena_ref, escena]);

  const registrar = useCallback((r: RegistroOperacion) => {
    setHistorial((h) => [...h, r].slice(-MAX_HISTORIAL));
  }, []);

  const fijarPila = useCallback((nueva: PasoDeshacer[]) => {
    pila.current = nueva.slice(-MAX_DESHACER);
    setPuedeDeshacer(pila.current.length > 0);
  }, []);

  const despachar = useCallback((a: Exclude<Accion, { tipo: "reemplazar" }>) => {
    if (a.tipo === "cargar" || a.tipo === "nuevo") {
      generacion.current++;
      fijarPila([]);
      setErrorOperacion(null);
      setHistorial(a.tipo === "cargar" ? leerHistorial(a.proyecto.id) : []);
    }
    despacharInterno(a);
  }, [fijarPila]);

  const operar = useCallback(
    (op: Operacion, autor: Autor = "usuario", alAplicar?: () => void) => {
      const gen = generacion.current;
      const tarea = cola.current.then(async (): Promise<RegistroOperacion | null> => {
        if (gen !== generacion.current) return null;
        const antes = proyectoRef.current;
        try {
          const r = await api.aplicarOperacion(antes, op, autor);
          if (gen !== generacion.current) return null;
          // Las preferencias de vista pudieron cambiar mientras viajaba el pedido.
          const actual = proyectoRef.current;
          const nuevo: Proyecto = {
            ...r.proyecto,
            terreno: {
              ...r.proyecto.terreno,
              fecha_sol: actual.terreno.fecha_sol,
              hora_sol: actual.terreno.hora_sol,
              huso_h: actual.terreno.huso_h,
            },
          };
          proyectoRef.current = nuevo;
          despacharInterno({ tipo: "reemplazar", proyecto: nuevo });
          alAplicar?.();
          setErrorOperacion(null);
          if (r.registro.cambios.length) {
            registrar(r.registro);
            // Lo que calcula el sistema (vincular una escena) no se deshace por separado.
            if (autor !== "sistema") {
              const momento = Date.now();
              const previos = pila.current;
              const ultimo = previos[previos.length - 1];
              const agrupar =
                ultimo &&
                ultimo.registro.operacion.tipo === op.tipo &&
                ultimo.registro.autor === autor &&
                momento - ultimo.momento < VENTANA_AGRUPAR_MS;
              fijarPila(
                agrupar
                  ? [...previos.slice(0, -1), { ...ultimo, registro: r.registro, momento }]
                  : [...previos, { antes, registro: r.registro, momento }],
              );
            }
          }
          return r.registro;
        } catch (e) {
          if (gen === generacion.current) setErrorOperacion((e as Error).message);
          return null;
        }
      });
      cola.current = tarea;
      return tarea;
    },
    [registrar, fijarPila],
  );

  const vincularEscena = useCallback(
    (e: RespuestaEscena) => operar({ tipo: "vincular_escena", ref: e.ref }, "sistema", () => setEscena(e)),
    [operar],
  );

  const deshacer = useCallback(() => {
    const ultimo = pila.current[pila.current.length - 1];
    if (!ultimo) return;
    generacion.current++;
    fijarPila(pila.current.slice(0, -1));
    const actual = proyectoRef.current;
    // La escena es caché regenerable, no diseño: deshacer conserva la vigente y la
    // escena se vuelve a generar si el lote o el origen restaurados lo piden.
    const restaurado: Proyecto = {
      ...ultimo.antes,
      modificado: ahora(),
      terreno: {
        ...ultimo.antes.terreno,
        escena_ref: actual.terreno.escena_ref,
        fecha_sol: actual.terreno.fecha_sol,
        hora_sol: actual.terreno.hora_sol,
        huso_h: actual.terreno.huso_h,
      },
    };
    proyectoRef.current = restaurado;
    despacharInterno({ tipo: "reemplazar", proyecto: restaurado });
    registrar({
      id: crypto.randomUUID().replaceAll("-", ""),
      proyecto_id: actual.id,
      operacion: { tipo: "deshacer", deshace: ultimo.registro.id },
      autor: "usuario",
      fecha: ahora(),
      cambios: ultimo.registro.cambios,
      estado_antes: actual.terreno.estado,
      estado_despues: restaurado.terreno.estado,
      avisos: [],
    });
  }, [registrar, fijarPila]);

  const limpiarError = useCallback(() => setErrorOperacion(null), []);

  const valor = useMemo(
    () => ({
      proyecto,
      despachar,
      operar,
      vincularEscena,
      deshacer,
      puedeDeshacer,
      historial,
      errorOperacion,
      limpiarError,
      escena,
      setEscena,
      trayectoria,
      setTrayectoria,
      clima,
      setClima,
    }),
    [proyecto, despachar, operar, vincularEscena, deshacer, puedeDeshacer, historial, errorOperacion, limpiarError, escena, trayectoria, clima],
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
