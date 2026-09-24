import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import {
  ETIQUETA_ESTADO,
  ETIQUETA_NATURALEZA,
  type Estado,
  type EstadoFuente,
  type Fuente,
  type Naturaleza,
} from "../modelo/proyecto";

export function Boton({
  primario,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { primario?: boolean }) {
  const base = "px-3 py-1.5 text-xs uppercase tracking-wide border disabled:opacity-40 disabled:cursor-not-allowed";
  const estilo = primario
    ? "bg-signal border-signal text-ink hover:bg-ink hover:text-concrete hover:border-ink"
    : "bg-transparent border-ink/40 text-ink hover:border-ink";
  return <button className={`${base} ${estilo} ${className}`} {...props} />;
}

export function Campo({
  etiqueta,
  sufijo,
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { etiqueta?: string; sufijo?: string }) {
  return (
    <label className={`flex flex-col gap-1 ${className}`}>
      {etiqueta && <span className="text-[11px] uppercase tracking-wide text-rebar">{etiqueta}</span>}
      <span className="flex items-baseline gap-1">
        <input
          className="w-full bg-concrete-2 border border-line px-2 py-1 text-ink focus:outline-none focus:border-signal"
          {...props}
        />
        {sufijo && <span className="text-rebar text-xs">{sufijo}</span>}
      </span>
    </label>
  );
}

export function Seccion({ titulo, children, accion }: { titulo: string; children: ReactNode; accion?: ReactNode }) {
  return (
    <section className="border-t border-line pt-3 mt-3 first:border-t-0 first:pt-0 first:mt-0">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[11px] uppercase tracking-widest text-rebar">{titulo}</h3>
        {accion}
      </div>
      {children}
    </section>
  );
}

const COLOR_ESTADO: Record<Estado, string> = {
  propuesto: "border-rebar text-rebar",
  comprobado_por_reglas: "border-resolved text-resolved",
  pendiente_datos: "border-rebar text-rebar",
  pendiente_calculo: "border-warn text-warn",
  pendiente_revision: "border-warn text-warn",
  revisado: "border-resolved text-resolved bg-resolved/10",
  desactualizado: "border-signal text-signal",
};

export function Etiqueta({ estado }: { estado: Estado }) {
  return (
    <span className={`inline-block border px-1.5 py-px text-[10px] uppercase tracking-wide ${COLOR_ESTADO[estado]}`}>
      {ETIQUETA_ESTADO[estado]}
    </span>
  );
}

const COLOR_FUENTE: Record<EstadoFuente, string> = {
  ok: "border-resolved text-resolved",
  parcial: "border-warn text-warn",
  pendiente_datos: "border-signal text-signal",
};

export function EtiquetaFuente({ estado }: { estado: EstadoFuente }) {
  return (
    <span className={`inline-block border px-1.5 py-px text-[10px] uppercase tracking-wide ${COLOR_FUENTE[estado]}`}>
      {estado === "pendiente_datos" ? "sin datos" : estado}
    </span>
  );
}

export function Dato({ etiqueta, valor, sufijo }: { etiqueta: string; valor: ReactNode; sufijo?: string }) {
  return (
    <div className="flex justify-between gap-2 py-0.5">
      <span className="text-rebar">{etiqueta}</span>
      <span className="text-right">
        {valor}
        {sufijo && <span className="text-rebar ml-1">{sufijo}</span>}
      </span>
    </div>
  );
}

/* Un dato medido, uno estimado a escala regional y uno calculado no valen lo mismo.
   La etiqueta de naturaleza los distingue en todos lados. */
const COLOR_NATURALEZA: Record<Naturaleza, string> = {
  medicion_satelital: "border-resolved text-resolved",
  reanalisis_regional: "border-warn text-warn",
  calculo_local: "border-rebar text-rebar",
  provisional: "border-signal text-signal bg-signal/10",
};

export function EtiquetaNaturaleza({ naturaleza }: { naturaleza: Naturaleza }) {
  return (
    <span className={`inline-block border px-1.5 py-px text-[10px] uppercase tracking-wide ${COLOR_NATURALEZA[naturaleza]}`}>
      {ETIQUETA_NATURALEZA[naturaleza]}
    </span>
  );
}

export function Aviso({ children, fuerte }: { children: ReactNode; fuerte?: boolean }) {
  return (
    <p
      className={`text-[10px] leading-snug border-l-2 pl-2 py-0.5 ${
        fuerte ? "border-signal text-signal" : "border-warn text-rebar"
      }`}
    >
      {children}
    </p>
  );
}

/** Ficha de procedencia de una capa: qué la produjo, con qué resolución y con qué reservas. */
export function FichaFuente({ fuente }: { fuente: Fuente }) {
  return (
    <li className="leading-snug border-t border-line pt-2 first:border-t-0 first:pt-0">
      <div className="flex items-start justify-between gap-2">
        <span className="flex-1">{fuente.nombre}</span>
        <EtiquetaNaturaleza naturaleza={fuente.naturaleza} />
      </div>
      <div className="text-[10px] text-rebar mt-0.5">Resolución: {fuente.resolucion}</div>
      {fuente.detalle && <div className="text-[10px] text-rebar">{fuente.detalle}</div>}
      <div className="text-[10px] text-rebar">{fuente.licencia}</div>
    </li>
  );
}
