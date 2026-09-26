import L from "leaflet";
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/cliente";
import { useProyecto } from "../../estado/ProyectoContext";
import { SistemaLocal } from "../../modelo/geometria";
import type { CurvasNivel, Punto } from "../../modelo/proyecto";

type Modo = "ubicacion" | "lote";

const CENTRO_INICIAL: L.LatLngTuple = [-31.4201, -64.1888]; // Córdoba, mercado de referencia

const ICONO_ORIGEN = L.divIcon({
  className: "",
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  html: `<svg width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="9" fill="none" stroke="#ff4f1f" stroke-width="2"/><path d="M11 0v6M11 16v6M0 11h6M16 11h6" stroke="#ff4f1f" stroke-width="2"/><circle cx="11" cy="11" r="1.5" fill="#ff4f1f"/></svg>`,
});

const iconoVertice = (i: number) =>
  L.divIcon({ className: "vertice-lote", iconSize: [14, 14], iconAnchor: [7, 7], html: `<span title="Vértice ${i + 1}"></span>` });

export default function Mapa({ modo }: { modo: Modo }) {
  const { proyecto, operar, escena } = useProyecto();
  const [curvas, setCurvas] = useState<CurvasNivel | null>(null);
  const capaCurvas = useRef<L.LayerGroup>(L.layerGroup());
  const t = proyecto.terreno;
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const origen = useRef<L.Marker | null>(null);
  const marco = useRef<L.Rectangle | null>(null);
  const capaLote = useRef<L.LayerGroup>(L.layerGroup());
  const modoRef = useRef(modo);
  const modoPrevio = useRef<Modo | null>(null);
  const verticesPrevios = useRef(0);
  const verticesRef = useRef<Punto[]>(t.lote.vertices);
  const ubicacionRef = useRef(t.ubicacion);
  modoRef.current = modo;
  verticesRef.current = t.lote.vertices;
  ubicacionRef.current = t.ubicacion;

  // Creación del mapa (una sola vez).
  useEffect(() => {
    if (!contenedor.current || mapa.current) return;
    const m = L.map(contenedor.current, {
      center: CENTRO_INICIAL,
      zoom: 13,
      maxZoom: ZOOM_MAXIMO,
      zoomControl: true,
      doubleClickZoom: false,
    });
    // Más allá del zoom nativo los mosaicos se estiran en lugar de pedirse: Esri
    // responde «Map data not yet available» donde no tiene imagen a ese zoom, y en
    // buena parte del país la tiene hasta el 17.
    const calles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: ZOOM_MAXIMO,
      maxNativeZoom: 19,
      attribution: "© OpenStreetMap contributors",
    });
    const satelite = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: ZOOM_MAXIMO, maxNativeZoom: 17, attribution: "Esri, Maxar, Earthstar Geographics" },
    );
    const etiquetas = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: ZOOM_MAXIMO, maxNativeZoom: 17, opacity: 0.9 },
    );
    satelite.addTo(m);
    etiquetas.addTo(m);
    L.control
      .layers(
        { Satélite: satelite, Calles: calles },
        { Nombres: etiquetas, "Curvas de nivel": capaCurvas.current, Lote: capaLote.current },
        { collapsed: true },
      )
      .addTo(m);
    L.control.scale({ metric: true, imperial: false }).addTo(m);
    capaCurvas.current.addTo(m);
    capaLote.current.addTo(m);

    m.on("click", (e: L.LeafletMouseEvent) => {
      if (modoRef.current === "ubicacion") {
        operar({ tipo: "definir_ubicacion", lat: round6(e.latlng.lat), lon: round6(e.latlng.lng), fuente: "mapa" });
      } else if (ubicacionRef.current) {
        const s = new SistemaLocal(ubicacionRef.current.lat, ubicacionRef.current.lon);
        const p = s.aLocal(e.latlng.lat, e.latlng.lng);
        operar({ tipo: "definir_lote", vertices: [...verticesRef.current, [round2(p[0]), round2(p[1])]] });
      }
    });
    mapa.current = m;
    return () => {
      m.remove();
      mapa.current = null;
      origen.current = null;
      marco.current = null;
    };
  }, [operar]);

  // Origen y marco del entorno que se modela. Es un cuadrado, no un círculo:
  // el recorte del relieve se hace sobre la rejilla de posts.
  useEffect(() => {
    const m = mapa.current;
    if (!m) return;
    if (!t.ubicacion) {
      origen.current?.remove();
      marco.current?.remove();
      origen.current = null;
      marco.current = null;
      return;
    }
    const ll: L.LatLngTuple = [t.ubicacion.lat, t.ubicacion.lon];
    if (!origen.current) {
      origen.current = L.marker(ll, { icon: ICONO_ORIGEN, draggable: true, zIndexOffset: 1000, title: "Origen del proyecto (0, 0)" }).addTo(m);
      origen.current.on("dragend", () => {
        const p = origen.current!.getLatLng();
        operar({ tipo: "definir_ubicacion", lat: round6(p.lat), lon: round6(p.lng), fuente: "mapa" });
      });
      m.setView(ll, t.margen_m > 1200 ? 14 : t.margen_m > 600 ? 15 : 17);
    } else {
      origen.current.setLatLng(ll);
      if (!m.getBounds().contains(ll)) m.panTo(ll);
    }

    const s = new SistemaLocal(t.ubicacion.lat, t.ubicacion.lon);
    const so = s.aGeografica(-t.margen_m, -t.margen_m);
    const ne = s.aGeografica(t.margen_m, t.margen_m);
    const limites: L.LatLngBoundsExpression = [
      [so.lat, so.lon],
      [ne.lat, ne.lon],
    ];
    if (!marco.current) {
      marco.current = L.rectangle(limites, {
        color: "#ff4f1f",
        weight: 1,
        dashArray: "4 4",
        fill: false,
        interactive: false,
      }).addTo(m);
    } else {
      marco.current.setBounds(limites);
    }
    origen.current.dragging?.[modo === "ubicacion" ? "enable" : "disable"]();
  }, [t.ubicacion, t.margen_m, modo, operar]);

  // Lote: polígono y vértices arrastrables.
  useEffect(() => {
    const g = capaLote.current;
    g.clearLayers();
    if (!t.ubicacion) return;
    const s = new SistemaLocal(t.ubicacion.lat, t.ubicacion.lon);
    const v = t.lote.vertices;
    const aLL = ([x, y]: Punto): L.LatLngTuple => {
      const g2 = s.aGeografica(x, y);
      return [g2.lat, g2.lon];
    };
    const latlngs = v.map(aLL);
    let poligono: L.Polygon | L.Polyline | null = null;
    if (v.length >= 3) {
      poligono = L.polygon(latlngs, { color: "#ff4f1f", weight: 2, fillColor: "#ff4f1f", fillOpacity: 0.12, interactive: false }).addTo(g);
      // Encuadre automático al crear el lote o al entrar al paso Lote; no mientras se edita.
      const m = mapa.current;
      if (m && modo === "lote" && (verticesPrevios.current < 3 || modoPrevio.current !== "lote")) {
        m.fitBounds(poligono.getBounds(), { padding: [80, 80], maxZoom: 19 });
      }
    } else if (v.length === 2) {
      poligono = L.polyline(latlngs, { color: "#ff4f1f", weight: 2, dashArray: "6 4", interactive: false }).addTo(g);
    }
    verticesPrevios.current = v.length;
    modoPrevio.current = modo;
    if (modo !== "lote") return;
    v.forEach((_, i) => {
      const marcador = L.marker(latlngs[i], { icon: iconoVertice(i), draggable: true, zIndexOffset: 500 }).addTo(g);
      marcador.on("drag", () => {
        const nuevos = v.map((p, k) => (k === i ? s.aLocal(marcador.getLatLng().lat, marcador.getLatLng().lng) : p));
        const ll = nuevos.map(aLL);
        if (poligono) poligono.setLatLngs(ll);
      });
      marcador.on("dragend", () => {
        const p = s.aLocal(marcador.getLatLng().lat, marcador.getLatLng().lng);
        operar({ tipo: "definir_lote", vertices: v.map((q, k) => (k === i ? [round2(p[0]), round2(p[1])] : q)) });
      });
      marcador.on("contextmenu", (e) => {
        L.DomEvent.stop(e);
        operar({ tipo: "definir_lote", vertices: v.filter((_, k) => k !== i) });
      });
    });
  }, [t.lote.vertices, t.ubicacion, modo, operar]);

  // Curvas de nivel del relieve reconstruido: se dibuja el lote sobre el mismo
  // terreno que después se ve en 3D, no sobre la foto.
  const refEscena = escena?.ref ?? null;
  useEffect(() => {
    if (!refEscena) {
      setCurvas(null);
      return;
    }
    let vigente = true;
    api
      .curvas(refEscena)
      .then((c) => vigente && setCurvas(c))
      .catch(() => vigente && setCurvas(null));
    return () => {
      vigente = false;
    };
  }, [refEscena]);

  useEffect(() => {
    const g = capaCurvas.current;
    g.clearLayers();
    if (!curvas || !t.ubicacion) return;
    const s = new SistemaLocal(t.ubicacion.lat, t.ubicacion.lon);
    const aLL = ([x, y]: Punto): L.LatLngTuple => {
      const q = s.aGeografica(x, y);
      return [q.lat, q.lon];
    };
    for (const c of curvas.curvas) {
      L.polyline(
        c.segmentos.map(([a, b]) => [aLL(a), aLL(b)]),
        {
          color: "#fff3c4",
          weight: c.maestra ? 1.8 : 0.9,
          opacity: c.maestra ? 0.95 : 0.7,
          interactive: true,
        },
      )
        .bindTooltip(`${c.cota.toLocaleString("es-AR")} m${curvas.absolutas ? " s.n.m." : ""}`, { sticky: true })
        .addTo(g);
    }
    // Las curvas quedan debajo del lote para que los vértices sigan tomándose con clic.
    capaLote.current.eachLayer((l) => (l as L.Path).bringToFront?.());
  }, [curvas, t.ubicacion]);

  return (
    <div className="absolute inset-0">
      <div ref={contenedor} className="absolute inset-0" />
      <div className="absolute left-3 bottom-6 z-[500] bg-concrete/90 border border-line px-2 py-1 text-[11px] text-rebar pointer-events-none max-w-md">
        <div>
          {modo === "ubicacion"
            ? "Clic en el mapa para fijar el origen del proyecto; arrastrá el marcador para ajustarlo."
            : "Clic para agregar vértices del lote · arrastrá para mover · clic derecho sobre un vértice para quitarlo."}
        </div>
        <div className="text-[10px] mt-0.5">
          La imagen es solo un fondo para dibujar. No entra al modelo 3D: el relieve viene de NASADEM.
        </div>
        {curvas && (
          <div className="text-[10px] mt-0.5 text-ink">
            {curvas.provisional
              ? "Sin curvas de nivel: la escena es provisional (plana)."
              : curvas.equidistancia_m
                ? `Curvas de nivel cada ${curvas.equidistancia_m.toLocaleString("es-AR")} m (maestras cada ${(curvas.equidistancia_m * 5).toLocaleString("es-AR")} m), de ${curvas.cota_min} a ${curvas.cota_max} m${curvas.absolutas ? " s.n.m." : ""} · relieve con posts cada ${curvas.paso_m ?? "—"} m.`
                : "Terreno prácticamente plano: no hay curvas que dibujar."}
          </div>
        )}
      </div>
    </div>
  );
}

const ZOOM_MAXIMO = 21;
const round2 = (n: number) => Math.round(n * 100) / 100;
const round6 = (n: number) => Math.round(n * 1e6) / 1e6;
