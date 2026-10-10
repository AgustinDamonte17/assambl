/** Capa 03 · Casa. Recorrido: elegir cómo empezar → (charla → alternativas | imagen | ejemplo | dibujo) → editor.
 *  El editor siempre trabaja sobre `proyecto.casa`; lo anterior son maneras de llegar a una primera planta. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/cliente";
import { useProyecto } from "../../estado/ProyectoContext";
import type { Proyecto, Punto } from "../../modelo/proyecto";
import {
  casaVacia,
  extension,
  type Alternativa,
  type AnalisisPlanta,
  type Casa,
  type EstadoIA,
  type ItemCatalogo,
  type MensajeChat,
  type Pieza,
  type RespuestaAsistente,
  type RespuestaImagen,
} from "../../modelo/casa";
import angus from "assambl-software/casos/angus_ranch.assambl.json";
import { Etiqueta } from "../../componentes/ui";
import Alternativas from "./Alternativas";
import Charla from "./Charla";
import EditorPlanta, { type Herramienta } from "./EditorPlanta";
import ImportarImagen, { type Calco } from "./ImportarImagen";
import Inicio, { EstadoAsistente } from "./Inicio";
import PanelEditor, { piezaDeId } from "./PanelEditor";
import { contarEstados, ORDEN_ESTADOS } from "./estados";
import { borrarAbertura, borrarAmbiente, borrarMuro } from "./operaciones";

type Pantalla = "inicio" | "charla" | "alternativas" | "imagen" | "editor";

/** Catálogo mínimo para dibujar sin API; el completo viene de backend/assambl/catalogo/ar.json. */
const CATALOGO_LOCAL: ItemCatalogo[] = [
  { codigo: "puerta_080", tipo: "puerta", nombre: "Puerta placa 80", ancho_m: 0.8, alto_m: 2.05, antepecho_m: 0, uso: "interior", sugerida_para: [] },
  { codigo: "ventana_150_110", tipo: "ventana", nombre: "Ventana 150 × 110", ancho_m: 1.5, alto_m: 1.1, antepecho_m: 1, uso: "exterior", sugerida_para: [] },
];

const HISTORIA_MAX = 80;

export default function PasoCasa({ apiOk }: { apiOk: boolean | null }) {
  const { proyecto, despachar } = useProyecto();
  const casa = proyecto.casa ?? null;
  const lat = proyecto.terreno.ubicacion?.lat ?? null;

  const [pantalla, setPantalla] = useState<Pantalla>(casa ? "editor" : "inicio");
  const [ia, setIa] = useState<EstadoIA | null>(null);
  const [catalogo, setCatalogo] = useState<ItemCatalogo[]>(CATALOGO_LOCAL);

  // Charla
  const [modo, setModo] = useState<"libre" | "orientador">("orientador");
  const [historial, setHistorial] = useState<MensajeChat[]>([]);
  const [respuesta, setRespuesta] = useState<RespuestaAsistente | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alternativas, setAlternativas] = useState<Alternativa[] | null>(null);

  // Imagen
  const [archivo, setArchivo] = useState<File | null>(null);
  const [calco, setCalco] = useState<Calco | null>(null);

  // Editor
  const [pasado, setPasado] = useState<(Casa | null)[]>([]);
  const [futuro, setFuturo] = useState<(Casa | null)[]>([]);
  const [seleccion, setSeleccion] = useState<Pieza | null>(null);
  const [herramienta, setHerramienta] = useState<Herramienta>("seleccionar");
  const [item, setItem] = useState<ItemCatalogo | null>(null);
  const [sistemaMuro, setSistemaMuro] = useState("exterior");
  const [verEstados, setVerEstados] = useState(true);
  const [analisis, setAnalisis] = useState<AnalisisPlanta | null>(null);
  const [resaltadas, setResaltadas] = useState<Set<string>>(new Set());
  const [encuadre, setEncuadre] = useState(0);
  const [aviso, setAviso] = useState<string | null>(null);
  const avisoTimer = useRef<number>(0);

  useEffect(() => {
    if (!apiOk) return;
    api.estadoIA().then(setIa).catch(() => setIa(null));
    api.catalogo().then(setCatalogo).catch(() => undefined);
  }, [apiOk]);

  // Verificación en vivo con las reglas R03 (backend). Sin API, se muestran los estados guardados.
  useEffect(() => {
    if (!casa || !apiOk) {
      setAnalisis(null);
      return;
    }
    const t = setTimeout(() => {
      api.analizarPlanta(casa).then(setAnalisis).catch(() => setAnalisis(null));
    }, 250);
    return () => clearTimeout(t);
  }, [casa, apiOk]);

  const avisar = useCallback((texto: string) => {
    setAviso(texto);
    window.clearTimeout(avisoTimer.current);
    avisoTimer.current = window.setTimeout(() => setAviso(null), 3500);
  }, []);

  /** Confirma un cambio de la planta con una entrada de deshacer. */
  const aplicar = useCallback(
    (nueva: Casa | null, sel?: Pieza | null) => {
      setPasado((h) => [...h.slice(-HISTORIA_MAX), proyecto.casa ?? null]);
      setFuturo([]);
      despachar({ tipo: "casa", casa: nueva });
      if (sel !== undefined) setSeleccion(sel);
    },
    [proyecto.casa, despachar],
  );

  const deshacer = pasado.length
    ? () => {
        setFuturo((f) => [proyecto.casa ?? null, ...f]);
        despachar({ tipo: "casa", casa: pasado[pasado.length - 1] });
        setPasado((h) => h.slice(0, -1));
        setSeleccion(null);
      }
    : null;
  const rehacer = futuro.length
    ? () => {
        setPasado((h) => [...h, proyecto.casa ?? null]);
        despachar({ tipo: "casa", casa: futuro[0] });
        setFuturo((f) => f.slice(1));
        setSeleccion(null);
      }
    : null;

  // Atajos de teclado del editor.
  useEffect(() => {
    if (pantalla !== "editor") return;
    const h = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
      const k = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && k === "z") {
        e.preventDefault();
        (e.shiftKey ? rehacer : deshacer)?.();
        return;
      }
      if ((e.ctrlKey || e.metaKey) && k === "y") {
        e.preventDefault();
        rehacer?.();
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (k === "v") setHerramienta("seleccionar");
      else if (k === "m") setHerramienta("muro");
      else if (k === "a") setHerramienta("abertura");
      else if (k === "r") setHerramienta("ambiente");
      else if (k === "escape") {
        setSeleccion(null);
        setHerramienta("seleccionar");
      } else if ((k === "delete" || k === "backspace") && seleccion && casa) {
        e.preventDefault();
        if (seleccion.tipo === "muro") aplicar(borrarMuro(casa, seleccion.id), null);
        else if (seleccion.tipo === "abertura") aplicar(borrarAbertura(casa, seleccion.muro, seleccion.id), null);
        else aplicar(borrarAmbiente(casa, seleccion.id), null);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [pantalla, seleccion, casa, aplicar, deshacer, rehacer]);

  useEffect(() => {
    if (herramienta === "abertura" && !item) setItem(catalogo.find((i) => i.codigo === "ventana_150_110") ?? catalogo[0] ?? null);
  }, [herramienta, item, catalogo]);

  /* ------------------------------------------------ charla */

  const turno = async (h: MensajeChat[], opciones: string[], m: "libre" | "orientador" = modo) => {
    setHistorial(h);
    setCargando(true);
    setError(null);
    try {
      const r = await api.conversar(m, h, respuesta?.programa ?? null, opciones);
      setRespuesta(r);
      setHistorial([...h, { rol: "asistente", texto: r.mensaje }]);
    } catch (e) {
      setError(`No pude hablar con el asistente: ${(e as Error).message}`);
    } finally {
      setCargando(false);
    }
  };

  const empezarCharla = (m: "libre" | "orientador", texto?: string) => {
    setModo(m);
    setRespuesta(null);
    setAlternativas(null);
    setPantalla("charla");
    const h: MensajeChat[] = texto ? [{ rol: "usuario", texto }] : [];
    // El turno usa `respuesta` del estado; al empezar va vacío a propósito.
    setHistorial(h);
    setCargando(true);
    setError(null);
    api
      .conversar(m, h, null, [])
      .then((r) => {
        setRespuesta(r);
        setHistorial([...h, { rol: "asistente", texto: r.mensaje }]);
        if (m === "libre" && r.listo) verPlantas(r);
      })
      .catch((e) => setError(`No pude hablar con el asistente: ${(e as Error).message}`))
      .finally(() => setCargando(false));
  };

  const verPlantas = (r: RespuestaAsistente | null = respuesta) => {
    if (!r) return;
    setPantalla("alternativas");
    setAlternativas(null);
    setCargando(true);
    setError(null);
    api
      .alternativas(r.programa, lat)
      .then(setAlternativas)
      .catch((e) => setError(`No se pudieron armar las plantas: ${(e as Error).message}`))
      .finally(() => setCargando(false));
  };

  /* ------------------------------------------------ llegar al editor */

  const loteEnCasa = useMemo(() => loteLocal(proyecto, casa), [proyecto, casa]);

  const abrirEnEditor = (c: Casa, nuevoCalco: Calco | null = null) => {
    const conNombre = { ...c, nombre: proyecto.nombre };
    aplicar(implantarEnLote(conNombre, proyecto), null);
    setCalco(nuevoCalco);
    setHerramienta("seleccionar");
    setEncuadre((n) => n + 1);
    setPantalla("editor");
  };

  const abrirEjemplo = () => {
    const ejemplo = angus as unknown as Proyecto;
    if (proyecto.terreno.ubicacion || proyecto.casa) {
      if (!confirm("El ejemplo reemplaza el proyecto actual (terreno y casa). Guardalo antes si lo necesitás. ¿Continuar?")) return;
    }
    setPasado([]);
    setFuturo([]);
    despachar({ tipo: "cargar", proyecto: JSON.parse(JSON.stringify(ejemplo)) });
    setCalco(null);
    setSeleccion(null);
    setEncuadre((n) => n + 1);
    setPantalla("editor");
  };

  const aceptarImagen = (r: RespuestaImagen, c: Calco) => abrirEnEditor(r.casa, c);

  /* ------------------------------------------------ pantallas */

  if (pantalla === "inicio")
    return (
      <Inicio
        ia={ia}
        apiOk={apiOk}
        hayCasa={!!casa}
        empezarLibre={(t) => empezarCharla("libre", t)}
        empezarOrientador={() => empezarCharla("orientador")}
        empezarImagen={(f) => {
          setArchivo(f ?? null);
          setPantalla("imagen");
        }}
        empezarDibujo={() => abrirEnEditor(casaVacia(proyecto.nombre))}
        abrirEjemplo={abrirEjemplo}
        volverAlEditor={() => setPantalla("editor")}
      />
    );

  if (pantalla === "charla")
    return (
      <Charla
        modo={modo}
        historial={historial}
        respuesta={respuesta}
        cargando={cargando}
        error={error}
        enviar={(texto, opciones) => turno([...historial, { rol: "usuario", texto }], opciones)}
        verPlantas={() => verPlantas()}
        volver={() => setPantalla("inicio")}
      />
    );

  if (pantalla === "alternativas")
    return (
      <Alternativas
        alternativas={alternativas}
        cargando={cargando}
        error={error}
        elegir={(a) => abrirEnEditor(a.casa)}
        volver={() => setPantalla("charla")}
      />
    );

  if (pantalla === "imagen")
    return <ImportarImagen archivoInicial={archivo} lat={lat} aceptar={aceptarImagen} volver={() => setPantalla("inicio")} />;

  if (!casa)
    return (
      <div className="h-full flex items-center justify-center">
        <button className="underline" onClick={() => setPantalla("inicio")}>
          Empezar la planta
        </button>
      </div>
    );

  return (
    <div className="h-full grid grid-rows-[40px_1fr]">
      <div className="flex items-center gap-4 border-b border-line bg-concrete px-4">
        <button className="text-xs text-rebar hover:text-ink" onClick={() => setPantalla("inicio")}>
          ← Formas de empezar
        </button>
        {alternativas && (
          <button className="text-xs text-rebar hover:text-ink" onClick={() => setPantalla("alternativas")}>
            Ver otras alternativas
          </button>
        )}
        <span className="text-[11px] uppercase tracking-widest text-rebar">Planta 2D</span>
        {analisis && <Etiqueta estado={estadoGlobal(casa, analisis)} />}
        <div className="flex-1" />
        {origenTexto(casa) && <span className="text-[11px] text-rebar">{origenTexto(casa)}</span>}
        <EstadoAsistente ia={ia} apiOk={apiOk} compacto />
      </div>
      <div className="grid grid-cols-[1fr_340px] min-h-0">
        <div className="relative min-h-0">
          <EditorPlanta
            casa={casa}
            analisis={analisis}
            aplicar={aplicar}
            seleccion={seleccion}
            setSeleccion={setSeleccion}
            herramienta={herramienta}
            setHerramienta={setHerramienta}
            item={item}
            sistemaMuro={sistemaMuro}
            verEstados={verEstados}
            calco={calco}
            lote={loteEnCasa}
            resaltadas={resaltadas}
            encuadre={encuadre}
            avisar={avisar}
          />
          {aviso && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-6 bg-ink text-concrete text-xs px-3 py-2 shadow">{aviso}</div>
          )}
          {!casa.muros.length && herramienta !== "muro" && (
            <div className="absolute top-4 left-4 bg-concrete-2 border border-line px-3 py-2 text-xs max-w-xs">
              Planta vacía. Elegí la herramienta <b>Muro</b> (tecla M) y hacé clic para marcar las esquinas de la casa.
            </div>
          )}
        </div>
        <aside className="border-l border-line bg-concrete overflow-y-auto p-4">
          <PanelEditor
            casa={casa}
            analisis={analisis}
            aplicar={aplicar}
            seleccion={seleccion && piezaDeId(casa, seleccion.id) ? seleccion : null}
            setSeleccion={(s) => {
              setSeleccion(s);
              if (s) setHerramienta("seleccionar");
            }}
            herramienta={herramienta}
            setHerramienta={setHerramienta}
            catalogo={catalogo}
            item={item}
            setItem={setItem}
            sistemaMuro={sistemaMuro}
            setSistemaMuro={setSistemaMuro}
            verEstados={verEstados}
            setVerEstados={setVerEstados}
            opacidadCalco={calco ? calco.opacidad : null}
            setOpacidadCalco={(o) => setCalco((c) => (c ? { ...c, opacidad: o } : c))}
            quitarCalco={() => setCalco(null)}
            encuadrar={() => setEncuadre((n) => n + 1)}
            deshacer={deshacer}
            rehacer={rehacer}
            resaltar={(ids) => setResaltadas(new Set(ids))}
            empezarDeNuevo={() => setPantalla("inicio")}
          />
        </aside>
      </div>
    </div>
  );
}

/** El estado de la planta es el más grave de los que se ven en sus piezas. */
function estadoGlobal(casa: Casa, analisis: AnalisisPlanta) {
  const c = contarEstados(casa, analisis);
  return ORDEN_ESTADOS.find((e) => (c[e] ?? 0) > 0) ?? analisis.estado;
}

function origenTexto(casa: Casa): string {
  const o = casa.origen as Record<string, unknown> | undefined;
  if (!o) return "";
  if (o.fuente === "imagen") return "Planta leída de una imagen";
  if (typeof o.partido === "string") return `Alternativa «${o.partido.replace("_", " ")}»`;
  if (typeof o.fuente === "string" && o.fuente.endsWith(".py")) return `Transcripción de ${o.fuente}`;
  return "";
}

/** Lote en coordenadas de la casa (deshace la implantación: traslación y giro). */
function loteLocal(p: Proyecto, casa: Casa | null): Punto[] | null {
  const v = p.terreno.lote.vertices;
  if (!casa || v.length < 3) return null;
  const imp = casa.implantacion ?? { origen_en_lote_m: [0, 0] as Punto, giro_deg: 0 };
  const g = (-(imp.giro_deg ?? 0) * Math.PI) / 180;
  const [ox, oy] = imp.origen_en_lote_m;
  return v.map(([x, y]) => {
    const dx = x - ox;
    const dy = y - oy;
    return [dx * Math.cos(g) - dy * Math.sin(g), dx * Math.sin(g) + dy * Math.cos(g)] as Punto;
  });
}

/** Una planta nueva se ubica en el centro del lote, sin giro. Se ajusta después en la implantación. */
function implantarEnLote(c: Casa, p: Proyecto): Casa {
  const v = p.terreno.lote.vertices;
  const ext = extension(c);
  if (v.length < 3 || !ext) return c;
  const cx = v.reduce((s, q) => s + q[0], 0) / v.length;
  const cy = v.reduce((s, q) => s + q[1], 0) / v.length;
  return {
    ...c,
    implantacion: {
      ...(c.implantacion ?? { cota_piso_sobre_terreno_m: 0.2 }),
      origen_en_lote_m: [Math.round((cx - (ext.x0 + ext.x1) / 2) * 100) / 100, Math.round((cy - (ext.y0 + ext.y1) / 2) * 100) / 100],
      giro_deg: 0,
    },
  };
}
