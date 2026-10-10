/** Vista 3D de la casa: la planta levantada y amoblada para decidir antes de la estructura.
 *
 *  Cámara isométrica (ortográfica) con cuatro esquinas, vista desde arriba y recorrido a la altura de los
 *  ojos. Los muros se cortan a la altura elegida para ver adentro. Tocar un mueble lo elige; arrastrarlo lo
 *  mueve sobre el piso y se pega a los muros cercanos. Todo cambio pasa por las mismas operaciones que la
 *  planta 2D y entra en el mismo deshacer. */

import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Punto } from "../../modelo/proyecto";
import { contiene, type AnalisisPlanta, type Casa, type Pieza } from "../../modelo/casa";
import { buscarPieza } from "../../modelo/muebles";
import { COLOR_ESCENA, construirCasa, extension3d, liberar, moverEnEscena } from "./escena3d";
import { imantarPieza, moverPieza, redondear } from "./operaciones";

export type Camara3D = "sureste" | "suroeste" | "noreste" | "noroeste" | "planta" | "recorrido";

export interface VistaCasa3DRef {
  /** PNG de la vista actual, con el tamaño pedido. */
  capturar: (ancho: number, alto: number) => string;
}

interface Props {
  casa: Casa;
  analisis: AnalisisPlanta | null;
  seleccion: Pieza | null;
  setSeleccion: (p: Pieza | null) => void;
  aplicar: (c: Casa, seleccion?: Pieza | null) => void;
  corte: number;
  camara: Camara3D;
  /** Cambia para volver a encuadrar con la cámara elegida. */
  encuadre: number;
  resaltadas: Set<string>;
  nuevas: Set<string>;
  verEstados: boolean;
  verMuebles: boolean;
  /** Mientras hay una propuesta de Lumo a la vista no se edita. */
  soloLectura?: boolean;
}

const DIRECCIONES: Record<Exclude<Camara3D, "recorrido">, [number, number]> = {
  // Desde dónde mira la cámara, en planta (x este, y norte).
  sureste: [1, -1],
  suroeste: [-1, -1],
  noreste: [1, 1],
  noroeste: [-1, 1],
  planta: [0, -0.0001],
};

interface Motor {
  renderer: THREE.WebGLRenderer;
  escena: THREE.Scene;
  orto: THREE.OrthographicCamera;
  persp: THREE.PerspectiveCamera;
  controles: OrbitControls;
  casa: THREE.Group | null;
}

const VistaCasa3D = forwardRef<VistaCasa3DRef, Props>(function VistaCasa3D(p, ref) {
  const caja = useRef<HTMLDivElement>(null);
  const motor = useRef<Motor | null>(null);
  const props = useRef(p);
  props.current = p;
  const arrastre = useRef<{ id: string; agarre: Punto; centro: Punto; movido: boolean } | null>(null);

  // Motor: se crea una vez.
  useEffect(() => {
    const el = caja.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    el.appendChild(renderer.domElement);
    const escena = new THREE.Scene();
    escena.background = new THREE.Color(COLOR_ESCENA.fondo);
    escena.add(new THREE.HemisphereLight("#ffffff", "#9b958a", 1.6));
    const sol = new THREE.DirectionalLight("#ffffff", 1.5);
    sol.position.set(-12, 22, 8);
    escena.add(sol);
    const relleno = new THREE.DirectionalLight("#fff6ea", 0.45);
    relleno.position.set(14, 10, -12);
    escena.add(relleno);
    const orto = new THREE.OrthographicCamera(-10, 10, 10, -10, -200, 400);
    const persp = new THREE.PerspectiveCamera(62, 1, 0.05, 300);
    const controles = new OrbitControls(orto, renderer.domElement);
    controles.enableDamping = true;
    controles.dampingFactor = 0.12;
    controles.screenSpacePanning = true;
    controles.maxPolarAngle = Math.PI / 2 - 0.05;
    controles.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };
    motor.current = { renderer, escena, orto, persp, controles, casa: null };

    const ajustar = () => {
      const w = el.clientWidth || 1;
      const h = el.clientHeight || 1;
      renderer.setSize(w, h);
      const alto = (orto.top - orto.bottom) / 2;
      orto.left = (-alto * w) / h;
      orto.right = (alto * w) / h;
      orto.updateProjectionMatrix();
      persp.aspect = w / h;
      persp.updateProjectionMatrix();
    };
    const ro = new ResizeObserver(ajustar);
    ro.observe(el);
    ajustar();
    let vivo = true;
    const cuadro = () => {
      if (!vivo) return;
      controles.update();
      renderer.render(escena, controles.object as THREE.Camera);
      requestAnimationFrame(cuadro);
    };
    cuadro();
    return () => {
      vivo = false;
      ro.disconnect();
      controles.dispose();
      if (motor.current?.casa) liberar(motor.current.casa);
      renderer.dispose();
      el.removeChild(renderer.domElement);
      motor.current = null;
    };
  }, []);

  // Escena: se rehace cuando cambia la casa o lo que se marca.
  const opciones = useMemo(
    () => ({
      corte: p.corte,
      analisis: p.analisis,
      seleccion: p.seleccion,
      resaltadas: p.resaltadas,
      nuevas: p.nuevas,
      verEstados: p.verEstados,
      verMuebles: p.verMuebles,
    }),
    [p.corte, p.analisis, p.seleccion, p.resaltadas, p.nuevas, p.verEstados, p.verMuebles],
  );
  useEffect(() => {
    const m = motor.current;
    if (!m) return;
    if (m.casa) {
      m.escena.remove(m.casa);
      liberar(m.casa);
    }
    m.casa = construirCasa(p.casa, opciones);
    m.escena.add(m.casa);
  }, [p.casa, opciones]);

  // Cámara: al cambiar de preset, al pedir encuadre o cuando la casa cambia de tamaño (una galería nueva).
  const tamano = useMemo(() => {
    const { centro, radio } = extension3d(p.casa);
    return `${Math.round(centro.x)},${Math.round(centro.z)},${Math.round(radio)}`;
  }, [p.casa]);
  useEffect(() => {
    const m = motor.current;
    if (!m) return;
    const { centro, radio } = extension3d(p.casa);
    const el = caja.current!;
    const aspecto = (el.clientWidth || 1) / (el.clientHeight || 1);
    if (p.camara === "recorrido") {
      const amb = (p.seleccion?.tipo === "ambiente" && p.casa.ambientes.find((a) => a.id === p.seleccion!.id)) ||
        [...p.casa.ambientes].filter((a) => a.contorno_m).sort((a, b) => area(b.contorno_m!) - area(a.contorno_m!))[0];
      const c = amb?.contorno_m ? centroDe(amb.contorno_m) : ([centro.x, -centro.z] as Punto);
      m.persp.position.set(c[0] - 0.6, 1.6, -c[1] + 1.2);
      m.controles.object = m.persp;
      m.controles.target.set(c[0] + 0.6, 1.2, -c[1] - 0.8);
      m.controles.minDistance = 0.3;
      m.controles.maxDistance = 6;
      m.controles.enablePan = false;
    } else {
      const [dx, dy] = DIRECCIONES[p.camara];
      const elev = p.camara === "planta" ? Math.PI / 2 - 0.001 : (34 * Math.PI) / 180;
      const l = Math.hypot(dx, dy);
      const dist = 80;
      const horiz = Math.cos(elev) * dist;
      m.orto.position.set(centro.x + (dx / l) * horiz, centro.y + Math.sin(elev) * dist, centro.z - (dy / l) * horiz);
      const alto = radio * 1.05;
      m.orto.top = alto;
      m.orto.bottom = -alto;
      m.orto.left = -alto * aspecto;
      m.orto.right = alto * aspecto;
      m.orto.zoom = 1;
      m.orto.updateProjectionMatrix();
      m.controles.object = m.orto;
      m.controles.target.copy(centro).setY(0.6);
      m.controles.minDistance = 0;
      m.controles.maxDistance = Infinity;
      m.controles.minZoom = 0.4;
      m.controles.maxZoom = 8;
      m.controles.enablePan = true;
    }
    m.controles.update();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.camara, p.encuadre, tamano]);

  useImperativeHandle(ref, () => ({
    capturar: (ancho, alto) => {
      const m = motor.current!;
      const camara = m.controles.object as THREE.Camera;
      const previo = new THREE.Vector2();
      m.renderer.getSize(previo);
      const ratio = m.renderer.getPixelRatio();
      m.renderer.setPixelRatio(1);
      m.renderer.setSize(ancho, alto, false);
      if (camara instanceof THREE.OrthographicCamera) {
        const h = (camara.top - camara.bottom) / 2;
        const [l, r] = [camara.left, camara.right];
        camara.left = (-h * ancho) / alto;
        camara.right = (h * ancho) / alto;
        camara.updateProjectionMatrix();
        m.renderer.render(m.escena, camara);
        const url = m.renderer.domElement.toDataURL("image/png");
        camara.left = l;
        camara.right = r;
        camara.updateProjectionMatrix();
        m.renderer.setPixelRatio(ratio);
        m.renderer.setSize(previo.x, previo.y);
        return url;
      }
      m.renderer.render(m.escena, camara);
      const url = m.renderer.domElement.toDataURL("image/png");
      m.renderer.setPixelRatio(ratio);
      m.renderer.setSize(previo.x, previo.y);
      return url;
    },
  }));

  /* ------------------------------------------------ puntero */

  const rayo = useRef(new THREE.Raycaster());

  const tocar = (e: React.PointerEvent): { pieza: Pieza | null; punto: THREE.Vector3 | null } => {
    const m = motor.current!;
    const r = caja.current!.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    rayo.current.setFromCamera(ndc, m.controles.object as THREE.Camera);
    const hits = m.casa ? rayo.current.intersectObject(m.casa, true) : [];
    const hit = hits.find((h) => h.object.userData.pieza && (h.object as THREE.Mesh).isMesh);
    return { pieza: (hit?.object.userData.pieza as Pieza) ?? null, punto: hit?.point ?? null };
  };

  const enPiso = (e: React.PointerEvent): Punto | null => {
    const m = motor.current!;
    const r = caja.current!.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    rayo.current.setFromCamera(ndc, m.controles.object as THREE.Camera);
    const q = new THREE.Vector3();
    return rayo.current.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), q) ? [q.x, -q.z] : null;
  };

  const bajar = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    const { pieza } = tocar(e);
    const pp = props.current;
    if (!pieza) return; // fondo: la cámara gira
    if (pieza.tipo === "mueble" && !pp.soloLectura) {
      const pz = buscarPieza(pp.casa, pieza.id);
      const q = enPiso(e);
      if (pz && q) {
        arrastre.current = { id: pz.id, agarre: [pz.centro_m[0] - q[0], pz.centro_m[1] - q[1]], centro: pz.centro_m, movido: false };
        motor.current!.controles.enabled = false;
        (e.target as Element).setPointerCapture(e.pointerId);
      }
    }
    pp.setSeleccion(pieza);
  };

  const mover = (e: React.PointerEvent) => {
    const a = arrastre.current;
    const m = motor.current;
    if (!a || !m?.casa) return;
    const q = enPiso(e);
    const pz = buscarPieza(props.current.casa, a.id);
    if (!q || !pz) return;
    const bruto: Punto = [redondear(q[0] + a.agarre[0], 0.05), redondear(q[1] + a.agarre[1], 0.05)];
    const c = imantarPieza(props.current.casa, pz, bruto);
    if (c[0] !== a.centro[0] || c[1] !== a.centro[1]) {
      a.centro = c;
      a.movido = true;
      moverEnEscena(m.casa, a.id, c);
    }
  };

  const soltar = () => {
    const a = arrastre.current;
    arrastre.current = null;
    if (motor.current) motor.current.controles.enabled = true;
    if (a?.movido) props.current.aplicar(moverPieza(props.current.casa, a.id, a.centro), { tipo: "mueble", id: a.id });
  };

  return (
    <div
      ref={caja}
      className="absolute inset-0"
      onPointerDownCapture={bajar}
      onPointerMove={mover}
      onPointerUp={soltar}
      onPointerCancel={soltar}
      onContextMenu={(e) => e.preventDefault()}
    />
  );
});

function area(p: Punto[]): number {
  let s = 0;
  for (let i = 0; i < p.length; i++) {
    const [x1, y1] = p[i];
    const [x2, y2] = p[(i + 1) % p.length];
    s += x1 * y2 - x2 * y1;
  }
  return Math.abs(s) / 2;
}

/** Un punto dentro del ambiente (el centroide si cae adentro; en una L, el centro de su parte mayor). */
function centroDe(p: Punto[]): Punto {
  const c: Punto = [p.reduce((s, v) => s + v[0], 0) / p.length, p.reduce((s, v) => s + v[1], 0) / p.length];
  if (contiene(p, c[0], c[1])) return c;
  return p.reduce((m, v) => (contiene(p, (v[0] + c[0]) / 2, (v[1] + c[1]) / 2) ? [(v[0] + c[0]) / 2, (v[1] + c[1]) / 2] : m), p[0]);
}

export default VistaCasa3D;
