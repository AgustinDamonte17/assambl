/** Espejo TypeScript de las operaciones del dominio (backend/assambl/modelo/operaciones.py).
 *  El backend valida y aplica; acá solo se describen para tiparlas. */

import type { AnalisisLote, Estado, Proyecto, Punto } from "./proyecto";

export type Operacion =
  | { tipo: "renombrar_proyecto"; nombre: string }
  | { tipo: "definir_ubicacion"; lat: number; lon: number; direccion?: string | null; fuente: string }
  | { tipo: "definir_margen"; margen_m: number }
  | { tipo: "definir_lote"; vertices: Punto[] }
  | { tipo: "definir_retiros"; frente_m: number; fondo_m: number; laterales_m: number }
  | { tipo: "vincular_escena"; ref: string };

export type Autor = "usuario" | "asistente" | "sistema";

export interface RegistroOperacion {
  id: string;
  proyecto_id: string;
  operacion: Operacion | { tipo: "deshacer"; deshace: string };
  autor: Autor;
  fecha: string;
  cambios: string[];
  estado_antes: Estado;
  estado_despues: Estado;
  avisos: string[];
}

export interface ResultadoOperacion {
  proyecto: Proyecto;
  registro: RegistroOperacion;
  analisis_lote: AnalisisLote | null;
}
