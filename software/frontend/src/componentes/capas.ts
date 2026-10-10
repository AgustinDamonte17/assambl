/** Secuencia de capas. El orden se ajusta a medida que se construyen: lo que resulta de las decisiones de
 *  la casa (instalaciones y cimientos) va al final. `id` es estable; el número que se ve es la posición. */
export const CAPAS = [
  { id: "terreno", nombre: "Terreno", nivel: "núcleo" },
  { id: "casa", nombre: "Casa · planta, volumen e interior", nivel: "núcleo" },
  { id: "estructura", nombre: "Estructura woodframe", nivel: "núcleo" },
  { id: "osb", nombre: "OSB", nivel: "núcleo" },
  { id: "membrana", nombre: "Membrana exterior", nivel: "núcleo" },
  { id: "rastreles", nombre: "Rastreles de siding", nivel: "hook" },
  { id: "siding", nombre: "Siding", nivel: "hook" },
  { id: "aislante", nombre: "Aislante de paredes", nivel: "hook" },
  { id: "roofing", nombre: "Roofing", nivel: "núcleo" },
  { id: "canaletas", nombre: "Canaletas", nivel: "hook" },
  { id: "durlock", nombre: "Durlock", nivel: "hook" },
  { id: "terminaciones", nombre: "Terminaciones", nivel: "hook" },
  { id: "plomeria", nombre: "Plomería", nivel: "hook" },
  { id: "electrico", nombre: "Eléctrico", nivel: "hook" },
  { id: "cimientos", nombre: "Cimientos", nivel: "núcleo" },
] as const;

/** Número de capa en la secuencia actual («01», «02»…). */
export function numeroCapa(id: (typeof CAPAS)[number]["id"]): string {
  return String(CAPAS.findIndex((c) => c.id === id) + 1).padStart(2, "0");
}
