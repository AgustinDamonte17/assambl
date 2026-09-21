// Genera PP_Fable_WF.html a partir del plan v0.1 y de los renders de Angus Ranch.
// Uso:  node build_pp_fable.cjs [--refresh]   (--refresh reprocesa las imágenes)
const fs = require('fs');
const path = require('path');
const os = require('os');
const root = __dirname;
const PW = 'C:/Users/adamonte/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const OUT = 'PP_Fable_WF.html';
const cacheDir = path.join(os.tmpdir(), 'pp_fable_assets');
const { esc, markdown, prepareAssets, chip, row, stat, fig, wallSvg, css, script } = require('./pp_shell.cjs');

const source = fs.readFileSync(path.join(root, 'Plan_de_negocios_Woodframe_v0.1.md'), 'utf8');

// ---------------------------------------------------------------- imágenes

// ---------------------------------------------------------------- helpers de contenido

const CHAPTERS = [
  { n: '01', name: 'Oportunidad', q: '¿Dónde se pierde el tiempo?', img: 'planta' },
  { n: '02', name: 'Producto', q: '¿Qué entregamos primero?', img: 'siding' },
  { n: '03', name: 'Tecnología', q: '¿Qué debe sobrevivir a la interfaz?', img: 'anclajes' },
  { n: '04', name: 'Mercado', q: '¿Contra qué competimos?', img: 'exterior' },
  { n: '05', name: 'Negocio', q: '¿Cuánto vale y cuánto cuesta?', img: 'despiece' },
  { n: '06', name: 'Ejecución', q: '¿Cómo decidimos avanzar?', img: 'interior' },
];

// SVG: matriz de segmentos
function matrixSvg() {
  const pts = [
    { x: 120, y: 310, l: 'Particular que diseña su casa', d: 'Baja recurrencia · alto acompañamiento' },
    { x: 290, y: 262, l: 'Desarrollista que terceriza', d: 'Compra, pero sus proyectistas deciden' },
    { x: 468, y: 208, l: 'Estudio woodframe', d: 'Documentación recurrente' },
    { x: 540, y: 170, l: 'Constructora con equipo técnico', d: 'Adapta modelos con frecuencia' },
    { x: 585, y: 62, l: 'Fabricante de paneles', d: 'Requiere detalle de fabricación' },
  ];
  let s = `<svg class="matrix" viewBox="0 0 680 400" role="img" aria-label="Segmentos de clientes ordenados por recurrencia de proyectos y profundidad de entrega">`;
  s += `<g class="axes"><line x1="60" y1="360" x2="660" y2="360"/><line x1="60" y1="360" x2="60" y2="20"/>`;
  s += `<text x="660" y="386" text-anchor="end">RECURRENCIA DE PROYECTOS →</text><text transform="translate(38 20) rotate(-90)" text-anchor="end">PROFUNDIDAD DE ENTREGA →</text></g>`;
  s += `<rect class="zone" x="420" y="128" width="228" height="128" rx="6"/><text class="zone-l" x="426" y="118">ENTRADA PROPUESTA</text>`;
  s += `<rect class="zone later" x="520" y="30" width="140" height="66" rx="6"/><text class="zone-l later" x="526" y="24">ETAPA POSTERIOR</text>`;
  for (const p of pts) {
    const hi = p.x > 420 && p.y > 128 && p.y < 256;
    s += `<g class="pt ${hi ? 'hi' : ''}"><circle cx="${p.x}" cy="${p.y}" r="${hi ? 9 : 7}"/><text x="${p.x + (p.x > 520 ? -16 : 16)}" y="${p.y - 6}" text-anchor="${p.x > 520 ? 'end' : 'start'}">${p.l}</text><text class="sub" x="${p.x + (p.x > 520 ? -16 : 16)}" y="${p.y + 12}" text-anchor="${p.x > 520 ? 'end' : 'start'}">${p.d}</text></g>`;
  }
  return s + '</svg>';
}

// SVG: embudo comercial
function funnelSvg() {
  const st = [[40, 'organizaciones calificadas contactadas'], [12, 'conversaciones sobre proyectos reales'], [5, 'candidatas para una prueba'], [3, 'pilotos activados']];
  const W = 1000, H = 320, bw = 150, gap = (W - 4 * bw) / 3, mid = 100, maxH = 170;
  let s = `<svg class="funnel" viewBox="0 0 ${W} ${H}" role="img" aria-label="Embudo: 40 organizaciones, 12 conversaciones, 5 candidatas, 3 pilotos">`;
  const hs = st.map(([n]) => Math.max(14, n / 40 * maxH));
  for (let i = 0; i < 3; i++) {
    const x1 = i * (bw + gap) + bw, x2 = x1 + gap;
    s += `<polygon class="link" points="${x1},${mid - hs[i] / 2} ${x2},${mid - hs[i + 1] / 2} ${x2},${mid + hs[i + 1] / 2} ${x1},${mid + hs[i] / 2}"/>`;
    const pct = Math.round(st[i + 1][0] / st[i][0] * 100);
    s += `<text class="pct" x="${(x1 + x2) / 2}" y="${mid + maxH / 2 + 30}" text-anchor="middle">${pct}% →</text>`;
  }
  st.forEach(([n, l], i) => {
    const x = i * (bw + gap);
    const words = l.split(' '), half = Math.ceil(words.length / 2);
    s += `<rect class="bar" x="${x}" y="${mid - hs[i] / 2}" width="${bw}" height="${hs[i]}"/>`;
    s += `<text class="num" x="${x}" y="${H - 50}">${n}</text><text class="lbl" x="${x}" y="${H - 26}">${words.slice(0, half).join(' ')}</text><text class="lbl" x="${x}" y="${H - 9}">${words.slice(half).join(' ')}</text>`;
  });
  return s + '</svg>';
}

// SVG: escenario a tres años
function yearsSvg() {
  const ing = [18, 144, 540], fix = [120, 240, 360], res = [-106.5, -124.8, 82.8];
  const W = 720, H = 400, x0 = 70, top = 24, bottom = 340, vmax = 600, vmin = -160;
  const y = v => top + (vmax - v) / (vmax - vmin) * (bottom - top);
  let s = `<svg class="years" viewBox="0 0 ${W} ${H}" role="img" aria-label="Ingresos 18, 144 y 540 mil; gastos fijos 120, 240 y 360 mil; resultado operativo −106,5, −124,8 y +82,8 mil dólares">`;
  for (const g of [600, 400, 200, 0]) s += `<line class="grid ${g === 0 ? 'zero' : ''}" x1="${x0}" y1="${y(g)}" x2="${W - 10}" y2="${y(g)}"/><text class="gl" x="${x0 - 10}" y="${y(g) + 4}" text-anchor="end">${g}</text>`;
  const gw = (W - 10 - x0) / 3;
  let pts = [];
  ing.forEach((v, i) => {
    const cx = x0 + gw * (i + .5);
    s += `<rect class="ing" x="${cx - 64}" y="${y(v)}" width="56" height="${y(0) - y(v)}"/>`;
    s += `<rect class="fix" x="${cx - 2}" y="${y(fix[i])}" width="56" height="${y(0) - y(fix[i])}"/>`;
    s += `<text class="vl" x="${cx - 36}" y="${y(v) - 8}" text-anchor="middle">${v}</text><text class="vl f" x="${cx + 26}" y="${y(fix[i]) - 8}" text-anchor="middle">${fix[i]}</text>`;
    s += `<text class="yr" x="${cx}" y="${H - 6}" text-anchor="middle">AÑO ${i + 1}</text>`;
    pts.push([cx, y(res[i])]);
  });
  s += `<polyline class="res" points="${pts.map(p => p.join(',')).join(' ')}"/>`;
  pts.forEach(([cx, cy], i) => { s += `<circle class="res ${res[i] < 0 ? 'neg' : 'pos'}" cx="${cx}" cy="${cy}" r="7"/><text class="rl ${res[i] < 0 ? 'neg' : 'pos'}" x="${cx + 14}" y="${cy + (res[i] < 0 ? 20 : -12)}">${res[i] > 0 ? '+' : '−'}${Math.abs(res[i]).toLocaleString('es-AR')}</text>`; });
  return s + '</svg>';
}

// SVG: punto de equilibrio
function breakevenSvg() {
  const W = 660, H = 360, x0 = 60, x1 = 630, yb = 310, yt = 30, N = 250, Vmax = 60;
  const X = n => x0 + n / N * (x1 - x0), Y = v => yb - v / Vmax * (yb - yt);
  const contrib = n => n * .205; const be = 30 / .205;
  let s = `<svg class="be" viewBox="0 0 ${W} ${H}" role="img" aria-label="Punto de equilibrio en 147 organizaciones: margen de contribución contra gastos fijos de 30 mil dólares mensuales">`;
  s += `<polygon class="loss" points="${X(0)},${Y(0)} ${X(0)},${Y(30)} ${X(be)},${Y(30)}"/>`;
  s += `<polygon class="gain" points="${X(be)},${Y(30)} ${X(N)},${Y(contrib(N))} ${X(N)},${Y(30)}"/>`;
  for (const g of [0, 20, 40, 60]) s += `<line class="grid" x1="${x0}" y1="${Y(g)}" x2="${x1}" y2="${Y(g)}"/><text class="gl" x="${x0 - 10}" y="${Y(g) + 4}" text-anchor="end">${g}k</text>`;
  for (const n of [0, 50, 100, 150, 200, 250]) s += `<text class="gl" x="${X(n)}" y="${yb + 22}" text-anchor="middle">${n}</text>`;
  s += `<line class="fixed" x1="${X(0)}" y1="${Y(30)}" x2="${X(N)}" y2="${Y(30)}"/><text class="ll" x="${X(0) + 8}" y="${Y(30) - 10}">GASTOS FIJOS · USD 30.000 / MES</text>`;
  s += `<line class="contrib" x1="${X(0)}" y1="${Y(0)}" x2="${X(N)}" y2="${Y(contrib(N))}"/><text class="ll w" x="${X(N) - 4}" y="${Y(contrib(N)) - 12}" text-anchor="end">MARGEN · USD 205 / ORG / MES</text>`;
  s += `<line class="drop" x1="${X(be)}" y1="${Y(30)}" x2="${X(be)}" y2="${yb}"/><circle class="pt" cx="${X(be)}" cy="${Y(30)}" r="8"/>`;
  s += `<text class="big" x="${X(be) + 18}" y="${Y(30) + 50}">147</text><text class="bl" x="${X(be) + 18}" y="${Y(30) + 70}">ORGANIZACIONES ACTIVAS · POR MES</text>`;
  s += `<text class="ax" x="${x1}" y="${H - 6}" text-anchor="end">ORGANIZACIONES PAGAS →</text>`;
  return s + '</svg>';
}

// ---------------------------------------------------------------- diapositivas
function buildSlides(img) {
  const S = [];
  const add = (o) => S.push(o);
  const divider = (c) => add({
    ch: c.n, kind: 'divider', title: c.name, cls: 'dark divider',
    body: `<div class="ghost">${c.n}</div><div class="div-copy"><p class="div-ch">CAPÍTULO ${c.n}</p><h2>${c.name}</h2><p class="div-q">${c.q}</p><p class="div-toc" data-toc="${c.n}"></p></div>${fig(img[c.img], '', '', 'div-img')}`
  });

  // 01 — Portada
  add({ ch: '00', kind: 'cover', title: 'Diseñar la casa. Resolver el sistema.', cls: 'dark cover', body:
    `<img class="cover-bg" src="${img.aerial}" alt=""><div class="cover-shade"></div>
     <div class="cover-copy"><p class="mono kick">PLAN DE NEGOCIOS · VERSIÓN 0.1 · DOCUMENTO DE TRABAJO</p>
     <h1>Diseñar la casa.<br><em>Resolver el sistema.</em></h1>
     <p class="lead">Una plataforma para diseñar viviendas woodframe y desarrollar su definición constructiva con IA, automatización y un modelo único del proyecto.</p></div>
     <div class="cover-stamp mono"><span>18 · 09 · 2026</span><span>NOMBRE COMERCIAL PENDIENTE</span><span>ANGUS RANCH · CÓRDOBA · CASO INICIAL</span></div>
     <p class="cover-cap mono">Imagen de estudio · no es una obra construida</p>` });

  // 02 — Mapa
  add({ ch: '00', kind: 'map', title: 'Seis capítulos, una decisión', cls: 'light', body:
    `<div class="map">${CHAPTERS.map(c => `<button class="map-card" data-chapter="${c.n}"><span class="mono">${c.n}</span><strong>${c.name}</strong><em>${c.q}</em><small class="mono" data-range="${c.n}"></small></button>`).join('')}</div>`,
    foot: chip('Todos los importes en USD de referencia. Metas, precios, plazos y finanzas son hipótesis para validar, no compromisos.') });

  // 03 — Tesis
  add({ ch: '00', kind: 'thesis', title: 'Una casa. Un modelo. Todas sus piezas.', cls: 'dark thesis', body:
    `<div class="split thesis-split"><div>
      <p class="lead">Cada decisión de diseño actualiza componentes, vistas y documentación dentro de un sistema constructivo definido.</p>
      <div class="two-promises">${row('Promesa inicial', 'Menos horas para transformar y modificar un diseño, con vistas, componentes y documentación consistentes.')}${row('Promesa de largo plazo', 'La vivienda completa como un conjunto coordinado de piezas y sistemas individualizables, verificables y cuantificables.')}</div>
     </div>${fig(img.frame, 'Entramado de madera del modelo Angus Ranch V06', '', 'thesis-img')}</div>
     <div class="stats">${stat('828', 'piezas con ID estable')}${stat('24', 'headers dobles')}${stat('100', 'pernos de solera')}${stat('13', 'capas de vista')}<p class="stats-src mono">ANGUS RANCH V06 · MODELO DE ESTUDIO, NO PRODUCTO</p></div>` });

  // ---- 01 Oportunidad
  divider(CHAPTERS[0]);
  add({ ch: '01', title: 'Cada cambio se paga tres veces', cls: 'light', body:
    `<div class="split problem"><figure class="sketch"><img src="${img.bosquejo}" alt="Planta de Angus Ranch V02 corregida a mano con marcas rojas"><figcaption><b>Angus Ranch V02 · boceto corregido a mano.</b> Cada trazo rojo obliga a rehacer planos, modelo, detalles y listados.</figcaption></figure>
     <div class="steps-v"><div><span class="mono red">01</span><h3>Trasladar</h3><p>Representar el mismo cambio en cada herramienta: planos, modelo, detalles, listados.</p></div><div><span class="mono red">02</span><h3>Revisar</h3><p>Detectar qué elementos y soluciones dejaron de ser válidos.</p></div><div><span class="mono red">03</span><h3>Corregir</h3><p>Conciliar versiones antes de poder seguir con el proyecto.</p></div></div></div>`,
    foot: chip('HIPÓTESIS DE PROBLEMA · Las entrevistas deben ubicar dónde se concentra el esfuerzo y cuánto cuesta.') });

  add({ ch: '01', title: 'Quién lo usa. Quién lo paga.', cls: 'light', body:
    `<div class="split client">${matrixSvg()}<div>
      <p class="eyebrow">CLIENTE INICIAL PROPUESTO</p>
      <h3 class="large">Constructoras y estudios que repiten un sistema y adaptan cada vivienda.</h3>
      ${row('Usuario', 'Arquitecto, proyectista o integrante del equipo técnico.')}${row('Comprador', 'Dueño, socio del estudio o responsable técnico.')}${row('Filtro de entrevistas', 'Organizaciones con ~5–30 viviendas por año. Argentina como hipótesis de entrada.')}
     </div></div>`,
    foot: chip('El rango 5–30 es un criterio de selección, no un dato de mercado. La frecuencia y similitud entre proyectos importan más que el tamaño.') });

  // ---- 02 Producto
  divider(CHAPTERS[1]);
  add({ ch: '02', title: 'Un MVP con límites explícitos', cls: 'light', body:
    `<div class="split mvp"><figure class="domain"><img src="${img.planta}" alt="Planta de Angus Ranch V04"><span class="tag t1 mono">1 PLANTA</span><span class="tag t2 mono">PLANTA ORTOGONAL</span><span class="tag t3 mono">TERRENO SIMPLE</span><span class="tag t4 mono">1 FAMILIA DE MUROS · 1 CUBIERTA</span><span class="tag t5 mono">CATÁLOGO ACOTADO DE ABERTURAS</span><figcaption>Dominio de partida · 164 m² · Angus Ranch V04</figcaption></figure>
     <div><p class="eyebrow">ENTREGABLE</p><h3 class="large">Definición arquitectónica y constructiva parcial, con alcance y pendientes explícitos.</h3>
     <ul class="pills">${['Inicio guiado', 'Edición de planta acotada', 'Visor 3D por capas', 'Entramado según reglas', 'Biblioteca de encuentros', 'Historial y deshacer', 'Asistente contextual', 'Identificación de piezas', 'Cantidades del alcance', 'Exportación básica'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>`,
    foot: chip('Los límites de dimensiones y soluciones se fijan con especialistas antes de automatizar decisiones técnicas.') });

  const layers = [
    ['04', 'Estructura', 'Montantes, soleras, headers y cabios.', 'estructura'],
    ['05', 'Aislación', 'Cavidades entre montantes.', 'insulation'],
    ['06', 'Placas OSB', 'Arriostramiento y cierre.', 'osb'],
    ['07', 'Membrana WRB', 'Control de agua y aire, retornos en aberturas.', 'wrb'],
    ['08', 'Siding y cámara', 'Terminación ventilada de 25 mm.', 'siding'],
  ];
  add({ ch: '02', title: 'Una casa, capa por capa', cls: 'light layers-slide', body:
    `<div class="layers" data-layers><div class="layers-stage">${layers.map((l, i) => `<img src="${img[l[3]]}" alt="Capa ${l[1]}" data-layer="${i}" class="${i === 0 ? 'on' : ''}">`).join('')}<figcaption class="mono">ANGUS RANCH V04 · MISMAS MALLAS, DISTINTAS CAPAS</figcaption></div>
     <ol class="layers-list">${layers.map((l, i) => `<li><button data-i="${i}" aria-pressed="${i === 0}"><b class="mono">${l[0]}</b><span><strong>${l[1]}</strong><small>${l[2]}</small></span></button></li>`).join('')}</ol></div>`,
    foot: chip('Cada capa sale del mismo modelo. El visor por capas relaciona diseño y solución constructiva.', 'neutral') });

  const icons = {
    conf: '<path d="M4 8h16M4 16h16"/><circle cx="9" cy="8" r="2.5"/><circle cx="15" cy="16" r="2.5"/>',
    dis: '<path d="M4 20V6h10v6h6v8H4z"/><path d="M8 20v-5h4v5"/>',
    des: '<path d="M4 4h16v16H4z"/><path d="M8 4v16M12 4v16M16 4v16M4 9h16"/>',
    rev: '<path d="M12 4 20 8l-8 4-8-4 8-4z"/><path d="M4 12l8 4 8-4M4 16l8 4 8-4"/>',
    exp: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v4h16v-4"/>',
  };
  const ico = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${icons[k]}</svg>`;
  add({ ch: '02', title: 'El primer flujo, de principio a fin', cls: 'light', body:
    `<div class="rail">${[['conf', 'Configurar', 'Datos básicos y sistema constructivo del cliente.'], ['dis', 'Diseñar', 'Planta, muros, ambientes y aberturas.'], ['des', 'Desarrollar', 'Entramado y encuentros admitidos por las reglas.'], ['rev', 'Revisar', 'Capas, cambios y definiciones pendientes.'], ['exp', 'Exportar', 'Un paquete consistente para continuar el trabajo profesional.']].map((s, i) => `<div><span class="mono">0${i + 1}</span>${ico(s[0])}<h3>${s[1]}</h3><p>${s[2]}</p></div>`).join('')}</div>
     <div class="band"><strong class="mono">DESDE EL INICIO</strong><span>Guardar y reabrir · Historial y deshacer · Identificadores de piezas · Cantidades del alcance modelado</span></div>
     <div class="band pkg"><strong class="mono">EL PAQUETE EXPORTADO</strong><span class="pkg-items">${['Vistas', 'Detalles seleccionados', 'Listado de componentes', 'Pendientes explícitos'].map(x => `<b>${x}</b>`).join('')}</span></div>`,
    foot: chip('No hace falta automatizar todo para ser útil. Sí hace falta completar un trabajo delimitado de principio a fin.', 'neutral') });

  add({ ch: '02', title: '“Quiero ampliar esta ventana.”', cls: 'dark window-slide', body:
    `<div class="win" data-window><div class="win-stage">${wallSvg()}<div class="win-legend mono"><span><i class="sw wood"></i>SIN CAMBIOS</span><span><i class="sw red"></i>MODIFICADO</span><span><i class="sw new"></i>NUEVO</span><span><i class="sw gone"></i>ELIMINADO</span></div></div>
     <aside class="win-log"><p class="mono head"><span class="st stA">ESTADO · VERSIÓN 12 · COMPROBADA</span><span class="st stB">PROPUESTA · VERSIÓN 13 · EN REVISIÓN</span></p>
      <ul class="log">
       <li class="a">Selección: ventana Norte O0 · RO 1.200 × 1.200 mm</li>
       <li class="a">Intención: <em>“ampliar 600 mm hacia el este”</em></li>
       <li class="b"><b>Header H-N-O0</b> · 1.290 → 1.890 mm</li>
       <li class="b"><b>Jack + king derechos</b> · desplazados +600 mm</li>
       <li class="b"><b>Montante M-09</b> · reemplazado por 2 cripples</li>
       <li class="b"><b>Montante M-10</b> · absorbido por el jack</li>
       <li class="b"><b>Antepecho</b> · 1.200 → 1.800 mm</li>
       <li class="b warn"><b>Verificación desactualizada</b> · dintel &gt; 1,8 m → cálculo pendiente</li>
       <li class="b ok">Despiece y cantidades actualizados · 7 piezas afectadas</li>
      </ul></aside></div>`,
    foot: chip('Planta editable + 3D por capas + asistente. La conversación expresa la intención; la selección y las cotas dan precisión. Los estados distinguen propuesto, pendiente, comprobado y revisado.', 'neutral') });

  add({ ch: '02', title: 'Cada componente tiene identidad', cls: 'light', body:
    `<div class="split identity"><div class="card-id mono"><p class="id">Muro_Norte_Montante_017</p>
      <dl><dt>tipo</dt><dd>montante común</dd><dt>sección</dt><dd>45 × 140 mm</dd><dt>largo</dt><dd>2.490 mm · blanco de corte 2.500</dd><dt>pertenece</dt><dd>Pared Norte → Módulo O0</dd><dt>relaciones</dt><dd>Solera_N_01 · Header_N_O0</dd><dt>regla</dt><dd>Montante_comun_v0.3 · origen y versión conservados</dd><dt>estado</dt><dd><i class="dot ok"></i>comprobado por reglas · sin revisión humana</dd><dt>cantidad</dt><dd>1 de 327 montantes y antepechos</dd><dt>historial</dt><dd>creado v04 · modificado v12 (cambio de abertura)</dd></dl></div>
     <div><p class="eyebrow">SE PRESERVA SIEMPRE</p><h3 class="large">Tipo, dimensiones, ubicación, pertenencia y relaciones. Esa base permite crecer y cuantificar la casa.</h3>
     <p class="eyebrow">DESPUÉS DEL MVP</p><ul class="clean">${['Fundaciones e instalaciones completas', 'Cálculo estructural general', 'Varias plantas y geometrías libres', 'Fabricación industrial e importación universal', 'Proveedores, precios y compras'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>`,
    foot: chip('Las fundaciones pueden aparecer como referencia geométrica y las instalaciones como zonas reservadas. No se presentan como disciplinas resueltas.', 'neutral') });

  // ---- 03 Tecnología
  divider(CHAPTERS[2]);
  add({ ch: '03', title: 'El modelo debe sobrevivir a la interfaz', cls: 'light', body:
    `<div class="arch"><div class="tier t-top"><span class="tier-l mono">INTERCAMBIABLE</span><div class="box">Interfaz simplificada<br>en Blender</div><div class="box">Interfaz propia<br>(planta + 3D)</div><div class="box ai">Asistente IA<br><small>interpreta intención</small></div></div>
     <div class="tier t-mid"><span class="tier-l mono">CONTRATO</span><div class="box wide">Operaciones definidas · parámetros validados · cambios revisables</div></div>
     <div class="tier t-core"><span class="tier-l mono">PERMANENTE</span><div class="box">Reglas constructivas<br><small>condiciones, alcance, resultados reproducibles</small></div><div class="box core">Modelo del proyecto<br><small>muros, ambientes, aberturas, piezas, sistemas · IDs estables</small></div><div class="box">Geometría y documentación<br><small>representaciones del mismo modelo</small></div></div></div>
     <p class="statement">Decidir la interfaz con el mismo ejercicio: abrir una casa, modificar una abertura, inspeccionar el entramado, deshacer y exportar. Al final de la etapa inicial, no como investigación permanente.</p>`,
    foot: chip('El asistente no improvisa geometría con código nuevo en cada conversación: llama operaciones definidas y devuelve cambios revisables.', 'neutral') });

  add({ ch: '03', title: 'Angus Ranch: la primera base', cls: 'dark base', body:
    `<div class="split base-split"><div class="base-figs">${fig(img.header, 'Vista explotada de un header doble', 'Header doble · vista explotada', 'bf1')}${fig(img.holddown, 'Corte de anclaje de solera y ejemplo de hold-down', 'Anclaje de solera y hold-down', 'bf2')}</div>
     <div>${row('Lo que ya existe', 'Generación geométrica, capas, identificadores, despiece, plan de cortes y cómputos: 828 piezas, 17,9 m³ brutos.')}${row('El salto necesario', 'Cerrar el circuito entre edición, reglas y regeneración coherente. Hoy los cambios manuales en Blender no vuelven al script.')}${row('La prueba de generalización', 'Al menos tres viviendas distintas dentro del dominio, con casos externos a Angus Ranch desde el prototipo.')}</div></div>`,
    foot: chip('V06 es evidencia de factibilidad parcial. No es una solución técnica completa ni una validación comercial.') });

  // ---- 04 Mercado
  divider(CHAPTERS[3]);
  const comp = [
    ['Higharc', 'https://www.higharc.com/', 'Diseño, configuración, estimación y documentación residencial.', 'Un segmento y una experiencia con valor propio.'],
    ['Chief Architect', 'https://www.chiefarchitect.com/products/home-design/premier/', 'Modelado residencial, materiales y documentación.', 'Ahorro en un flujo recurrente concreto.'],
    ['hsbcad', 'https://www.hsbcad.com/', 'Diseño, fabricación y montaje industrializado.', 'Un alcance útil sin complejidad innecesaria.'],
    ['ARKANCE Be.Smart', 'https://arkance.world/global/products/be-smart?showpopup=true', 'Ecosistema de herramientas para flujos BIM.', 'Facilidad de adopción y continuidad de datos.'],
    ['El flujo actual', null, 'Herramientas conocidas, planillas, detalles propios y revisión manual.', 'Que el ahorro supere el costo de cambiar de hábito.'],
  ];
  add({ ch: '04', title: 'La categoría ya tiene competencia', cls: 'light', body:
    `<div class="comp">${comp.map(c => `<div class="comp-card ${c[1] ? '' : 'status'}"><h3>${c[1] ? `<a href="${c[1]}" target="_blank" rel="noopener">${c[0]} ↗</a>` : c[0]}</h3><p>${c[2]}</p><p class="eyebrow">QUÉ DEBEMOS DEMOSTRAR</p><p class="demo">${c[3]}</p></div>`).join('')}</div>`,
    foot: chip('Ofertas relevadas en sitios oficiales el 18/09/2026, sin pruebas propias. No se presume que los competidores carezcan de estas capacidades.') });

  add({ ch: '04', title: 'La ventaja hay que construirla', cls: 'light', body:
    `<div class="split adv"><div class="pillars">${[['Conocimiento aplicable', 'Soluciones comprobadas, reglas con alcance definido y casos de prueba.'], ['Cambios coherentes', 'Dependencias que mantienen alineados componentes y entregables.'], ['Uso recurrente', 'Una experiencia que se incorpora al trabajo del equipo y requiere cada vez menos asistencia.']].map((p, i) => `<div><span class="mono">0${i + 1}</span><h3>${p[0]}</h3><p>${p[1]}</p></div>`).join('')}</div>
     <div class="callout"><p class="eyebrow">SEÑAL DE MERCADO</p><p class="big-num">USD 95 M</p><p>Serie C de <a href="https://www.higharc.com/newsroom/higharc-95m-series-c-for-homebuilding-ai" target="_blank" rel="noopener">Higharc ↗</a>, junio 2026. Los inversores financian esta categoría.</p><p class="small">No es una valoración comparable ni una prueba de demanda local.</p></div></div>`,
    foot: chip('Tener acceso a un modelo de IA o a libros no constituye una ventaja sostenible. La diferenciación se demuestra en proyectos reales.') });

  const scale = [[50, 150, 'USD 90 mil'], [250, 250, 'USD 750 mil'], [1000, 350, 'USD 4,2 M'], [3000, 450, 'USD 16,2 M']];
  add({ ch: '04', title: 'La escala que exige el negocio', cls: 'light', body:
    `<p class="sub">Ingreso recurrente anualizado = organizaciones × cuota media × 12 · un punto = 50 organizaciones</p>
     <div class="scale">${scale.map(s => `<div><span class="mono lbl">${s[0].toLocaleString('es-AR')} org × USD ${s[1]}/mes</span><span class="dots">${'<i></i>'.repeat(s[0] / 50)}</span><strong>${s[2]}</strong></div>`).join('')}</div>
     <div class="band"><strong class="mono">A USD 250 / MES</strong><span>334 organizaciones superan USD 1 M anualizado · 3.334 superan USD 10 M. Obliga a evaluar pronto si el segmento inicial sostiene el negocio.</span></div>`,
    foot: chip('No representa tamaño de mercado ni previsión de captación. Próximo paso: lista de 50 organizaciones identificadas y estimación de abajo hacia arriba.') });

  // ---- 05 Negocio
  divider(CHAPTERS[4]);
  add({ ch: '05', title: 'Precios para probar con clientes', cls: 'light', body:
    `<div class="pricing">${[['Piloto acompañado', '200–600', 'por proyecto delimitado', '¿Existe compromiso económico por un resultado?'], ['Equipo pequeño', '100–250', 'por mes', '¿El uso recurrente sostiene una cuota?'], ['Mayor volumen', '300–600', 'por mes', '¿Colaboración y reutilización justifican más ingreso?']].map((p, i) => `<div class="price ${i === 1 ? 'first' : ''}"><p class="eyebrow">${p[0]}</p><p class="amt"><small>USD</small>${p[1]}</p><p class="mono per">${p[2].toUpperCase()}</p><p class="learn">${p[3]}</p>${i === 1 ? '<span class="mono flag">OFERTA INICIAL PROPUESTA</span>' : ''}</div>`).join('')}<div class="price extra"><p class="eyebrow">Configuración específica</p><p class="amt sep">Presupuesto<br>separado</p><p class="mono per">POR SISTEMA DEL CLIENTE</p><p class="learn">¿Cuánto trabajo de incorporación exige cada sistema constructivo?</p></div></div>
     <div class="band"><strong class="mono">EJEMPLO DE VALOR</strong><span>20 h/mes liberadas × USD 15 = USD 300 de capacidad. Una cuota de USD 150 consume la mitad. Liberar horas no siempre reduce gastos: hay que preguntar si permite producir más o entregar antes.</span></div>`,
    foot: chip('Hipótesis, no tarifas. Configuración específica y servicios se presupuestan aparte y no cuentan como ingreso recurrente.') });

  add({ ch: '05', title: 'El piloto debe probar valor y repetición', cls: 'light', body:
    `<div class="metrics">${stat('≥30%', 'menos horas totales del flujo elegido, incluyendo revisión y correcciones')}${stat('3', 'organizaciones piloto independientes')}${stat('5', 'proyectos completados entre los pilotos')}${stat('2', 'decisiones de pago o renovación')}</div>
     <p class="eyebrow pilot-l">DISEÑO DEL PILOTO</p><div class="pilot">${['Medir el flujo actual sobre un caso soportado', 'Procesar el mismo trabajo con el producto', 'Revisar el resultado con un profesional', 'Registrar correcciones y toda la asistencia', 'Ofrecer continuidad paga'].map((s, i) => `<div><b class="mono">0${i + 1}</b><span>${s}</span></div>`).join('')}</div>`,
    foot: chip('Metas, no resultados. 8–12 entrevistas totales con participantes externos al círculo cercano. Comparar el mismo alcance y calidad; registrar toda asistencia.') });

  add({ ch: '05', title: 'Ventas lideradas por el fundador', cls: 'light', body:
    `${funnelSvg()}<div class="band"><strong class="mono">SECUENCIA</strong><span>Entrevista sobre un proyecto real → demostración sobre un caso compatible → piloto con alcance y precio acordados → revisión → suscripción o segundo proyecto pago.</span></div>`,
    foot: chip('Embudo objetivo, no tasas históricas. El mensaje comercial muestra un cambio concreto y su efecto, no “IA que diseña casas”.') });

  const budget = [['Desarrollo o dedicación técnica remunerada', 9000, 18000], ['Arquitectura y revisión especializada', 2000, 5000], ['Diseño de interfaz y pruebas', 1000, 3000], ['Infraestructura y herramientas', 300, 1000], ['Entrevistas, traslados y administración', 500, 1500], ['Reserva del 20 %', 2560, 5700]];
  const bmax = 18000;
  add({ ch: '05', title: 'Presupuesto para los primeros 90 días', cls: 'light', body:
    `<div class="split budget"><div class="ranges">${budget.map(b => `<div class="rng"><span class="rl">${b[0]}</span><span class="track"><i style="left:${b[1] / bmax * 100}%;width:${(b[2] - b[1]) / bmax * 100}%"></i></span><span class="mono rv">${b[1].toLocaleString('es-AR')}–${b[2].toLocaleString('es-AR')}</span></div>`).join('')}<p class="mono axis"><span><em>0</em><em>USD 9.000</em><em>USD 18.000</em></span></p></div>
     <div class="total"><p class="eyebrow">CAJA ORIENTATIVA · USD</p><p class="hero">15.360<span>a 34.200</span></p><p>Escenario con desarrollo remunerado. Cada etapa se autoriza por separado; al final de la semana 4 debe existir un presupuesto con personas, horas y cotizaciones reales.</p></div></div>`,
    foot: chip('Asignaciones de planificación, no cotizaciones. Excluye sueldo del fundador, equipamiento e impuestos. No equivale al costo total del MVP.') });

  add({ ch: '05', title: 'Escenario ilustrativo a tres años', cls: 'light', body:
    `<div class="split years-split">${yearsSvg()}<div><table class="tbl"><thead><tr><th>USD miles</th><th>A1</th><th>A2</th><th>A3</th></tr></thead><tbody><tr><td>Clientes promedio</td><td>10</td><td>60</td><td>180</td></tr><tr><td>Cuota media / mes</td><td>150</td><td>200</td><td>250</td></tr><tr><td>Ingresos</td><td>18</td><td>144</td><td>540</td></tr><tr><td>Costos directos</td><td>4,5</td><td>28,8</td><td>97,2</td></tr><tr><td>Gastos fijos</td><td>120</td><td>240</td><td>360</td></tr><tr class="tot"><td>Resultado operativo</td><td class="neg">−106,5</td><td class="neg">−124,8</td><td class="pos">+82,8</td></tr></tbody></table>
     <p class="legend mono"><i class="sw wood"></i>INGRESOS <i class="sw outline"></i>GASTOS FIJOS <i class="sw dot"></i>RESULTADO</p></div></div>`,
    foot: chip('Supuestos, no pronóstico. Omite impuestos, financiación, activos, diferencias de cambio y plazos de cobro: resultado operativo ≠ flujo de caja. Pérdida acumulada A1+A2: USD 231.300.') });

  add({ ch: '05', title: 'El precio y la recurrencia importan', cls: 'light', body:
    `<div class="split be-split">${breakevenSvg()}<div><p class="eyebrow">SENSIBILIDAD DEL AÑO 3</p>
      <div class="sens"><div><span>180 clientes × USD 250</span><b class="pos">+82.800</b></div><div><span>120 clientes × USD 250</span><b class="neg">−64.800</b></div><div><span>180 clientes × USD 175</span><b class="neg">−50.040</b></div></div>
      <p class="statement small">Un precio bajo impide sostener el equipo; un servicio demasiado intensivo reduce el margen. Ambos se miden durante los pilotos.</p></div></div>`,
    foot: chip('Margen bruto 82 % y gastos fijos de USD 360.000 anuales constantes. Relación aritmética: no incorpora costos nuevos al escalar.') });

  // ---- 06 Ejecución
  divider(CHAPTERS[5]);
  add({ ch: '06', title: 'Equipo inicial y forma de trabajo', cls: 'light', body:
    `<div class="split team"><div>${row('Fundador', 'Producto, entrevistas, ventas y seguimiento de caja, con dedicación semanal explícita.')}${row('Responsable técnico', 'Modelo de datos, geometría y aplicación. Una sola persona responsable, con experiencia pertinente.')}${row('Arquitecto asesor', 'Flujo profesional y revisión de entregables, con dedicación acordada.')}${row('Especialista en estructuras de madera', 'Reglas estructurales y límites de aplicación, por alcance.')}${row('Diseño de producto', 'Interfaz y pruebas de uso, apoyo puntual.')}</div>
     <div><div class="cadence"><p class="eyebrow">CADENCIA PROPUESTA</p><div><b class="mono">SEMANAL</b><span>Revisión de producto y aprendizaje.</span></div><div><b class="mono">QUINCENAL</b><span>Demostración con un usuario real.</span></div><div><b class="mono">MENSUAL</b><span>Horas, caja y avance frente a criterios.</span></div></div>
     <p class="statement small">Los roles pueden combinarse, pero no conviene diluir la responsabilidad técnica ni asumir que un único desarrollador domina construcción, geometría e interfaz por igual.</p></div></div>`,
    foot: chip('Dedicación, remuneración y responsabilidades por acordar antes de sumar socios. El contacto con los dos arquitectos no implica asesoría permanente.') });

  add({ ch: '06', title: 'La hoja de ruta del primer año', cls: 'light', body:
    `<div class="roadmap"><div class="months mono">${Array.from({ length: 12 }, (_, i) => `<span>M${i + 1}</span>`).join('')}</div>
     <div class="phases">${[[1, 1, 'Descubrir', 'Problema, alcance y decisión de interfaz', 'Dolor repetido, casos y compradores identificados', 'SEM. 1–4'], [2, 2, 'Prototipar', 'Modelo editable y un cambio propagado', 'Funciona también fuera de Angus Ranch', 'SEM. 5–8'], [3, 3, 'Probar', 'Exportar, revisar y medir el flujo', 'Usuarios completan el trabajo y reconocen valor', 'SEM. 9–12'], [4, 6, 'Completar el MVP', 'Guardado, historial, controles de consistencia, flujo delimitado estable y pilotos pagos.', 'Ahorro medido, calidad aceptable y primeros pagos', 'MESES 4–6'], [7, 12, 'Repetir', 'Incorporación repetible, clientes que regresan y menor dependencia del fundador. Después: un módulo o mercado adicional, solo con núcleo estable y demanda demostrada.', 'Menos asistencia por cliente, uso en proyectos nuevos', 'MESES 7–12']].map(p => `<div class="ph" style="grid-column:${p[0]} / ${p[1] + 1}"><span class="mono range">${p[5]}</span><h3>${p[2]}</h3><p>${p[3]}</p><p class="gate mono">◆ ${p[4]}</p></div>`).join('')}</div></div>`,
    foot: chip('Plazos orientativos con dedicación técnica sostenida. Se avanza por evidencia: el calendario no reemplaza los criterios de aceptación.') });

  add({ ch: '06', title: 'Cuándo avanzar y cuándo ajustar', cls: 'light', body:
    `<div class="split signals"><div class="go"><p class="eyebrow">SEÑALES PARA AVANZAR</p><ul class="clean">${['Ahorro que sobrevive a la revisión y a las correcciones', 'Clientes que pagan y usan el producto en otro proyecto', 'Menos asistencia con cada incorporación', 'Resultados consistentes fuera de Angus Ranch'].map(x => `<li>${x}</li>`).join('')}</ul></div>
     <div class="stop"><p class="eyebrow">SEÑALES PARA REORIENTAR</p><ul class="clean">${['Cada proyecto exige cambiar código', 'El soporte absorbe el ingreso', 'Los usuarios solo valoran los renders', 'El ahorro desaparece al revisar'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>
     <p class="eyebrow risks-l">RIESGOS PRIORITARIOS</p><div class="risks mono">${['ALCANCE EXCESIVO', 'MODELO VISTOSO PERO INCONSISTENTE', 'DEPENDENCIA DE UNA SOLA CASA', 'ERROR DE INTERPRETACIÓN TÉCNICA', 'DEMANDA LOCAL INSUFICIENTE', 'CONSULTORÍA DIFÍCIL DE REPETIR'].map(r => `<span>${r}</span>`).join('')}</div>`,
    foot: chip('Respuesta a los riesgos: dominio acotado, reglas reproducibles, casos externos desde el prototipo y revisión profesional.', 'neutral') });

  add({ ch: '06', title: 'Inversión después de la evidencia', cls: 'dark invest', body:
    `<div class="split invest-split"><div><p class="lead">El capital debería financiar un hito de expansión comprobable: ampliar cobertura técnica y captar clientes de forma repetible en un segmento definido.</p>
      <div class="paths">${row('Nicho rentable', 'Crecer con ingresos propios y capital acotado.')}${row('Demanda amplia', 'Vía creíble hacia miles de organizaciones o contratos mayores: candidato a capital de riesgo.')}</div></div>
     <div class="callout dark-c"><p class="eyebrow">REFERENCIA PARA EVALUAR UNA RONDA</p><p class="big-num">10–20</p><p>organizaciones pagas, varias cohortes con uso repetido y casos medidos fuera de la red personal.</p></div></div>
     <p class="eyebrow chain-l">LA CASA COMPLETA SIGUE COMO HORIZONTE · SECUENCIA CONDICIONADA POR DEMANDA</p><div class="chain mono">${['Núcleo de diseño y entramado', 'Más sistemas coordinados', 'Documentación más profunda', 'Empresas y mercados', 'Cuantificación integral', 'Abastecimiento'].map((c, i) => `<span class="${i === 0 ? 'now' : ''}">${c}</span>`).join('<i>→</i>')}</div>`,
    foot: chip('No se propone una ronda ahora. Monto y estructura se calcularán con 18–24 meses de operación y metas concretas. Sin valoración ni dilución en esta versión.') });

  add({ ch: '06', title: 'Cuatro semanas para decidir el MVP', cls: 'light', body:
    `<div class="weeks">${[['Entender el trabajo', 'Conversaciones con los dos arquitectos; reconstruir un proyecto reciente; dedicación y caja disponibles.', 'Flujo, entregables, tiempos y límites de inversión'], ['Contrastar la demanda', 'Entrevistas externas; base inicial de organizaciones; selección del trabajo a automatizar.', 'Problema repetido, comprador y casos candidatos'], ['Definir el sistema', 'Especificación del dominio; prueba comparativa de interfaz; reutilización de V06.', 'Alcance, riesgos técnicos y decisión sobre Blender'], ['Decidir con evidencia', 'Demostración de un cambio coherente si es factible; propuesta de pilotos y presupuesto real.', 'Avanzar, ajustar o reformular la etapa siguiente']].map((w, i) => `<div><span class="mono">SEMANA ${i + 1}</span><h3>${w[0]}</h3><p>${w[1]}</p><p class="ev"><b class="mono">EVIDENCIA</b>${w[2]}</p></div>`).join('')}</div>
     <p class="statement">La versión 0.2 reemplaza supuestos por respuestas: quién compra, qué trabajo ahorramos, cuánto paga y qué cuesta construirlo.</p>` });

  // Cierre
  add({ ch: '06', kind: 'closing', title: 'Una visión ambiciosa. Un primer alcance concreto.', cls: 'dark closing', body:
    `<img class="cover-bg dim" src="${img.aerial}" alt=""><div class="cover-shade strong"></div>
     <div class="close-copy"><h2>Una visión ambiciosa.<br><em>Un primer alcance concreto.</em></h2>
     <p class="lead">Desarrollar el núcleo que conecta diseño y construcción, probarlo con profesionales y ampliar el producto con evidencia.</p>
     <div class="actions"><button class="primary" data-action="doc">Leer el plan completo</button><button class="ghost-btn" data-action="restart">Volver al inicio</button></div>
     <p class="mono end-note">DECISIÓN RECOMENDADA · UN PERÍODO DE DESCUBRIMIENTO Y FACTIBILIDAD DE CUATRO SEMANAS, CON GASTO LIMITADO Y ENTREGABLES DEFINIDOS.</p></div>` });

  return S;
}

// ---------------------------------------------------------------- CSS

// ---------------------------------------------------------------- HTML
async function main() {
  const img = await prepareAssets();
  const slides = buildSlides(img);
  const total = slides.length;
  const pad = n => String(n).padStart(2, '0');
  const plain = t => t.replace(/<br>/g, ' ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  // rangos de capítulos para el mapa y las portadas
  const ranges = {}; slides.forEach((s, i) => { if (s.ch === '00') return; (ranges[s.ch] ||= []).push(i + 1); });
  const chapterName = ch => (CHAPTERS.find(c => c.n === ch) || { name: 'Introducción' }).name;

  const sectionHtml = slides.map((s, i) => {
    const isCover = s.kind === 'cover' || s.kind === 'closing';
    const head = `<header class="s-head mono"><span>${isCover ? (s.kind === 'cover' ? 'WOODFRAME · PLATAFORMA DE DISEÑO Y DESARROLLO' : 'CIERRE') : `<b>${pad(i + 1)}</b>— ${chapterName(s.ch).toUpperCase()}`}</span><span class="s-stamp">PLAN v0.1 · 18.09.2026 · HOJA ${pad(i + 1)}/${total}</span></header>`;
    const title = (isCover || s.kind === 'divider') ? '' : `<h2>${s.title}</h2>`;
    const foot = isCover ? '' : `<footer class="s-foot">${s.foot || '<span></span>'}<span class="s-mark">Woodframe · plan de negocios v0.1 · caso Angus Ranch</span></footer>`;
    const marks = '<i class="cm tl"></i><i class="cm tr"></i><i class="cm bl"></i><i class="cm br"></i>';
    return `<section class="slide ${s.cls} ${i === 0 ? 'active' : ''}" data-title="${esc(plain(s.title))}" data-chapter="${s.ch}" data-kind="${s.kind || 'content'}" aria-label="Diapositiva ${i + 1}: ${esc(plain(s.title))}" aria-hidden="${i !== 0}">${marks}${head}${title}<div class="s-body">${s.body}</div>${foot}</section>`;
  }).join('');

  const tocText = {}; for (const c of CHAPTERS) tocText[c.n] = (ranges[c.n] || []).slice(1).map(n => `${pad(n)} ${plain(slides[n - 1].title)}`).join(' · ');
  const rangeText = {}; for (const c of CHAPTERS) { const r = ranges[c.n] || []; rangeText[c.n] = `HOJAS ${pad(r[0])}–${pad(r[r.length - 1])}`; }
  const dividerIndex = {}; slides.forEach((s, i) => { if (s.kind === 'divider') dividerIndex[s.ch] = i; });

  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><title>Woodframe — Plan de negocios v0.1</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>${css}</style></head><body>
<header class="topbar mono"><span class="brand"><i></i>WOODFRAME <span>— PLAN DE NEGOCIOS v0.1</span></span><div class="top-actions"><button id="indexBtn">Índice</button><button id="docBtn">Plan completo</button><button id="readingBtn" aria-pressed="false">Lectura</button><button id="fullscreen" aria-label="Pantalla completa">⛶</button></div></header>
<main class="stage" aria-label="Presentación del plan de negocios">${sectionHtml}</main>
<nav class="nav mono" aria-label="Navegación"><button id="prev" aria-label="Anterior">←</button><span class="counter" id="counter"></span><span class="nav-title" id="navTitle"></span><button id="next" aria-label="Siguiente">→</button><span class="keyhint">← → navegar · I índice · F pantalla completa</span></nav>
<div class="progress" id="progress"></div><div class="sr-only" role="status" aria-live="polite" id="live"></div>
<dialog id="indexDialog" class="index-dialog" aria-labelledby="indexHeading"><div class="dialog-head"><strong id="indexHeading">Contenido</strong><button data-close="indexDialog">Cerrar ×</button></div><div class="index-list">${slides.map((s, i) => `<button data-slide="${i}" class="${s.kind === 'divider' ? 'div' : ''}"><span>${pad(i + 1)}</span>${plain(s.title)}</button>`).join('')}</div></dialog>
<dialog id="docDialog" class="doc-dialog" aria-labelledby="docHeading"><div class="dialog-head"><strong id="docHeading">Plan de negocios · texto completo</strong><button data-close="docDialog">Cerrar ×</button></div><article class="document">${markdown(source)}</article></dialog>
<script>
${script(tocText, rangeText, dividerIndex)}
</script></body></html>`;
  fs.writeFileSync(path.join(root, OUT), html, 'utf8');
  console.log(JSON.stringify({ slides: total, bytes: Buffer.byteLength(html), output: OUT }));
}
main().catch(e => { console.error(e); process.exit(1); });
