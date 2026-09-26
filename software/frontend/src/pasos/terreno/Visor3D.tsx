/**
 * Visor de la escena 3D.
 *
 * No construye geometría: carga el .glb que arma el backend. El mismo archivo lo
 * abre Blender y lo usará el HTML autocontenido, así que hay una sola
 * implementación de la geometría y no puede desincronizarse.
 *
 * El .glb trae un nodo raíz rotado −90° en X que convierte el sistema del
 * proyecto (Z arriba) al de glTF (Y arriba). El visor no toca esa rotación.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { api } from "../../api/cliente";
import { Boton } from "../../componentes/ui";
import { useProyecto } from "../../estado/ProyectoContext";
import { centroide } from "../../modelo/geometria";
import { arcoDiurno, horaTexto, solALaHora } from "./sol";

interface Capas {
  terreno: boolean;
  lote: boolean;
  referencias: boolean;
  arcoSolar: boolean;
  malla: boolean;
  sombras: boolean;
}

const MAPA_SOMBRA = 4096;
const CAPA_RELIEVE = "01_terreno";
const CAPAS_GLB = [CAPA_RELIEVE, "01_lote", "01_referencias"];

/** Capa del .glb a la que pertenece un objeto. GLTFLoader agrupa las mallas de
 *  varias primitivas y les agrega un sufijo, así que se busca hacia arriba. */
function capaDe(objeto: THREE.Object3D): string | null {
  for (let n: THREE.Object3D | null = objeto; n; n = n.parent) {
    const nombre = n.name;
    const capa = CAPAS_GLB.find((c) => nombre === c || nombre.startsWith(`${c}_`));
    if (capa) return capa;
  }
  return null;
}

const CAPAS_INICIALES: Capas = {
  terreno: true,
  lote: true,
  referencias: true,
  arcoSolar: true,
  malla: false,
  sombras: true,
};

interface Motor {
  renderer: THREE.WebGLRenderer;
  escena: THREE.Scene;
  camara: THREE.PerspectiveCamera;
  controles: OrbitControls;
  contenido: THREE.Group;
  sol: THREE.DirectionalLight;
  ambiente: THREE.HemisphereLight;
  arco: THREE.Line | null;
  disco: THREE.Mesh;
}

export default function Visor3D() {
  const { proyecto, escena: datos, trayectoria, despachar } = useProyecto();
  const contenedor = useRef<HTMLDivElement>(null);
  const motor = useRef<Motor | null>(null);
  const [capas, setCapas] = useState<Capas>(CAPAS_INICIALES);
  const [carga, setCarga] = useState<"vacio" | "cargando" | "ok" | "error">("vacio");
  const [error, setError] = useState("");
  const t = proyecto.terreno;
  const vertices = t.lote.vertices;
  const margen = t.margen_m;

  const estadoSol = useMemo(
    () => (trayectoria ? solALaHora(trayectoria, t.hora_sol) : null),
    [trayectoria, t.hora_sol],
  );

  // Renderer, cámara, luces y bucle de dibujo: una sola vez por montaje.
  useEffect(() => {
    const el = contenedor.current;
    if (!el) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xe8e6e1);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    // Sin mapeo tonal, un sol alto satura el relieve a blanco y la escena se
    // vuelve ilegible justo al mediodía.
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    el.appendChild(renderer.domElement);

    const escena = new THREE.Scene();
    // El plano cercano no puede ser muy chico: con escenas de más de 1 km el
    // búfer de profundidad pierde precisión y el lote parpadea contra el terreno.
    const camara = new THREE.PerspectiveCamera(50, 1, 1.0, 60000);
    const controles = new OrbitControls(camara, renderer.domElement);
    controles.enableDamping = true;
    controles.dampingFactor = 0.08;
    controles.maxPolarAngle = Math.PI / 2 - 0.02;

    const contenido = new THREE.Group();
    escena.add(contenido);

    const ambiente = new THREE.HemisphereLight(0xdfe6f0, 0x8a857a, 0.5);
    escena.add(ambiente);
    const sol = new THREE.DirectionalLight(0xfff4e6, 1.6);
    sol.castShadow = true;
    sol.shadow.mapSize.set(MAPA_SOMBRA, MAPA_SOMBRA);
    escena.add(sol, sol.target);

    // Disco que marca la posición del sol; no proyecta ni recibe sombra.
    const disco = new THREE.Mesh(
      new THREE.SphereGeometry(1, 16, 12),
      new THREE.MeshBasicMaterial({ color: 0xff4f1f }),
    );
    escena.add(disco);

    const ajustar = () => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      camara.aspect = w / h;
      camara.updateProjectionMatrix();
    };
    ajustar();
    const ro = new ResizeObserver(ajustar);
    ro.observe(el);

    let vivo = true;
    const cuadro = () => {
      if (!vivo) return;
      controles.update();
      renderer.render(escena, camara);
      requestAnimationFrame(cuadro);
    };
    cuadro();

    motor.current = { renderer, escena, camara, controles, contenido, sol, ambiente, arco: null, disco };
    return () => {
      vivo = false;
      ro.disconnect();
      controles.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
      motor.current = null;
    };
  }, []);

  // Carga del .glb generado por el backend.
  useEffect(() => {
    const m = motor.current;
    if (!m || !datos) return;
    let cancelado = false;
    setCarga("cargando");
    setError("");

    new GLTFLoader().load(
      api.urlGlb(datos.ref),
      (gltf) => {
        if (cancelado || !motor.current) return;
        limpiar(m.contenido);
        // Solo el relieve interviene en las sombras. El lote y las referencias son
        // anotaciones apoyadas sobre el suelo: si proyectaran sombra se sombrearían
        // a sí mismas y aparecerían bandas que no significan nada.
        gltf.scene.traverse((o) => {
          if (!(o instanceof THREE.Mesh)) return;
          const esRelieve = capaDe(o) === "01_terreno";
          o.castShadow = esRelieve;
          o.receiveShadow = esRelieve;
        });
        m.contenido.add(gltf.scene);
        setCarga("ok");
        encuadrar(vertices.length >= 3 ? "lote" : "entorno");
      },
      undefined,
      (e) => {
        if (cancelado) return;
        setCarga("error");
        setError(e instanceof Error ? e.message : "No se pudo cargar la escena");
      },
    );
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datos?.ref]);

  // Arco solar del día: polilínea con las muestras que manda el backend.
  useEffect(() => {
    const m = motor.current;
    if (!m) return;
    if (m.arco) {
      m.escena.remove(m.arco);
      m.arco.geometry.dispose();
      m.arco = null;
    }
    if (!trayectoria) return;
    const radio = margen * 1.15;
    const crudo = arcoDiurno(trayectoria, radio);
    if (crudo.length < 6) return;
    // Del sistema del proyecto (x este, y norte, z arriba) al de three (x, z arriba, −y).
    const puntos = new Float32Array(crudo.length);
    for (let i = 0; i < crudo.length; i += 3) {
      puntos[i] = crudo[i];
      puntos[i + 1] = crudo[i + 2];
      puntos[i + 2] = -crudo[i + 1];
    }
    const geometria = new THREE.BufferGeometry();
    geometria.setAttribute("position", new THREE.BufferAttribute(puntos, 3));
    const arco = new THREE.Line(geometria, new THREE.LineDashedMaterial({ color: 0x8a857a, dashSize: 12, gapSize: 8 }));
    arco.computeLineDistances();
    m.escena.add(arco);
    m.arco = arco;
  }, [trayectoria, margen]);

  // Orientación del sol y de la sombra.
  useEffect(() => {
    const m = motor.current;
    if (!m || !estadoSol) return;
    const [x, y, z] = estadoSol.direccion;
    const distancia = margen * 3;
    m.sol.position.set(x * distancia, z * distancia, -y * distancia);
    m.sol.target.position.set(0, 0, 0);
    m.sol.target.updateMatrixWorld();

    const extension = margen * 1.6;
    const camaraSombra = m.sol.shadow.camera;
    camaraSombra.left = -extension;
    camaraSombra.right = extension;
    camaraSombra.top = extension;
    camaraSombra.bottom = -extension;
    camaraSombra.near = margen;
    camaraSombra.far = distancia * 2;
    camaraSombra.updateProjectionMatrix();

    // El desplazamiento tiene que medirse en metros de terreno, no en un número
    // fijo: un texel del mapa de sombras cubre varios metros y con el sol bajo la
    // altura cambia mucho dentro de un mismo texel. Sin esto el relieve se raya
    // con su propia sombra.
    const texel = (2 * extension) / MAPA_SOMBRA;
    const rasante = Math.max(Math.sin((estadoSol.elevacion_deg * Math.PI) / 180), 0.08);
    m.sol.shadow.normalBias = texel * (1.5 + 1.5 / rasante);

    // De noche solo queda luz ambiente tenue: la escena no debe mentir sobre la hora.
    const altura = Math.max(Math.sin((estadoSol.elevacion_deg * Math.PI) / 180), 0);
    m.sol.intensity = estadoSol.sobre_horizonte ? 0.3 + 1.6 * altura : 0;
    m.ambiente.intensity = estadoSol.sobre_horizonte ? 0.35 + 0.35 * altura : 0.2;
    m.disco.visible = estadoSol.sobre_horizonte;
    m.disco.position.copy(m.sol.position).multiplyScalar(0.4);
    m.disco.scale.setScalar(margen * 0.03);
  }, [estadoSol, margen]);

  // Visibilidad por capa.
  useEffect(() => {
    const m = motor.current;
    if (!m) return;
    const visible: Record<string, boolean> = {
      [CAPA_RELIEVE]: capas.terreno,
      "01_lote": capas.lote,
      "01_referencias": capas.referencias,
    };
    m.contenido.traverse((o) => {
      if (o.name in visible) o.visible = visible[o.name];
      const capa = capaDe(o);
      if (o instanceof THREE.Mesh) {
        const mat = o.material as THREE.MeshStandardMaterial;
        if (capa === CAPA_RELIEVE) mat.wireframe = capas.malla;
        mat.needsUpdate = true;
      }
    });
    if (m.arco) m.arco.visible = capas.arcoSolar;
    m.renderer.shadowMap.enabled = capas.sombras;
  }, [capas, carga]);

  /** (x, y, z) del proyecto → (x, z, −y) de three. */
  const encuadrar = (que: "lote" | "entorno") => {
    const m = motor.current;
    if (!m) return;
    let objetivo: [number, number] = [0, 0];
    let d = margen * 1.6;
    if (que === "lote" && vertices.length >= 3) {
      objetivo = centroide(vertices);
      const xs = vertices.map((p) => p[0]);
      const ys = vertices.map((p) => p[1]);
      const diagonal = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
      d = Math.min(Math.max(diagonal * 2.2, 40), margen * 1.6);
    }
    m.camara.position.set(objetivo[0] - d * 0.7, d * 0.55, -(objetivo[1] - d * 0.7));
    m.controles.target.set(objetivo[0], 0, -objetivo[1]);
    m.camara.near = Math.max(d / 2000, 0.5);
    m.camara.far = margen * 20;
    m.camara.updateProjectionMatrix();
    m.controles.update();
  };

  const planta = () => {
    const m = motor.current;
    if (!m) return;
    const objetivo = m.controles.target;
    const d = m.camara.position.distanceTo(objetivo);
    m.camara.position.set(objetivo.x, objetivo.y + d, objetivo.z + 0.01);
    m.controles.update();
  };

  const alternar = (k: keyof Capas) => setCapas((c) => ({ ...c, [k]: !c[k] }));

  return (
    <div className="absolute inset-0">
      <div ref={contenedor} className="absolute inset-0 [&>canvas]:block [&>canvas]:w-full [&>canvas]:h-full" />

      <div className="absolute left-3 top-3 z-10 bg-concrete/90 border border-line p-2 text-[11px] flex flex-col gap-1">
        {(
          [
            ["terreno", "Relieve"],
            ["lote", "Lote"],
            ["referencias", "Norte y origen"],
            ["arcoSolar", "Recorrido del sol"],
            ["sombras", "Sombras"],
            ["malla", "Ver la malla"],
          ] as [keyof Capas, string][]
        ).map(([k, etiqueta]) => (
          <label key={k} className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={capas[k]} onChange={() => alternar(k)} className="accent-signal" />
            {etiqueta}
          </label>
        ))}
        <div className="flex gap-1 mt-1">
          <Boton disabled={vertices.length < 3} onClick={() => encuadrar("lote")}>
            Ir al lote
          </Boton>
          <Boton onClick={() => encuadrar("entorno")}>Todo</Boton>
          <Boton onClick={planta}>Planta</Boton>
        </div>
      </div>

      {datos?.relieve.provisional && (
        <div className="absolute left-1/2 -translate-x-1/2 top-3 z-10 bg-signal text-concrete text-[11px] px-3 py-1 uppercase tracking-widest">
          Escena provisional · sin datos de relieve
        </div>
      )}

      {carga !== "ok" && (
        <div className="absolute inset-0 grid place-items-center text-xs text-rebar pointer-events-none">
          {carga === "cargando" && "Cargando la escena…"}
          {carga === "error" && <span className="text-signal">{error}</span>}
          {carga === "vacio" &&
            (t.escena_ref ? "Reconstruyendo el terreno…" : "Generá la escena desde el panel de ubicación.")}
        </div>
      )}

      {trayectoria && (
        <ControlHorario
          hora={t.hora_sol}
          fecha={t.fecha_sol}
          amanecer={trayectoria.eventos.amanecer_local}
          atardecer={trayectoria.eventos.atardecer_local}
          azimut={estadoSol?.azimut_deg ?? 0}
          elevacion={estadoSol?.elevacion_deg ?? 0}
          onHora={(h) => despachar({ tipo: "sol_hora", hora: h })}
        />
      )}
    </div>
  );
}

function limpiar(grupo: THREE.Group) {
  for (const hijo of [...grupo.children]) {
    grupo.remove(hijo);
    hijo.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        o.geometry.dispose();
        const m = o.material;
        Array.isArray(m) ? m.forEach((x) => x.dispose()) : m.dispose();
      }
    });
  }
}

function ControlHorario(props: {
  hora: number;
  fecha: string;
  amanecer: string | null;
  atardecer: string | null;
  azimut: number;
  elevacion: number;
  onHora: (h: number) => void;
}) {
  const bajoHorizonte = props.elevacion <= 0;
  return (
    <div className="absolute left-3 right-3 bottom-3 z-10 bg-concrete/95 border border-line px-3 py-2">
      <div className="flex items-center gap-3 text-[11px]">
        <span className="uppercase tracking-widest text-rebar">{props.fecha}</span>
        <span className="font-mono text-base text-ink tabular-nums">{horaTexto(props.hora)}</span>
        <input
          type="range"
          min={0}
          max={24}
          step={1 / 12}
          value={props.hora}
          onChange={(e) => props.onHora(Number(e.target.value))}
          className="flex-1 accent-signal"
        />
        <span className={bajoHorizonte ? "text-rebar" : "text-ink"}>
          {bajoHorizonte ? "sol bajo el horizonte" : `azimut ${props.azimut.toFixed(0)}° · altura ${props.elevacion.toFixed(0)}°`}
        </span>
      </div>
      <div className="flex gap-4 text-[10px] text-rebar mt-1">
        <span>amanece {props.amanecer ?? "—"}</span>
        <span>atardece {props.atardecer ?? "—"}</span>
        <span className="ml-auto">
          Posición astronómica calculada localmente. La sombra sale del modelo 3D, con la resolución del relieve.
        </span>
      </div>
    </div>
  );
}
