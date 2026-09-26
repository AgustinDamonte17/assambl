import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import {
  EASE,
  PART_RULES,
  STEPS,
  HIGHLIGHT_END,
  HIGHLIGHT_FADE,
  LAYER_FADES,
  type LayerId,
  type Motion,
} from "./config";
import { segment } from "./progress";

/** Colores de marca leídos de globals.css; se actualizan al cambiar de tema. */
export type Palette = {
  bg: string;
  signal: string;
  model: readonly [dark: string, light: string];
  terrain: readonly [dark: string, light: string];
};

type Uniforms = {
  uDark: { value: THREE.Color };
  uLight: { value: THREE.Color };
  uSignal: { value: THREE.Color };
  uLumScale: { value: number };
  uHighlight: { value: number };
  /** 1: el resalte se aplica después de la luz (terreno), para no amplificarlo. */
  uTintAfter: { value: number };
  uBg: { value: THREE.Color };
  /** Radios (m) entre los que el terreno se funde con el fondo; 0 = sin fundido. */
  uFade: { value: THREE.Vector2 };
};

export type AnimatedPart = {
  object: THREE.Object3D;
  layer: LayerId;
  rest: THREE.Vector3;
  restQuaternion: THREE.Quaternion;
  /** Normal de fachada en XZ (sin normalizar: las esquinas se mueven en diagonal). */
  dir: THREE.Vector3;
  size: THREE.Vector3;
  motions: readonly Motion[];
};

export type PreparedModel = {
  root: THREE.Object3D;
  parts: AnimatedPart[];
  /** Alto del entramado de muros y lado mayor de la casa, en metros. */
  unit: { height: number; width: number };
  layerUniforms: Map<LayerId, Uniforms>;
  setPalette: (palette: Palette) => void;
  apply: (progress: number) => void;
  /**
   * Cajas de la casa (sin terreno) para encuadrar. `focus`: solo las capas que
   * siguen visibles tras desvanecer las exteriores, desde ese momento al final.
   */
  envelopePoints: (focus?: boolean) => THREE.Vector3[];
  dispose: () => void;
};

// Tono arquitectónico: la luminancia del color original del material se lleva a
// una rampa entre dos colores de marca; la capa nombrada se tiñe con --signal.
const TONE_FRAGMENT = /* glsl */ `
#if defined( USE_COLOR_ALPHA )
  vec3 srcColor = vColor.rgb;
#elif defined( USE_COLOR )
  vec3 srcColor = vColor;
#else
  vec3 srcColor = vec3( 1.0 );
#endif
  float lum = clamp( dot( srcColor, vec3( 0.2126, 0.7152, 0.0722 ) ) * uLumScale, 0.0, 1.0 );
  vec3 tone = mix( uDark, uLight, pow( lum, 0.42 ) );
  diffuseColor.rgb = mix( tone, uSignal, uHighlight * ( 1.0 - uTintAfter ) );
`;

const FADE_FRAGMENT = /* glsl */ `
  gl_FragColor.rgb = mix( gl_FragColor.rgb, uSignal, uHighlight * uTintAfter );
  if ( uFade.y > 0.0 ) {
    float fade = smoothstep( uFade.x, uFade.y, length( vFadeXZ ) );
    gl_FragColor.rgb = mix( gl_FragColor.rgb, uBg, fade );
  }
  #include <tonemapping_fragment>
`;

const UNIFORM_DECLARATIONS = [
  "uniform vec3 uDark;",
  "uniform vec3 uLight;",
  "uniform vec3 uSignal;",
  "uniform vec3 uBg;",
  "uniform vec2 uFade;",
  "uniform float uLumScale;",
  "uniform float uHighlight;",
  "uniform float uTintAfter;",
  "varying vec2 vFadeXZ;",
].join("\n");

const GLASS_OPACITY = 0.28;

function toneMaterial(uniforms: Uniforms, glass: boolean) {
  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    flatShading: true,
    roughness: glass ? 0.2 : 0.92,
    metalness: 0,
    transparent: glass,
    opacity: glass ? GLASS_OPACITY : 1,
    depthWrite: !glass,
    side: glass ? THREE.DoubleSide : THREE.FrontSide,
  });
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec2 vFadeXZ;")
      .replace(
        "#include <project_vertex>",
        "#include <project_vertex>\nvFadeXZ = ( modelMatrix * vec4( transformed, 1.0 ) ).xz;",
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>\n${UNIFORM_DECLARATIONS}`,
      )
      .replace("#include <color_fragment>", TONE_FRAGMENT)
      .replace("#include <tonemapping_fragment>", FADE_FRAGMENT);
  };
  material.customProgramCacheKey = () => "assambl-tone";
  return material;
}

function rulesFor(layer: LayerId, part: string): Motion[] {
  return PART_RULES.filter(
    (r) => r.layer === layer && (r.part === undefined || r.part === part),
  ).flatMap((r) => r.motions);
}

export async function loadModel(
  url: string,
  signal: AbortSignal,
): Promise<PreparedModel> {
  const loader = new GLTFLoader();
  const response = await fetch(url, { signal });
  if (!response.ok)
    throw new Error(`No se pudo cargar ${url}: ${response.status}`);
  const gltf = await loader.parseAsync(await response.arrayBuffer(), "");
  return prepare(gltf.scene);
}

function prepare(scene: THREE.Object3D): PreparedModel {
  const layerUniforms = new Map<LayerId, Uniforms>();
  const materials: THREE.Material[] = [];
  const shared = {
    uSignal: { value: new THREE.Color() },
    uBg: { value: new THREE.Color() },
  };
  const modelRamp = {
    uDark: { value: new THREE.Color() },
    uLight: { value: new THREE.Color() },
  };
  const terrainRamp = {
    uDark: { value: new THREE.Color() },
    uLight: { value: new THREE.Color() },
  };
  const byLayer = new Map<
    LayerId,
    { solid: THREE.Material; glass: THREE.Material }
  >();

  const materialsFor = (layer: LayerId) => {
    let entry = byLayer.get(layer);
    if (!entry) {
      const terrain = layer === "L01_Terreno";
      const uniforms: Uniforms = {
        ...(terrain ? terrainRamp : modelRamp),
        ...shared,
        uLumScale: { value: terrain ? 3.2 : 1 },
        uHighlight: { value: 0 },
        uTintAfter: { value: terrain ? 1 : 0 },
        uFade: { value: new THREE.Vector2() },
      };
      layerUniforms.set(layer, uniforms);
      entry = {
        solid: toneMaterial(uniforms, false),
        glass: toneMaterial(uniforms, true),
      };
      materials.push(entry.solid, entry.glass);
      byLayer.set(layer, entry);
    }
    return entry;
  };

  const parts: AnimatedPart[] = [];
  let unit = { height: 3.8, width: 18 };
  scene.traverse((object) => {
    const data = object.userData as {
      layer?: LayerId;
      part?: string;
      dir?: [number, number];
      size?: [number, number, number];
    };
    if (!data.layer || !data.part) return;
    const { solid, glass } = materialsFor(data.layer);
    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const original = child.material as THREE.Material;
        child.material = original.name === "vidrio" ? glass : solid;
        original.dispose();
      }
      // Solo el nodo de la parte se mueve; sus primitivas hijas quedan fijas.
      if (child !== object) {
        child.matrixAutoUpdate = false;
        child.updateMatrix();
      }
    });
    const size = new THREE.Vector3(...(data.size ?? [0, 0, 0]));
    if (data.layer === "L03_Estructura" && data.part === "entramado") {
      unit = { height: size.y, width: Math.max(size.x, size.z) };
    }
    parts.push({
      object,
      layer: data.layer,
      rest: object.position.clone(),
      restQuaternion: object.quaternion.clone(),
      dir: data.dir
        ? new THREE.Vector3(data.dir[0], 0, data.dir[1])
        : new THREE.Vector3(),
      size,
      motions: rulesFor(data.layer, data.part),
    });
  });
  // El lote se funde con el fondo lejos de la casa: la maqueta no tiene bordes duros.
  layerUniforms
    .get("L01_Terreno")
    ?.uFade.value.set(unit.width * 0.45, unit.width * 1.1);
  if (parts.length === 0)
    throw new Error("El GLB no tiene nodos de capa (userData.layer).");

  const offset = new THREE.Vector3();
  const euler = new THREE.Euler();
  const quaternion = new THREE.Quaternion();
  const up = new THREE.Vector3(0, 1, 0);

  const offsetAt = (
    part: AnimatedPart,
    progress: number,
    target: THREE.Vector3,
  ) => {
    target.set(0, 0, 0);
    let rx = 0;
    let ry = 0;
    let rz = 0;
    for (const m of part.motions) {
      const t = EASE[m.ease ?? "inOutCubic"](
        segment(progress, m.range[0], m.range[1]),
      );
      if (t === 0) continue;
      if (m.lift) target.addScaledVector(up, m.lift * unit.height * t);
      if (m.out) target.addScaledVector(part.dir, m.out * unit.width * t);
      if (m.rotate) {
        rx += m.rotate[0] * t;
        ry += m.rotate[1] * t;
        rz += m.rotate[2] * t;
      }
    }
    return [rx, ry, rz] as const;
  };

  const highlightFor = (progress: number) => {
    const levels = new Map<string, number>();
    STEPS.forEach((step, i) => {
      // La última capa se apaga antes del final: la vista explotada queda neutra.
      const next = STEPS[i + 1]?.from ?? HIGHLIGHT_END;
      const h =
        segment(progress, step.from, step.from + HIGHLIGHT_FADE) *
        (1 - segment(progress, next - HIGHLIGHT_FADE, next));
      levels.set(step.layer, h);
    });
    return levels;
  };

  const apply = (progress: number) => {
    for (const part of parts) {
      const [rx, ry, rz] = offsetAt(part, progress, offset);
      part.object.position.copy(part.rest).add(offset);
      if (rx || ry || rz) {
        part.object.quaternion
          .copy(part.restQuaternion)
          .multiply(quaternion.setFromEuler(euler.set(rx, ry, rz)));
      } else {
        part.object.quaternion.copy(part.restQuaternion);
      }
    }
    const levels = highlightFor(progress);
    layerUniforms.forEach((u, layer) => {
      const strength = layer === "L01_Terreno" ? 0.05 : 0.78;
      u.uHighlight.value = (levels.get(layer) ?? 0) * strength;
    });
    // Capas ya atravesadas: opacidad desde el progreso, nunca acumulada.
    const opacities = new Map<LayerId, number>();
    for (const f of LAYER_FADES) {
      const t = EASE[f.ease ?? "inOutSine"](
        segment(progress, f.range[0], f.range[1]),
      );
      opacities.set(f.layer, 1 - t);
    }
    opacities.forEach((opacity, layer) => {
      const entry = byLayer.get(layer);
      if (!entry) return;
      entry.solid.opacity = opacity;
      entry.solid.transparent = opacity < 1;
      entry.glass.opacity = GLASS_OPACITY * opacity;
    });
    for (const part of parts) {
      part.object.visible = (opacities.get(part.layer) ?? 1) > 0.001;
    }
  };

  const faded = new Set(LAYER_FADES.map((f) => f.layer));
  const clearEnd = Math.max(...LAYER_FADES.map((f) => f.range[1]), 0);
  const envelopePoints = (focus = false) => {
    const points: THREE.Vector3[] = [];
    const half = new THREE.Vector3();
    const center = new THREE.Vector3();
    // Los desplazamientos son monótonos: alcanzan los extremos del tramo.
    const samples = focus ? [clearEnd, 1] : [0, 1];
    for (const part of parts) {
      if (part.layer === "L01_Terreno") continue;
      if (focus && faded.has(part.layer)) continue;
      half.copy(part.size).multiplyScalar(0.5);
      for (const p of samples) {
        offsetAt(part, p, offset);
        center.copy(part.rest).add(offset);
        for (let i = 0; i < 8; i++) {
          points.push(
            new THREE.Vector3(
              center.x + (i & 1 ? half.x : -half.x),
              center.y + (i & 2 ? half.y : -half.y),
              center.z + (i & 4 ? half.z : -half.z),
            ),
          );
        }
      }
    }
    return points;
  };

  const setPalette = (palette: Palette) => {
    shared.uSignal.value.set(palette.signal);
    shared.uBg.value.set(palette.bg);
    modelRamp.uDark.value.set(palette.model[0]);
    modelRamp.uLight.value.set(palette.model[1]);
    terrainRamp.uDark.value.set(palette.terrain[0]);
    terrainRamp.uLight.value.set(palette.terrain[1]);
  };

  const dispose = () => {
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) child.geometry.dispose();
    });
    materials.forEach((m) => m.dispose());
  };

  return {
    root: scene,
    parts,
    unit,
    layerUniforms,
    setPalette,
    apply,
    envelopePoints,
    dispose,
  };
}
