/** Capa Casa. Recorrido: elegir cómo empezar → (Lumo | imagen | ejemplo | dibujo) → editor.
 *  El editor siempre trabaja sobre `proyecto.casa`; lo anterior son maneras de llegar a una primera planta.
 *  El editor tiene dos vistas de la misma casa: la planta 2D y la vista 3D amoblada. Comparten la selección,
 *  el deshacer y las reglas; muros y aberturas se dibujan en la planta, los muebles se acomodan en las dos. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/cliente";
import { useProyecto } from "../../estado/ProyectoContext";
import type { Proyecto, Punto } from "../../modelo/proyecto";
import {
  alturaMuros,
  casaVacia,
  extension,
  superficieGaleria,
  SIN_DECISIONES,
  type AnalisisPlanta,
  type Casa,
  type Decisiones,
  type EstadoIA,
  type ItemCatalogo,
  type MensajeChat,
  type Pieza,
  type RespuestaImagen,
  superficieCubierta,
  areaPoligono,
  type VerificacionPlanta,
} from "../../modelo/casa";
import angus from "assambl-software/casos/angus_ranch.assambl.json";
import { Etiqueta } from "../../componentes/ui";
import DisenarConLumo from "./DisenarConLumo";
import EditorPlanta, { type Herramienta } from "./EditorPlanta";
import ImportarImagen, { type Calco } from "./ImportarImagen";
import Inicio, { EstadoAsistente } from "./Inicio";
import LumoEditor, { type PedidoResolver } from "./LumoEditor";
import PanelEditor, { piezaDeId } from "./PanelEditor";
import { contarEstados, ORDEN_ESTADOS } from "./estados";
import { borrarAbertura, borrarAmbiente, borrarMuro, borrarPieza, duplicarPieza, girarPieza } from "./operaciones";
import { piezasInterior } from "../../modelo/muebles";
import Lumo from "../../componentes/lumo/Lumo";
import PanelInterior, { type Propuesta } from "./PanelInterior";
import VistaCasa3D, { type Camara3D, type VistaCasa3DRef } from "./VistaCasa3D";

type Pantalla = "inicio" | "lumo" | "imagen" | "editor";

/** Catálogo mínimo para dibujar sin API; el completo viene de backend/assambl/catalogo/ar.json. */
const CATALOGO_LOCAL: ItemCatalogo[] = [
  { codigo: "puerta_080", tipo: "puerta", nombre: "Puerta placa 80", ancho_m: 0.8, alto_m: 2.05, antepecho_m: 0, uso: "interior", sugerida_para: [] },
  { codigo: "ventana_150_110", tipo: "ventana", nombre: "Ventana 150 × 110", ancho_m: 1.5, alto_m: 1.1, antepecho_m: 1, uso: "exterior", sugerida_para: [] },
];

const HISTORIA_MAX = 80;
const SIN_VERIFICACIONES: VerificacionPlanta[] = [];

export default function PasoCasa({ apiOk }: { apiOk: boolean | null }) {
  const { proyecto, despachar } = useProyecto();
  const casa = proyecto.casa ?? null;
  const lat = proyecto.terreno.ubicacion?.lat ?? null;

  const [pantalla, setPantalla] = useState<Pantalla>(casa ? "editor" : "inicio");
  const [ia, setIa] = useState<EstadoIA | null>(null);
  const [catalogo, setCatalogo] = useState<ItemCatalogo[]>(CATALOGO_LOCAL);

  // Lumo: desde el inicio arranca de cero; desde el editor retoma las decisiones de la planta.
  const [retomarLumo, setRetomarLumo] = useState(false);
  const irALumo = (retomar: boolean) => {
    setRetomarLumo(retomar);
    setPantalla("lumo");
  };

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
  const [cotas, setCotas] = useState(false);
  const [pedidoLumo, setPedidoLumo] = useState<PedidoResolver | null>(null);
  const [focoNombre, setFocoNombre] = useState(0);
  const resolverConLumo = (v: VerificacionPlanta) => {
    const pieza = v.piezas[0] && casa ? piezaDeId(casa, v.piezas[0]) : null;
    if (pieza) setSeleccion(pieza);
    setPedidoLumo((p) => ({ n: (p?.n ?? 0) + 1, verificacion: v }));
  };
  const [analisis, setAnalisis] = useState<AnalisisPlanta | null>(null);
  const [resaltadas, setResaltadas] = useState<Set<string>>(new Set());
  const [encuadre, setEncuadre] = useState(0);
  const [aviso, setAviso] = useState<string | null>(null);
  const avisoTimer = useRef<number>(0);

  // Vista 3D
  const [vista, setVista] = useState<"planta" | "3d">("planta");
  const [camara, setCamara] = useState<Camara3D>("suroeste");
  const [encuadre3d, setEncuadre3d] = useState(0);
  const [corte, setCorte] = useState<number | null>(null);
  const [verMuebles, setVerMuebles] = useState(true);
  const [propuesta, setPropuesta] = useState<Propuesta | null>(null);
  const [historialInterior, setHistorialInterior] = useState<MensajeChat[]>([]);
  const [amoblando, setAmoblando] = useState(false);
  const vista3d = useRef<VistaCasa3DRef>(null);

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
      // Muebles: girar, duplicar y borrar, en las dos vistas.
      if (seleccion?.tipo === "mueble" && casa && !propuesta) {
        if (k === "r" && !e.ctrlKey && !e.metaKey) {
          aplicar(girarPieza(casa, seleccion.id, e.shiftKey ? -1 : 1), seleccion);
          return;
        }
        if ((e.ctrlKey || e.metaKey) && k === "d") {
          e.preventDefault();
          const r = duplicarPieza(casa, seleccion.id);
          if (r) aplicar(r.casa, { tipo: "mueble", id: r.id });
          return;
        }
        if (k === "delete" || k === "backspace") {
          e.preventDefault();
          aplicar(borrarPieza(casa, seleccion.id), null);
          return;
        }
      }
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
      if (vista === "3d") {
        if (k === "escape") setSeleccion(null);
        return;
      }
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
  }, [pantalla, seleccion, casa, aplicar, deshacer, rehacer, vista, propuesta]);

  useEffect(() => {
    if (herramienta === "abertura" && !item) setItem(catalogo.find((i) => i.codigo === "ventana_150_110") ?? catalogo[0] ?? null);
  }, [herramienta, item, catalogo]);

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

  /* ------------------------------------------------ vista 3D */

  /** Al entrar a la vista 3D por primera vez, la casa aparece amoblada (se puede deshacer). */
  const verEn3D = async () => {
    setVista("3d");
    setEncuadre3d((n) => n + 1);
    if (!casa || !apiOk || amoblando) return;
    const marca = (casa.interior as { amoblado_automatico?: string } | undefined)?.amoblado_automatico;
    if (marca || piezasInterior(casa).length) return;
    setAmoblando(true);
    try {
      const r = await api.amoblar(casa);
      aplicar({ ...r.casa, interior: { amoblado_automatico: new Date().toISOString().slice(0, 10) } }, null);
      setHistorialInterior((h) => [
        ...h,
        {
          rol: "asistente",
          texto:
            "Te propuse un amoblado para ver la casa habitada. Movelo, cambialo o pedime ajustes; si no te gusta, Ctrl+Z lo deshace." +
            (r.notas.length ? ` ${r.notas.join(" ")}` : ""),
        },
      ]);
    } catch (e) {
      avisar(`No pude amoblar: ${(e as Error).message}`);
    } finally {
      setAmoblando(false);
    }
  };

  const irAPlanta = (p: Pieza | null) => {
    setVista("planta");
    setPropuesta(null);
    if (p) setSeleccion(p);
    setHerramienta("seleccionar");
  };

  /** Lámina con la vista actual: título, la imagen y los datos de superficie. */
  const exportarImagen = async () => {
    if (!casa || !vista3d.current) return;
    // La lámina sale sin selección ni resaltados.
    setSeleccion(null);
    setResaltadas(new Set());
    await new Promise((ok) => setTimeout(ok, 150));
    if (!vista3d.current) return;
    const [W, H, img] = [1800, 1300, 1100];
    const url = vista3d.current.capturar(W, img);
    const lienzo = document.createElement("canvas");
    lienzo.width = W;
    lienzo.height = H;
    const g = lienzo.getContext("2d")!;
    await document.fonts.ready;
    g.fillStyle = "#f3f2ef";
    g.fillRect(0, 0, W, H);
    const imagen = new Image();
    await new Promise((ok) => {
      imagen.onload = ok;
      imagen.src = url;
    });
    g.drawImage(imagen, 0, 110, W, img);
    g.fillStyle = "#7a7a78";
    g.font = '500 22px "Chivo Mono", monospace';
    g.fillText(proyecto.nombre.toUpperCase(), 64, 58);
    g.fillStyle = "#111111";
    g.font = '800 40px "Chivo", sans-serif';
    g.fillText("Vista seccionada", 64, 100);
    g.fillStyle = "#7a7a78";
    g.font = '500 22px "Chivo Mono", monospace';
    const fecha = new Date().toISOString().slice(0, 10);
    g.textAlign = "right";
    g.fillText(`ASSAMBL · ${fecha}`, W - 64, 58);
    g.textAlign = "left";
    g.strokeStyle = "rgba(17,17,17,0.2)";
    g.beginPath();
    g.moveTo(64, H - 80);
    g.lineTo(W - 64, H - 80);
    g.stroke();
    const sup = superficieCubierta(casa);
    const gal = superficieGaleria(casa);
    g.fillStyle = "#111111";
    g.font = '400 24px "Chivo", sans-serif';
    g.fillText(
      `${sup ? `${sup.toFixed(1)} m² cubiertos` : "Superficie a definir"}${gal ? ` + ${gal.toFixed(1)} m² de galería` : ""} · ${piezasInterior(casa).length} muebles y artefactos`,
      64,
      H - 44,
    );
    g.fillStyle = "#7a7a78";
    g.font = '400 18px "Chivo", sans-serif';
    g.fillText("Vista calculada desde la planta. Muros recortados para ver adentro; muebles en medidas reales.", 64, H - 16);
    const a = document.createElement("a");
    a.href = lienzo.toDataURL("image/png");
    a.download = `${proyecto.nombre.replace(/[^\w-]+/g, "_")}_vista.png`;
    a.click();
  };

  /* ------------------------------------------------ pantallas */

  if (pantalla === "inicio")
    return (
      <Inicio
        ia={ia}
        apiOk={apiOk}
        hayCasa={!!casa}
        empezarConLumo={() => irALumo(false)}
        empezarImagen={(f) => {
          setArchivo(f ?? null);
          setPantalla("imagen");
        }}
        empezarDibujo={() => abrirEnEditor(casaVacia(proyecto.nombre))}
        abrirEjemplo={abrirEjemplo}
        volverAlEditor={() => setPantalla("editor")}
      />
    );

  if (pantalla === "lumo")
    return (
      <DisenarConLumo
        lat={lat}
        inicial={retomarLumo ? decisionesDe(casa) : SIN_DECISIONES}
        elegir={(c) => abrirEnEditor(c)}
        volver={() => setPantalla(retomarLumo && casa ? "editor" : "inicio")}
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

  const graves = (analisis?.verificaciones ?? []).filter((v) => v.gravedad === "grave" && v.estado !== "comprobado_por_reglas");

  return (
    <div className="h-full grid grid-rows-[40px_1fr]">
      <div className="flex items-center gap-4 border-b border-line bg-concrete px-4">
        <button className="text-xs text-rebar hover:text-ink" onClick={() => setPantalla("inicio")}>
          ← Formas de empezar
        </button>
        {esDeLumo(casa) && (
          <button className="text-xs text-rebar hover:text-ink" onClick={() => irALumo(true)}>
            Cambiar decisiones con Lumo
          </button>
        )}
        <div className="flex border border-line">
          {(["planta", "3d"] as const).map((v) => (
            <button
              key={v}
              onClick={() => (v === "3d" ? verEn3D() : irAPlanta(null))}
              className={`font-label text-[11px] uppercase tracking-widest px-2.5 py-1 ${
                vista === v ? "bg-ink text-concrete" : "text-rebar hover:text-ink"
              }`}
            >
              {v === "planta" ? "Planta 2D" : "Vista 3D"}
            </button>
          ))}
        </div>
        {analisis && <Etiqueta estado={estadoGlobal(casa, analisis)} />}
        <div className="flex-1" />
        {origenTexto(casa) && <span className="text-xs text-rebar truncate min-w-0">{origenTexto(casa)}</span>}
        <EstadoAsistente ia={ia} apiOk={apiOk} compacto />
      </div>
      {vista === "3d" ? (
        <div className="grid grid-cols-[1fr_360px] min-h-0">
          <div className="relative min-h-0">
            <VistaCasa3D
              ref={vista3d}
              casa={propuesta?.casa ?? casa}
              analisis={propuesta ? null : analisis}
              seleccion={seleccion}
              setSeleccion={setSeleccion}
              aplicar={aplicar}
              corte={corte ?? Math.min(CORTE_INICIAL, alturaMuros(casa))}
              camara={camara}
              encuadre={encuadre3d}
              resaltadas={resaltadas}
              nuevas={propuesta?.nuevas ?? VACIO}
              verEstados={verEstados}
              verMuebles={verMuebles}
              soloLectura={!!propuesta}
            />
            {propuesta && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-concrete-2 border border-[#6c4dff] px-3 py-1.5 text-xs shadow">
                <Lumo state="success" size={26} />
                <span>Propuesta de Lumo: {propuesta.mensaje}</span>
              </div>
            )}
            {amoblando && (
              <div className="absolute inset-0 grid place-items-center bg-concrete/60">
                <div className="flex flex-col items-center gap-2">
                  <Lumo state="build" size={72} />
                  <span className="text-sm">Amoblando la casa…</span>
                </div>
              </div>
            )}
            {aviso && (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-6 bg-ink text-concrete text-xs px-3 py-2 shadow">{aviso}</div>
            )}
          </div>
          <aside className="border-l border-line bg-concrete min-h-0">
            <PanelInterior
              casa={propuesta?.casa ?? casa}
              analisis={propuesta ? null : analisis}
              aplicar={aplicar}
              seleccion={seleccion}
              setSeleccion={setSeleccion}
              apiOk={apiOk}
              lat={lat}
              camara={camara}
              setCamara={(c) => {
                setCamara(c);
                setEncuadre3d((n) => n + 1);
              }}
              corte={corte ?? Math.min(CORTE_INICIAL, alturaMuros(casa))}
              setCorte={setCorte}
              verMuebles={verMuebles}
              setVerMuebles={setVerMuebles}
              exportar={exportarImagen}
              irAPlanta={irAPlanta}
              resaltar={(ids) => setResaltadas(new Set(ids))}
              avisar={avisar}
              propuesta={propuesta}
              setPropuesta={setPropuesta}
              historial={historialInterior}
              setHistorial={setHistorialInterior}
            />
          </aside>
        </div>
      ) : (
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
            cotas={cotas}
            alRenombrar={(id) => {
              setSeleccion({ tipo: "ambiente", id });
              setFocoNombre((n) => n + 1);
            }}
            calco={calco}
            lote={loteEnCasa}
            resaltadas={resaltadas}
            encuadre={encuadre}
            avisar={avisar}
          />
          {aviso && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-6 bg-ink text-concrete text-xs px-3 py-2 shadow">{aviso}</div>
          )}
          <div className="absolute top-3 left-3 flex items-center gap-3 bg-concrete-2 border border-line px-2.5 py-1.5 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer select-none">
              <input type="checkbox" checked={cotas} onChange={(e) => setCotas(e.target.checked)} />
              Cotas
            </label>
            {cotas && (
              <span>
                <b className="font-label font-medium text-sm leading-none">{(superficieCubierta(casa) ?? 0).toFixed(1)} m²</b>
                <span className="text-rebar">
                  {" "}cubiertos · <span className="font-label">{casa.ambientes.reduce((s, a) => s + (a.contorno_m ? areaPoligono(a.contorno_m) : 0), 0).toFixed(1)} m²</span> de ambientes
                </span>
              </span>
            )}
          </div>
          {graves.length > 0 && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 max-w-[min(520px,60%)] flex flex-col gap-1.5">
              {graves.map((v) => (
                <div key={v.id} className="bg-signal text-ink px-3 py-2 text-xs leading-snug shadow flex items-start gap-3">
                  <span>
                    <b>Antes de seguir:</b> {v.detalle}
                  </span>
                  <button className="shrink-0 border border-ink px-2 py-0.5 uppercase tracking-wide text-[10px] hover:bg-ink hover:text-concrete" onClick={() => resolverConLumo(v)}>
                    Resolver
                  </button>
                </div>
              ))}
            </div>
          )}
          {!casa.muros.length && herramienta !== "muro" && (
            <div className="absolute top-14 left-3 bg-concrete-2 border border-line px-3 py-2 text-xs max-w-xs">
              Planta vacía. Elegí la herramienta <b>Muro</b> (tecla M) y hacé clic para marcar las esquinas de la casa.
            </div>
          )}
        </div>
        <aside className="border-l border-line bg-concrete flex flex-col min-h-0">
          <LumoEditor
            casa={casa}
            seleccion={seleccion}
            catalogo={catalogo}
            apiOk={apiOk}
            aplicar={aplicar}
            pedido={pedidoLumo}
            verificaciones={analisis?.verificaciones ?? SIN_VERIFICACIONES}
          />
          <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
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
            cotas={cotas}
            setCotas={setCotas}
            resolver={resolverConLumo}
            focoNombre={focoNombre}
            opacidadCalco={calco ? calco.opacidad : null}
            setOpacidadCalco={(o) => setCalco((c) => (c ? { ...c, opacidad: o } : c))}
            quitarCalco={() => setCalco(null)}
            encuadrar={() => setEncuadre((n) => n + 1)}
            deshacer={deshacer}
            rehacer={rehacer}
            resaltar={(ids) => setResaltadas(new Set(ids))}
            empezarDeNuevo={() => setPantalla("inicio")}
          />
          </div>
        </aside>
      </div>
      )}
    </div>
  );
}

const VACIO = new Set<string>();

/** Los muros arrancan cortados a la altura de una mesada alta: se ve adentro sin perder los vanos. */
const CORTE_INICIAL = 1.35;

/** El estado de la planta es el más grave de los que se ven en sus piezas. */
function estadoGlobal(casa: Casa, analisis: AnalisisPlanta) {
  const c = contarEstados(casa, analisis);
  return ORDEN_ESTADOS.find((e) => (c[e] ?? 0) > 0) ?? analisis.estado;
}

function origenTexto(casa: Casa): string {
  const o = casa.origen as Record<string, unknown> | undefined;
  if (!o) return "";
  if (o.fuente === "imagen") return "Planta leída de una imagen";
  if (esDeLumo(casa)) return "Planta base de Lumo";
  if (typeof o.fuente === "string" && o.fuente.endsWith(".py")) return `Transcripción de ${o.fuente}`;
  return "";
}

function esDeLumo(casa: Casa | null): boolean {
  const fuente = (casa?.origen as Record<string, unknown> | undefined)?.fuente;
  return typeof fuente === "string" && fuente.endsWith("planta_base.py");
}

/** Las decisiones con las que Lumo armó la planta, para retomarlas; vacías si la planta no salió de Lumo. */
function decisionesDe(casa: Casa | null): Decisiones {
  const d = (casa?.origen as { decisiones?: Partial<Decisiones> } | undefined)?.decisiones;
  return esDeLumo(casa) && d ? { ...SIN_DECISIONES, ...d } : SIN_DECISIONES;
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
