/**
 * Progreso de scroll compartido entre la sección HTML y la escena 3D sin pasar
 * por estado de React: un valor mutable y suscriptores que se notifican una vez
 * por frame de scroll/resize.
 */
export type ProgressStore = {
  value: number;
  subscribe: (listener: () => void) => () => void;
  set: (value: number) => void;
};

export function createProgressStore(initial = 0): ProgressStore {
  const listeners = new Set<() => void>();
  const store: ProgressStore = {
    value: initial,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    set(value) {
      if (value === store.value) return;
      store.value = value;
      listeners.forEach((l) => l());
    },
  };
  return store;
}

/** 0 cuando el tope de la sección toca el tope del viewport; 1 cuando su base toca la base. */
export function measureProgress(section: HTMLElement): number {
  const rect = section.getBoundingClientRect();
  const travel = rect.height - window.innerHeight;
  if (travel <= 0) return 0;
  return Math.min(1, Math.max(0, -rect.top / travel));
}

export const clamp01 = (t: number) => Math.min(1, Math.max(0, t));

/** 0→1 dentro de [a, b]. */
export const segment = (p: number, a: number, b: number) =>
  clamp01((p - a) / (b - a));
