// Genera PP_YC_W27.html: el plan de trabajo hacia la aplicación a Y Combinator W27,
// con el mismo motor visual que PP_Fable_WF.html.
// Uso:  node build_pp_yc.cjs [--refresh]   (--refresh reprocesa las imágenes)
const fs = require('fs');
const path = require('path');
const root = __dirname;
const OUT = 'PP_YC_W27.html';
const { esc, markdown, prepareAssets, chip, row, stat, fig, wallSvg, css, script } = require('./pp_shell.cjs');

const source = fs.readFileSync(path.join(root, 'YC_W27_Plan_de_trabajo.md'), 'utf8');

const CHAPTERS = [
  { n: '01', name: 'Situación', q: '¿Desde dónde arrancamos?', img: 'planta' },
  { n: '02', name: 'Evidencia', q: '¿Quién lo necesita y cómo lo probamos?', img: 'exterior' },
  { n: '03', name: 'Demo', q: '¿Qué tiene que ver el evaluador?', img: 'frame' },
  { n: '04', name: 'Relato', q: '¿Qué contestamos en el formulario?', img: 'despiece' },
  { n: '05', name: 'Calendario', q: '¿Qué pasa cada semana?', img: 'estructura' },
  { n: '06', name: 'Riesgos', q: '¿Qué recortamos si vamos tarde?', img: 'anclajes' },
];

// SVG: las seis semanas en tres frentes paralelos
function ganttSvg() {
  const weeks = [['S0', '19–20 SEP'], ['S1', '21–27 SEP'], ['S2', '28/9–4/10'], ['S3', '5–11 OCT'],
                 ['S4', '12–18 OCT'], ['S5', '19–25 OCT'], ['S6', '26/10–1/11']];
  const W = 1140, H = 330, x0 = 122, cw = (W - x0 - 22) / 7, top = 72, rh = 76, bh = 30;
  const X = i => x0 + i * cw;
  const xs = X(6) + cw * .62; // viernes 30 de octubre, dentro de la semana 6
  const tracks = [
    ['EVIDENCIA', [[1, 2, 'Entrevistas · 15 contactos'], [3, 4, 'Pilotos reales'], [5, 5, 'Cierre de datos']]],
    ['PRODUCTO', [[1, 1, 'Especificar'], [2, 3, 'Operador de cambio + diff de piezas'], [4, 4, 'Congelar']]],
    ['APLICACIÓN', [[1, 1, 'Decisiones'], [2, 2, 'Borrador v1'], [3, 3, 'Landing'], [4, 4, 'Videos + inglés'], [5, 5, 'Revisión'], [6, 6, 'Envío']]],
  ];
  let s = `<svg class="gantt" viewBox="0 0 ${W} ${H}" role="img" aria-label="Calendario de seis semanas en tres frentes: evidencia, producto y aplicación, con envío el 30 de octubre">`;
  weeks.forEach(([c, d], i) => {
    s += `<line class="col" x1="${X(i)}" y1="46" x2="${X(i)}" y2="${top + 3 * rh - 16}"/>`;
    s += `<text class="wk" x="${X(i) + 8}" y="26">${c}</text><text class="dt" x="${X(i) + 8}" y="42">${d}</text>`;
  });
  s += `<line class="axis" x1="0" y1="52" x2="${W}" y2="52"/>`;
  tracks.forEach(([name, bars], r) => {
    const y = top + r * rh;
    s += `<text class="tr" x="0" y="${y + bh / 2 + 4}">${name}</text>`;
    s += `<line class="row" x1="0" y1="${y + rh - 22}" x2="${W}" y2="${y + rh - 22}"/>`;
    bars.forEach(([a, b, label]) => {
      const x = X(a) + 4;
      const w = label === 'Envío' ? xs - x : (b - a + 1) * cw - 10;
      s += `<rect class="bar ${label === 'Envío' ? 'send' : ''}" x="${x}" y="${y}" width="${w}" height="${bh}"/>`;
      s += `<text class="bl" x="${x + 9}" y="${y + bh / 2 + 4}">${label}</text>`;
    });
  });
  const yb = top + 3 * rh - 8;
  s += `<text class="now" x="${X(0) + 8}" y="${yb + 18}">HOY</text>`;
  s += `<line class="send-l" x1="${xs}" y1="46" x2="${xs}" y2="${yb + 6}"/>`;
  s += `<text class="send-t" x="${xs - 10}" y="${yb + 18}" text-anchor="end">30 OCT · ENVÍO</text>`;
  s += `<line class="lim-l" x1="${W - 1}" y1="46" x2="${W - 1}" y2="${yb + 6}"/>`;
  s += `<text class="lim" transform="translate(${W - 9} ${(52 + yb) / 2}) rotate(-90)" text-anchor="middle">2 NOV · LÍMITE</text>`;
  return s + '</svg>';
}

// SVG: embudo de contactos a pilotos
function funnelSvg() {
  const st = [[15, 'contactos abiertos'], [12, 'entrevistas documentadas'], [5, 'candidatos a probar'], [3, 'pilotos activos']];
  const W = 1000, H = 300, bw = 150, gap = (W - 4 * bw) / 3, mid = 96, maxH = 160;
  let s = `<svg class="funnel" viewBox="0 0 ${W} ${H}" role="img" aria-label="Embudo: 15 contactos, 12 entrevistas, 5 candidatos, 3 pilotos">`;
  const hs = st.map(([n]) => Math.max(14, n / 15 * maxH));
  for (let i = 0; i < 3; i++) {
    const x1 = i * (bw + gap) + bw, x2 = x1 + gap;
    s += `<polygon class="link" points="${x1},${mid - hs[i] / 2} ${x2},${mid - hs[i + 1] / 2} ${x2},${mid + hs[i + 1] / 2} ${x1},${mid + hs[i] / 2}"/>`;
    s += `<text class="pct" x="${(x1 + x2) / 2}" y="${mid + maxH / 2 + 26}" text-anchor="middle">${Math.round(st[i + 1][0] / st[i][0] * 100)}% →</text>`;
  }
  st.forEach(([n, l], i) => {
    const x = i * (bw + gap);
    s += `<rect class="bar" x="${x}" y="${mid - hs[i] / 2}" width="${bw}" height="${hs[i]}"/>`;
    s += `<text class="num" x="${x}" y="${H - 46}">${n}</text>`;
    const words = l.split(' ');
    s += `<text class="lbl" x="${x}" y="${H - 22}">${words[0]}</text><text class="lbl" x="${x}" y="${H - 5}">${words.slice(1).join(' ')}</text>`;
  });
  return s + '</svg>';
}

// ---------------------------------------------------------------- diapositivas
function buildSlides(img) {
  const S = [];
  const add = o => S.push(o);
  const divider = c => add({
    ch: c.n, kind: 'divider', title: c.name, cls: 'dark divider',
    body: `<div class="ghost">${c.n}</div><div class="div-copy"><p class="div-ch">CAPÍTULO ${c.n}</p><h2>${c.name}</h2><p class="div-q">${c.q}</p><p class="div-toc" data-toc="${c.n}"></p></div>${fig(img[c.img], '', '', 'div-img')}`,
  });

  // 01 — Portada
  add({ ch: '00', kind: 'cover', title: 'Cuarenta y cuatro días', cls: 'dark cover', body:
    `<img class="cover-bg" src="${img.aerial}" alt=""><div class="cover-shade"></div>
     <div class="cover-copy"><p class="mono kick">PLAN DE TRABAJO · APLICACIÓN A Y COMBINATOR · WINTER 2027</p>
     <h1>Cuarenta y cuatro días.<br><em>Una aplicación.</em></h1>
     <p class="lead">Seis semanas para convertir un prototipo y un plan en evidencia: gente usando el producto, una demo que muestra el circuito completo y respuestas que se sostienen con números.</p></div>
     <div class="cover-stamp mono"><span>19 · 09 · 2026</span><span>ENVÍO OBJETIVO 30 · 10</span><span>LÍMITE 2 · 11</span></div>
     <p class="cover-cap mono">Angus Ranch · caso de trabajo</p>` });

  // 02 — Mapa
  add({ ch: '00', kind: 'map', title: 'Seis capítulos, un envío', cls: 'light', body:
    `<div class="map">${CHAPTERS.map(c => `<button class="map-card" data-chapter="${c.n}"><span class="mono">${c.n}</span><strong>${c.name}</strong><em>${c.q}</em><small class="mono" data-range="${c.n}"></small></button>`).join('')}</div>`,
    foot: chip('Este documento es el plan de trabajo, no la aplicación. Las respuestas definitivas se escriben en inglés y se cargan en el formulario.', 'neutral') });

  // 03 — Tesis
  add({ ch: '00', title: 'Aplicar es la meta. Entender el producto es el resultado.', cls: 'dark thesis', body:
    `<div class="split thesis-split"><div>
      <p class="lead">El proceso obliga a responder en veinte segundos lo que hoy explicamos en treinta láminas: qué construimos, para quién, cómo lo sabemos y cuánto vale.</p>
      <div class="two-promises">${row('Resultado visible', 'Una aplicación completa, enviada el 30 de octubre.')}${row('Resultado que queda', 'Plan de negocios v0.2: las hipótesis de la v0.1 reemplazadas por respuestas de gente real.')}</div>
     </div>${fig(img.frame, 'Entramado de madera del modelo V06', '', 'thesis-img')}</div>
     <div class="stats">${stat('44', 'días hasta el límite')}${stat('6', 'semanas de trabajo efectivo')}${stat('29', 'campos del formulario')}${stat('3', 'frentes en paralelo')}<p class="stats-src mono">EVIDENCIA<br>PRODUCTO<br>APLICACIÓN</p></div>`,
    foot: chip('Regla de honestidad: ninguna respuesta afirma algo que no podamos mostrar el 30 de octubre.') });

  // ---------------------------------------------------------------- 01 Situación
  divider(CHAPTERS[0]);

  add({ ch: '01', title: 'El reloj, en tres frentes', cls: 'light', body:
    `<p class="sub">Cada semana cierra con un entregable por frente. Si algo no está listo, se recorta el alcance; la fecha no se mueve.</p>
     ${ganttSvg()}`,
    foot: chip('Los viernes a las 17:00 se revisa contra el criterio de listo de la semana. Tres entregables por semana como máximo.', 'neutral') });

  add({ ch: '01', title: 'Lo que ya existe', cls: 'dark stack', body:
    `<div class="split base-split"><div>
      ${row('Un modelo que se regenera solo', 'Angus Ranch V06: cada abertura es un parámetro y el entramado —montantes, kings, trimmers, headers dobles, cripples— se deriva de ella.')}
      ${row('Identidad por pieza', 'Cada elemento tiene un identificador estable derivado del muro y la abertura: Norte/O1_Header_0.')}
      ${row('Cantidades que siguen a la geometría', 'Despiece, cotización de tablas y plan de cortes se rehacen desde el modelo, no a mano.')}
      ${row('Relato armado', 'Plan de negocios v0.1 y una presentación de 33 láminas con los números y las hipótesis explícitas.')}
     </div>${fig(img.despiece, 'Despiece de madera del modelo V06', 'Despiece regenerado desde la geometría · V06')}</div>
     <div class="stats">${stat('828', 'piezas con identificador')}${stat('24', 'headers resueltos por regla')}${stat('13', 'capas de vista')}${stat('17,9', 'm³ brutos modelados')}<p class="stats-src mono">QA_V06.json<br>Cómputo V06</p></div>` });

  add({ ch: '01', title: 'Lo que el formulario pide y hoy no tenemos', cls: 'light', body:
    `<table class="tbl check"><thead><tr><th>Campo</th><th>Hoy</th><th>Meta al 30 de octubre</th></tr></thead><tbody>
      ${[['Nombre y descripción en 50 caracteres', 'no', 'Nombre elegido, dominio comprado, frase probada en entrevistas'],
         ['Company URL / product link', 'no', 'Una página con demo, deck y contacto'],
         ['Demo de hasta 3 minutos', 'no', 'Video del circuito: cambio de abertura, diff de piezas y cantidades'],
         ['Video del fundador, 1 minuto', 'no', 'Grabado sin editar, menos de 100 MB'],
         ['¿Hay gente usando el producto?', 'no', '2 o 3 profesionales sobre un proyecto propio, con horas registradas'],
         ['¿Tienen ingresos?', 'no', 'Un piloto pago o una carta de intención firmada'],
         ['¿Quién escribe el código?', 'parcial', 'Quién, cuánto y con qué herramientas de IA'],
         ['¿Buscan cofundador?', 'parcial', 'Decisión tomada en la semana 1'],
         ['Sociedad, inversión, ronda', 'ok', 'Se responde No, No y No. YC constituye la sociedad en el batch']]
        .map(([a, st, b]) => `<tr><td>${a}</td><td class="st ${st}">${st === 'ok' ? 'resuelto' : st === 'parcial' ? 'a precisar' : 'falta'}</td><td>${b}</td></tr>`).join('')}
     </tbody></table>`,
    foot: chip('La aplicación se puede editar hasta el cierre, incluso después de enviada: conviene enviar temprano y seguir mejorando.', 'neutral') });

  add({ ch: '01', title: 'Tres decisiones que bloquean todo lo demás', cls: 'light vc', body:
    `<div class="pillars">
      <div><span class="mono">A</span><h3>Nombre</h3><p>Cinco candidatos el lunes, decisión el jueves, dominio comprado el viernes. Sin nombre no hay landing, ni video, ni frase de 50 caracteres.</p></div>
      <div><span class="mono">B</span><h3>Cofundador</h3><p>¿Hay alguien con horas reales en el proyecto? Si no, la respuesta es que se busca, con el perfil descripto. No se suma un cofundador nominal en seis semanas.</p></div>
      <div><span class="mono">C</span><h3>Ubicación</h3><p>Dónde vivís hoy y si vas a estar en San Francisco durante el batch. El formulario pide el formato "Ciudad A, País A / Ciudad B, País B" y una explicación.</p></div>
     </div>`,
    foot: chip('Las tres se cierran en la semana 1. Cada una cambia el texto de varias respuestas.') });

  // ---------------------------------------------------------------- 02 Evidencia
  divider(CHAPTERS[1]);

  add({ ch: '02', title: 'Cómo se lee una aplicación', cls: 'dark', body:
    `<div class="split adv"><div class="pillars">
      <div><span class="mono">01</span><h3>Fundadores</h3><p>Claridad y velocidad. Se nota en el video y en el largo de las respuestas.</p></div>
      <div><span class="mono">02</span><h3>Progreso</h3><p>Qué existe hoy que no existía hace tres meses, medido en cosas verificables.</p></div>
      <div><span class="mono">03</span><h3>Problema</h3><p>Usuarios identificables con un dolor repetido, no un mercado en abstracto.</p></div>
     </div>
     <div class="callout dark-c"><p class="eyebrow">LO QUE MÁS PESA EN NUESTRO CASO</p><p class="big-num">3</p><p>profesionales que hayan usado el prototipo sobre un proyecto propio. Es la diferencia entre una idea prolija y una empresa empezada.</p><p class="small">Todo lo demás de la aplicación ya lo tenemos escrito en el plan v0.1.</p></div></div>`,
    foot: chip('Frases cortas, números concretos, cero adjetivos. Cada respuesta se lee en menos de veinte segundos.', 'neutral') });

  add({ ch: '02', title: 'De quince contactos a tres pilotos', cls: 'light', body:
    `<p class="sub">Constructoras woodframe, estudios que repiten el sistema, fabricantes de paneles y desarrollistas en Córdoba, Rosario y Buenos Aires.</p>
     ${funnelSvg()}
     <div class="band"><strong>CIERRE DE CADA ENTREVISTA</strong><p>“¿Probarías esto en un proyecto tuyo la semana que viene? ¿Cuál?” La respuesta a esa pregunta define quién entra al piloto.</p></div>`,
    foot: chip('Los dos arquitectos ya contactados son el punto de partida y la principal fuente de presentaciones a terceros.') });

  add({ ch: '02', title: 'Qué preguntamos y qué queda registrado', cls: 'light vc', body:
    `<div class="split identity"><div>
      <p class="eyebrow">GUION DE ENTREVISTA · SOBRE UN PROYECTO CONCRETO, NO SOBRE OPINIONES</p>
      <ul class="clean">
       <li>¿Cuál fue el último cambio de diseño y qué se rehízo por ese cambio?</li>
       <li>¿Cuántas horas llevó y quién las hizo?</li>
       <li>¿Qué información quedó desactualizada sin que nadie lo notara?</li>
       <li>¿Quién decide una compra de software y con qué presupuesto?</li>
      </ul>
      <p class="statement small">Lo que no se registra el mismo día no existe el 30 de octubre.</p>
     </div>
     <div class="card-id mono"><p class="id">ENTREVISTA · 03 · ESTUDIO WOODFRAME</p>
      <dl><dt>proyecto</dt><dd>Vivienda 140 m², obra en ejecución</dd>
       <dt>cambio</dt><dd>Se amplió una ventana del frente</dd>
       <dt>horas</dt><dd>11 h entre planos, listados y cortes</dd>
       <dt>rehecho</dt><dd>Despiece, cómputo y dos vistas</dd>
       <dt>decide</dt><dd>Socio técnico · presupuesto propio</dd>
       <dt>piloto</dt><dd><span class="dot ok"></span>Acepta probar en octubre</dd></dl></div></div>`,
    foot: chip('Ficha modelo. Una por entrevista, en entrevistas.md, el mismo día.', 'neutral') });

  add({ ch: '02', title: 'Las métricas que tienen que existir el 30 de octubre', cls: 'light', body:
    `<table class="tbl"><thead><tr><th>Métrica</th><th>Mínimo</th><th>Objetivo</th></tr></thead><tbody>
      ${[['Entrevistas documentadas fuera del círculo cercano', '8', '12'],
         ['Profesionales que operaron el prototipo', '2', '3'],
         ['Proyectos reales procesados además de Angus Ranch', '1', '2'],
         ['Comparaciones de horas: flujo actual contra prototipo', '1', '3'],
         ['Compromiso económico: pago o carta de intención', '1 carta', '1 pago'],
         ['Citas con nombre y permiso para publicarlas', '2', '3']]
        .map(([a, b, c]) => `<tr><td>${a}</td><td>${b}</td><td class="goal">${c}</td></tr>`).join('')}
     </tbody></table>
     <div class="band"><strong>SI EL MÍNIMO NO SE CUMPLE</strong><p>Se responde “No” en “¿hay gente usando el producto?” y se explica qué sí existe. Una aplicación honesta con poco progreso es mejor que una inflada.</p></div>` });

  // ---------------------------------------------------------------- 03 Demo
  divider(CHAPTERS[2]);

  add({ ch: '03', title: 'Un cambio, todas las piezas', cls: 'dark', body:
    `<div class="win" data-window><div class="win-stage">${wallSvg()}<div class="win-legend mono"><span><i class="sw wood"></i>SIN CAMBIOS</span><span><i class="sw red"></i>MODIFICADO</span><span><i class="sw new"></i>NUEVO</span><span><i class="sw gone"></i>ELIMINADO</span></div></div>
     <aside class="win-log"><p class="mono head"><span class="st stA">LO QUE LA DEMO TIENE QUE MOSTRAR</span><span class="st stB">LO QUE EL EVALUADOR TERMINA VIENDO</span></p>
      <ul class="log">
       <li class="a">Selección: ventana Norte O0 · RO 1.200 × 1.200 mm</li>
       <li class="a">Intención: <em>“ampliar 600 mm hacia el este”</em></li>
       <li class="b"><b>Header H-N-O0</b> · 1.290 → 1.890 mm</li>
       <li class="b"><b>Jack + king derechos</b> · desplazados +600 mm</li>
       <li class="b"><b>Montante M-09</b> · reemplazado por 2 cripples</li>
       <li class="b"><b>Antepecho</b> · 1.200 → 1.800 mm</li>
       <li class="b warn"><b>Dintel &gt; 1,8 m</b> · queda marcado para cálculo</li>
       <li class="b ok">Despiece y cantidades actualizados · 7 piezas afectadas</li>
      </ul></aside></div>`,
    foot: chip('El circuito ya existe como script: las aberturas son parámetros y el entramado se deriva de ellas. Falta exponerlo como operación y mostrar la diferencia.', 'neutral') });

  add({ ch: '03', title: 'Lo que hay que construir', cls: 'light', body:
    `<div class="rail">
      <div><span class="mono">01</span><h3>Operar</h3><p>modificar_abertura(id, medidas) con las validaciones que ya existen: espacio de jamba, solapes, altura bajo cubierta.</p></div>
      <div><span class="mono">02</span><h3>Comparar</h3><p>diff por identificador: piezas sin cambio, modificadas, nuevas y eliminadas, con metros cúbicos y tablas afectadas.</p></div>
      <div><span class="mono">03</span><h3>Mostrar</h3><p>Panel en Blender: elegir abertura, cambiar medidas, aplicar, ver las piezas afectadas pintadas en la escena.</p></div>
      <div><span class="mono">04</span><h3>Marcar</h3><p>Estado por pieza: comprobada por reglas o pendiente de cálculo. Un dintel de más de 1,8 m nunca se declara resuelto.</p></div>
      <div><span class="mono">05</span><h3>Exportar</h3><p>Un paquete con fecha: render, listados y diff en HTML. Es lo que el cliente se lleva y lo que se ve en el video.</p></div>
     </div>
     <div class="band pkg"><strong>CASO EXTERNO · SEMANA 3</strong><div class="pkg-items"><b>Una planta de un entrevistado</b><b>4 a 6 muros ortogonales</b><b>Sin muebles ni terreno</b><b>El mismo cambio, en una casa que no es la nuestra</b></div></div>`,
    foot: chip('Si el panel no llega, el flujo por línea de comando más el video demuestran lo mismo. El circuito importa más que la interfaz.') });

  add({ ch: '03', title: 'Y lo que no se construye ahora', cls: 'light vc', body:
    `<div class="split signals">
      <div class="go"><p class="eyebrow">ENTRA EN LAS SEIS SEMANAS</p><ul class="clean">
       <li>Operación de cambio con validaciones</li>
       <li>Diferencia de piezas y cantidades</li>
       <li>Panel mínimo dentro de Blender</li>
       <li>Un segundo proyecto, ajeno</li>
      </ul></div>
      <div class="stop"><p class="eyebrow">QUEDA FUERA, AUNQUE TIENTE</p><ul class="clean">
       <li>Interfaz propia fuera de Blender</li>
       <li>Asistente conversacional en vivo</li>
       <li>Cálculo estructural y fundaciones</li>
       <li>Varias plantas y techos complejos</li>
      </ul></div></div>
     <p class="eyebrow risks-l">CONCESIÓN ACEPTABLE SI SOBRA TIEMPO</p>
     <div class="risks"><span>Un campo de texto que acepta órdenes fijas: “ampliar O1 600”</span><span>Sin modelo de lenguaje detrás, sin promesas de conversación</span></div>`,
    foot: chip('Congelamos funcionalidades en la semana 4. Después solo se corrigen errores encontrados por los pilotos.') });

  add({ ch: '03', title: 'Guion del video demo', cls: 'dark shotslide', body:
    `<div class="shots mono">${[['0:00', 20, 'LA CASA'], ['0:20', 30, 'EL CAMBIO'], ['0:50', 40, 'LA CONSECUENCIA'], ['1:30', 40, 'LAS CANTIDADES'], ['2:10', 30, 'LA CASA AJENA'], ['2:40', 20, 'EL ESTADO']]
      .map(([t, d, n]) => `<span style="flex:${d}"><b>${t}</b>${n}</span>`).join('')}</div>
     <div class="board">
      ${[['0:00', 'La casa', 'Planta con el entramado visible. “Cada una de sus 828 piezas tiene identificador y sale de un mismo modelo.”'],
         ['0:20', 'El cambio', 'Seleccionar la ventana Norte O1. Cambiar el ancho de 1.000 a 1.600 mm. Aplicar.'],
         ['0:50', 'La consecuencia', 'Header en rojo, cripples nuevos en verde, montante eliminado en fantasma. Leer el diff en voz alta.'],
         ['1:30', 'Las cantidades', 'El cómputo regenerado, señalando la fila que cambió. “Antes eran tres archivos y una tarde.”'],
         ['2:10', 'La casa ajena', 'El mismo cambio sobre la planta del caso externo. “No depende de nuestro proyecto.”'],
         ['2:40', 'El estado', 'Pilotos, horas medidas, qué sigue. Cerrar con el nombre y la dirección web.']]
        .map(([t, h, p]) => `<div><span class="mono">${t}</span><h3>${h}</h3><p>${p}</p></div>`).join('')}
     </div>`,
    foot: chip('Grabación de pantalla con voz. Sin música, sin títulos animados, sin transiciones. Tres tomas y se elige la mejor.', 'neutral') });

  add({ ch: '03', title: 'Video del fundador', cls: 'light', body:
    `<div class="split mvp"><div>
      <p class="eyebrow">SESENTA SEGUNDOS · CINCO FRASES</p>
      <div class="steps-v">
       <div><span class="mono">1</span><h3>Quién sos</h3><p>Nombre, ciudad, a qué te dedicaste hasta ahora.</p></div>
       <div><span class="mono">2</span><h3>Qué construís</h3><p>Una frase: cambiar el diseño y que todas las piezas, planos y cantidades se actualicen solas.</p></div>
       <div><span class="mono">3</span><h3>Por qué vos</h3><p>El origen concreto: la casa que estás construyendo y las semanas perdidas por cada cambio.</p></div>
       <div><span class="mono">4</span><h3>Qué lograste</h3><p>El modelo con piezas identificadas y los profesionales que ya lo están probando.</p></div>
      </div></div>
      <div>
       <p class="eyebrow">CÓMO SE GRABA</p>
       <ul class="pills">
        <li>Celular en horizontal</li><li>Luz natural de frente</li><li>Fondo limpio</li><li>Mirar a cámara</li>
        <li>Sin leer</li><li>Sin edición</li><li>Sin música</li><li>Menos de 100 MB</li>
       </ul>
       <p class="statement">Cinco tomas y se elige la más natural, no la más pulida. Es el único momento en que el evaluador ve a la persona.</p>
      </div></div>`,
    foot: chip('Semana 4. Los dos videos se graban el mismo día, cuando ya hay algo real para mostrar.') });

  // ---------------------------------------------------------------- 04 Relato
  divider(CHAPTERS[3]);

  add({ ch: '04', title: 'Cincuenta caracteres', cls: 'light', body:
    `<p class="sub">El campo más difícil del formulario. Se prueban las tres versiones en las entrevistas: gana la que se entiende sin explicación.</p>
     <div class="fifty">
      ${[['Cambiá el diseño; la casa woodframe se actualiza', 'Pone el verbo primero. Suena a promesa.'],
         ['Diseño woodframe que actualiza todas sus piezas', 'Más descriptivo, menos memorable.'],
         ['Casas woodframe editables pieza por pieza', 'La más corta. “Editable” puede sonar a maqueta.']]
        .map(([t, n]) => `<div><p class="ph-t">${t}</p><p class="cnt mono">${t.length} caracteres</p><p class="nt">${n}</p></div>`).join('')}
     </div>
     <div class="band"><strong>CÓMO SE ELIGE</strong><p>Se dice la frase al principio de cada entrevista y se anota la primera repregunta. La versión que no genera repreguntas es la que va al formulario, a la landing y al video.</p></div>`,
    foot: chip('La misma frase se usa en la landing, en el video y en el asunto de los mails a entrevistados.', 'neutral') });

  add({ ch: '04', title: 'Qué vamos a construir, en cinco líneas', cls: 'dark', body:
    `<div class="split invest-split"><div>
      <p class="lead">Software para estudios y constructoras que diseñan viviendas woodframe de forma recurrente.</p>
      <div class="paths">
       ${row('Qué hace', 'El usuario edita la planta y las aberturas; el sistema regenera el entramado dentro de reglas constructivas, mantiene el identificador de cada pieza y actualiza vistas, listados y cantidades.')}
       ${row('Qué existe hoy', 'Prototipo sobre Blender: 828 piezas identificadas, despiece y plan de cortes regenerables, y una operación de cambio con diferencia de piezas.')}
       ${row('Qué sigue', 'Más sistemas coordinados, documentación más profunda y adaptación por empresa y por mercado.')}
      </div></div>
      <div class="callout dark-c"><p class="eyebrow">LA TRAMPA A EVITAR</p><p>Describir la casa completa como si estuviera resuelta. El evaluador premia el alcance chico y demostrado, y castiga la promesa amplia sin evidencia.</p><p class="small">El horizonte se menciona una vez, al final, condicionado por la demanda.</p></div></div>`,
    foot: chip('Las mismas cinco líneas sirven para “What is your company going to make” y para la primera pantalla de la landing.', 'neutral') });

  add({ ch: '04', title: 'Contra quién competimos', cls: 'light', body:
    `<div class="comp">
      ${[['Higharc', 'Diseño, configuración y documentación residencial en una plataforma. Serie C de USD 95 M en junio de 2026.', 'MERCADO ESTADOUNIDENSE · VIVIENDA EN VOLUMEN'],
         ['Chief Architect', 'Estándar de diseño residencial con entramado automático. Licencia perpetua, ecosistema instalado.', 'HERRAMIENTA DE DIBUJO · SIN MODELO DE DEPENDENCIAS'],
         ['hsbcad', 'Software de fabricación para paneles y estructuras de madera, sobre Autodesk.', 'PENSADO PARA LA FÁBRICA, NO PARA EL DISEÑO'],
         ['ARKANCE Be.Smart', 'Automatización de entramado dentro del ecosistema Autodesk.', 'REQUIERE EQUIPO Y LICENCIAS BIM'],
         ['El flujo actual', 'CAD, planillas de cálculo y revisión manual. Es el competidor real de casi todos los entrevistados.', 'GRATIS, CONOCIDO Y CARÍSIMO EN HORAS']]
        .map(([h, p, e], i) => `<div class="comp-card ${i === 4 ? 'status' : ''}"><h3>${h}</h3><p>${p}</p><p class="eyebrow">${e}</p></div>`).join('')}
     </div>`,
    foot: chip('Lo que entendemos y ellos no se completa con evidencia de entrevistas. Hipótesis: un equipo chico que repite un sistema no necesita una suite de fabricación, necesita que un cambio no rompa el resto.') });

  add({ ch: '04', title: 'Cómo ganamos dinero', cls: 'light money', body:
    `<div class="split budget"><div class="scale">
      ${[['Piloto pago por proyecto', 'USD 200–600', 5],
         ['Suscripción · equipos chicos', 'USD 100–250 /mes', 14],
         ['Suscripción · mayor volumen', 'USD 300–600 /mes', 26],
         ['250 organizaciones a USD 250', 'USD 750 k /año', 40],
         ['3.000 organizaciones a USD 450', 'USD 16 M /año', 60]]
        .map(([l, v, n]) => `<div><span class="mono lbl">${l}</span><span class="dots">${'<i></i>'.repeat(n)}</span><strong>${v}</strong></div>`).join('')}
     </div>
     <div class="total"><p class="eyebrow">LA PREGUNTA REAL DETRÁS DEL CAMPO</p><p class="hero">¿Miles?<span>¿o decenas?</span></p><p>Si el producto sirve solo a estudios que repiten un sistema, es un nicho rentable. Si sirve a cualquier organización que construye en madera con reglas propias, es un mercado de capital de riesgo. Todavía no sabemos cuál de las dos es.</p></div></div>
     <div class="band"><strong>EN EL FORMULARIO</strong><p>Se responde con el precio de entrada, el rango de suscripción y una sola cuenta de escala, aclarando que es una estimación. Nadie espera precisión; esperan que el razonamiento cierre.</p></div>`,
    foot: chip('Los números son hipótesis del plan v0.1. En la aplicación se presentan como estimación, no como proyección.', 'neutral') });

  add({ ch: '04', title: 'Siete preguntas que bloquean el texto', cls: 'dark', body:
    `<div class="split qs">
      <ol class="clean num">
       <li>¿Sos fundador único hoy? ¿Alguien más tiene horas reales en el proyecto?</li>
       <li>¿Escribís vos el código y con qué herramientas de IA exactamente?</li>
       <li>¿Hubo aportes de terceros en código o en reglas constructivas?</li>
       <li>¿Dónde vivís y estarías en San Francisco entre enero y marzo de 2027?</li>
      </ol>
      <ol class="clean num" start="5">
       <li>¿Cuál es tu vínculo con la construcción en madera? ¿Angus Ranch es tu casa?</li>
       <li>¿Desde cuándo trabajás en esto y qué porcentaje de tu tiempo le dedicás?</li>
       <li>¿Los dos arquitectos aceptarían ser pilotos con un proyecto real en octubre?</li>
      </ol></div>
     <p class="statement">Ninguna cambia la estructura del plan. Todas cambian el texto de la aplicación, y varias aparecen en más de una respuesta.</p>
     <p class="eyebrow risks-l">EN CAMBIO, ESTO YA ESTÁ DECIDIDO</p>
     <div class="risks dark-r"><span>Batch: Winter 2027</span><span>Sociedad: no</span><span>Inversión recibida: no</span><span>Ronda en curso: no</span><span>Aceleradoras previas: ninguna</span></div>`,
    foot: chip('Se responden en la semana 1, por escrito, en respuestas_borrador.md.', 'neutral') });

  // ---------------------------------------------------------------- 05 Calendario
  divider(CHAPTERS[4]);

  add({ ch: '05', title: 'Semanas 0 a 3: evidencia y circuito', cls: 'light', body:
    `<div class="weeks">
      ${[['S0 · 19–20 SEP', 'Arranque', 'Leer la aplicación completa, armar la lista de quince contactos y crear la carpeta de trabajo.', 'Cada contacto con canal y fecha objetivo'],
         ['S1 · 21–27 SEP', 'Descubrir', 'Entrevistas con los dos arquitectos, diez mensajes a desconocidos y las tres decisiones de fondo.', 'Nombre, cofundador y ubicación por escrito'],
         ['S2 · 28/9–4/10', 'Construir', 'Operación de cambio, diferencia de piezas y marcado en la escena. Cuatro entrevistas externas.', 'El cambio corre sin intervención manual'],
         ['S3 · 5–11 OCT', 'Usar', 'Panel en Blender, caso externo y la primera sesión guiada con un profesional. Landing publicada.', 'Un tercero usó el prototipo']]
        .map(([m, h, p, ev]) => `<div><span class="mono">${m}</span><h3>${h}</h3><p>${p}</p><p class="ev"><b>CRITERIO DE LISTO</b>${ev}</p></div>`).join('')}
     </div>`,
    foot: chip('En la semana 3 se propone el piloto pago: entre 200 y 400 dólares por un alcance acotado, o una carta de intención.') });

  add({ ch: '05', title: 'Semanas 4 a 6: relato y envío', cls: 'light', body:
    `<div class="weeks">
      ${[['S4 · 12–18 OCT', 'Grabar', 'Los dos videos, la traducción al inglés y los pilotos 2 y 3. Se congelan las funcionalidades.', 'Videos listos y respuestas en inglés'],
         ['S5 · 19–25 OCT', 'Revisar', 'Tres lectores externos, reescritura, plan de negocios v0.2 y carga del formulario como borrador.', 'Formulario completo, sin enviar'],
         ['S6 · 26–30 OCT', 'Enviar', 'Relectura en voz alta, coherencia de números entre respuestas, landing y deck. Envío el viernes.', 'Enviado el 30 de octubre'],
         ['31/10 – 2/11', 'Margen', 'Solo para incorporar algo nuevo y verdadero: un pago, un usuario más, una cita mejor.', 'La aplicación se edita después de enviada']]
        .map(([m, h, p, ev], i) => `<div${i === 3 ? ' class="last"' : ''}><span class="mono">${m}</span><h3>${h}</h3><p>${p}</p><p class="ev"><b>CRITERIO DE LISTO</b>${ev}</p></div>`).join('')}
     </div>`,
    foot: chip('Una sola pregunta a los tres lectores externos: “¿qué no entendiste y qué no te creíste?”.', 'neutral') });

  add({ ch: '05', title: 'La rutina que sostiene el plan', cls: 'light vc', foot: chip('El plan completo, con los borradores de cada respuesta, está en el botón “Plan completo” de la barra superior.', 'neutral'), body:
    `<div class="split"><div class="cadence">
      <div><span class="mono">LUNES 9:00</span><p>Plan de la semana en treinta minutos. Tres entregables como máximo.</p></div>
      <div><span class="mono">MIÉRCOLES</span><p>Una demostración a alguien de afuera, aunque dure diez minutos.</p></div>
      <div><span class="mono">VIERNES 17:00</span><p>Revisión contra el criterio de listo. Se actualizan las métricas y se decide qué se recorta.</p></div>
      <div><span class="mono">TODOS LOS DÍAS</span><p>Una línea en el registro de entrevistas o de métricas.</p></div>
     </div>
     <div><p class="eyebrow">TRES ARCHIVOS, NINGUNA HERRAMIENTA NUEVA</p>
      <ul class="pills"><li>respuestas_borrador.md</li><li>entrevistas.md</li><li>metricas.md</li></ul>
      <p class="statement">El riesgo no es quedarse sin tiempo: es llegar al 30 de octubre con trabajo hecho y sin registro de que se hizo.</p></div></div>` });

  // ---------------------------------------------------------------- 06 Riesgos
  divider(CHAPTERS[5]);

  add({ ch: '06', title: 'Riesgos de estas seis semanas', cls: 'light', body:
    `<table class="tbl risk"><thead><tr><th>Riesgo</th><th>Señal de alarma</th><th>Respuesta</th></tr></thead><tbody>
      ${[['La demo se agranda', 'Semana 3 sin panel funcionando', 'Congelar en línea de comando y grabar el video igual'],
         ['Nadie externo responde', 'Semana 2 con menos de tres entrevistas', 'Pedir presentaciones a los arquitectos; ir a obras y aserraderos'],
         ['Los pilotos no llegan a tiempo', 'Semana 4 sin sesiones guiadas', 'Responder “No” y mostrar el caso externo procesado por nosotros'],
         ['Perfeccionismo en los videos', 'Más de cinco tomas', 'Elegir la más natural y seguir; crudo es mejor que producido'],
         ['Respuestas largas', 'Más de veinte segundos de lectura', 'Cortar al 60 %. Una idea por respuesta'],
         ['La decisión de cofundador se posterga', 'Semana 2 sin definición', 'Responder que se busca, con el perfil descripto']]
        .map(([a, b, c]) => `<tr><td>${a}</td><td class="sig">${b}</td><td>${c}</td></tr>`).join('')}
     </tbody></table>`,
    foot: chip('Cada riesgo tiene una respuesta que ya está decidida hoy, para no tener que decidirla cansados en octubre.', 'neutral') });

  add({ ch: '06', title: 'Qué se recorta, y en qué orden', cls: 'light vc cuts', body:
    `<div class="arch">
      <div class="tier t-top"><span class="mono tier-l">PRIMERO</span><div class="box">Panel gráfico en Blender<small>Se reemplaza por línea de comando</small></div><div class="box">Segundo caso externo<small>Alcanza con uno</small></div><div class="box">Exportación del paquete<small>Se muestra en pantalla</small></div></div>
      <div class="tier"><span class="mono tier-l">DESPUÉS</span><div class="box">Landing elaborada<small>Una página con el video basta</small></div><div class="box">Traducción pulida<small>Inglés claro, no elegante</small></div><div class="box">Piloto pago<small>Alcanza una carta de intención</small></div></div>
      <div class="tier t-core"><span class="mono tier-l">NUNCA</span><div class="box core">El circuito completo en video<small>Cambio, diff, cantidades</small></div><div class="box core">Al menos un usuario real<small>Alguien que no seamos nosotros</small></div><div class="box core">El envío del 30 de octubre<small>La fecha no se mueve</small></div></div>
     </div>`,
    foot: chip('Recortar temprano y a conciencia es lo que permite llegar. Recortar el último día es lo que arruina una aplicación.') });

  // Cierre
  add({ ch: '00', kind: 'closing', title: 'El 30 de octubre enviamos', cls: 'dark closing', body:
    `<img class="cover-bg dim" src="${img.aerial}" alt=""><div class="cover-shade strong"></div>
     <div class="close-copy"><h2>El 30 de octubre<br><em>enviamos.</em></h2>
     <p class="lead">Y el 3 de noviembre tenemos algo que hoy no existe: un producto que alguien usó, un circuito que se puede mostrar en tres minutos y un relato que se sostiene con números propios.</p>
     <div class="actions"><button class="primary" data-action="doc">Ver el plan completo</button><button class="ghost-btn" data-action="top">Volver al inicio</button></div>
     <p class="end-note">Independientemente del resultado, el proceso deja la versión 0.2 del plan de negocios: las hipótesis de la v0.1 reemplazadas por respuestas de gente que construye.</p></div>` });

  return S;
}

// ---------------------------------------------------------------- estilos propios
const extra = `
/* --- calendario --- */
.gantt{width:100%;display:block;margin-top:6px}
.gantt .col{stroke:var(--line);stroke-width:1}
.gantt .axis,.gantt .row{stroke:var(--line);stroke-width:1}
.gantt .axis{stroke:var(--ink);stroke-width:1.2}
.gantt .wk{font-family:var(--mono);font-size:13px;fill:var(--ink);font-weight:500;letter-spacing:.06em}
.gantt .dt,.gantt .tr,.gantt .now,.gantt .lim{font-family:var(--mono);font-size:10px;fill:var(--muted);letter-spacing:.08em}
.gantt .tr{fill:var(--ink);font-size:10.5px}
.gantt .bar{fill:var(--wood);opacity:.92}
.gantt .bar.send{fill:var(--ink)}
.gantt .bl{font-family:var(--sans);font-size:12.5px;fill:var(--paper);font-weight:500}
.gantt .send-l,.gantt .lim-l{stroke:var(--red);stroke-width:1.2;stroke-dasharray:4 4}
.gantt .send-t,.gantt .lim{font-family:var(--mono);font-size:10px;fill:var(--red);letter-spacing:.08em}
.gantt .now{fill:var(--wood)}

/* --- tablas de estado --- */
.tbl td:last-child,.tbl th:last-child{text-align:left;width:46%}
.tbl.check td,.tbl.risk td{padding:9px 0;font-size:14.5px;vertical-align:top}
.tbl.check td:nth-child(2),.tbl.check th:nth-child(2){text-align:left;width:120px}
.tbl.risk td:nth-child(2),.tbl.risk th:nth-child(2){text-align:left;width:30%;color:var(--muted)}
.tbl .st{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase}
.tbl .st::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;background:var(--red)}
.tbl .st.no{color:var(--red)}
.tbl .st.parcial{color:var(--wood)}.tbl .st.parcial::before{background:var(--wood)}
.tbl .st.ok{color:#2E7D4F}.tbl .st.ok::before{background:#2E7D4F}
.tbl .goal{color:var(--wood);font-weight:600}
.tbl .sig{font-size:14px}

/* --- storyboard --- */
.shotslide .s-body{display:flex;flex-direction:column}
.shotslide .board{flex:1;grid-template-rows:1fr 1fr}
.shots{display:flex;gap:4px;margin-bottom:6px}
.shots span{display:flex;align-items:baseline;gap:8px;min-width:0;padding:9px 11px;background:var(--ink2);border:1px solid var(--line-d);border-bottom:2px solid var(--wood);color:#9AA79F;font-size:9.5px;overflow:hidden;white-space:nowrap}
.shots b{color:var(--wood2);font-weight:500}
.board{display:grid;grid-template-columns:repeat(3,1fr);gap:18px 22px;margin-top:4px}
.board>div{border-top:1px solid var(--line-d);padding-top:14px}
.board .mono{color:var(--wood2);font-size:13px}
.board h3{font-family:var(--serif);font-weight:400;font-size:24px;margin:8px 0 6px;letter-spacing:-.01em}
.board p{font-size:14.5px;color:#B4BFB8;line-height:1.4}

/* --- cincuenta caracteres --- */
.fifty{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:10px}
.fifty>div{background:#fff;border:1px solid var(--line);border-top:3px solid var(--wood);padding:28px 24px 24px;display:flex;flex-direction:column;min-height:290px}
.ph-t{font-family:var(--serif);font-weight:400;font-size:27px;line-height:1.14;letter-spacing:-.02em}
.fifty .cnt{color:var(--wood);font-size:10.5px;margin:14px 0 0!important}
.fifty .nt{margin-top:auto!important;padding-top:16px;border-top:1px dashed var(--line);color:var(--muted);font-size:14px}

/* --- preguntas abiertas --- */
.qs{gap:48px}
.clean.num{counter-reset:q;padding-left:0}
.qs .clean li{font-size:16.5px;padding-left:30px;margin-bottom:16px;color:#D9DFD8}
.clean.num li::before{counter-increment:q;content:counter(q);width:auto;height:auto;background:none;color:var(--wood2);font-family:var(--mono);font-size:11px;top:3px}
.qs .clean[start="5"]{counter-reset:q 4}

/* --- ajustes --- */
.document blockquote{margin:20px 0;padding:14px 20px;border-left:2px solid var(--wood);background:var(--paper2);font-size:16px;line-height:1.6}
.vc .s-body{display:flex;flex-direction:column;justify-content:center}
.stack .s-body{display:flex;flex-direction:column}
.stack .base-split{flex:1;min-height:0;align-items:center}
.stack .base-split figure img{max-height:300px;object-fit:contain}
.stack .stats{margin-top:14px;padding-top:14px;gap:26px}
.stack .stat strong{font-size:44px}
.money .scale>div{grid-template-columns:200px 1fr 235px;gap:20px;padding:12px 0}
.money .scale strong{font-size:26px}
.money .total .hero{font-size:62px}
.money .total .hero span{font-size:34px}
.money .band{margin-top:22px}
.risks.dark-r span{background:transparent;border-color:var(--line-d);color:#C9D1CB}
.cuts .box{min-height:96px}
.weeks>div{min-height:320px}
.weeks>div.last{border-top-color:var(--wood)}
.weeks .ev{font-size:13.5px}
.signals .go .clean li,.signals .stop .clean li{font-size:17px}
.board+.s-foot{margin-top:0}
@media(max-width:650px){.reading .board,.reading .fifty,.reading .qs{grid-template-columns:1fr}.reading .gantt{min-width:0}}
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
    const head = `<header class="s-head mono"><span>${isCover ? (s.kind === 'cover' ? 'PLAN DE TRABAJO · Y COMBINATOR WINTER 2027' : 'CIERRE') : `<b>${pad(i + 1)}</b>— ${chapterName(s.ch).toUpperCase()}`}</span><span class="s-stamp">YC W27 · 19.09.2026 · HOJA ${pad(i + 1)}/${total}</span></header>`;
    const title = (isCover || s.kind === 'divider') ? '' : `<h2>${s.title}</h2>`;
    const foot = isCover ? '' : `<footer class="s-foot">${s.foot || '<span></span>'}<span class="s-mark">Plan de trabajo · aplicación YC Winter 2027 · 44 días</span></footer>`;
    const marks = '<i class="cm tl"></i><i class="cm tr"></i><i class="cm bl"></i><i class="cm br"></i>';
    return `<section class="slide ${s.cls} ${i === 0 ? 'active' : ''}" data-title="${esc(plain(s.title))}" data-chapter="${s.ch}" data-kind="${s.kind || 'content'}" aria-label="Diapositiva ${i + 1}: ${esc(plain(s.title))}" aria-hidden="${i !== 0}">${marks}${head}${title}<div class="s-body">${s.body}</div>${foot}</section>`;
  }).join('');

  const tocText = {}; for (const c of CHAPTERS) tocText[c.n] = (ranges[c.n] || []).slice(1).map(n => `${pad(n)} ${plain(slides[n - 1].title)}`).join(' · ');
  const rangeText = {}; for (const c of CHAPTERS) { const r = ranges[c.n] || []; rangeText[c.n] = `HOJAS ${pad(r[0])}–${pad(r[r.length - 1])}`; }
  const dividerIndex = {}; slides.forEach((s, i) => { if (s.kind === 'divider') dividerIndex[s.ch] = i; });

  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><title>YC Winter 2027 — Plan de trabajo</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>${css}${extra}</style></head><body>
<header class="topbar mono"><span class="brand"><i></i>YC W27 <span>— PLAN DE TRABAJO · 44 DÍAS</span></span><div class="top-actions"><button id="indexBtn">Índice</button><button id="docBtn">Plan completo</button><button id="readingBtn" aria-pressed="false">Lectura</button><button id="fullscreen" aria-label="Pantalla completa">⛶</button></div></header>
<main class="stage" aria-label="Plan de trabajo hacia la aplicación a Y Combinator">${sectionHtml}</main>
<nav class="nav mono" aria-label="Navegación"><button id="prev" aria-label="Anterior">←</button><span class="counter" id="counter"></span><span class="nav-title" id="navTitle"></span><button id="next" aria-label="Siguiente">→</button><span class="keyhint">← → navegar · I índice · F pantalla completa</span></nav>
<div class="progress" id="progress"></div><div class="sr-only" role="status" aria-live="polite" id="live"></div>
<dialog id="indexDialog" class="index-dialog" aria-labelledby="indexHeading"><div class="dialog-head"><strong id="indexHeading">Contenido</strong><button data-close="indexDialog">Cerrar ×</button></div><div class="index-list">${slides.map((s, i) => `<button data-slide="${i}" class="${s.kind === 'divider' ? 'div' : ''}"><span>${pad(i + 1)}</span>${plain(s.title)}</button>`).join('')}</div></dialog>
<dialog id="docDialog" class="doc-dialog" aria-labelledby="docHeading"><div class="dialog-head"><strong id="docHeading">Plan de trabajo · texto completo</strong><button data-close="docDialog">Cerrar ×</button></div><article class="document">${markdown(source)}</article></dialog>
<script>
${script(tocText, rangeText, dividerIndex)}
</script></body></html>`;
  fs.writeFileSync(path.join(root, OUT), html, 'utf8');
  console.log(JSON.stringify({ slides: total, bytes: Buffer.byteLength(html), output: OUT }));
}
main().catch(e => { console.error(e); process.exit(1); });
