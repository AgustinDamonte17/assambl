// Genera MVP_01.html a partir de MVP_01.md con el motor visual compartido (../pp_shell.cjs).
// Uso:  node build_mvp_01.cjs          (usa la caché de imágenes de pp_shell; --refresh la reprocesa)
'use strict';
const fs = require('fs');
const path = require('path');
const root = __dirname;
const OUT = 'MVP_01.html';
const { esc, markdown, prepareAssets, chip, row, stat, fig, css, script } = require('../pp_shell.cjs');

const source = fs.readFileSync(path.join(root, 'MVP_01.md'), 'utf8');
const STAMP = 'MVP_01 · v0.1 · 22.09.2026';

// ---------------------------------------------------------------- markdown extendido (código en bloque e inline)
function markdownExt(md) {
  const parts = md.split(/^```[^\n]*\n([\s\S]*?)^```\s*$/m);
  let out = '';
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) { out += `<pre class="code">${esc(parts[i].replace(/\s+$/, ''))}</pre>`; continue; }
    out += markdown(parts[i])
      .replace(/\[([^\]<>]+)\]\(([^)\s<>]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 ↗</a>')
      .replace(/`([^`<>]+)`/g, '<code>$1</code>')
      .replace(/(^|[\s(>])\*([^*<>\n]+)\*(?=[\s.,;:)<]|$)/g, '$1<em>$2</em>');
  }
  return out;
}

// ---------------------------------------------------------------- datos
const CHAPTERS = [
  { n: '01', name: 'Alcance', q: '¿Qué construye la primera versión?', img: 'planta' },
  { n: '02', name: 'Capas', q: '¿De qué está hecha la casa?', img: 'siding' },
  { n: '03', name: 'Modelo', q: '¿Dónde vive el diseño?', img: 'frame' },
  { n: '04', name: 'Fundamentos', q: '¿Qué hace realista al diseño?', img: 'anclajes' },
  { n: '05', name: 'Entregables', q: '¿Qué recibe el usuario?', img: 'despiece' },
  { n: '06', name: 'Ejecución', q: '¿Cómo sabemos que está listo?', img: 'exterior' },
];

const LAYERS = [
  ['01', 'Terreno', 'core', 'Lote, vecinos, calles, sol y clima', '—', '02 · 03 · 09'],
  ['02', 'Cimientos', 'core', 'Platea, vigas, refuerzos, pases, anclajes', '01 · 03 · 13', '03'],
  ['03', 'Estructura woodframe', 'core', 'Piso, muros, aberturas, techo, uniones', '02 · 13 · 14', '04–12 · 14'],
  ['04', 'OSB', 'core', 'Layout de placas 1,22 × 2,44', '03', '05 · 06 · 09'],
  ['05', 'Membrana exterior', 'core', 'Rollos, solapes, retornos', '04', '06'],
  ['06', 'Rastreles de siding', 'hook', 'Listones y cámara ventilada', '05', '07'],
  ['07', 'Siding', 'hook', '5 tipos · 6 colores · cantidades', '06', '—'],
  ['08', 'Aislante de paredes', 'hook', 'Lana, barrera de vapor, m²', '03 · 13 · 14', '11'],
  ['09', 'Roofing', 'core', 'OSB, membrana, tejas o chapa', '03', '10'],
  ['10', 'Canaletas', 'hook', 'Tramos, bajadas, pendientes', '09', '01'],
  ['11', 'Durlock', 'hook', 'Placas 1,20 × 2,40, RH en wet rooms', '03 · 08 · 13 · 14', '12'],
  ['12', 'Mobiliario y terminaciones', 'hook', 'Biblioteca básica, pisos, pintura', '11 · 13', '—'],
  ['13', 'Plomería', 'hook', 'Trazado, pases, perforaciones', '03', '02 · 03 · 08 · 11'],
  ['14', 'Eléctrico', 'hook', 'Tablero, circuitos, cajas, cañerías', '03', '03 · 08 · 11'],
];

const TIMBER = [
  ['1" × 2"', '19 × 45', 'Rastreles, listones'], ['1" × 4"', '19 × 95', 'Tapajuntas, terminación'], ['2" × 2"', '45 × 45', 'Rastreles, bloqueos'],
  ['2" × 3"', '45 × 70', 'Tabiques no portantes'], ['2" × 4"', '45 × 95', 'Montantes, soleras'], ['2" × 6"', '45 × 145', 'Montantes ext., cabios'],
  ['2" × 8"', '45 × 195', 'Viguetas, cabios, headers'], ['2" × 10"', '45 × 245', 'Viguetas, headers'], ['2" × 12"', '45 × 295', 'Cumbreras, headers grandes'],
];

const PHASES = [
  ['0', 'Replanteo y nivelación', '01', ''], ['1', 'Excavación, base, film', '02', ''], ['2', 'Desagües y camisas de pases', '13', 'La plomería bajo platea se decide ahora'],
  ['3', 'Armado, pernos, hormigonado', '02 · 13', 'Curado ≥ 7 días'], ['4', 'Soleras y muros por paneles', '03', ''], ['5', 'Cabios, OSB de techo, membrana', '03 · 04 · 09', 'Techo estanco antes de interiores'],
  ['6', 'OSB, membrana, carpinterías', '04 · 05', 'Membrana antes de las carpinterías'], ['7', 'Rastreles, siding, canaletas', '06 · 07 · 10', ''], ['8', 'Agua interior y ventilación cloacal', '13', 'Prueba hidráulica antes de cerrar'],
  ['9', 'Cañerías eléctricas, cajas, tablero', '14', 'Después del cierre exterior, antes del aislante'], ['10', 'Aislante y barrera de vapor', '08', 'Sellar cajas y perforaciones'], ['11', 'Durlock y cielorrasos', '11', 'Sólo con instalaciones aprobadas'],
  ['12', 'Cubierta final, pintura, pisos', '09 · 12', ''], ['13', 'Cableado, artefactos, mobiliario', '12 · 14', 'Prueba eléctrica antes de habilitar'],
];

// ---------------------------------------------------------------- SVG: grafo de capas
function graphSvg() {
  // posiciones en columnas por "altura" constructiva
  const P = {
    '01': [70, 330], '02': [200, 330], '13': [200, 130], '03': [360, 230], '14': [360, 60],
    '04': [520, 330], '05': [640, 330], '06': [760, 330], '07': [880, 330],
    '09': [520, 130], '10': [640, 130], '08': [520, 230], '11': [700, 230], '12': [880, 230],
  };
  const E = [['01', '02'], ['01', '03'], ['01', '09'], ['02', '03'], ['13', '02'], ['13', '03'], ['14', '03'], ['03', '04'], ['04', '05'], ['05', '06'], ['06', '07'], ['03', '09'], ['09', '10'], ['03', '08'], ['13', '08'], ['14', '08'], ['08', '11'], ['13', '11'], ['14', '11'], ['11', '12'], ['12', '13']];
  const hi = new Set(['12', '13', '02', '03', '08', '11']);
  const hiE = new Set(['12-13', '13-02', '13-03', '13-08', '13-11']);
  let s = `<svg class="graph" viewBox="0 0 960 400" role="img" aria-label="Grafo de dependencias entre las 14 capas; se resalta la propagación de mover un artefacto sanitario">`;
  s += `<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5 0 10z"/></marker></defs>`;
  for (const [a, b] of E) {
    const [x1, y1] = P[a], [x2, y2] = P[b];
    s += `<line class="e ${hiE.has(a + '-' + b) ? 'hi' : ''}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" marker-end="url(#ar)"/>`;
  }
  for (const l of LAYERS) {
    const [x, y] = P[l[0]];
    s += `<g class="n ${l[2]} ${hi.has(l[0]) ? 'hi' : ''}"><circle cx="${x}" cy="${y}" r="26"/><text class="num" x="${x}" y="${y + 5}" text-anchor="middle">${l[0]}</text><text class="lbl" x="${x}" y="${y + 46}" text-anchor="middle">${l[1].replace(' woodframe', '').replace(' de paredes', '').replace(' y terminaciones', '').replace(' de siding', '').replace(' exterior', '')}</text></g>`;
  }
  return s + '</svg>';
}

// ---------------------------------------------------------------- diapositivas
function buildSlides(img) {
  const S = [];
  const add = o => S.push(o);
  const divider = c => add({
    ch: c.n, kind: 'divider', title: c.name, cls: 'dark divider',
    body: `<div class="ghost">${c.n}</div><div class="div-copy"><p class="div-ch">CAPÍTULO ${c.n}</p><h2>${c.name}</h2><p class="div-q">${c.q}</p><p class="div-toc" data-toc="${c.n}"></p></div>${fig(img[c.img], '', '', 'div-img')}`
  });
  const lvl = k => `<span class="lvl ${k}">${k === 'core' ? 'NÚCLEO' : 'HOOK'}</span>`;

  // Portada
  add({ ch: '00', kind: 'cover', title: 'Desde el suelo. Pieza por pieza.', cls: 'dark cover', body:
    `<img class="cover-bg" src="${img.aerial}" alt=""><div class="cover-shade"></div>
     <div class="cover-copy"><p class="mono kick">ASSAMBL · MVP_01 · ESPECIFICACIÓN DE LA PRIMERA VERSIÓN · v0.1</p>
     <h1>Desde el suelo.<br><em>Pieza por pieza.</em></h1>
     <p class="lead">Un software para modelar residencias woodframe <em>from the ground up</em>: catorce capas, un solo modelo, planos listos para construir y la secuencia para hacerlo.</p></div>
     <div class="cover-stamp mono"><span>22 · 09 · 2026</span><span>DOCUMENTO DE TRABAJO</span><span>CASO INICIAL · ANGUS RANCH</span></div>
     <p class="cover-cap mono">Imagen de estudio · no es una obra construida</p>` });

  // Mapa
  add({ ch: '00', kind: 'map', title: 'Seis capítulos, una especificación', cls: 'light', body:
    `<div class="map">${CHAPTERS.map(c => `<button class="map-card" data-chapter="${c.n}"><span class="mono">${c.n}</span><strong>${c.name}</strong><em>${c.q}</em><small class="mono" data-range="${c.n}"></small></button>`).join('')}</div>`,
    foot: chip('Dimensiones comerciales y umbrales son valores de partida para el perfil Argentina. Se verifican con proveedores y especialistas antes de usarse en obra.') });

  // Tesis
  add({ ch: '00', kind: 'thesis', title: 'Una casa descrita una vez. Catorce capas coherentes.', cls: 'dark thesis', body:
    `<div class="split thesis-split"><div>
      <p class="lead">El profesional describe la casa una vez. Assambl devuelve una casa coherente en las 14 capas, con planos ejecutables y el orden para construirla. Cada cambio se propaga y marca lo que dejó de estar verificado.</p>
      <div class="two-promises">${row('Realismo material', 'Cada pieza tiene la medida que se compra en una maderera o corralón argentino.')}${row('Coherencia física', 'La platea conoce su carga, el header su luz, la canaleta sus m². Cuando no puede verificarlo, lo dice.')}</div>
     </div>${fig(img.frame, 'Entramado de madera del modelo Angus Ranch V06', '', 'thesis-img')}</div>
     <div class="stats">${stat('14', 'capas en el modelo desde el día uno')}${stat('6', 'capas núcleo: geometría, catálogo, reglas, planos')}${stat('8', 'capas hook: geometría reservada y estados')}${stat('3', 'casas distintas como criterio de éxito')}<p class="stats-src mono">ANGUS RANCH V06 · 828 PIEZAS · BASE DE REGRESIÓN</p></div>` });

  // ---- 01 Alcance
  divider(CHAPTERS[0]);
  add({ ch: '01', title: 'Dominio de partida', cls: 'light', body:
    `<div class="split mvp"><figure class="domain"><img src="${img.planta}" alt="Planta de Angus Ranch V04"><span class="tag t1 mono">1 PLANTA · PLATEA</span><span class="tag t2 mono">ORTOGONAL · ≤ 3 VOLÚMENES</span><span class="tag t3 mono">40–200 M²</span><span class="tag t4 mono">LOTE ≤ 5 % PENDIENTE</span><span class="tag t5 mono">2 AGUAS O 1 AGUA · CABIOS</span><figcaption>Angus Ranch · 164 m² · primer caso; el segundo y el tercero son externos</figcaption></figure>
     <div><p class="eyebrow">ADMITE</p><ul class="pills">${['Muro exterior 45 × 140 / 45 × 95', 'Tabique 45 × 70 / 45 × 95', 'Aberturas de catálogo', 'Pendiente de techo 15–45 %', 'Platea con vigas y refuerzos', 'Instalaciones trazadas, sin cálculo'].map(x => `<li>${x}</li>`).join('')}</ul>
     <p class="eyebrow" style="margin-top:22px">QUEDA FUERA</p><ul class="pills muted">${['Dos plantas', 'Ángulos libres', 'Cerchas y cubiertas planas', 'Pilotes y sótanos', 'SIP · CLT', 'Gas y climatización'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>`,
    foot: chip('Los límites se fijan con especialistas antes de automatizar decisiones técnicas. Lo que excede el dominio no falla en silencio: queda marcado como pendiente.') });

  add({ ch: '01', title: 'Dos niveles de compromiso', cls: 'light', body:
    `<div class="split levels"><div class="lvl-card core"><p class="eyebrow">${lvl('core')} · CAPAS 01–05 Y 09</p><h3 class="large">Construible en MVP_01</h3>
      <ul class="clean">${['Geometría completa, pieza por pieza', 'Catálogo real: escuadrías, placas, rollos', 'Reglas verificables con estado por pieza', 'Planos, detalles y cantidades exportables'].map(x => `<li>${x}</li>`).join('')}</ul></div>
     <div class="lvl-card hook"><p class="eyebrow">${lvl('hook')} · CAPAS 06–08 Y 10–14</p><h3 class="large">Presente, con pendientes explícitos</h3>
      <ul class="clean">${['Geometría reservada y dependencias declaradas', 'Catálogo inicial y cantidades', 'Reglas parciales: lo que no alcanzan queda <code>pendiente</code>', 'Visible en el visor y en la secuencia de ensamble'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>
     <p class="statement">Ninguna capa se omite. La diferencia está en cuánto garantiza el sistema, no en si existe.</p>`,
    foot: chip('Resuelve la diferencia entre el plan v0.1 (fundaciones como referencia, instalaciones como reservas) y la visión de la casa completa.', 'neutral') });

  // ---- 02 Capas
  divider(CHAPTERS[1]);
  add({ ch: '02', title: 'Las catorce capas', cls: 'light g14-slide', body:
    `<div class="g14">${LAYERS.map(l => `<div class="l ${l[2]}"><span class="mono num">${l[0]}</span><strong>${l[1]}</strong><small>${l[3]}</small><span class="dep mono">← ${l[4]} &nbsp;·&nbsp; → ${l[5]}</span></div>`).join('')}</div>`,
    foot: chip('Cada capa es una vista del 3D, un conjunto de piezas con ID y un nodo del grafo de dependencias. ← depende de · → afecta a.', 'neutral') });

  const layers = [
    ['03', 'Estructura', 'Montantes, soleras, headers y cabios.', 'estructura'],
    ['08', 'Aislante', 'Cavidades entre montantes, barrera de vapor.', 'insulation'],
    ['04', 'OSB', 'Placas 1,22 × 2,44 con juntas sobre montantes.', 'osb'],
    ['05', 'Membrana', 'Solapes 150 / 300 mm, retornos en aberturas.', 'wrb'],
    ['06 · 07', 'Rastreles y siding', 'Cámara ventilada de 20 mm y terminación.', 'siding'],
  ];
  add({ ch: '02', title: 'La envolvente, capa por capa', cls: 'light layers-slide', body:
    `<div class="layers" data-layers><div class="layers-stage">${layers.map((l, i) => `<img src="${img[l[3]]}" alt="Capa ${l[1]}" data-layer="${i}" class="${i === 0 ? 'on' : ''}">`).join('')}<figcaption class="mono">ANGUS RANCH V04 · MISMAS MALLAS, DISTINTAS CAPAS</figcaption></div>
     <ol class="layers-list">${layers.map((l, i) => `<li><button data-i="${i}" aria-pressed="${i === 0}"><b class="mono">${l[0]}</b><span><strong>${l[1]}</strong><small>${l[2]}</small></span></button></li>`).join('')}</ol></div>`,
    foot: chip('El visor del MVP_01 extiende esto a las 14 capas con GLB embebidos y three.js; estas cinco ya existen en Angus Ranch V04.', 'neutral') });

  add({ ch: '02', title: 'Terreno y cimientos', cls: 'dark', body:
    `<div class="split base-split"><div>${row('01 · Terreno', 'Lote y contexto desde Topoexport si es viable (DXF/OBJ), o polígono manual. Sol por cálculo astronómico; temperaturas y vientos desde fuente abierta con origen y fecha. Cota 0 ≥ 150 mm sobre terreno; escurrimiento 2 %.')}${row('02 · Platea', 'H-21/H-25, 120–150 mm, vigas de borde y bajo muros portantes 300–400 mm, malla Q188, film 200 µ. Toma la huella de los muros más 100–150 mm.')}${row('Carga y pases', 'Acumula el peso que baja de 03, 04, 08, 09 y 11 por muro y marca <code>pendiente_calculo</code> sobre el umbral. Las camisas de plomería (Ø 50/63/110) se generan antes que el hormigón: sin capa 13, la platea queda <code>incompleta</code>.')}${row('Anclajes', 'Pernos J/L Ø 12,7 mm, empotramiento 180 mm, paso ≤ 1,20 m, lejos de montantes y aberturas. Criterio heredado de V06.')}</div>
     ${fig(img.anclajes, 'Anclajes y cimientos del modelo V06', 'Angus Ranch V06 · capa 10 · anclajes y cimientos', 'bf1')}</div>`,
    foot: chip('El modelo no dimensiona hormigón. Orienta al profesional con la carga acumulada y deja la sección final como decisión revisada.') });

  add({ ch: '02', title: 'Estructura woodframe: madera que se consigue', cls: 'light', body:
    `<div class="split timber"><div><table class="tbl tt"><thead><tr><th>Nominal</th><th>Real (mm)</th><th>Uso principal</th></tr></thead><tbody>${TIMBER.map(t => `<tr><td>${t[0]}</td><td>${t[1]}</td><td>${t[2]}</td></tr>`).join('')}</tbody></table>
      <p class="legend mono">LARGOS 2,44 · 3,05 · 3,66 · 4,27 · 4,88 · 6,10 M · PINO ELLIOTTII/TAEDA · PERFIL AR POR DEFECTO</p></div>
     <div>${row('Muros', 'Solera simple abajo, doble arriba con solape ≥ 1,20 m; montantes a 400/600; esquina de tres montantes; bloqueo escalera en T.')}${row('Aberturas', 'Rough opening = abertura + 10–20 mm por lado. King, jack, header doble con alma, antepecho y cripples derivados. 2 × 6 hasta 1,20 m · 2 × 8 hasta 1,80 · 2 × 10 hasta 2,40 · más: <code>pendiente_calculo</code>.')}${row('Techo', 'Cabios 2 × 6 / 2 × 8 a 600, cumbrera, birdsmouth ≥ 45 mm, rafter ties, alero 300–600.')}${row('Identidad', '<code>Muro_Norte/O1/Header_A</code> · blanco de corte · regla y versión que la generó.')}</div></div>`,
    foot: chip('Límites de header de partida, a ratificar con el especialista. Se hereda de V06: wall(), despiece, cotización por tablas y plan de cortes.') });

  add({ ch: '02', title: 'Cierre exterior y terminaciones', cls: 'light', body:
    `<div class="cards6">${[
      ['04', 'OSB', 'core', '1,22 × 2,44 · 9,5 / 11,1 / 15,1 / 18,3 mm. Vertical en muros con juntas sobre montantes; clavado 150/300. Mapa de placas y desperdicio.'],
      ['05', 'Membrana', 'core', 'Rollos 1,5 / 2,7 / 3,0 × 30 m. Solape 150 horizontal, 300 vertical, retornos en aberturas, antepecho autoadhesivo, cinta.'],
      ['06', 'Rastreles', 'hook', '1 × 2 o 2 × 2 sobre cada montante; cámara ≥ 20 mm; ventilación protegida arriba y abajo.'],
      ['07', 'Siding', 'hook', '5 tipos: madera lap, board & batten, fibrocemento 200 × 3.600, chapa, vinilo. 6 colores. Solape 25–30.'],
      ['09', 'Roofing', 'core', 'Tejas asfálticas (≥ 17 %, rec. 34 %) sobre OSB 15,1 + membrana, o chapa T-101 (≥ 10 %) sobre clavaderas. Cumbrera, aleros, babetas.'],
      ['10', 'Canaletas', 'hook', '100–125 mm, pendiente 0,5–1 %, una bajada Ø 75–100 cada ≤ 12 m o ≤ 60 m², descarga a ≥ 1 m de la platea.'],
    ].map(c => `<div class="c"><span class="mono num">${c[0]}</span>${lvl(c[2])}<h3>${c[1]}</h3><p>${c[3]}</p></div>`).join('')}</div>`,
    foot: chip('Todas las placas, rollos y tablas se contabilizan como piezas enteras, cortadas y desperdicio, para saber cuántas de qué tamaño entran en la casa.', 'neutral') });

  add({ ch: '02', title: 'Interior: aislante, Durlock y mobiliario', cls: 'light', body:
    `<div class="cards3">${[
      ['08', 'Aislante', 'Lana de vidrio 1,20 × 18 m × 50 mm o paneles 70/100; lana de roca; barrera de vapor 200 µ del lado caliente. Cavidades netas descontando cajas (14) y pasajes (13).'],
      ['11', 'Durlock', '1,20 × 2,40 × 12,5 mm; 9,5 en cielorrasos; RH en wet rooms hasta 1,80 m mínimo. Tornillos T2 a 250/300, cinta, masilla. Recortes de cajas y salidas contabilizados.'],
      ['12', 'Mobiliario', 'Biblioteca migrada de V06: cocina, baño, dormitorio, estar, lavadero, exterior. Cada artefacto sanitario trae su punto de conexión para la capa 13. Pisos y pintura por ambiente con 10 % de desperdicio.'],
    ].map(c => `<div class="c"><span class="mono num">${c[0]}</span>${lvl('hook')}<h3>${c[1]}</h3><p>${c[2]}</p></div>`).join('')}</div>
     <div class="band"><strong class="mono">CIRCULACIÓN</strong><span>Pasillos ≥ 900 mm · frente a artefactos ≥ 600 · frente a inodoro ≥ 700. Los artefactos sanitarios sólo se ubican en ambientes marcados como wet room.</span></div>`,
    foot: chip('Capas hook: cantidades completas desde MVP_01; selección automática de espesor por clima y detalles de zócalos en la segunda iteración.', 'neutral') });

  add({ ch: '02', title: 'Instalaciones: trazadas, no calculadas', cls: 'dark', body:
    `<div class="split"><div><p class="eyebrow">13 · PLOMERÍA</p>${row('Desde los wet rooms', 'Cada artefacto genera desagüe y alimentaciones. PVC Ø 40 / 50 / 63 / 110 con pendiente 1–2 % hacia la cámara 60 × 60; agua en PP termofusión o PEX Ø 20 / 25.')}${row('Lo que produce en otras capas', 'Camisas en la platea (02); perforaciones de montante ≤ 40 % no portante / ≤ 25 % portante, o bloqueo, muro húmedo 2 × 6 y <code>pendiente_revision</code> (03); recortes en Durlock (11).')}</div>
     <div><p class="eyebrow">14 · ELÉCTRICO</p>${row('Tablero y circuitos', 'Tablero 12–24 módulos cerca de acometida, a 1,20–1,60 m, nunca en wet rooms. IUG ≤ 15 bocas · TUG ≤ 15 bocas · ACU para termotanque, anafe, aire. Referencia AEA 90364-7-771, parametrizable.')}${row('Recorrido por la estructura', 'Corrugado 20/25 por cavidades; perforaciones centradas Ø ≤ 25 mm; chapa protectora a < 32 mm del borde. Las cajas descuentan aislante (08) y definen el recorte de placa (11).')}</div></div>
     <p class="statement">Salidas: planta sanitaria e isométrico, planta eléctrica y unifilar básico, listados y las tablas de pases y perforaciones que reciben cimientos y estructura.</p>`,
    foot: chip('Sin cálculo hidráulico ni verificación normativa completa. Dimensiones de práctica habitual; la revisión profesional sigue siendo necesaria.') });

  // ---- 03 Modelo
  divider(CHAPTERS[2]);
  add({ ch: '03', title: 'De un script a un modelo', cls: 'light', body:
    `<div class="split cmp"><div class="cmp-col was"><p class="eyebrow">HOY · ANGUS RANCH V06</p><h3 class="large">Un script de 2.200 líneas en Blender</h3><ul class="clean">${['Datos y lógica mezclados: cambiar la casa es editar código', 'Dependencias implícitas en el orden de las funciones', 'Blender como única salida; las ediciones no vuelven', 'Advertencias en el LEEME, no en el modelo', 'Cada casa nueva es una copia del script'].map(x => `<li>${x}</li>`).join('')}</ul></div>
     <div class="cmp-col will"><p class="eyebrow">MVP_01 · ASSAMBL</p><h3 class="large">Proyecto + catálogo + reglas + generadores</h3><ul class="clean">${['<code>casa.assambl.json</code> versionado, editable por operaciones', 'Grafo de capas explícito; recalcula sólo lo alcanzado', 'Blender, GLB, SVG, CSV y HTML salen del mismo modelo', 'Estados por pieza, regla y capa', 'Angus Ranch es un caso de prueba: debe reproducir sus 828 piezas'].map(x => `<li>${x}</li>`).join('')}</ul></div></div>`,
    foot: chip('Seccionar el script no alcanza: no da edición sin código, ni estados, ni propagación selectiva, ni independencia de Blender.', 'neutral') });

  add({ ch: '03', title: 'Cuatro partes con contratos claros', cls: 'light', body:
    `<div class="arch"><div class="tier t-top"><span class="tier-l mono">INTERCAMBIABLE</span><div class="box">Panel en Blender</div><div class="box">Interfaz propia<br>(planta + 3D)</div><div class="box ai">Asistente IA<br><small>llama operaciones, no escribe geometría</small></div></div>
     <div class="tier t-mid"><span class="tier-l mono">CONTRATO</span><div class="box wide">Operaciones · crear_muro · modificar_abertura · marcar_wet_room · ubicar_artefacto · ubicar_tablero · elegir_material</div></div>
     <div class="tier t-core"><span class="tier-l mono">PERMANENTE</span><div class="box">Catálogo<br><small><code>catalogo/ar.json</code> · escuadrías, placas, rollos, artefactos · perfil por mercado</small></div><div class="box core">Proyecto<br><small><code>casa.assambl.json</code> · terreno, muros, aberturas, wet rooms, materiales, historial</small></div><div class="box">Reglas<br><small>módulos Python puros · ID, versión, origen, alcance</small></div></div>
     <div class="tier t-mid"><span class="tier-l mono">GENERADORES</span><div class="box wide">Motor de capas → modelo resuelto → Blender · GLB · planos SVG · CSV · HTML · secuencia</div></div></div>`,
    foot: chip('El modelo resuelto (piezas con ID y estados) se guarda como caché regenerable. La fuente de verdad es siempre el proyecto declarativo.', 'neutral') });

  add({ ch: '03', title: 'El grafo de capas propaga los cambios', cls: 'dark graph-slide', body:
    `<div class="split graph-split">${graphSvg()}<aside class="win-log b"><p class="mono head"><span class="st stB">OPERACIÓN · UBICAR_ARTEFACTO · INODORO +300 MM ESTE</span></p>
      <ul class="log">
       <li class="a"><b>12 · Mobiliario</b> · nuevo punto de conexión</li>
       <li class="a"><b>13 · Plomería</b> · ramal Ø 110 rehecho · nuevo pase</li>
       <li class="a"><b>02 · Cimientos</b> · camisa movida · platea <em>desactualizada</em></li>
       <li class="a warn"><b>03 · Estructura</b> · perforación sobre montante → bloqueo · <em>pendiente_revision</em></li>
       <li class="a"><b>08 · 11</b> · cavidad y recorte de placa recalculados</li>
       <li class="a ok">04 · 05 · 06 · 07 · 09 · 10 · 14 sin cambios · diff registrado en el historial</li>
      </ul></aside></div>`,
    foot: chip('Cimientos ↔ plomería ↔ estructura se resuelven en dos pasadas: reservas primero, geometría después. Se recalculan sólo las capas alcanzables desde el cambio.', 'neutral') });

  add({ ch: '03', title: 'Cada pieza sabe en qué estado está', cls: 'light', body:
    `<div class="split identity"><div class="card-id mono"><p class="id">Muro_Norte/O1/Header_A</p>
      <dl><dt>catálogo</dt><dd>2" × 8" · 45 × 195 mm · pino</dd><dt>largo</dt><dd>1.890 mm · blanco de corte 1.900</dd><dt>pertenece</dt><dd>Muro Norte → Abertura O1</dd><dt>regla</dt><dd>R03.header_doble v0.4 · Thallon 68C</dd><dt>estado</dt><dd><i class="dot warn"></i>pendiente_calculo · luz &gt; 1,80 m</dd><dt>afecta</dt><dd>04 OSB (recorte) · 02 carga lineal</dd><dt>historial</dt><dd>creado v03 · modificado v12 (ampliar O1)</dd></dl></div>
     <div><p class="eyebrow">ESTADOS</p><div class="states">${[['propuesto', 'Generado por reglas, sin verificación específica'], ['comprobado_por_reglas', 'Todas las reglas aplicables se cumplen'], ['pendiente_datos', 'Falta una entrada: wet rooms sin definir'], ['pendiente_calculo', 'La regla reconoce que excede su alcance'], ['pendiente_revision', 'Heurística aplicada; debe mirarla una persona'], ['revisado', 'Aprobado por un usuario identificado en una versión'], ['desactualizado', 'Estaba revisado y un cambio lo invalidó']].map(s => `<div><code>${s[0]}</code><span>${s[1]}</span></div>`).join('')}</div></div></div>`,
    foot: chip('Los estados viven en el modelo, no en un LEEME. El visor, los planos y el paquete los muestran; ninguna salida es silenciosa.', 'neutral') });

  // ---- 04 Fundamentos
  divider(CHAPTERS[3]);
  add({ ch: '04', title: 'Seis familias de verdades', cls: 'light', body:
    `<div class="cards6 fam">${[
      ['Geométricas', 'Las piezas ocupan espacio real y no se superponen. Montantes centrados, placas sin solape, jambas mínimas.'],
      ['De catálogo', 'Todo lo modelado se puede comprar. Cada pieza referencia un ítem; largos ≤ comercial o empalme declarado.'],
      ['Constructivas', 'Las uniones son las del sistema woodframe. Solera doble, esquina de tres, header doble, solape de membrana, clavado.'],
      ['Físicas simplificadas', 'La casa responde a gravedad y agua. Carga acumulada a la platea; pendientes mínimas; el agua va hacia abajo y afuera.'],
      ['Normativas de referencia', 'Las instalaciones no contradicen práctica conocida. AEA 90364; diámetros por artefacto; RH en wet rooms.'],
      ['De secuencia', 'El orden de construcción es posible. Pases antes de hormigonar; cableado antes de aislar; Durlock con instalaciones aprobadas.'],
    ].map((f, i) => `<div class="c"><span class="mono num">0${i + 1}</span><h3>${f[0]}</h3><p>${f[1]}</p></div>`).join('')}</div>`,
    foot: chip('Origen conservado: Woodframe fundamentals, Thallon, manuales de fabricantes y AEA. Las medidas de libros extranjeros no se presentan como reglamento argentino.', 'neutral') });

  add({ ch: '04', title: 'Cómo se escribe una regla', cls: 'dark', body:
    `<div class="split rule-split"><div class="card-id mono rule"><p class="id">R03.header_doble · v0.4</p>
      <dl><dt>origen</dt><dd>Woodframe fundamentals · Thallon 68C · revisión especialista pendiente</dd><dt>aplica si</dt><dd>abertura en muro exterior o portante · luz ≤ 2,40 m</dd><dt>parámetros</dt><dd>luz → sección: ≤ 1,20 → 2×6 · ≤ 1,80 → 2×8 · ≤ 2,40 → 2×10</dd><dt>produce</dt><dd>Header_A · Header_B · alma 12,5 · jacks · cripples</dd><dt>otorga</dt><dd>comprobado_por_reglas dentro del rango · pendiente_calculo fuera</dd><dt>prueba</dt><dd>Angus Ranch · 24 headers · mismos IDs y dimensiones que V06</dd></dl></div>
     <div><p class="eyebrow">PRINCIPIOS</p>${row('Alcance explícito', 'Cada regla dice qué cubre. Fuera de alcance emite un estado, no un resultado plausible.')}${row('Reproducibilidad', 'Mismo proyecto, catálogo y versiones → mismo modelo, byte a byte. Base del diff y de la regresión.')}${row('Parámetros, no constantes', 'Separaciones, solapes y umbrales con valor por defecto y rango admitido por cliente.')}${row('Revisión antes de automatizar', 'Ninguna regla estructural otorga <code>comprobado</code> sin el especialista en estructuras de madera.')}</div></div>`,
    foot: chip('La interfaz no muestra bibliografía. El origen y la versión se conservan internamente para mantener las reglas.', 'neutral') });

  // ---- 05 Entregables
  divider(CHAPTERS[4]);
  add({ ch: '05', title: 'Seis entregables desde un solo comando', cls: 'light', body:
    `<div class="rail rail6">${[['01', 'Planos', 'SVG → PDF, cotas en mm, ready to build.'], ['02', 'Detalles', '10 detalles paramétricos de uniones y capas.'], ['03', 'HTML interactivo', 'Un archivo, 14 capas en 3D, ≤ 40 MB.'], ['04', 'Secuencia', 'Instructivo por fases desde el grafo.'], ['05', 'Perspectivas', '8 vistas con cámaras por regla.'], ['06', 'Render animado', 'No prioritario; opciones evaluadas.']].map(e => `<div><span class="mono">${e[0]}</span><h3>${e[1]}</h3><p>${e[2]}</p></div>`).join('')}</div>
     <div class="band"><strong class="mono">UN COMANDO</strong><span><code>assambl exportar casa.assambl.json --paquete</code> → carpeta con fecha y versión: planos, detalles, HTML, secuencia, perspectivas, CSV de cantidades y pendientes.</span></div>`,
    foot: chip('Todos salen del modelo resuelto. No hay copias que se desincronicen entre planos, visor y listados.', 'neutral') });

  add({ ch: '05', title: 'Planos listos para construir', cls: 'light', body:
    `<div class="plans">${[['Implantación', '01'], ['Planta de platea', '02 · 13'], ['Planta arquitectónica', '03 · 12'], ['Planta estructural', '03'], ['Entramado por muro', '03'], ['Cabios y techos', '03 · 09 · 10'], ['Mapas de placas OSB / Durlock', '04 · 11'], ['Fachadas', '07'], ['Cortes', '02–11'], ['Sanitaria + isométrico', '13'], ['Eléctrica + unifilar', '14']].map(p => `<div><strong>${p[0]}</strong><span class="mono">CAPAS ${p[1]}</span></div>`).join('')}</div>
     <div class="split" style="margin-top:22px;align-items:end">${fig(img.despiece, 'Despiece de madera de Angus Ranch V06', 'V06 · despiece por uso, sector y dimensiones · base del plano de entramado', 'plan-fig')}<p class="statement small">Escala declarada, norte, rótulo con versión del proyecto y estado de revisión. El plano de entramado por muro muestra cada pieza acotada e identificada; es el que un constructor woodframe debe reconocer como ejecutable.</p></div>`,
    foot: chip('Criterio de aceptación: al menos un constructor externo revisa los planos de entramado y los considera ejecutables, en una revisión documentada.', 'neutral') });

  add({ ch: '05', title: 'Detalles de partes clave', cls: 'dark base', body:
    `<div class="split base-split"><div class="base-figs">${fig(img.header, 'Vista explotada de un header doble', 'Header doble · explotado · V06', 'bf1')}${fig(img.holddown, 'Corte de anclaje de solera y hold-down', 'Anclaje y hold-down · V06', 'bf2')}</div>
     <ol class="details">${['Anclaje solera–platea con perno y junta', 'Header doble con alma, king, jack y cripples', 'Esquina exterior de tres montantes, capa por capa', 'Encuentro T con bloqueo escalera', 'Solape de solera superior doble', 'Apoyo de cabio: birdsmouth, bloqueo, frontis', 'Corte completo de pared: Durlock → siding, espesores acotados', 'Antepecho: membrana autoadhesiva, retornos, gotero', 'Pase de desagüe en platea con camisa', 'Perforación de montante para cañería con protección'].map(d => `<li>${d}</li>`).join('')}</ol></div>`,
    foot: chip('Detalles paramétricos: se dibujan con las dimensiones reales del proyecto, no como láminas fijas. Los dos primeros ya existen en V06.', 'neutral') });

  add({ ch: '05', title: 'La casa en un solo archivo HTML', cls: 'light', body:
    `<div class="split"><div>${row('Mismo lenguaje que esta presentación', 'Láminas, índice, modo lectura y documento embebido con <code>pp_shell.cjs</code>. Se agrega el visor.')}${row('Lámina “capa por capa”', 'three.js con las 14 capas como GLB embebidos. Activar, apagar, apilar en orden de ensamble y orbitar. Ficha por capa: piezas, m², cantidades, estado.')}${row('Lámina de cambios', 'El último diff del historial sobre el modelo: nuevas, modificadas, eliminadas.')}${row('Planos, detalles y secuencia', 'SVG navegables y línea de tiempo sincronizada con el visor.')}</div>
     <div class="callout"><p class="eyebrow">RESTRICCIÓN</p><p class="big-num">≤ 40 MB</p><p>Para compartir por correo o link directo. GLB simplificado por capa, muebles en baja densidad, texturas procedurales.</p><p class="small">Abre sin conexión en un navegador de escritorio. Tipografías externas opcionales.</p></div></div>`,
    foot: chip('El visor no depende de Blender en el navegador. Blender sigue siendo prototipado, render y verificación visual.', 'neutral') });

  add({ ch: '05', title: 'Secuencia de ensamble: el orden importa', cls: 'light seq-slide', body:
    `<div class="seq">${PHASES.map(p => `<div class="${p[3] ? 'warn' : ''}"><span class="mono num">F${p[0]}</span><strong>${p[1]}</strong><span class="mono cap">CAPAS ${p[2]}</span>${p[3] ? `<small>⚠ ${p[3]}</small>` : ''}</div>`).join('')}</div>`,
    foot: chip('Generada desde el grafo y las reglas de secuencia. Cada fase enlaza los planos y detalles que usa y la lista de materiales que hay que tener en obra.', 'neutral') });

  add({ ch: '05', title: 'Perspectivas y render animado', cls: 'dark', body:
    `<div class="split"><div><p class="eyebrow">05 · PERSPECTIVAS · EN MVP_01</p>${row('Ocho vistas por regla', 'Cuatro exteriores (una por esquina), dos interiores (estar, cocina), una axonométrica explotada por capas y una aérea con el lote.')}${row('Cámaras fijadas por regla', 'Altura de ojo 1,60 m, distancia proporcional al ancho de la casa. Todas las casas se presentan igual. Render en Blender Eevee.')}</div>
     <div><p class="eyebrow">06 · RENDER ANIMADO · NO PRIORITARIO</p><div class="options">${[['Órbita automática en three.js', 'Costo nulo · ya viene con el visor'], ['Apilado animado de las 14 capas', 'Costo bajo · misma tecnología'], ['Video MP4 desde Blender', 'Costo medio · órbita 15–20 s, ffmpeg'], ['Recorrido interior con cámara', 'Costo alto · segunda etapa']].map((o, i) => `<div><span class="mono">0${i + 1}</span><strong>${o[0]}</strong><small>${o[1]}</small></div>`).join('')}</div></div></div>`,
    foot: chip('Las opciones 1 y 2 salen gratis del visor; se evalúan las demás cuando el núcleo esté cerrado.', 'neutral') });

  // ---- 06 Ejecución
  divider(CHAPTERS[5]);
  add({ ch: '06', title: 'Criterios de aceptación', cls: 'light', body:
    `<ol class="crit">${['Tres casas distintas (Angus Ranch + dos externas) completan las 14 capas y exportan el paquete sin intervención del desarrollador.', 'El modelo declarativo de Angus Ranch reproduce las 828 piezas de V06: mismos IDs, dimensiones y cotización.', 'Cada pieza referencia un ítem del catálogo argentino; ningún largo supera el comercial sin empalme declarado.', '<code>modificar_abertura</code>, <code>mover_muro</code> y <code>ubicar_artefacto</code> propagan a las capas afectadas, dejan intactas las demás y producen un diff legible.', 'Un constructor woodframe externo reconoce los planos de entramado como ejecutables, en revisión documentada.', 'La secuencia incluye las advertencias de plomería en cimientos y cableado antes de aislar; cada fase enlaza planos y materiales.', 'El HTML abre sin conexión, muestra las 14 capas y pesa ≤ 40 MB.', 'Las cantidades coinciden con las piezas únicas; las copias de presentación no se suman.', 'Todo lo fuera de alcance lleva un estado <code>pendiente_*</code> visible. No hay salidas silenciosas.'].map(c => `<li>${c}</li>`).join('')}</ol>`,
    foot: chip('Se miden al cierre de H4. Si un criterio no se cumple, se recorta alcance de los hooks, no se corre la fecha ni se relaja el núcleo.', 'neutral') });

  const HITOS = [[1, 4, 'H0 · Modelo y motor', 'Esquema, catálogo AR v0, registro de reglas, grafo, migración de wall() y despiece. Angus Ranch declarativa.', 'Regresión 828 piezas · modificar_abertura con diff'], [5, 10, 'H1 · Núcleo de la envolvente', 'Capas 01 simple, 02, 03, 04, 05, 09. Planos de entramado, platea y techo. Detalles 1–8.', 'Segunda casa (externa) exporta planos revisables'], [11, 16, 'H2 · Hooks y visor', 'Capas 06, 07, 08, 10, 11, 12. Visor three.js con 14 capas. Perspectivas.', 'Tercera casa · HTML ≤ 40 MB · revisión de constructor'], [17, 22, 'H3 · Instalaciones y secuencia', 'Capas 13 y 14 con propagación a 02, 03, 08, 11. Secuencia de ensamble. Detalles 9–10.', 'Mover un baño propaga a platea y estructura'], [23, 26, 'H4 · Cierre', 'Historial y deshacer, estados de revisión, paquete completo, correcciones de pilotos.', 'Criterios de aceptación cumplidos']];
  add({ ch: '06', title: 'Cinco hitos, 26 semanas', cls: 'light', body:
    `<div class="roadmap" style="--cols:repeat(26,1fr)"><div class="months mono">${HITOS.map(h => `<span style="grid-column:${h[0]} / ${h[1] + 1}">SEM ${h[0]}–${h[1]}</span>`).join('')}</div>
     <div class="phases">${HITOS.map(h => `<div class="ph" style="grid-column:${h[0]} / ${h[1] + 1}"><span class="mono range">${h[1] - h[0] + 1} SEMANAS</span><h3>${h[2]}</h3><p>${h[3]}</p><p class="gate mono">◆ ${h[4]}</p></div>`).join('')}</div></div>`,
    foot: chip('Plazos orientativos con dedicación técnica sostenida, alineados a los 4–6 meses del plan v0.1. Cada hito cierra con una casa exportable, no con una lista de funciones.') });

  add({ ch: '06', title: 'Riesgos del MVP_01', cls: 'light', body:
    `<div class="risk-grid">${[['Catorce capas dispersan el esfuerzo', 'Ninguna capa termina exportable', 'Congelar hooks en versión mínima; cerrar núcleo primero'], ['Catálogo no coincide con la oferta real', 'Madereras sin 2 × 8 en 6,10 m', 'Verificar con dos proveedores en semana 2; el catálogo es dato, no código'], ['Topoexport no cubre o no licencia', 'Sin lote real importable', 'Polígono manual desde el inicio; Topoexport como mejora'], ['Reglas estructurales plausibles pero erradas', 'Especialista rechaza headers por defecto', 'Estados pendiente_calculo amplios; nunca comprobado sin especialista'], ['Grafo inmanejable', 'Cambios menores regeneran todo', 'Dependencias declaradas por capa; pruebas de propagación por operación'], ['GLB demasiado pesado', 'HTML > 40 MB', 'Simplificación por capa, muebles en baja densidad'], ['Migrar V06 consume el producto', 'Semana 6 sin caso externo', 'Regresión con tolerancia; se completa después del caso externo']].map(r => `<div><strong>${r[0]}</strong><span><b class="mono">SEÑAL</b>${r[1]}</span><span><b class="mono">RESPUESTA</b>${r[2]}</span></div>`).join('')}</div>`,
    foot: chip('Complementan los riesgos generales del plan v0.1: alcance excesivo, modelo vistoso pero inconsistente, dependencia de una sola casa.') });

  add({ ch: '06', title: 'Ocho preguntas abiertas', cls: 'light', body:
    `<div class="qgrid">${[['Muro exterior', '¿45 × 140 con alma de contrachapado como V06, o 2 × 6 real (45 × 145)? Decidir con especialista y dos madereras.'], ['Piso', '¿Piso sobre viguetas además de platea directa, o se posterga?'], ['Topoexport', 'Confirmar licencia, formatos y cobertura en Córdoba; probar en tres lotes.'], ['Cubierta', '¿Tejas y chapa en H1, o chapa primero por frecuencia local?'], ['Catálogo por cliente', '¿Edita su catálogo desde el inicio o elige entre perfiles?'], ['Interfaz de edición', 'Panel en Blender o interfaz propia. No bloquea H0–H1.'], ['Hooks en el visor', '¿Se muestran al usuario del piloto con estado pendiente, o sólo al equipo?'], ['Unidades', '¿Nominales en pulgadas en la interfaz y mm en planos?']].map((q, i) => `<div><span class="mono">0${i + 1}</span><strong>${q[0]}</strong><p>${q[1]}</p></div>`).join('')}</div>`,
    foot: chip('Se resuelven durante H0. Las respuestas actualizan este documento a MVP_01 v0.2.', 'neutral') });

  // Cierre
  add({ ch: '06', kind: 'closing', title: 'La casa completa como horizonte. Seis capas como primer suelo firme.', cls: 'dark closing', body:
    `<img class="cover-bg dim" src="${img.aerial}" alt=""><div class="cover-shade strong"></div>
     <div class="close-copy"><h2>La casa completa como horizonte.<br><em>Seis capas como primer suelo firme.</em></h2>
     <p class="lead">Catorce capas en el modelo desde el día uno; seis resueltas hasta el plano ejecutable; ocho presentes con pendientes explícitos. Tres casas para demostrarlo.</p>
     <div class="actions"><button class="primary" data-action="doc">Leer la especificación completa</button><button class="ghost-btn" data-action="restart">Volver al inicio</button></div>
     <p class="mono end-note">PRÓXIMO PASO · H0: ESQUEMA DEL PROYECTO, CATÁLOGO ARGENTINA v0, REGISTRO DE REGLAS Y ANGUS RANCH DECLARATIVA CON REGRESIÓN DE 828 PIEZAS.</p></div>` });

  return S;
}

// ---------------------------------------------------------------- CSS adicional de esta presentación
const extraCss = `
.lvl{display:inline-block;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;padding:3px 7px;border:1px solid var(--wood);color:var(--wood);vertical-align:2px;margin-right:6px}
.lvl.hook{border-color:var(--muted);color:var(--muted)}
.dark .lvl{border-color:var(--wood2);color:var(--wood2)}
code{font-family:var(--mono);font-size:.85em;background:rgba(15,27,23,.06);padding:1px 5px;border-radius:2px}
.dark code{background:rgba(245,242,234,.1)}
.pre.code,pre.code{font-family:var(--mono);font-size:13px;line-height:1.5;background:var(--paper2);padding:16px 18px;overflow:auto;margin:16px 0}
.pills.muted li{color:var(--muted);background:transparent;border-style:dashed}
.levels{gap:28px}
.lvl-card{padding:28px 30px;border:1px solid var(--line);background:#fff;min-height:330px}
.lvl-card.hook{background:var(--paper2);border-style:dashed}
.lvl-card .large{margin-bottom:18px!important}
.lvl-card .clean li{font-size:16.5px}
.g14{display:grid;grid-template-columns:repeat(7,1fr);gap:10px}
.g14 .l{background:#fff;border:1px solid var(--line);border-top:3px solid var(--wood);padding:14px 12px 12px;min-height:200px;display:flex;flex-direction:column;gap:6px}
.g14 .l.hook{border-top-color:var(--muted);background:var(--paper2)}
.g14 .num{color:var(--wood);font-size:13px}
.g14 .l.hook .num{color:var(--muted)}
.g14 strong{font-size:15.5px;line-height:1.2;letter-spacing:-.01em}
.g14 small{font-size:12.5px;color:var(--muted);line-height:1.35;flex:1}
.g14 .dep{font-size:9px;color:var(--muted);letter-spacing:.04em;text-transform:none;border-top:1px solid var(--line);padding-top:8px}
.timber{grid-template-columns:.95fr 1.05fr;gap:44px}
.tbl.tt td,.tbl.tt th{text-align:left;padding:8px 10px 8px 0;font-size:14.5px}
.tbl.tt td:first-child{font-family:var(--mono);font-size:13px;letter-spacing:.02em;text-transform:none}
.cards6{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cards6 .c,.cards3 .c{background:#fff;border:1px solid var(--line);padding:20px 20px 18px;min-height:170px}
.cards6 .num,.cards3 .num{color:var(--wood);font-size:12px;margin-right:8px}
.cards6 h3,.cards3 h3{font-family:var(--serif);font-weight:400;font-size:24px;margin:8px 0 8px;letter-spacing:-.01em}
.cards6 p,.cards3 p{font-size:14.5px;color:var(--muted);line-height:1.4}
.cards6.fam .c{min-height:220px}
.cards6.fam p{font-size:15.5px}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.cards3 .c{min-height:250px}
.cmp{gap:28px}
.cmp-col{padding:28px 30px;border:1px solid var(--line);min-height:420px}
.cmp-col.was{background:var(--paper2)}
.cmp-col.will{background:#fff;border-color:var(--wood)}
.cmp-col .large{margin-bottom:18px!important;font-size:26px}
.cmp-col .clean li{font-size:16px}
.graph-split{grid-template-columns:1.2fr .8fr;gap:40px;align-items:start}
.graph{width:100%;display:block}
.graph .e{stroke:#4F5E57;stroke-width:1.2;fill:none}
.graph .e.hi{stroke:var(--red);stroke-width:2.2}
.graph marker path{fill:#4F5E57}
.graph .n circle{fill:var(--ink2);stroke:var(--wood2);stroke-width:1.5}
.graph .n.hook circle{stroke:#7E8A83;stroke-dasharray:3 3}
.graph .n.hi circle{fill:var(--wood);stroke:var(--wood2)}
.graph .num{font-family:var(--mono);font-size:15px;fill:#EDE9DF;font-weight:500}
.graph .n.hi .num{fill:var(--ink)}
.graph .lbl{font-size:11px;fill:#B4BFB8}
.graph-slide .win-log{min-height:0}
.dot.warn{background:#F1B08E}
.base-split .li p{font-size:15.5px}
.states>div{display:grid;grid-template-columns:230px 1fr;gap:16px;padding:9px 0;border-bottom:1px solid var(--line);font-size:14.5px;align-items:baseline}
.states code{font-size:12.5px}
.rule-split{grid-template-columns:1.05fr .95fr;gap:44px}
.card-id.rule dl{grid-template-columns:110px 1fr}
.rail6{grid-template-columns:repeat(6,1fr);gap:18px}
.rail6 h3{font-size:24px}
.rail6 p{font-size:14.5px}
.rail6>div{min-height:150px}
.plans{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.plans>div{background:#fff;border:1px solid var(--line);padding:12px 14px;display:flex;flex-direction:column;gap:4px}
.plans strong{font-size:14.5px}
.plans .mono{font-size:9.5px;color:var(--wood)}
.plan-fig img{max-height:190px;object-fit:contain}
.details{margin:0;padding-left:0;list-style:none;counter-reset:d}
.details li{counter-increment:d;position:relative;padding:9px 0 9px 44px;border-bottom:1px solid var(--line-d);font-size:15.5px;color:#EDE9DF}
.details li::before{content:counter(d,decimal-leading-zero);position:absolute;left:0;top:10px;font-family:var(--mono);font-size:11px;color:var(--wood2);letter-spacing:.06em}
.seq{display:grid;grid-template-columns:repeat(7,1fr);gap:10px}
.seq>div{background:#fff;border:1px solid var(--line);padding:14px 12px 12px;min-height:200px;display:flex;flex-direction:column;gap:6px;position:relative}
.seq>div.warn{border-color:var(--wood);background:#FBF6EE}
.seq .num{color:var(--wood);font-size:12px}
.seq strong{font-size:14.5px;line-height:1.25;letter-spacing:-.01em;flex:1}
.seq .cap{font-size:9px;color:var(--muted);letter-spacing:.06em}
.seq small{font-size:11.5px;color:var(--wood);line-height:1.35;border-top:1px dashed var(--line);padding-top:6px}
.options>div{display:grid;grid-template-columns:34px 1fr;gap:4px 12px;padding:12px 0;border-bottom:1px solid var(--line-d)}
.options .mono{color:var(--wood2);padding-top:4px;grid-row:span 2}
.options strong{font-size:17px;color:#EDE9DF}
.options small{font-size:13px;color:#9AA79F}
.crit{margin:0;padding:0;list-style:none;counter-reset:c;display:grid;grid-template-columns:1fr 1fr;gap:0 40px}
.crit li{counter-increment:c;position:relative;padding:11px 0 11px 46px;border-bottom:1px solid var(--line);font-size:15.5px;line-height:1.4}
.crit li::before{content:counter(c,decimal-leading-zero);position:absolute;left:0;top:13px;font-family:var(--mono);font-size:12px;color:var(--wood);letter-spacing:.06em}
.risk-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px 28px}
.risk-grid>div{display:grid;grid-template-columns:1.1fr 1fr 1.3fr;gap:14px;padding:11px 0;border-bottom:1px solid var(--line);font-size:13.5px;align-items:start}
.risk-grid strong{font-size:14.5px;line-height:1.3}
.risk-grid span{color:var(--muted);line-height:1.35}
.risk-grid b{display:block;font-size:9px;color:var(--wood);margin-bottom:3px}
.qgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.qgrid>div{background:#fff;border:1px solid var(--line);padding:18px 18px 16px;min-height:200px}
.qgrid .mono{color:var(--wood);display:block;margin-bottom:10px}
.qgrid strong{font-family:var(--serif);font-weight:400;font-size:24px;letter-spacing:-.01em;display:block;margin-bottom:8px}
.qgrid p{font-size:14.5px;color:var(--muted);line-height:1.4}
.reading .g14,.reading .seq,.reading .cards6,.reading .cards3,.reading .qgrid,.reading .plans,.reading .rail6,.reading .crit,.reading .risk-grid,.reading .levels,.reading .cmp,.reading .graph-split,.reading .timber,.reading .rule-split{grid-template-columns:1fr}
.reading .risk-grid>div{grid-template-columns:1fr}
`;

// ---------------------------------------------------------------- HTML
async function main() {
  const img = await prepareAssets();
  const slides = buildSlides(img);
  const total = slides.length;
  const pad = n => String(n).padStart(2, '0');
  const plain = t => t.replace(/<br>/g, ' ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  const ranges = {}; slides.forEach((s, i) => { if (s.ch === '00') return; (ranges[s.ch] ||= []).push(i + 1); });
  const chapterName = ch => (CHAPTERS.find(c => c.n === ch) || { name: 'Introducción' }).name;

  const sectionHtml = slides.map((s, i) => {
    const isCover = s.kind === 'cover' || s.kind === 'closing';
    const head = `<header class="s-head mono"><span>${isCover ? (s.kind === 'cover' ? 'ASSAMBL · MVP_01 · ESPECIFICACIÓN' : 'CIERRE') : `<b>${pad(i + 1)}</b>— ${chapterName(s.ch).toUpperCase()}`}</span><span class="s-stamp">${STAMP} · HOJA ${pad(i + 1)}/${total}</span></header>`;
    const title = (isCover || s.kind === 'divider') ? '' : `<h2>${s.title}</h2>`;
    const foot = isCover ? '' : `<footer class="s-foot">${s.foot || '<span></span>'}<span class="s-mark">Assambl · MVP_01 · especificación v0.1</span></footer>`;
    const marks = '<i class="cm tl"></i><i class="cm tr"></i><i class="cm bl"></i><i class="cm br"></i>';
    return `<section class="slide ${s.cls} ${i === 0 ? 'active' : ''}" data-title="${esc(plain(s.title))}" data-chapter="${s.ch}" data-kind="${s.kind || 'content'}" aria-label="Diapositiva ${i + 1}: ${esc(plain(s.title))}" aria-hidden="${i !== 0}">${marks}${head}${title}<div class="s-body">${s.body}</div>${foot}</section>`;
  }).join('');

  const tocText = {}; for (const c of CHAPTERS) tocText[c.n] = (ranges[c.n] || []).slice(1).map(n => `${pad(n)} ${plain(slides[n - 1].title)}`).join(' · ');
  const rangeText = {}; for (const c of CHAPTERS) { const r = ranges[c.n] || []; rangeText[c.n] = `HOJAS ${pad(r[0])}–${pad(r[r.length - 1])}`; }
  const dividerIndex = {}; slides.forEach((s, i) => { if (s.kind === 'divider') dividerIndex[s.ch] = i; });

  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><title>Assambl — MVP_01 · Especificación v0.1</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>${css}${extraCss}</style></head><body>
<header class="topbar mono"><span class="brand"><i></i>ASSAMBL <span>— MVP_01 · ESPECIFICACIÓN v0.1</span></span><div class="top-actions"><button id="indexBtn">Índice</button><button id="docBtn">Documento completo</button><button id="readingBtn" aria-pressed="false">Lectura</button><button id="fullscreen" aria-label="Pantalla completa">⛶</button></div></header>
<main class="stage" aria-label="Presentación del MVP_01">${sectionHtml}</main>
<nav class="nav mono" aria-label="Navegación"><button id="prev" aria-label="Anterior">←</button><span class="counter" id="counter"></span><span class="nav-title" id="navTitle"></span><button id="next" aria-label="Siguiente">→</button><span class="keyhint">← → navegar · I índice · F pantalla completa</span></nav>
<div class="progress" id="progress"></div><div class="sr-only" role="status" aria-live="polite" id="live"></div>
<dialog id="indexDialog" class="index-dialog" aria-labelledby="indexHeading"><div class="dialog-head"><strong id="indexHeading">Contenido</strong><button data-close="indexDialog">Cerrar ×</button></div><div class="index-list">${slides.map((s, i) => `<button data-slide="${i}" class="${s.kind === 'divider' ? 'div' : ''}"><span>${pad(i + 1)}</span>${plain(s.title)}</button>`).join('')}</div></dialog>
<dialog id="docDialog" class="doc-dialog" aria-labelledby="docHeading"><div class="dialog-head"><strong id="docHeading">MVP_01 · texto completo</strong><button data-close="docDialog">Cerrar ×</button></div><article class="document">${markdownExt(source)}</article></dialog>
<script>
${script(tocText, rangeText, dividerIndex)}
</script></body></html>`;
  fs.writeFileSync(path.join(root, OUT), html, 'utf8');
  console.log(JSON.stringify({ slides: total, bytes: Buffer.byteLength(html), output: OUT }));
}
main().catch(e => { console.error(e); process.exit(1); });
