/** Monti: el orientador de Assambl. Un montante de madera con casco de obra.
 *  Es deliberadamente simple (pocas formas, dos colores de marca) para que se lea chico,
 *  y tiene tres estados: quieto (respira y parpadea), pensando y hablando. */

export type AnimoMonti = "quieto" | "pensando" | "hablando" | "contento";

export default function Monti({ animo = "quieto", tamano = 72 }: { animo?: AnimoMonti; tamano?: number }) {
  const mirando = animo === "pensando" ? -2.5 : 0;
  return (
    <svg
      width={tamano}
      height={tamano * 1.25}
      viewBox="0 0 64 80"
      className={`monti monti-${animo}`}
      role="img"
      aria-label={`Monti, ${animo}`}
    >
      <g className="monti-cuerpo">
        {/* Sombra */}
        <ellipse cx="32" cy="77" rx="14" ry="2.5" fill="var(--ink)" opacity="0.12" className="monti-sombra" />
        {/* Montante: tabla de 2 × 4 vista de frente */}
        <rect x="18" y="16" width="28" height="58" rx="3" fill="#d9a066" stroke="var(--ink)" strokeWidth="2" />
        {/* Veta */}
        <path d="M24 22 q3 14 0 26 q-3 12 1 22" fill="none" stroke="#b87a3d" strokeWidth="1.2" opacity="0.8" />
        <path d="M40 20 q-2 10 1 20 q3 12 -1 30" fill="none" stroke="#b87a3d" strokeWidth="1.2" opacity="0.6" />
        <ellipse cx="38" cy="58" rx="2.4" ry="3.4" fill="none" stroke="#b87a3d" strokeWidth="1" opacity="0.7" />
        {/* Brazos */}
        <path d="M18 46 q-8 2 -9 10" fill="none" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" className="monti-brazo-i" />
        <path d="M46 46 q8 -2 10 -10" fill="none" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" className="monti-brazo-d" />
        {/* Ojos */}
        <g className="monti-ojos" transform={`translate(0 ${mirando})`}>
          <ellipse cx="27" cy="34" rx="3" ry="3.6" fill="var(--ink)" />
          <ellipse cx="37" cy="34" rx="3" ry="3.6" fill="var(--ink)" />
          <circle cx="28" cy="33" r="1" fill="#fff" />
          <circle cx="38" cy="33" r="1" fill="#fff" />
        </g>
        {/* Boca */}
        {animo === "hablando" ? (
          <ellipse cx="32" cy="43" rx="3" ry="2" fill="var(--ink)" className="monti-boca-habla" />
        ) : animo === "pensando" ? (
          <path d="M29 44 h6" stroke="var(--ink)" strokeWidth="1.8" strokeLinecap="round" />
        ) : (
          <path d="M28 42 q4 4 8 0" fill="none" stroke="var(--ink)" strokeWidth="1.8" strokeLinecap="round" />
        )}
        {/* Casco */}
        <path d="M15 17 q0 -13 17 -13 q17 0 17 13 z" fill="var(--signal)" stroke="var(--ink)" strokeWidth="2" />
        <rect x="12" y="15" width="40" height="4" rx="2" fill="var(--signal)" stroke="var(--ink)" strokeWidth="2" />
        <path d="M32 4 v11" stroke="var(--ink)" strokeWidth="1.5" opacity="0.5" />
      </g>
      {animo === "pensando" && (
        <g className="monti-puntos" fill="var(--rebar)">
          <circle cx="52" cy="10" r="2" />
          <circle cx="57" cy="5" r="2.5" />
          <circle cx="62" cy="1" r="1.5" />
        </g>
      )}
    </svg>
  );
}
