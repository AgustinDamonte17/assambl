/**
 * LUMO · Mascota IA de Assambl · v1.0
 * ------------------------------------------------------------
 * Forma:  llama asimétrica con mechón inclinado a la derecha (base "07 Prompt")
 * Cara:   ojos ovalados con brillo + sonrisa fija (de "10 Geo")
 * Color:  Índigo #6C4DFF  → contraste 3.7:1 vs Ink y 4.1:1 vs Concrete (≥3:1 WCAG gráficos),
 *         tono opuesto al Signal #FF4F1F (no compite con los paréntesis del logo)
 * Efectos: los bloques de "build" usan Signal; todo lo demás usa el color de Lumo.
 *
 * Uso:
 *   <Lumo />                          // idle, 64px
 *   <Lumo state="think" size={32} />  // avatar en el chat mientras procesa
 *   <Lumo state="build" />            // mientras assambl() genera
 *
 * Requiere lumo.css (estados y keyframes). Sin dependencias.
 */
import { useEffect, useRef, type CSSProperties } from "react";
import "./lumo.css";

export type LumoState =
  | "idle"     // 01 reposo: respira y parpadea
  | "wave"     // 02 saludo: dos saltitos + guiño
  | "listen"   // 03 escuchando: se inclina, ondas
  | "think"    // 04 pensando: se balancea, mira arriba, chispas suben
  | "build"    // 05 ensamblando: bloques Signal se apilan a su lado
  | "reply"    // 06 respondiendo: rebote + puntos de escritura
  | "success"  // 07 éxito: salto squash & stretch + estallido de chispas
  | "oops"     // 08 ups: sacudida + gotita de sudor
  | "sleep"    // 09 durmiendo: desaturado, ojos cerrados, zzz
  | "curious"; // 10 curioso: sigue el puntero con la mirada

export const LUMO = {
  version: "1.0",
  colors: {
    lumo: "#6C4DFF",   // cuerpo
    ink: "#111111",    // ojos, sonrisa
    glint: "#FFFFFF",  // brillo de ojos
    signal: "#FF4F1F", // bloques del estado build
    sweat: "#CFE3FF",  // gotita del estado oops
  },
  /** Lienzo completo con margen para efectos. Cuadrado. */
  viewBox: "-20 -10 240 240",
  /** Recorte ajustado sólo al cuerpo (avatar / favicon). Cuadrado. */
  markViewBox: "2 12 196 196",
  paths: {
    body: "M112 16 C104 50 150 84 160 128 C170 172 140 205 100 205 C60 205 36 176 40 140 C44 104 76 88 86 66 C90 84 100 92 106 94 C100 70 100 40 112 16 Z",
    smile: "M93 154 Q103 162 113 154",
    sweat: "M150 60 C153 67 156 70 156 74 C156 77.5 153.3 80 150 80 C146.7 80 144 77.5 144 74 C144 70 147 67 150 60 Z",
  },
  eyes: {
    left:  { cx: 86,  cy: 136, rx: 7, ry: 10, glint: { cx: 88,  cy: 131, r: 2.6 } },
    right: { cx: 120, cy: 136, rx: 7, ry: 10, glint: { cx: 122, cy: 131, r: 2.6 } },
  },
  smileStroke: 4.5,
  /** Centro de la mirada en coordenadas del viewBox (para el estado curious). */
  gazeOrigin: { x: 103, y: 136 },
} as const;

type Props = {
  state?: LumoState;
  size?: number;
  color?: string;
  title?: string;
  className?: string;
};

export function Lumo({ state = "idle", size = 64, color, title = "Lumo", className }: Props) {
  const ref = useRef<SVGSVGElement>(null);

  // Estado "curious": la mirada y la inclinación siguen al puntero.
  useEffect(() => {
    if (state !== "curious") return;
    const svg = ref.current;
    if (!svg) return;
    const look = svg.querySelector<SVGGElement>(".lumo-look");
    const rig = svg.querySelector<SVGGElement>(".lumo-rig");
    if (!look || !rig) return;
    const [vx, vy, vw, vh] = LUMO.viewBox.split(" ").map(Number);

    const onMove = (e: PointerEvent) => {
      const r = svg.getBoundingClientRect();
      const cx = r.left + ((LUMO.gazeOrigin.x - vx) / vw) * r.width;
      const cy = r.top + ((LUMO.gazeOrigin.y - vy) / vh) * r.height;
      const dx = e.clientX - cx, dy = e.clientY - cy;
      const d = Math.hypot(dx, dy) || 1;
      const k = Math.min(1, d / 280);
      const ux = (dx / d) * k, uy = (dy / d) * k;
      look.style.transform = `translate(${(ux * 6).toFixed(2)}px, ${(uy * 5).toFixed(2)}px)`;
      rig.style.transform = `rotate(${(ux * 6).toFixed(2)}deg)`;
    };
    window.addEventListener("pointermove", onMove);
    return () => {
      window.removeEventListener("pointermove", onMove);
      look.style.transform = "";
      rig.style.transform = "";
    };
  }, [state]);

  const { colors, paths, eyes } = LUMO;
  const style = (color ? { "--lumo": color } : undefined) as CSSProperties | undefined;

  return (
    <svg
      ref={ref}
      className={["lumo", className].filter(Boolean).join(" ")}
      data-state={state}
      viewBox={LUMO.viewBox}
      width={size}
      height={size}
      role="img"
      aria-label={title}
      style={style}
    >
      {/* listen */}
      <g className="lumo-fx-rings" style={{ fill: "none", stroke: "var(--lumo)", strokeWidth: 3 }}>
        <circle cx="100" cy="120" r="92" />
        <circle cx="100" cy="120" r="92" />
      </g>

      <ellipse className="lumo-shadow" cx="100" cy="213" rx="52" ry="6" style={{ fill: "currentColor", fillOpacity: 0.14 }} />

      {/* build */}
      <g className="lumo-fx-blocks" style={{ fill: "var(--lumo-signal)" }}>
        <rect x="172" y="191" width="14" height="14" rx="1.5" />
        <rect x="172" y="175" width="14" height="14" rx="1.5" />
        <rect x="172" y="159" width="14" height="14" rx="1.5" />
      </g>

      {/* reply */}
      <g className="lumo-fx-dots" style={{ fill: "var(--lumo)" }}>
        <circle cx="178" cy="112" r="4.5" />
        <circle cx="191" cy="112" r="4.5" />
        <circle cx="204" cy="112" r="4.5" />
      </g>

      {/* sleep */}
      <g className="lumo-fx-zz" style={{ fill: "var(--lumo)", fontFamily: "'Archivo Black','Arial Black',sans-serif" }}>
        <text x="150" y="54" fontSize="20">z</text>
        <text x="150" y="54" fontSize="15">z</text>
      </g>

      <g className="lumo-rig">
        <path className="lumo-body" d={paths.body} style={{ fill: "var(--lumo)" }} />
        <g className="lumo-face">
          <g className="lumo-look">
            {(["left", "right"] as const).map((side) => {
              const e = eyes[side];
              return (
                <g key={side} className={`lumo-eye lumo-eye-${side === "left" ? "l" : "r"}`}>
                  <ellipse cx={e.cx} cy={e.cy} rx={e.rx} ry={e.ry} style={{ fill: "var(--lumo-ink)" }} />
                  <circle cx={e.glint.cx} cy={e.glint.cy} r={e.glint.r} style={{ fill: colors.glint }} />
                </g>
              );
            })}
          </g>
          <path
            className="lumo-mouth"
            d={paths.smile}
            style={{ fill: "none", stroke: "var(--lumo-ink)", strokeWidth: LUMO.smileStroke, strokeLinecap: "round" }}
          />
        </g>
      </g>

      {/* think + success (--tx/--ty = dirección del estallido) */}
      <g className="lumo-fx-sparks" style={{ fill: "var(--lumo)" }}>
        <circle cx="112" cy="6" r="4" style={{ "--tx": "0px", "--ty": "-26px" } as CSSProperties} />
        <circle cx="128" cy="16" r="3" style={{ "--tx": "24px", "--ty": "-12px" } as CSSProperties} />
        <circle cx="96" cy="18" r="3" style={{ "--tx": "-24px", "--ty": "-10px" } as CSSProperties} />
      </g>

      {/* oops */}
      <g className="lumo-fx-sweat">
        <path d={paths.sweat} style={{ fill: colors.sweat, stroke: "var(--lumo)", strokeWidth: 2 }} />
      </g>
    </svg>
  );
}

export default Lumo;
