import { useEffect, useRef, useState } from "react";
import { api } from "../api/cliente";
import { descargarProyecto, leerArchivoProyecto, useProyecto } from "../estado/ProyectoContext";
import { useSitio } from "../estado/useSitio";
import PasoDiseno from "../pasos/diseno/PasoDiseno";
import PasoTerreno from "../pasos/terreno/PasoTerreno";
import { Boton, Etiqueta } from "./ui";

/** Las 14 capas del MVP_01. La 01 es la etapa de terreno; de la 02 en adelante
 *  salen del diseño de la casa y todavía solo muestran la secuencia. */
const CAPAS = [
  { n: "02", nombre: "Cimientos", nivel: "núcleo" },
  { n: "03", nombre: "Estructura woodframe", nivel: "núcleo" },
  { n: "04", nombre: "OSB", nivel: "núcleo" },
  { n: "05", nombre: "Membrana exterior", nivel: "núcleo" },
  { n: "06", nombre: "Rastreles de siding", nivel: "hook" },
  { n: "07", nombre: "Siding", nivel: "hook" },
  { n: "08", nombre: "Aislante de paredes", nivel: "hook" },
  { n: "09", nombre: "Roofing", nivel: "núcleo" },
  { n: "10", nombre: "Canaletas", nivel: "hook" },
  { n: "11", nombre: "Durlock", nivel: "hook" },
  { n: "12", nombre: "Mobiliario y terminaciones", nivel: "hook" },
  { n: "13", nombre: "Plomería", nivel: "hook" },
  { n: "14", nombre: "Eléctrico", nivel: "hook" },
] as const;

type Etapa = "terreno" | "diseno";
const CLAVE_ETAPA = "assambl.etapa";

function leerEtapa(): Etapa {
  try {
    return localStorage.getItem(CLAVE_ETAPA) === "diseno" ? "diseno" : "terreno";
  } catch {
    return "terreno";
  }
}

export default function Shell() {
  const {
    proyecto,
    despachar,
    operar,
    deshacer,
    puedeDeshacer,
    errorOperacion,
    limpiarError,
    requisitos,
    setEscena,
    setTrayectoria,
    setClima,
  } = useProyecto();
  const [etapa, setEtapaInterna] = useState<Etapa>(leerEtapa);
  const setEtapa = (e: Etapa) => {
    setEtapaInterna(e);
    try {
      localStorage.setItem(CLAVE_ETAPA, e);
    } catch {
      /* sin almacenamiento: la etapa no se recuerda */
    }
  };
  const disenoHabilitado = !!requisitos?.listo;

  /** Al cambiar de proyecto se descarta todo lo descargado: es caché regenerable. */
  const limpiarCache = () => {
    setEscena(null);
    setTrayectoria(null);
    setClima(null);
  };
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  useSitio(apiOk);
  const [editandoNombre, setEditandoNombre] = useState(false);
  const archivoRef = useRef<HTMLInputElement>(null);

  // Ctrl+Z / Cmd+Z deshace la última operación, salvo mientras se escribe en un campo.
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey) || e.shiftKey || e.key.toLowerCase() !== "z") return;
      const destino = e.target as HTMLElement | null;
      if (destino && (destino.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(destino.tagName))) return;
      e.preventDefault();
      deshacer();
    };
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [deshacer]);

  useEffect(() => {
    let vivo = true;
    const sondear = () => api.salud().then(() => vivo && setApiOk(true)).catch(() => vivo && setApiOk(false));
    sondear();
    const t = setInterval(sondear, 15000);
    return () => {
      vivo = false;
      clearInterval(t);
    };
  }, []);

  const abrir = async (archivo: File | undefined) => {
    if (!archivo) return;
    try {
      const p = await leerArchivoProyecto(archivo);
      limpiarCache();
      despachar({ tipo: "cargar", proyecto: p });
      setEtapa("terreno");
    } catch (e) {
      alert(`No se pudo abrir el proyecto: ${(e as Error).message}`);
    }
  };

  const nuevo = () => {
    if (proyecto.terreno.ubicacion && !confirm("Se descarta el proyecto actual (guardalo antes si lo necesitás). ¿Continuar?")) return;
    limpiarCache();
    despachar({ tipo: "nuevo" });
    setEtapa("terreno");
  };

  return (
    <div className="h-full grid grid-rows-[48px_1fr] grid-cols-[220px_1fr]">
      <header className="col-span-2 flex items-center justify-between border-b border-line px-4 bg-concrete">
        <div className="flex items-center gap-6">
          <span className="font-display text-lg tracking-tight select-none">
            ASSAMBL<span className="text-signal">(</span>
            <span className="font-mono text-[0.7em] font-normal">{etapa === "diseno" ? "diseño" : "terreno"}</span>
            <span className="text-signal">)</span>
          </span>
          {editandoNombre ? (
            <input
              autoFocus
              className="bg-concrete-2 border border-line px-2 py-0.5 text-sm w-72 focus:outline-none focus:border-signal"
              defaultValue={proyecto.nombre}
              onBlur={(e) => {
                const nombre = e.target.value.trim();
                if (nombre && nombre !== proyecto.nombre) operar({ tipo: "renombrar_proyecto", nombre });
                setEditandoNombre(false);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                if (e.key === "Escape") setEditandoNombre(false);
              }}
            />
          ) : (
            <button
              className="text-sm hover:text-signal text-left"
              title="Renombrar proyecto"
              onClick={() => setEditandoNombre(true)}
            >
              {proyecto.nombre}
            </button>
          )}
          <Etiqueta estado={proyecto.terreno.estado} />
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[11px] uppercase tracking-wide ${apiOk ? "text-resolved" : apiOk === false ? "text-signal" : "text-rebar"}`}>
            api {apiOk ? "conectada" : apiOk === false ? "sin conexión" : "…"}
          </span>
          {errorOperacion && (
            <button
              className="text-[11px] text-signal max-w-md truncate text-left"
              title={`${errorOperacion} (clic para cerrar)`}
              onClick={limpiarError}
            >
              No se aplicó: {errorOperacion}
            </button>
          )}
          <Boton disabled={!puedeDeshacer} onClick={deshacer} title="Deshacer la última operación (Ctrl+Z)">
            Deshacer
          </Boton>
          <Boton onClick={nuevo}>Nuevo</Boton>
          <Boton onClick={() => archivoRef.current?.click()}>Abrir</Boton>
          <input
            ref={archivoRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={(e) => {
              abrir(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
          <Boton primario onClick={() => descargarProyecto(proyecto)}>
            Guardar .json
          </Boton>
        </div>
      </header>

      <nav className="border-r border-line bg-concrete overflow-y-auto">
        <div className="px-4 pt-4 pb-2 text-[11px] uppercase tracking-widest text-rebar">Secuencia</div>
        <ol>
          <ItemSecuencia n="01" nombre="Terreno" nivel="núcleo" activa={etapa === "terreno"} onClick={() => setEtapa("terreno")} />
          <ItemSecuencia
            n="·"
            nombre="Diseño de la casa"
            nivel="planta"
            activa={etapa === "diseno"}
            onClick={disenoHabilitado || etapa === "diseno" ? () => setEtapa("diseno") : undefined}
            titulo={disenoHabilitado ? "" : "Se habilita cuando el terreno está completo"}
          />
          {CAPAS.map((c) => (
            <ItemSecuencia key={c.n} n={c.n} nombre={c.nombre} nivel={c.nivel} titulo="Se habilita cuando el diseño de la casa está resuelto" />
          ))}
        </ol>
        <div className="px-4 py-4 text-[10px] text-rebar leading-relaxed border-t border-line mt-2">
          Proyecto <span className="text-ink">{proyecto.id.slice(0, 8)}</span>
          <br />
          modificado {proyecto.modificado.replace("T", " ").slice(0, 16)}
          <br />
          se guarda solo en este navegador; usá «Guardar .json» para llevarlo.
        </div>
      </nav>

      <main className="min-h-0 min-w-0 overflow-hidden">
        {etapa === "diseno" ? (
          <PasoDiseno onVolver={() => setEtapa("terreno")} />
        ) : (
          <PasoTerreno apiOk={apiOk} onAvanzar={() => setEtapa("diseno")} />
        )}
      </main>
    </div>
  );
}

function ItemSecuencia({
  n,
  nombre,
  nivel,
  activa = false,
  onClick,
  titulo = "",
}: {
  n: string;
  nombre: string;
  nivel: string;
  activa?: boolean;
  onClick?: () => void;
  titulo?: string;
}) {
  const clase = `w-full flex items-baseline gap-3 px-4 py-2 border-l-2 text-left ${
    activa ? "border-signal bg-concrete-2" : onClick ? "border-transparent hover:bg-concrete-2" : "border-transparent text-rebar/70"
  }`;
  const contenido = (
    <>
      <span className={`text-xs ${activa ? "text-signal" : ""}`}>{n}</span>
      <span className="flex-1 text-xs leading-tight">{nombre}</span>
      <span className="text-[9px] uppercase tracking-wide opacity-60">{nivel}</span>
    </>
  );
  return (
    <li title={titulo}>
      {onClick ? (
        <button className={clase} onClick={onClick}>
          {contenido}
        </button>
      ) : (
        <div className={clase}>{contenido}</div>
      )}
    </li>
  );
}
