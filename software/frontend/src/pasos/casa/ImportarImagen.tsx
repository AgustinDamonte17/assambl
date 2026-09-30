/** Subir un bosquejo o un plano: la IA lo lee, el generador reconstruye la planta y se muestra encima
 *  de la imagen para compararla. Nada se da por bueno: todo queda «a revisar». */

import { useEffect, useRef, useState } from "react";
import { api } from "../../api/cliente";
import type { RespuestaImagen } from "../../modelo/casa";
import { Aviso, Boton, Campo, Etiqueta } from "../../componentes/ui";
import DibujoPlanta, { aPantalla, encuadrar, Tramas } from "./DibujoPlanta";
import Monti from "./Monti";

export interface Calco {
  url: string;
  /** Rectángulo que ocupa la imagen, en metros de la casa. */
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  opacidad: number;
}

/** Achica la imagen a un máximo de 1600 px de lado: alcanza para leerla y el pedido pesa poco. */
async function prepararImagen(archivo: File): Promise<string> {
  const url = URL.createObjectURL(archivo);
  try {
    const img = await new Promise<HTMLImageElement>((ok, mal) => {
      const i = new Image();
      i.onload = () => ok(i);
      i.onerror = () => mal(new Error("No se pudo leer la imagen"));
      i.src = url;
    });
    const k = Math.min(1, 1600 / Math.max(img.naturalWidth, img.naturalHeight));
    const c = document.createElement("canvas");
    c.width = Math.round(img.naturalWidth * k);
    c.height = Math.round(img.naturalHeight * k);
    const ctx = c.getContext("2d")!;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.drawImage(img, 0, 0, c.width, c.height);
    return c.toDataURL("image/jpeg", 0.88);
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function calcoDesde(r: RespuestaImagen, url: string): Calco {
  const xs = r.rectangulos.flatMap((q) => [q.x0, q.x1]);
  const ys = r.rectangulos.flatMap((q) => [q.y0, q.y1]);
  const [mx0, mx1, my0, my1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const rec = r.lectura.recuadro_imagen ?? { x0: 0, y0: 0, x1: 1, y1: 1 };
  const fw = Math.max(rec.x1 - rec.x0, 0.05);
  const fh = Math.max(rec.y1 - rec.y0, 0.05);
  const W = (mx1 - mx0) / fw;
  const H = (my1 - my0) / fh;
  const x0 = mx0 - rec.x0 * W;
  const y1 = my1 + rec.y0 * H;
  return { url, x0, x1: x0 + W, y0: y1 - H, y1, opacidad: 0.45 };
}

interface Props {
  archivoInicial?: File | null;
  lat: number | null;
  aceptar: (r: RespuestaImagen, calco: Calco) => void;
  volver: () => void;
}

export default function ImportarImagen({ archivoInicial, lat, aceptar, volver }: Props) {
  const [imagen, setImagen] = useState<string | null>(null);
  const [ancho, setAncho] = useState("");
  const [notas, setNotas] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<RespuestaImagen | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const entrada = useRef<HTMLInputElement>(null);

  const cargar = async (f: File | undefined | null) => {
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      setError("Tiene que ser una imagen (PNG o JPG). Si tenés un PDF, exportá la página como imagen.");
      return;
    }
    setError(null);
    setResultado(null);
    try {
      setImagen(await prepararImagen(f));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    if (archivoInicial) cargar(archivoInicial);
    else entrada.current?.click();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [archivoInicial]);

  const interpretar = async (notasExtra = "") => {
    if (!imagen) return;
    setCargando(true);
    setError(null);
    try {
      const n = [notas, notasExtra].filter(Boolean).join("\n");
      const r = await api.interpretarImagen(imagen, n, ancho ? parseFloat(ancho.replace(",", ".")) : null, lat);
      setResultado(r);
      if (notasExtra) setNotas(n);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="h-full grid grid-cols-[1fr_360px] min-h-0">
      <div
        className={`relative min-h-0 flex items-center justify-center bg-concrete-3 ${arrastrando ? "outline-2 outline-signal -outline-offset-8" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastrando(false);
          cargar(e.dataTransfer.files?.[0]);
        }}
      >
        {!imagen && (
          <button className="border-2 border-dashed border-ink/30 px-10 py-12 text-rebar hover:border-signal hover:text-ink" onClick={() => entrada.current?.click()}>
            Arrastrá una imagen acá o hacé clic para elegirla
          </button>
        )}
        {imagen && !resultado && <img src={imagen} alt="Bosquejo cargado" className="max-w-[92%] max-h-[92%] object-contain shadow" />}
        {imagen && resultado && <Superpuesto resultado={resultado} imagen={imagen} />}
        {cargando && (
          <div className="absolute inset-0 bg-concrete/70 flex flex-col items-center justify-center gap-2">
            <Monti animo="pensando" tamano={64} />
            <span className="text-sm">Leyendo el dibujo… puede tardar hasta un minuto.</span>
          </div>
        )}
        <input
          ref={entrada}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            cargar(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      <aside className="border-l border-line bg-concrete overflow-y-auto p-4 flex flex-col gap-3">
        <button className="text-xs text-rebar hover:text-ink self-start" onClick={volver}>
          ← Otras formas de empezar
        </button>
        <h2 className="font-semibold">Planta desde una imagen</h2>
        <p className="text-xs text-rebar leading-relaxed">
          Funciona mejor con un dibujo prolijo, visto desde arriba y con alguna medida escrita. Si no hay medidas,
          decinos cuánto mide el frente y la IA escala el resto.
        </p>
        <Campo etiqueta="Ancho total del frente (opcional)" sufijo="m" inputMode="decimal" value={ancho} onChange={(e) => setAncho(e.target.value)} placeholder="ej. 12" />
        <label className="flex flex-col gap-1">
          <span className="text-[11px] uppercase tracking-wide text-rebar">Aclaraciones (opcional)</span>
          <textarea
            rows={3}
            value={notas}
            onChange={(e) => setNotas(e.target.value)}
            placeholder="ej. arriba del dibujo es el norte; el rectángulo chico es el lavadero"
            className="bg-concrete-2 border border-line px-2 py-1 text-xs focus:outline-none focus:border-signal resize-none"
          />
        </label>
        <div className="flex gap-2">
          <Boton onClick={() => entrada.current?.click()}>{imagen ? "Cambiar imagen" : "Elegir imagen"}</Boton>
          <Boton primario disabled={!imagen || cargando} onClick={() => interpretar()}>
            {resultado ? "Volver a interpretar" : "Interpretar"}
          </Boton>
        </div>
        {error && <Aviso fuerte>{error}</Aviso>}

        {resultado && (
          <div className="border-t border-line pt-3 flex flex-col gap-2">
            {resultado.simulado && (
              <Aviso fuerte>
                Modo demostración: la IA no está configurada, así que esta planta es un ejemplo fijo y no sale de tu
                imagen.
              </Aviso>
            )}
            {!resultado.simulado && <p className="text-sm">{resultado.lectura.resumen}</p>}
            <div className="text-xs grid grid-cols-2 gap-y-1">
              <span className="text-rebar">Escala</span>
              <span className="text-right">
                {{ cotas: "por cotas del dibujo", referencia_usuario: "por tu medida", estimada: "estimada" }[resultado.lectura.escala.fuente] ??
                  resultado.lectura.escala.fuente}
              </span>
              <span className="text-rebar">Confianza</span>
              <span className="text-right">{Math.round(resultado.lectura.confianza * 100)} %</span>
              <span className="text-rebar">Ambientes</span>
              <span className="text-right">{resultado.rectangulos.length}</span>
              <span className="text-rebar">Estado</span>
              <span className="text-right">
                <Etiqueta estado="pendiente_revision" />
              </span>
            </div>
            {resultado.lectura.escala.detalle && <p className="text-[10px] text-rebar">{resultado.lectura.escala.detalle}</p>}
            {resultado.advertencias.map((a, i) => (
              <Aviso key={i}>{a}</Aviso>
            ))}
            {resultado.lectura.preguntas.map((p, i) => (
              <div key={i} className="border border-line bg-concrete-2 p-2">
                <div className="text-xs mb-1.5">{p.texto}</div>
                <div className="flex flex-wrap gap-1">
                  {p.opciones.map((o) => (
                    <button
                      key={o.id}
                      className="text-[11px] border border-ink/30 px-2 py-0.5 hover:border-signal"
                      title={o.detalle}
                      onClick={() => interpretar(`${p.texto} → ${o.etiqueta}`)}
                    >
                      {o.etiqueta}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <Boton primario onClick={() => aceptar(resultado, calcoDesde(resultado, imagen!))}>
              Usar esta planta y revisarla →
            </Boton>
            <p className="text-[10px] text-rebar">
              En el editor vas a ver tu dibujo de fondo para corregir lo que la IA leyó mal.
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}

function Superpuesto({ resultado, imagen }: { resultado: RespuestaImagen; imagen: string }) {
  const caja = useRef<HTMLDivElement>(null);
  const [tam, setTam] = useState({ w: 800, h: 600 });
  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setTam({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const c = calcoDesde(resultado, imagen);
  const vista = encuadrar({ x0: c.x0, y0: c.y0, x1: c.x1, y1: c.y1 }, tam.w, tam.h, 24);
  const [ix, iy] = aPantalla(vista, [c.x0, c.y1]);
  return (
    <div ref={caja} className="absolute inset-0">
      <svg width={tam.w} height={tam.h}>
        <Tramas />
        <image href={imagen} x={ix} y={iy} width={(c.x1 - c.x0) * vista.escala} height={(c.y1 - c.y0) * vista.escala} opacity={0.55} preserveAspectRatio="none" />
        <DibujoPlanta casa={resultado.casa} vista={vista} analisis={resultado.analisis} translucido />
      </svg>
    </div>
  );
}
