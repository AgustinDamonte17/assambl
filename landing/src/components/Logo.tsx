"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

const NAME_TAIL = "SSAMBL";
const ARGS = ["idea", "design", "house", "structure", "bom", "r2b"] as const;
const RESOLVED_ARG = "r2b";

const T = {
  mark: 1400,
  typeName: 70,
  afterName: 900,
  typeArg: 75,
  holdArg: 1500,
  resolvedHold: 900,
  deleteArg: 40,
  betweenArgs: 350,
  emptyPause: 1300,
  deleteName: 45,
} as const;

type Frame = {
  tail: number;
  arg: string;
  resolved: boolean;
  cursor: boolean;
};

const STATIC_FRAME: Frame = {
  tail: NAME_TAIL.length,
  arg: "house",
  resolved: false,
  cursor: false,
};

const INITIAL_FRAME: Frame = { tail: 0, arg: "", resolved: false, cursor: false };

const REDUCED_MQ = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(onChange: () => void) {
  const mq = window.matchMedia(REDUCED_MQ);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribeReducedMotion,
    () => window.matchMedia(REDUCED_MQ).matches,
    () => false,
  );
}

export default function Logo() {
  const reduced = usePrefersReducedMotion();
  const [animated, setFrame] = useState<Frame>(INITIAL_FRAME);
  const alive = useRef(true);
  const frame = reduced ? STATIC_FRAME : animated;

  useEffect(() => {
    if (reduced) return;

    alive.current = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const sleep = (ms: number) =>
      new Promise<void>((resolve) => {
        timer = setTimeout(resolve, ms);
      });

    const set = (patch: Partial<Frame>) => {
      if (alive.current) setFrame((f) => ({ ...f, ...patch }));
    };

    const run = async () => {
      while (alive.current) {
        // A()
        set({ tail: 0, arg: "", resolved: false, cursor: false });
        await sleep(T.mark);

        // A() -> ASSAMBL()
        for (let i = 1; i <= NAME_TAIL.length; i++) {
          set({ tail: i });
          await sleep(T.typeName);
        }
        set({ cursor: true });
        await sleep(T.afterName);

        // ASSAMBL(arg) for each arg
        for (const arg of ARGS) {
          for (let i = 1; i <= arg.length; i++) {
            set({ arg: arg.slice(0, i) });
            await sleep(T.typeArg);
          }
          await sleep(T.holdArg);

          if (arg === RESOLVED_ARG) {
            set({ resolved: true });
            await sleep(T.resolvedHold);
          }

          for (let i = arg.length - 1; i >= 0; i--) {
            set({ arg: arg.slice(0, i) });
            await sleep(T.deleteArg);
          }
          set({ resolved: false });
          await sleep(T.betweenArgs);
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
      alive.current = false;
      if (timer) clearTimeout(timer);
    };
  }, [reduced]);

  const label = `ASSAMBL(${frame.arg || " "})`;

  return (
    <h1
      aria-label={label}
      className="font-display whitespace-nowrap leading-none tracking-[-0.045em] select-none text-[clamp(1.9rem,7.4vw,8.5rem)]"
    >
      <span aria-hidden="true">
        <span>A{NAME_TAIL.slice(0, frame.tail)}</span>
        <span className="text-signal">(</span>
        <span
          className={
            frame.resolved
              ? "text-resolved transition-colors duration-300"
              : "text-fg transition-colors duration-300"
          }
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
