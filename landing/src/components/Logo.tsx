"use client";

import { useEffect, useState } from "react";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

const NAME_TAIL = "SSAMBL";

type Step = { word: string; speed: number; resolved?: boolean };

const STEPS: readonly Step[] = [
  { word: "idea", speed: 1 },
  { word: "diseño", speed: 1 },
  { word: "ajuste", speed: 1 },
  { word: "agregar", speed: 0.9 },
  { word: "quitar", speed: 0.85 },
  { word: "redefinir", speed: 0.84 },
  { word: "terreno", speed: 0.83 },
  { word: "planos", speed: 0.78 },
  { word: "modelo3D", speed: 0.75 },
  { word: "render", speed: 0.73 },
  { word: "vistas", speed: 0.7 },
  { word: "explorar", speed: 0.65 },
  { word: "re-ajuste", speed: 1 },
  { word: "cómputo", speed: 0.65 },
  { word: "despiece", speed: 0.7 },
  { word: "paneles", speed: 0.73 },
  { word: "materiales", speed: 0.75 },
  { word: "montaje", speed: 0.78 },
  { word: "secuencia", speed: 0.81 },
  { word: "casa", speed: 1 },
  { word: "r2b", speed: 1, resolved: true },
];

const LONGEST_ARG = STEPS.reduce(
  (longest, { word }) => (word.length > longest.length ? word : longest),
  "",
);

const ARG_CLASS = "font-mono text-[0.62em] font-normal tracking-normal";
const CURSOR_SPACE = "0.19em";

const T = {
  mark: 2000,
  typeName: 70,
  afterName: 2000,
  typeArg: 75,
  holdArg: 1500,
  resolvedHold: 900,
  deleteArg: 40,
  betweenArgs: 350,
  emptyPause: 1300,
  deleteName: 45,
  // floors that keep the fastest steps readable
  minHold: 260,
  minGap: 70,
} as const;

type Frame = {
  tail: number;
  arg: string;
  resolved: boolean;
  cursor: boolean;
};

const STATIC_FRAME: Frame = {
  tail: NAME_TAIL.length,
  arg: "casa",
  resolved: false,
  cursor: false,
};

const INITIAL_FRAME: Frame = { tail: 0, arg: "", resolved: false, cursor: false };

export default function Logo() {
  const reduced = usePrefersReducedMotion();
  const [animated, setFrame] = useState<Frame>(INITIAL_FRAME);
  const frame = reduced ? STATIC_FRAME : animated;

  useEffect(() => {
    if (reduced) return;

    // scoped to this effect run: a remount must not resurrect the previous loop
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const sleep = (ms: number) =>
      new Promise<void>((resolve) => {
        timer = setTimeout(resolve, ms);
      });

    const set = (patch: Partial<Frame>) => {
      if (alive) setFrame((f) => ({ ...f, ...patch }));
    };

    const run = async () => {
      while (alive) {
        // A()
        set({ tail: 0, arg: "", resolved: false, cursor: false });
        await sleep(T.mark);

        // A() -> ASSAMBL(), cursor lands with the last letter so the pin is seamless
        for (let i = 1; i <= NAME_TAIL.length; i++) {
          set({ tail: i, cursor: i === NAME_TAIL.length });
          await sleep(T.typeName);
        }
        await sleep(T.afterName);

        for (const { word, speed, resolved = false } of STEPS) {
          for (let i = 1; i <= word.length; i++) {
            set({ arg: word.slice(0, i) });
            await sleep(T.typeArg * speed);
          }
          await sleep(Math.max(T.minHold, T.holdArg * speed));

          if (resolved) {
            set({ resolved: true });
            await sleep(T.resolvedHold);
          }

          for (let i = word.length - 1; i >= 0; i--) {
            set({ arg: word.slice(0, i) });
            await sleep(T.deleteArg * speed);
          }
          set({ resolved: false });
          await sleep(Math.max(T.minGap, T.betweenArgs * speed));
        }

        // ASSAMBL() empty, then collapse back to A()
        await sleep(T.emptyPause);
        set({ cursor: false });
        for (let i = NAME_TAIL.length - 1; i >= 0; i--) {
          set({ tail: i });
          await sleep(T.deleteName);
        }
      }
    };

    run();

    return () => {
      alive = false;
      if (timer) clearTimeout(timer);
    };
  }, [reduced]);

  const label = `ASSAMBL(${frame.arg || " "})`;

  return (
    <h1
      aria-label={label}
      className="font-display relative whitespace-nowrap leading-none tracking-[-0.045em] select-none text-[clamp(1.9rem,7.4vw,8.5rem)]"
    >
      {/* the box is sized for the longest argument so the name never moves and no frame overflows */}
      <span aria-hidden="true" className="invisible">
        A{NAME_TAIL}(<span className={ARG_CLASS}>{LONGEST_ARG}</span>
        <span className="inline-block" style={{ width: CURSOR_SPACE }} />)
      </span>

      <span aria-hidden="true" className="absolute top-0 left-0">
        <span>A{NAME_TAIL.slice(0, frame.tail)}</span>
        <span className="text-signal">(</span>
        <span
          className={`${ARG_CLASS} transition-colors duration-300 ${
            frame.resolved ? "text-resolved" : "text-fg"
          }`}
        >
          {frame.arg}
        </span>
        {frame.cursor && (
          <span
            className="cursor-blink inline-block bg-signal align-baseline"
            style={{ width: "0.16em", height: "0.72em", marginLeft: "0.03em" }}
          />
        )}
        <span className="text-signal">)</span>
      </span>
    </h1>
  );
}
