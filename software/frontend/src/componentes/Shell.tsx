import { useEffect, useRef, useState } from "react";
import { api } from "../api/cliente";
import { descargarProyecto, leerArchivoProyecto, useProyecto } from "../estado/ProyectoContext";
import PasoCasa from "../pasos/casa/PasoCasa";
import PasoTerreno from "../pasos/terreno/PasoTerreno";
import { CAPAS } from "./capas";
import Lumo from "./lumo/Lumo";
import { Boton, Etiqueta } from "./ui";

type Paso = "terreno" | "casa";

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
  const [paso, setPaso] = useState<Paso>(proyecto.casa ? "casa" : "terreno");
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
    if ((proyecto.terreno.ubicacion || proyecto.casa) && !confirm("Se descarta el proyecto actual (guardalo antes si lo necesitás). ¿Continuar?")) return;
    limpiarCache();
    despachar({ tipo: "nuevo" });
  };

  return (
    <div className="h-full grid grid-rows-[48px_1fr] grid-cols-[220px_1fr]">
      <header className="col-span-2 flex items-center justify-between border-b border-line px-4 bg-concrete">
        <div className="flex items-center gap-6">
          <span className="font-display text-lg tracking-tight select-none">
            ASSAMBL<span className="text-signal">(</span>
            <span className="font-label text-[0.7em] font-normal">{paso}</span>
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
          {paso === "terreno" && <Etiqueta estado={proyecto.terreno.estado} />}
        </div>
        <div className="flex items-center gap-2">
          <Lumo state={apiOk === false ? "sleep" : "idle"} size={26} title={apiOk === false ? "Lumo, sin conexión" : "Lumo"} />
          <span className={`font-label text-[11px] uppercase tracking-wide ${apiOk ? "text-resolved" : apiOk === false ? "text-signal" : "text-rebar"}`}>
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
        <div className="px-4 pt-4 pb-2 font-label text-[11px] uppercase tracking-widest text-rebar">Secuencia</div>
        <ol>
          {CAPAS.map((c, i) => {
            const activa = c.id === paso;
            const disponible = c.id === "terreno" || c.id === "casa";
            return (
              <li key={c.id}>
                <button
                  disabled={!disponible}
                  onClick={() => setPaso(c.id as Paso)}
                  className={`w-full text-left flex items-baseline gap-3 px-4 py-1.5 border-l-2 ${
                    activa
                      ? "border-signal bg-concrete-2"
                      : disponible
                        ? "border-transparent hover:bg-concrete-2"
                        : "border-transparent text-rebar/70 cursor-default"
                  }`}
                  title={disponible ? "" : "Se habilita cuando la capa anterior está resuelta"}
                >
                  <span className={`font-label text-xs ${activa || disponible ? "text-signal" : ""}`}>{String(i + 1).padStart(2, "0")}</span>
                  <span className={`flex-1 text-xs leading-snug ${activa ? "font-medium" : ""}`}>{c.nombre}</span>
                  <span className="font-label text-[9px] uppercase tracking-wide opacity-60">{c.nivel}</span>
                </button>
              </li>
            );
          })}
        </ol>
        <div className="px-4 py-4 text-[11px] text-rebar leading-relaxed border-t border-line mt-2">
          <div className="font-label text-[10px]">
            Proyecto <span className="text-ink">{proyecto.id.slice(0, 8)}</span>
            <br />
            modificado {proyecto.modificado.replace("T", " ").slice(0, 16)}
          </div>
          <p className="mt-1">Se guarda solo en este navegador; usá «Guardar .json» para llevarlo.</p>
        </div>
      </nav>

      <main className="min-h-0 min-w-0 overflow-hidden">
        {paso === "terreno" ? <PasoTerreno apiOk={apiOk} /> : <PasoCasa key={proyecto.id} apiOk={apiOk} />}
      </main>
    </div>
  );
}
