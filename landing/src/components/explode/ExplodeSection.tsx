"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "../usePrefersReducedMotion";
import { CAPTIONS, STEPS, stepAt } from "./config";
import { createProgressStore, measureProgress, segment } from "./progress";

const ExplodeScene = dynamic(() => import("./ExplodeScene"), { ssr: false });

type Status = "idle" | "loading" | "ready" | "error";

const POSTER = { width: 1600, height: 1000 } as const;

function hasWebGL() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

function Poster({
  state,
  className,
}: {
  state: "assembled" | "exploded";
  className?: string;
}) {
  const alt =
    state === "assembled"
      ? "Angus Ranch: la casa ensamblada sobre su terreno."
      : "Angus Ranch por capas: sin techo ni envolvente, la estructura elevada deja ver instalaciones e interior.";
  return (
    <>
      <Image
        src={`/models/angus-ranch-poster-light-${state}.png`}
        alt={alt}
        {...POSTER}
        className={`dark:hidden ${className ?? ""}`}
        sizes="100vw"
      />
      <Image
        src={`/models/angus-ranch-poster-dark-${state}.png`}
        alt={alt}
        {...POSTER}
        className={`hidden dark:block ${className ?? ""}`}
        sizes="100vw"
      />
    </>
  );
}

function LayerList({
  activeRef,
}: {
  activeRef?: React.RefObject<(HTMLLIElement | null)[]>;
}) {
  return (
    <ol className="flex flex-col gap-0.5 font-mono text-[0.68rem] leading-snug text-rebar sm:text-xs">
      {STEPS.map((step, i) => (
        <li
          key={step.label}
          ref={(el) => {
            if (activeRef) activeRef.current[i] = el;
          }}
          className="explode-layer transition-colors duration-200"
        >
          {step.label}
        </li>
      ))}
    </ol>
  );
}

/** Versión estática: sin recorrido de scroll ni 3D. */
function StaticExplode() {
  return (
    <section aria-labelledby="explode-title" className="px-6 py-16 sm:px-10">
      <div className="grid gap-8 sm:grid-cols-[minmax(12rem,1fr)_3fr] sm:items-center">
        <div className="flex flex-col gap-6">
          <h2
            id="explode-title"
            className="font-mono text-xs uppercase tracking-[0.18em] text-rebar"
          >
            <span className="text-signal">{"//"}</span> angus ranch · capas
          </h2>
          <LayerList />
        </div>
        <Poster
          state="exploded"
          className="aspect-[11/10] h-auto w-full object-cover object-right"
        />
      </div>
    </section>
  );
}

function ScrollExplode() {
  const sectionRef = useRef<HTMLElement>(null);
  const labelRef = useRef<HTMLSpanElement>(null);
  const noteRef = useRef<HTMLParagraphElement>(null);
  const itemsRef = useRef<(HTMLLIElement | null)[]>([]);
  const captionsRef = useRef<(HTMLParagraphElement | null)[]>([]);
  const [store] = useState(() => createProgressStore());
  const [near, setNear] = useState(false);
  const [status, setStatus] = useState<Status>("idle");

  // Progreso de scroll -> store + HUD por DOM directo (sin re-render de React).
  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    let frame = 0;
    let shownStep = -1;
    const renderHud = () => {
      const p = store.value;
      const step = stepAt(p);
      if (step !== shownStep) {
        shownStep = step;
        const { label, note } = STEPS[step];
        if (labelRef.current) labelRef.current.textContent = label;
        if (noteRef.current) noteRef.current.textContent = note;
        itemsRef.current.forEach((el, i) => {
          if (el) el.dataset.active = String(i === step);
        });
      }
      CAPTIONS.forEach(({ range: [a, b] }, i) => {
        const el = captionsRef.current[i];
        if (!el) return;
        const fade = 0.03;
        const o = Math.min(
          a <= 0 ? 1 : segment(p, a, a + fade),
          b >= 1 ? 1 : 1 - segment(p, b - fade, b),
        );
        el.style.opacity = String(o);
      });
    };
    const update = () => {
      frame = 0;
      store.set(measureProgress(section));
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    const unsubscribe = store.subscribe(renderHud);
    store.set(measureProgress(section));
    renderHud();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      unsubscribe();
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [store]);

  // Cargar el módulo 3D y el GLB cuando la sección se acerca al viewport.
  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        if (hasWebGL()) {
          setNear(true);
          setStatus("loading");
        } else {
          setStatus("error");
        }
      },
      { rootMargin: "0px 0px -10% 0px" },
    );
    observer.observe(section);
    return () => observer.disconnect();
  }, []);

  const onReady = useCallback(() => setStatus("ready"), []);
  const onError = useCallback((error: unknown) => {
    console.warn("[explode] se muestra el poster:", error);
    setStatus("error");
  }, []);

  return (
    <section
      ref={sectionRef}
      aria-labelledby="explode-title"
      data-status={status}
      className="explode-track relative"
    >
      <div className="sticky top-0 h-svh overflow-hidden">
        <div className="absolute inset-0">
          <Poster
            state="assembled"
            className={`absolute inset-0 h-full w-full object-contain transition-opacity duration-500 ${
              status === "ready" ? "opacity-0" : "opacity-100"
            }`}
          />
          {near && status !== "error" && (
            <ExplodeScene store={store} onReady={onReady} onError={onError} />
          )}
        </div>

        <div
          data-explode-hud
          className="pointer-events-none absolute inset-0 flex flex-col justify-between px-6 py-6 sm:px-10 sm:py-8"
        >
          <div className="flex flex-col gap-5 sm:gap-8">
            <h2
              id="explode-title"
              className="font-mono text-xs uppercase tracking-[0.18em] text-rebar"
            >
              <span className="text-signal">{"//"}</span> angus ranch · capas
            </h2>
            <div className="flex flex-col gap-2" aria-hidden="true">
              <p className="font-display text-[clamp(1.35rem,3.4vw,2.6rem)] leading-none tracking-[-0.03em]">
                <span className="text-signal">(</span>
                <span ref={labelRef}>{STEPS[0].label}</span>
                <span className="text-signal">)</span>
              </p>
              <p
                ref={noteRef}
                className="max-w-[28ch] font-mono text-xs text-rebar sm:text-sm"
              >
                {STEPS[0].note}
              </p>
            </div>
            <div className="hidden sm:block">
              <LayerList activeRef={itemsRef} />
            </div>
          </div>

          <div className="relative min-h-[2.5em] font-mono text-sm sm:text-base">
            {CAPTIONS.map((caption, i) => (
              <p
                key={caption.text}
                ref={(el) => {
                  captionsRef.current[i] = el;
                }}
                className="absolute bottom-0 left-0 max-w-[32ch]"
                style={{ opacity: i === 0 ? 1 : 0 }}
              >
                <span className="text-signal">{"//"}</span> {caption.text}
              </p>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function ExplodeSection() {
  const reduced = usePrefersReducedMotion();
  return reduced ? <StaticExplode /> : <ScrollExplode />;
}
