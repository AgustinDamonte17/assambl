/** La planta entera en un recuadro, sin edición: para mostrar una propuesta antes de abrirla en el editor. */

import type { AnalisisPlanta, Casa } from "../../modelo/casa";
import { extension } from "../../modelo/casa";
import DibujoPlanta, { encuadrar, Tramas } from "./DibujoPlanta";

interface Props {
  casa: Casa;
  analisis: AnalisisPlanta | null;
  ancho?: number;
  alto?: number;
  verEstados?: boolean;
  className?: string;
}

export default function MiniPlanta({ casa, analisis, ancho = 340, alto = 220, verEstados = true, className = "" }: Props) {
  const ext = extension(casa);
  if (!ext) return null;
  const vista = encuadrar(ext, ancho, alto, 16);
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} width="100%" className={`block bg-concrete ${className}`}>
      <Tramas />
      <DibujoPlanta casa={casa} vista={vista} analisis={analisis} etiquetas={vista.escala > 22} verEstados={verEstados} />
    </svg>
  );
}
