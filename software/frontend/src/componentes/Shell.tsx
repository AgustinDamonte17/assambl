import { useEffect, useRef, useState } from "react";
import { api } from "../api/cliente";
import { descargarProyecto, leerArchivoProyecto, useProyecto } from "../estado/ProyectoContext";
import PasoTerreno from "../pasos/terreno/PasoTerreno";
import { Boton, Etiqueta } from "./ui";

/** Las 14 capas del MVP_01. Solo la 01 está construida; el resto muestra la secuencia. */
const CAPAS = [
  { n: "01", nombre: "Terreno", nivel: "núcleo" },
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

export default function Shell() {
  const { proyecto, despachar, setEscena, setTrayectoria, setClima } = useProyecto();

  /** Al cambiar de proyecto se descarta todo lo descargado: es caché regenerable. */
  const limpiarCache = () => {
    setEscena(null);
    setTrayectoria(null);
    setClima(null);
  };
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [editandoNombre, setEditandoNombre] = useState(false);
  const archivoRef = useRef<HTMLInputElement>(null);

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
    } catch (e) {
      alert(`No se pudo abrir el proyecto: ${(e as Error).message}`);
    }
  };

  const nuevo = () => {
    if (proyecto.terreno.ubicacion && !confirm("Se descarta el proyecto actual (guardalo antes si lo necesitás). ¿Continuar?")) return;
    limpiarCache();
    despachar({ tipo: "nuevo" });
  };

  return (
    <div className="h-full grid grid-rows-[48px_1fr] grid-cols-[220px_1fr]">
      <header className="col-span-2 flex items-center justify-between border-b border-line px-4 bg-concrete">
        <div className="flex items-center gap-6">
          <span className="font-display text-lg tracking-tight select-none">
            ASSAMBL<span className="text-signal">(</span>
            <span className="font-mono text-[0.7em] font-normal">terreno</span>
            <span className="text-signal">)</span>
          </span>
          {editandoNombre ? (
            <input
              autoFocus
              className="bg-concrete-2 border border-line px-2 py-0.5 text-sm w-72 focus:outline-none focus:border-signal"
              defaultValue={proyecto.nombre}
              onBlur={(e) => {
                despachar({ tipo: "nombre", nombre: e.target.value.trim() || proyecto.nombre });
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
          {CAPAS.map((c, i) => {
            const activa = i === 0;
            return (
              <li
                key={c.n}
                className={`flex items-baseline gap-3 px-4 py-2 border-l-2 ${
                  activa ? "border-signal bg-concrete-2" : "border-transparent text-rebar/70"
                }`}
                title={activa ? "" : "Se habilita cuando la capa anterior está resuelta"}
              >
                <span className={`text-xs ${activa ? "text-signal" : ""}`}>{c.n}</span>
                <span className="flex-1 text-xs leading-tight">{c.nombre}</span>
                <span className="text-[9px] uppercase tracking-wide opacity-60">{c.nivel}</span>
              </li>
            );
          })}
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
        <PasoTerreno apiOk={apiOk} />
      </main>
    </div>
  );
}
