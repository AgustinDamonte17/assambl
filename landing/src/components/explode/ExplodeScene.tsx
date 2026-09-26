"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import * as THREE from "three";
import { MODEL_URL } from "./config";
import { loadModel, type Palette, type PreparedModel } from "./model";
import type { ProgressStore } from "./progress";

type Props = {
  store: ProgressStore;
  onReady: () => void;
  onError: (error: unknown) => void;
};

/** Vista arquitectónica de tres cuartos desde el noreste: galería (norte) y fachada este. */
const VIEW_DIRECTION = new THREE.Vector3(0.78, 0.62, -0.62).normalize();

/**
 * Zona libre del lienzo (fracciones del ancho/alto) donde debe caber la casa
 * ensamblada y explotada; el resto queda para los textos.
 */
function safeArea(width: number, height: number) {
  if (width >= 768) return { x0: 0.3, x1: 0.98, y0: 0.06, y1: 0.94 };
  if (width > height) return { x0: 0.34, x1: 0.98, y0: 0.06, y1: 0.94 };
  return { x0: 0.04, x1: 0.96, y0: 0.24, y1: 0.86 };
}

function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement);
  const v = (name: string, fallback: string) =>
    css.getPropertyValue(name).trim() || fallback;
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return {
    bg: v("--bg", dark ? "#111111" : "#e8e6e1"),
    signal: v("--signal", "#ff4f1f"),
    // Maqueta clara sobre concrete / sobre ink, con sombras en rebar.
    model: dark ? ["#3a3a38", "#dddbd6"] : ["#5f5f5c", "#fbfaf7"],
    terrain: dark ? ["#0c0c0c", "#121211"] : ["#c9c5bc", "#dedbd4"],
  };
}

function Explode({ store, onReady, onError }: Props) {
  const size = useThree((s) => s.size);
  const invalidate = useThree((s) => s.invalidate);
  // La cámara se lee del store dentro del efecto: R3F la expone mutable a propósito.
  const getState = useThree((s) => s.get);
  const [model, setModel] = useState<PreparedModel | null>(null);
  const shown = useRef(store.value);
  const lastTime = useRef<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let prepared: PreparedModel | null = null;
    loadModel(MODEL_URL, controller.signal)
      .then((m) => {
        prepared = m;
        m.setPalette(readPalette());
        shown.current = store.value;
        m.apply(shown.current);
        setModel(m);
      })
      .catch((error) => {
        if (!controller.signal.aborted) onError(error);
      });
    return () => {
      controller.abort();
      prepared?.dispose();
    };
  }, [store, onError]);

  // Tema claro/oscuro.
  useEffect(() => {
    if (!model) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      model.setPalette(readPalette());
      invalidate();
    };
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, [model, invalidate]);

  // Encuadre fijo: la envolvente completa del explode cabe en la zona libre.
  useLayoutEffect(() => {
    const camera = getState().camera;
    if (!model || !(camera instanceof THREE.OrthographicCamera)) return;
    const distance = 200;
    camera.position.copy(VIEW_DIRECTION).multiplyScalar(distance);
    camera.up.set(0, 1, 0);
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld();
    const view = camera.matrixWorldInverse;
    const box = new THREE.Box2();
    for (const p of model.envelopePoints()) {
      const v = p.applyMatrix4(view);
      box.expandByPoint(new THREE.Vector2(v.x, v.y));
    }
    const area = safeArea(size.width, size.height);
    const scale = Math.min(
      ((area.x1 - area.x0) * size.width) / (box.max.x - box.min.x),
      ((area.y1 - area.y0) * size.height) / (box.max.y - box.min.y),
    );
    const cx = (box.min.x + box.max.x) / 2;
    const cy = (box.min.y + box.max.y) / 2;
    const px = ((area.x0 + area.x1) / 2) * size.width;
    const py = ((area.y0 + area.y1) / 2) * size.height;
    camera.left = cx - px / scale;
    camera.right = camera.left + size.width / scale;
    camera.top = cy + py / scale;
    camera.bottom = camera.top - size.height / scale;
    camera.zoom = 1;
    camera.near = 1;
    camera.far = distance * 2 + 200;
    camera.updateProjectionMatrix();
    invalidate();
  }, [model, getState, size, invalidate]);

  // Scroll -> un frame; el suavizado pide frames hasta alcanzar el objetivo.
  useEffect(() => {
    if (!model) return;
    return store.subscribe(() => invalidate());
  }, [model, store, invalidate]);

  useEffect(() => {
    if (model) {
      // Primer frame con el modelo en pantalla antes de ocultar el poster.
      invalidate();
      const id = requestAnimationFrame(() => onReady());
      return () => cancelAnimationFrame(id);
    }
  }, [model, invalidate, onReady]);

  useFrame(({ clock }) => {
    if (!model) return;
    const now = clock.elapsedTime;
    // Primer frame tras una pausa: paso nominal; luego tiempo real, acotado.
    const dt =
      lastTime.current === null
        ? 1 / 60
        : Math.min(now - lastTime.current, 0.1);
    lastTime.current = now;
    const target = store.value;
    const diff = target - shown.current;
    if (Math.abs(diff) < 1e-4) {
      shown.current = target;
      lastTime.current = null;
    } else {
      shown.current += diff * (1 - Math.exp(-dt * 9));
      invalidate();
    }
    model.apply(shown.current);
  });

  return model ? <primitive object={model.root} /> : null;
}

export default function ExplodeScene(props: Props) {
  const [maxDpr] = useState(() =>
    Math.min(window.innerWidth, window.innerHeight) < 600 ? 1.5 : 2,
  );
  return (
    <Canvas
      orthographic
      flat
      frameloop="demand"
      dpr={[1, maxDpr]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      camera={{ position: [150, 120, -120], near: 1, far: 600 }}
      style={{ position: "absolute", inset: 0 }}
      aria-hidden="true"
      onCreated={({ gl }) => gl.setClearColor(0x000000, 0)}
    >
      <hemisphereLight args={["#ffffff", "#c9c5bc", 2.1]} />
      <directionalLight position={[20, 60, -45]} intensity={1.35} />
      <directionalLight position={[40, 20, 35]} intensity={0.35} />
      <Explode {...props} />
    </Canvas>
  );
}
