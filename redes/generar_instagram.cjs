// Genera las piezas de Instagram de Assambl en redes/instagram.
//   node redes/generar_instagram.cjs
//
// Usa el puppeteer instalado en software/node_modules y las fuentes de Google Fonts.

const fs = require("fs");
const path = require("path");
const puppeteer = require(path.join(__dirname, "..", "software", "node_modules", "puppeteer"));

const SALIDA = path.join(__dirname, "instagram", "v2");

const C = {
  ink: "#111111",
  concrete: "#E8E6E1",
  signal: "#FF4F1F",
  rebar: "#7A7A78",
  rebarDark: "#8B8B88",
  resolved: "#15803D",
  resolvedDark: "#2FD968",
};

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&display=block');
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
.lienzo { position: relative; overflow: hidden; font-family: 'IBM Plex Mono', monospace; }
.oscuro { background: ${C.ink}; color: ${C.concrete}; --rebar: ${C.rebarDark}; --ok: ${C.resolvedDark}; --fg: ${C.concrete}; --bg: ${C.ink}; }
.claro { background: ${C.concrete}; color: ${C.ink}; --rebar: ${C.rebar}; --ok: ${C.resolved}; --fg: ${C.ink}; --bg: ${C.concrete}; }
.disp { font-family: 'Archivo Black', sans-serif; letter-spacing: -0.045em; line-height: 0.92; font-weight: 400; }
.s { color: ${C.signal}; }
.r { color: var(--rebar); }
.ok { color: var(--ok); }
.kw { color: ${C.signal}; font-style: italic; }
.arg { font-family: 'IBM Plex Mono', monospace; font-size: 0.62em; font-weight: 400; letter-spacing: 0; }
.cursor { display: inline-block; background: ${C.signal}; width: 0.16em; height: 0.72em; margin-left: 0.03em; vertical-align: baseline; }
[data-fit] { display: inline-block; white-space: nowrap; }
.cab, .pie { position: absolute; left: 80px; right: 80px; display: flex; justify-content: space-between; align-items: center;
  font-size: 22px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--rebar); }
.cab { top: 72px; }
.pie { bottom: 72px; text-transform: none; letter-spacing: 0; font-size: 26px; }
.centro { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.bloque { position: absolute; left: 80px; right: 80px; }
.mono { font-family: 'IBM Plex Mono', monospace; }
`;

const logo = ({ arg = "", cursor = false, resolved = false, fit, size } = {}) => `
  <div class="disp" ${fit ? `data-fit="${fit}"` : ""} style="${size ? `font-size:${size}px` : ""}">ASSAMBL<span class="s">(</span><span class="arg ${resolved ? "ok" : ""}">${arg}</span>${cursor ? '<span class="cursor" style="width:0.07em;height:0.6em;margin:0 0.07em"></span>' : ""}<span class="s">)</span></div>`;

const cabecera = (derecha = "// 2027") => `
  <div class="cab"><span>assambl</span><span><span class="s">${derecha.startsWith("//") ? "//" : ""}</span>${derecha.replace(/^\/\//, "")}</span></div>`;

const MARCA_A = "M6 50 L18 14 H27 L39 50 H30.5 L28.2 42.5 H16.8 L14.5 50 Z M18.8 35.5 H26.2 L22.5 23.2 Z";
const MARCA_P1 = "M46 20 C42 26 42 38 46 44 L42.5 46 C37.5 39 37.5 25 42.5 18 Z";
const MARCA_P2 = "M50 20 C54 26 54 38 50 44 L53.5 46 C58.5 39 58.5 25 53.5 18 Z";

// ---------- Piezas ----------

function perfil(tema = "oscuro") {
  return {
    ancho: 1080,
    alto: 1080,
    tema,
    html: `
      <div class="centro">
        <svg width="700" height="700" viewBox="0 0 64 64">
          <path fill="${tema === "oscuro" ? C.concrete : C.ink}" d="${MARCA_A}"/>
          <path fill="${C.signal}" d="${MARCA_P1}"/>
          <path fill="${C.signal}" d="${MARCA_P2}"/>
        </svg>
      </div>`,
  };
}

function postLogo() {
  return {
    tema: "oscuro",
    html: `
      ${cabecera("// 2027")}
      <div class="centro" style="gap:44px">
        ${logo({ fit: 900 })}
        <div class="mono r" style="font-size:34px">Vos diseñás. Assambl resuelve.</div>
      </div>
      <div class="pie"><span class="r">software de diseño</span><span class="r">assambl.com</span></div>`,
  };
}

function postLanzamiento() {
  return {
    tema: "claro",
    html: `
      ${cabecera("waitlist")}
      <div class="bloque" style="top:250px">
        <div class="disp s" style="font-size:220px">//</div>
        <div class="disp" data-fit="920" style="margin-top:10px">lanzamiento</div>
        <div class="disp" style="font-size:330px;margin-top:6px">2027</div>
      </div>
      <div class="bloque mono" style="bottom:170px;font-size:44px">
        <span class="kw">from</span> waitlist <span class="kw">import</span> <span class="ok">abierta</span><span class="cursor" style="height:0.8em"></span>
      </div>
      <div class="pie"><span>→ assambl.com</span><span class="r">ASSAMBL<span class="s">()</span></span></div>`,
  };
}

function secuencia() {
  const pasos = [
    "idea", "diseño", "terreno", "planos", "modelo3d",
    "cómputo", "lista_de_corte", "paneles", "montaje",
  ];
  const n = pasos.length;
  const lineas = pasos
    .map((p, i) => {
      const op = (0.18 + (0.62 * i) / (n - 1)).toFixed(2);
      return `<div style="opacity:${op}">ASSAMBL<span class="s">(</span><span class="arg">${p}</span><span class="s">)</span></div>`;
    })
    .join("");
  return {
    tema: "oscuro",
    html: `
      ${cabecera("// de la idea a la obra")}
      <div class="bloque disp" style="top:170px;font-size:66px;line-height:1.16">
        ${lineas}
        <div style="margin-top:14px;font-size:98px">ASSAMBL<span class="s">(</span><span class="arg ok">casa</span><span class="s">)</span> <span class="mono ok" style="font-size:0.5em;letter-spacing:0">✓</span></div>
      </div>
      <div class="pie"><span class="r">un solo modelo, todas las salidas</span><span class="r">assambl.com</span></div>`,
  };
}

function queEs() {
  return {
    tema: "claro",
    html: `
      ${cabecera("// qué es")}
      <div class="bloque" style="top:210px">
        <div class="disp" style="font-size:150px">¿Qué es</div>
        <div class="disp" style="font-size:150px">Assambl<span class="s">()</span>?</div>
      </div>
      <div class="bloque mono" style="top:620px;font-size:38px;line-height:1.5">
        Software para diseñar viviendas en <b style="font-weight:500">woodframe</b>, <span class="s">from the ground up</span>: del terreno al circuito eléctrico.
        <div class="r" style="margin-top:36px">Un solo modelo del proyecto del que salen planos, vistas, cantidades e instructivos de montaje.</div>
      </div>
      <div class="pie"><span><span class="s">//</span> Vos diseñás. Assambl resuelve.</span></div>`,
  };
}

function capas() {
  const nombres = [
    "terreno", "cimientos", "estructura", "aislante", "siding",
    "techo", "interior", "terminaciones", "plomería", "eléctrico",
  ];
  const col = (desde) =>
    nombres
      .slice(desde, desde + 5)
      .map((nombre, i) => `<div><span class="s">${String(desde + i + 1).padStart(2, "0")}</span> ${nombre}</div>`)
      .join("");
  return {
    tema: "oscuro",
    html: `
      ${cabecera("// capas")}
      <div class="bloque" style="top:200px">
        <div class="disp" style="font-size:168px">10 capas<span class="s">.</span></div>
        <div class="disp" style="font-size:168px">1 modelo<span class="s">.</span></div>
      </div>
      <div class="bloque mono" style="top:660px;display:grid;grid-template-columns:1fr 1fr;gap:0 40px;font-size:44px;line-height:1.75">
        <div>${col(0)}</div><div>${col(5)}</div>
      </div>
      <div class="pie"><span class="r">cada pieza con su ID, en su capa</span><span class="r">assambl.com</span></div>`,
  };
}

function curvasDeNivel() {
  const cx = 820, cy = 360;
  const trazos = [];
  for (let k = 1; k <= 26; k++) {
    const r0 = 38 * k;
    const pts = [];
    for (let j = 0; j <= 180; j++) {
      const t = (j / 180) * Math.PI * 2;
      const r = r0 * (1 + 0.13 * Math.sin(3 * t + k * 0.35) + 0.07 * Math.sin(5 * t - k * 0.2) + 0.04 * Math.cos(7 * t + k));
      pts.push(`${(cx + r * Math.cos(t) * 1.25).toFixed(1)},${(cy + r * Math.sin(t)).toFixed(1)}`);
    }
    const mayor = k % 5 === 0;
    trazos.push(
      `<polyline points="${pts.join(" ")}" fill="none" stroke="${C.rebar}" stroke-opacity="${mayor ? 0.75 : 0.38}" stroke-width="${mayor ? 2.4 : 1.3}"/>`,
    );
  }
  return trazos.join("");
}

function terreno() {
  const lote = [[300, 520], [610, 440], [700, 760], [380, 850]];
  const vertices = lote
    .map(([x, y]) => `<rect x="${x - 11}" y="${y - 11}" width="22" height="22" fill="${C.concrete}" stroke="${C.signal}" stroke-width="4"/>`)
    .join("");
  return {
    tema: "claro",
    html: `
      <svg width="1080" height="1350" style="position:absolute;inset:0">
        ${curvasDeNivel()}
        <polygon points="${lote.map((p) => p.join(",")).join(" ")}" fill="${C.signal}" fill-opacity="0.14" stroke="${C.signal}" stroke-width="4"/>
        ${vertices}
        <g transform="translate(960,230)" font-family="IBM Plex Mono" font-size="24" fill="${C.ink}">
          <polygon points="0,-44 14,0 0,-10 -14,0" fill="${C.ink}"/>
          <text x="0" y="36" text-anchor="middle">N</text>
        </g>
        <g transform="translate(80,190)" font-family="IBM Plex Mono" font-size="22" fill="${C.rebar}">
          <line x1="0" y1="0" x2="200" y2="0" stroke="${C.ink}" stroke-width="3"/>
          <line x1="0" y1="-10" x2="0" y2="10" stroke="${C.ink}" stroke-width="3"/>
          <line x1="200" y1="-10" x2="200" y2="10" stroke="${C.ink}" stroke-width="3"/>
          <text x="0" y="40">0</text><text x="200" y="40" text-anchor="middle">20 m</text>
        </g>
        <text x="${lote[1][0] + 30}" y="${lote[1][1] - 20}" font-family="IBM Plex Mono" font-size="24" fill="${C.ink}">lote 01 · 612 m²</text>
      </svg>
      ${cabecera("-31.42, -64.19")}
      <div class="bloque" style="bottom:180px">
        ${logo({ arg: "terreno", size: 112 })}
        <div class="mono r" style="font-size:32px;margin-top:26px;line-height:1.45">Todo empieza en el lote real:<br>relieve, sol, viento y clima.</div>
      </div>
      <div class="pie"><span class="r">capa 01</span><span class="r">assambl.com</span></div>`,
  };
}

function woodframe() {
  const esc = 210; // px por metro
  const x0 = 140, y0 = 230;
  const L = 3.6, H = 2.44, e = 0.045 * esc;
  const W = L * esc, Hp = H * esc;
  const v = { desde: 1.2, hasta: 2.4, alfeizar: 0.9, dintel: 2.1 };
  const trazo = `fill="none" stroke="${C.concrete}" stroke-width="2.4"`;
  const piezas = [];
  piezas.push(`<rect x="${x0}" y="${y0 + Hp - e}" width="${W}" height="${e}" ${trazo}/>`);
  piezas.push(`<rect x="${x0}" y="${y0}" width="${W}" height="${e}" ${trazo}/>`);
  piezas.push(`<rect x="${x0}" y="${y0 + e}" width="${W}" height="${e}" ${trazo}/>`);
  const yDintel = y0 + (H - v.dintel) * esc;
  const yAlf = y0 + (H - v.alfeizar) * esc;
  const xa = x0 + v.desde * esc, xb = x0 + v.hasta * esc;
  for (let m = 0; m <= L + 1e-6; m += 0.4) {
    const x = Math.min(x0 + m * esc, x0 + W - e) - (m > 0 && m < L - 1e-6 ? e / 2 : 0);
    const cx = x + e / 2;
    if (cx > xa && cx < xb) {
      piezas.push(`<rect x="${x}" y="${y0 + 2 * e}" width="${e}" height="${yDintel - 2 * e - y0 - 1.5 * e}" ${trazo}/>`);
      piezas.push(`<rect x="${x}" y="${yAlf + e}" width="${e}" height="${y0 + Hp - e - yAlf - e}" ${trazo}/>`);
    } else {
      piezas.push(`<rect x="${x}" y="${y0 + 2 * e}" width="${e}" height="${Hp - 3 * e}" ${trazo}/>`);
    }
  }
  piezas.push(`<rect x="${xa - e}" y="${yDintel}" width="${e}" height="${y0 + Hp - e - yDintel}" stroke="${C.signal}" stroke-width="2.4" fill="none"/>`);
  piezas.push(`<rect x="${xb}" y="${yDintel}" width="${e}" height="${y0 + Hp - e - yDintel}" stroke="${C.signal}" stroke-width="2.4" fill="none"/>`);
  piezas.push(`<rect x="${xa - e}" y="${yDintel - 1.5 * e}" width="${xb - xa + 2 * e}" height="${1.5 * e}" fill="${C.signal}" fill-opacity="0.2" stroke="${C.signal}" stroke-width="2.4"/>`);
  piezas.push(`<rect x="${xa}" y="${yAlf}" width="${xb - xa}" height="${e}" ${trazo}/>`);

  const cota = (x1, x2, y, texto) => `
    <line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${C.signal}" stroke-width="2"/>
    <line x1="${x1}" y1="${y - 12}" x2="${x1}" y2="${y + 12}" stroke="${C.signal}" stroke-width="2"/>
    <line x1="${x2}" y1="${y - 12}" x2="${x2}" y2="${y + 12}" stroke="${C.signal}" stroke-width="2"/>
    <text x="${(x1 + x2) / 2}" y="${y - 14}" text-anchor="middle" font-family="IBM Plex Mono" font-size="22" fill="${C.signal}">${texto}</text>`;
  const yCota = y0 + Hp + 60;
  return {
    tema: "oscuro",
    html: `
      ${cabecera("// woodframe")}
      <svg width="1080" height="1350" style="position:absolute;inset:0">
        ${piezas.join("")}
        ${cota(x0, x0 + 0.4 * esc, y0 - 40, "400")}
        ${cota(x0, x0 + W, yCota, "3600")}
        <g transform="translate(${x0 + W + 44},${y0 + Hp / 2}) rotate(-90)">
          <line x1="${-Hp / 2}" y1="0" x2="${Hp / 2}" y2="0" stroke="${C.signal}" stroke-width="2"/>
          <line x1="${-Hp / 2}" y1="-12" x2="${-Hp / 2}" y2="12" stroke="${C.signal}" stroke-width="2"/>
          <line x1="${Hp / 2}" y1="-12" x2="${Hp / 2}" y2="12" stroke="${C.signal}" stroke-width="2"/>
          <text x="0" y="-14" text-anchor="middle" font-family="IBM Plex Mono" font-size="22" fill="${C.signal}">2440</text>
        </g>
        <text x="${xa + (xb - xa) / 2}" y="${yDintel - 1.5 * e - 16}" text-anchor="middle" font-family="IBM Plex Mono" font-size="20" fill="${C.rebarDark}">dintel</text>
        <text x="${x0 + 0.8 * esc + e}" y="${y0 + Hp * 0.55}" font-family="IBM Plex Mono" font-size="20" fill="${C.rebarDark}" transform="rotate(-90 ${x0 + 0.8 * esc + e + 30} ${y0 + Hp * 0.55})">montante 45 × 95</text>
      </svg>
      <div class="bloque" style="top:850px">
        <div class="disp" style="font-size:80px;line-height:1">Cada pieza,<br>con la medida<br>que se compra<span class="s">.</span></div>
        <div class="mono r" style="font-size:30px;margin-top:28px;line-height:1.45">Escuadrías reales, placas de 1,22 × 2,44 m,<br>cortes y desperdicio calculados.</div>
      </div>
      <div class="pie" style="justify-content:flex-end"><span class="r">assambl.com</span></div>`,
  };
}

function cambio() {
  const filas = [
    ["platea", "recalculada"],
    ["montantes", "+2 piezas"],
    ["osb", "+1 placa"],
    ["membrana", "+2,6 m²"],
    ["cubierta", "ajustada"],
    ["planos", "actualizados"],
  ];
  return {
    tema: "claro",
    html: `
      ${cabecera("// un modelo")}
      <div class="bloque" style="top:200px">
        <div class="disp" style="font-size:100px">Movés un muro<span class="s">.</span></div>
        <div class="disp" style="font-size:100px;margin-top:8px">Assambl mueve<br>el resto<span class="s">.</span></div>
      </div>
      <div class="bloque mono" style="top:590px;font-size:36px;line-height:1.75;border-top:2px solid ${C.ink};padding-top:36px">
        <div style="color:#B42318">- muro_03.largo = 4.20</div>
        <div class="ok">+ muro_03.largo = 4.80</div>
        <div style="height:18px"></div>
        ${filas
          .map(
            ([capa, estado]) =>
              `<div style="display:flex"><span class="s" style="width:56px">→</span><span style="width:300px">${capa}</span><span class="r" style="flex:1">${estado}</span><span class="ok">✓</span></div>`,
          )
          .join("")}
      </div>
      <div class="pie"><span class="r">los cambios se propagan a cada capa</span></div>`,
  };
}

function waitlist() {
  return {
    tema: "oscuro",
    html: `
      ${cabecera("// lanzamiento 2027")}
      <div class="bloque" style="top:300px">
        <div class="disp" style="font-size:200px">Waitlist</div>
        <div class="disp" style="font-size:200px">abierta<span class="s">.</span></div>
      </div>
      <div class="bloque mono" style="top:760px;font-size:40px;line-height:1.7">
        <div class="r"><span class="s">//</span> sé de los primeros en usar Assambl</div>
        <div style="margin-top:30px"><span class="kw">try</span>: open assambl.com<span class="cursor" style="height:0.8em"></span></div>
      </div>
      <div class="pie"><span class="r">ASSAMBL<span class="s">()</span></span><span class="r">link en bio ↑</span></div>`,
  };
}

const PIEZAS = [
  ["01_perfil", () => perfil("oscuro")],
  ["01b_perfil_claro", () => perfil("claro")],
  ["02_post1_logo", postLogo],
  ["03_post1_lanzamiento_2027", postLanzamiento],
  ["04_de_la_idea_a_la_casa", secuencia],
  ["05_que_es_assambl", queEs],
  ["06_10_capas", capas],
  ["07_terreno", terreno],
  ["08_woodframe", woodframe],
  ["09_un_modelo", cambio],
  ["10_waitlist_abierta", waitlist],
];

function documento({ ancho = 1080, alto = 1350, tema, html }) {
  return `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>${CSS}</style></head>
  <body><div class="lienzo ${tema}" style="width:${ancho}px;height:${alto}px">${html}</div></body></html>`;
}

async function main() {
  fs.mkdirSync(SALIDA, { recursive: true });
  const navegador = await puppeteer.launch();
  try {
    for (const [nombre, crear] of PIEZAS) {
      const pieza = crear();
      const ancho = pieza.ancho ?? 1080;
      const alto = pieza.alto ?? 1350;
      const pagina = await navegador.newPage();
      await pagina.setViewport({ width: ancho, height: alto, deviceScaleFactor: 1 });
      await pagina.setContent(documento(pieza), { waitUntil: "load" });
      await pagina.evaluate(async () => {
        await Promise.all([
          document.fonts.load("40px 'Archivo Black'"),
          document.fonts.load("40px 'IBM Plex Mono'"),
          document.fonts.load("500 40px 'IBM Plex Mono'"),
          document.fonts.load("italic 40px 'IBM Plex Mono'"),
        ]);
        await document.fonts.ready;
        for (const el of document.querySelectorAll("[data-fit]")) {
          el.style.fontSize = "100px";
          el.style.fontSize = `${(100 * Number(el.dataset.fit)) / el.scrollWidth}px`;
        }
      });
      const fuentesOk = await pagina.evaluate(
        () => document.fonts.check("40px 'Archivo Black'") && document.fonts.check("40px 'IBM Plex Mono'"),
      );
      if (!fuentesOk) throw new Error(`Fuentes no cargadas en ${nombre}`);
      const archivo = path.join(SALIDA, `${nombre}.png`);
      await pagina.screenshot({ path: archivo, clip: { x: 0, y: 0, width: ancho, height: alto } });
      await pagina.close();
      console.log("ok", path.relative(process.cwd(), archivo));
    }
  } finally {
    await navegador.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
