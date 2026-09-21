// Motor visual compartido de las presentaciones (estilo, activos y runtime).
// Generado a partir de build_pp_fable.cjs; lo usan build_pp_fable.cjs y build_pp_yc.cjs.
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const root = __dirname;
const PW = 'C:/Users/adamonte/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const cacheDir = path.join(os.tmpdir(), 'pp_fable_assets');
const refresh = process.argv.includes('--refresh');

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const inline = s => esc(s)
  .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 ↗</a>')
  .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

function markdown(md) {
  const lines = md.split(/\r?\n/); let out = '', i = 0;
  while (i < lines.length) {
    let l = lines[i]; if (!l.trim()) { i++; continue; }
    if (l.startsWith('|')) {
      let rows = []; while (i < lines.length && lines[i].startsWith('|')) rows.push(lines[i++]);
      const cells = r => r.split('|').slice(1, -1).map(s => s.trim());
      out += '<div class="table-scroll"><table><thead><tr>' + cells(rows[0]).map(c => '<th>' + inline(c) + '</th>').join('') + '</tr></thead><tbody>' + rows.slice(2).map(r => '<tr>' + cells(r).map(c => '<td>' + inline(c) + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>'; continue;
    }
    if (/^#{1,3} /.test(l)) { let n = l.match(/^#+/)[0].length; out += `<h${n}>${inline(l.slice(n + 1))}</h${n}>`; i++; continue; }
    if (/^(- |\d+\. )/.test(l)) { let tag = /^\d/.test(l) ? 'ol' : 'ul'; out += '<' + tag + '>'; while (i < lines.length && /^(- |\d+\. )/.test(lines[i])) out += '<li>' + inline(lines[i++].replace(/^(- |\d+\. )/, '')) + '</li>'; out += '</' + tag + '>'; continue; }
    if (l === '---') { out += '<hr>'; i++; continue; }
    if (l.startsWith('> ')) { let q = []; while (i < lines.length && lines[i].startsWith('> ')) q.push(lines[i++].slice(2)); out += '<blockquote>' + inline(q.join(' ')) + '</blockquote>'; continue; }
    let p = []; while (i < lines.length && lines[i].trim() && !/^(#|\||- |\d+\. )/.test(lines[i])) p.push(lines[i++]);
    out += '<p>' + inline(p.join(' ')) + '</p>';
  }
  return out;
}

// ---------------------------------------------------------------- imágenes
const V04 = 'Angus_Ranch_Blender_V04/Angus_Ranch_Blender_V04/';
const V06 = 'Angus_Ranch_V06/';
const PAPER = [0xF5, 0xF2, 0xEA], GRAY = [0xEB, 0xEC, 0xE8];
const v04crop = [0, 130, 1800, 1070];
const ASSETS = {
  aerial:     { src: 'ChatGPT Image 6 sept 2026, 18_32_24.png', width: 1600, type: 'jpeg', quality: .82 },
  bosquejo:   { src: 'arrgelos bosquejo v3 angus ranch.png', crop: [0, 88, 1222, 580], type: 'jpeg', quality: .86 },
  frame:      { src: V06 + '09_Headers_dobles.png', key: GRAY, tol: 10, width: 1200 },
  anclajes:   { src: V06 + '10_Anclajes_y_cimientos.png', key: GRAY, tol: 10, width: 1200 },
  header:     { src: V06 + '12_Detalle_header_explotado.png', crop: [560, 40, 680, 830], key: GRAY, tol: 10 },
  holddown:   { src: V06 + '13_Detalle_anclajes.png', crop: [320, 210, 440, 510], key: GRAY, tol: 10 },
  despiece:   { src: V06 + '11_Despiece_madera.png', key: GRAY, tol: 10, width: 1400 },
  estructura: { src: V04 + 'Vista_estructura_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  insulation: { src: V04 + 'Vista_insulation_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  osb:        { src: V04 + 'Vista_osb_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  wrb:        { src: V04 + 'Vista_wrb_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  siding:     { src: V04 + 'Vista_siding_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  planta:     { src: V04 + 'Vista_planta_V04.png', crop: [0, 130, 1800, 1080], key: PAPER, tol: 8, width: 1300 },
  interior:   { src: V04 + 'Vista_interior_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
  exterior:   { src: V04 + 'Vista_exterior_V04.png', crop: v04crop, key: PAPER, tol: 8, width: 1300 },
};

async function prepareAssets() {
  fs.mkdirSync(cacheDir, { recursive: true });
  const pending = Object.entries(ASSETS).filter(([k]) => refresh || !fs.existsSync(path.join(cacheDir, k + '.txt')));
  const img = {};
  if (pending.length) {
    const { chromium } = require(PW);
    const browser = await chromium.launch({ executablePath: EDGE, headless: true });
    const page = await browser.newPage();
    await page.setContent('<!doctype html><html><body></body></html>');
    for (const [k, a] of pending) {
      const buf = fs.readFileSync(path.join(root, a.src));
      const dataUrl = 'data:image/png;base64,' + buf.toString('base64');
      const out = await page.evaluate(async ({ src, a }) => {
        const im = new Image(); im.src = src; await im.decode();
        const [sx, sy, sw, sh] = a.crop || [0, 0, im.width, im.height];
        const scale = a.width ? Math.min(1, a.width / sw) : 1;
        const w = Math.round(sw * scale), h = Math.round(sh * scale);
        const c = document.createElement('canvas'); c.width = w; c.height = h;
        const ctx = c.getContext('2d'); ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(im, sx, sy, sw, sh, 0, 0, w, h);
        if (a.key) {
          const [kr, kg, kb] = a.key, tol = a.tol, soft = tol * 2.6;
          const d = ctx.getImageData(0, 0, w, h), p = d.data;
          for (let i = 0; i < p.length; i += 4) {
            const dr = p[i] - kr, dg = p[i + 1] - kg, db = p[i + 2] - kb;
            const dist = Math.sqrt(dr * dr + dg * dg + db * db);
            if (dist < tol) { p[i + 3] = 0; continue; }
            if (dist < soft) {
              const al = (dist - tol) / (soft - tol);
              p[i + 3] = Math.round(255 * al);
              // quitar el tinte del fondo en los bordes semitransparentes
              p[i] = Math.max(0, Math.min(255, (p[i] - kr * (1 - al)) / al));
              p[i + 1] = Math.max(0, Math.min(255, (p[i + 1] - kg * (1 - al)) / al));
              p[i + 2] = Math.max(0, Math.min(255, (p[i + 2] - kb * (1 - al)) / al));
            }
          }
          ctx.putImageData(d, 0, 0);
        }
        return a.type === 'jpeg' ? c.toDataURL('image/jpeg', a.quality || .8) : c.toDataURL('image/png');
      }, { src: dataUrl, a });
      fs.writeFileSync(path.join(cacheDir, k + '.txt'), out);
      console.error(`asset ${k}: ${(out.length / 1024 | 0)} KB`);
    }
    await browser.close();
  }
  for (const k of Object.keys(ASSETS)) img[k] = fs.readFileSync(path.join(cacheDir, k + '.txt'), 'utf8');
  return img;
}

// ---------------------------------------------------------------- helpers de contenido
const chip = (t, kind = '') => `<span class="chip ${kind}"><i></i>${t}</span>`;
const row = (a, b) => `<div class="li"><h3>${a}</h3><p>${b}</p></div>`;
const stat = (n, l, extra = '') => `<div class="stat"><strong>${n}</strong><span>${l}</span>${extra}</div>`;
const fig = (src, alt, cap = '', cls = '') => `<figure class="${cls}"><img src="${src}" alt="${alt}">${cap ? `<figcaption>${cap}</figcaption>` : ''}</figure>`;

// SVG: pared animada "ampliar esta ventana" (medidas en mm)
function wallSvg() {
  const S = (x, y, w, h, cls = '', id = '') => `<rect ${id ? `id="${id}" ` : ''}class="pc ${cls}" x="${x}" y="${y}" width="${w}" height="${h}"/>`;
  let s = '';
  s += S(0, 2655, 4800, 45) + S(0, 0, 4800, 45) + S(0, 45, 4800, 45); // soleras
  for (const x of [0, 400, 800, 1200, 1600]) s += S(x, 90, 45, 2565); // montantes izquierda
  for (const x of [4000, 4400, 4755]) s += S(x, 90, 45, 2565); // montantes derecha
  s += S(3200, 90, 45, 2565, 'gone-b', 'm09'); // montante que cae dentro del vano ampliado
  s += S(3600, 90, 45, 2565, 'gone-b', 'm10'); // montante absorbido por el jack
  for (const x of [2000, 2400, 2800]) s += S(x, 90, 45, 390) + S(x, 1945, 45, 710); // cripples existentes
  s += S(3200, 90, 45, 390, 'new-b') + S(3200, 1945, 45, 710, 'new-b'); // cripples nuevos
  s += S(1710, 90, 45, 2565) + S(1755, 700, 45, 1955); // king + jack izquierdos
  s += `<g id="rightJK" class="mv-b chg">${S(3045, 90, 45, 2565)}${S(3000, 700, 45, 1955)}</g>`;
  s += S(1755, 480, 1290, 220, 'grow-b chg', 'hdr'); // header
  s += S(1755, 1900, 1290, 45, 'grow-b chg', 'sill'); // antepecho
  s += `<rect id="glass" class="glass" x="1800" y="700" width="1200" height="1200"/>`;
  // cotas
  s += `<g class="dim dimA"><line x1="1800" y1="2830" x2="3000" y2="2830"/><line x1="1800" y1="2790" x2="1800" y2="2870"/><line x1="3000" y1="2790" x2="3000" y2="2870"/><text x="2400" y="2960">RO 1.200</text></g>`;
  s += `<g class="dim dimB"><line x1="1800" y1="2830" x2="3600" y2="2830"/><line x1="1800" y1="2790" x2="1800" y2="2870"/><line x1="3600" y1="2790" x2="3600" y2="2870"/><text x="2700" y="2960">RO 1.800</text></g>`;
  s += `<text class="tag" x="0" y="-60">PARED NORTE · MÓDULO O0 · MONTANTES @400 · 45×140</text>`;
  return `<svg class="wall" viewBox="-40 -140 4880 3160" role="img" aria-label="Entramado de una pared con una ventana que se amplía de 1200 a 1800 mm; las piezas afectadas se marcan en rojo">${s}</svg>`;
}

// ---------------------------------------------------------------- estilo
const css = `
:root{--paper:#F5F2EA;--paper2:#ECE8DD;--ink:#0F1B17;--ink2:#182620;--moss:#2F4A3F;--sage:#8FA692;--wood:#B8703F;--wood2:#E2B58A;--red:#D8472B;--muted:#5E6B64;--line:rgba(15,27,23,.16);--line-d:rgba(245,242,234,.16);--serif:'Fraunces',Georgia,'Times New Roman',serif;--sans:'Inter','Segoe UI',system-ui,Arial,sans-serif;--mono:'JetBrains Mono',Consolas,'Courier New',monospace}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:#0B1310;color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.45;overflow:hidden;-webkit-font-smoothing:antialiased}
button{font:inherit;cursor:pointer;color:inherit}
a{color:inherit;text-decoration-thickness:1px;text-underline-offset:4px}
button:focus-visible,a:focus-visible{outline:2px solid var(--wood);outline-offset:4px}
.mono{font-family:var(--mono);font-weight:500;letter-spacing:.06em;font-size:11.5px;text-transform:uppercase}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}

/* --- chrome --- */
.topbar{height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;color:#C9D1CB;border-bottom:1px solid var(--line-d)}
.brand{display:flex;align-items:center;gap:12px;color:#EDE9DF}
.brand i{width:10px;height:10px;background:var(--wood);display:inline-block}
.top-actions{display:flex;gap:4px}
.top-actions button,.nav button{border:0;background:transparent;padding:8px 12px;color:#C9D1CB;border-radius:2px}
.top-actions button:hover,.nav button:hover{background:rgba(255,255,255,.07);color:#fff}
.stage{height:calc(100dvh - 104px);display:flex;align-items:center;justify-content:center;padding:8px 20px;overflow:hidden}
.nav{height:52px;display:flex;align-items:center;justify-content:center;gap:22px;color:#C9D1CB;border-top:1px solid var(--line-d);position:relative;z-index:6}
.nav button{font-size:18px;padding:4px 14px}
.nav button:disabled{opacity:.25;cursor:default}
.nav-title{min-width:160px;max-width:50vw;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.counter{font-variant-numeric:tabular-nums}
.keyhint{position:absolute;right:24px;color:#7E8A83}
.progress{position:fixed;bottom:0;left:0;height:2px;background:var(--wood);transition:width .3s;z-index:5}

/* --- slide --- */
.slide{display:none;position:relative;width:1280px;height:720px;flex-shrink:0;overflow:hidden;padding:44px 64px 84px;background:var(--paper);color:var(--ink);transform-origin:center;box-shadow:0 30px 90px rgba(0,0,0,.55)}
.slide.active{display:flex;flex-direction:column;animation:appear .3s ease}
.slide.dark{background:var(--ink);color:#EDE9DF}
.slide.dark::before{content:"";position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(var(--line-d) 1px,transparent 1px),linear-gradient(90deg,var(--line-d) 1px,transparent 1px);background-size:64px 64px;opacity:.35;mask-image:radial-gradient(ellipse at 70% 40%,#000 0%,transparent 75%);-webkit-mask-image:radial-gradient(ellipse at 70% 40%,#000 0%,transparent 75%)}
.cm{position:absolute;width:12px;height:12px;pointer-events:none;opacity:.55}
.cm::before,.cm::after{content:"";position:absolute;background:currentColor}
.cm::before{left:0;top:5.5px;width:12px;height:1px}.cm::after{top:0;left:5.5px;width:1px;height:12px}
.cm.tl{left:22px;top:22px}.cm.tr{right:22px;top:22px}.cm.bl{left:22px;bottom:22px}.cm.br{right:22px;bottom:22px}
.s-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:22px;color:var(--muted);position:relative;z-index:1}
.dark .s-head{color:#9AA79F}
.s-head b{color:var(--wood);font-weight:500;margin-right:6px}
.s-stamp{border:1px solid currentColor;padding:4px 10px;opacity:.75}
.slide h1,.slide h2,.slide h3,.slide p,.slide figure,.slide ul,.slide ol,.slide dl{margin:0}
h1,h2{font-family:var(--serif);font-weight:400;letter-spacing:-.02em;line-height:1.02;font-variation-settings:"opsz" 144,"SOFT" 30}
h1{font-size:84px}
h2{font-size:44px;margin-bottom:26px!important;max-width:1000px;position:relative;z-index:1}
h2 em,h1 em{font-style:italic;color:var(--wood);font-weight:300}
.dark h2 em,.dark h1 em{color:var(--wood2)}
h3{font-size:19px;font-weight:600;line-height:1.3;letter-spacing:-.01em}
p{font-size:17px}
.s-body{flex:1;min-height:0;position:relative;z-index:1}
.s-foot{position:absolute;left:64px;right:64px;bottom:34px;display:flex;justify-content:space-between;align-items:flex-end;gap:32px;z-index:1}
.s-mark{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.dark .s-mark{color:#7E8A83}
.chip{display:inline-flex;align-items:flex-start;gap:10px;font-size:13px;line-height:1.45;color:var(--muted);max-width:900px}
.chip i{flex:none;width:8px;height:8px;border-radius:50%;background:var(--red);margin-top:6px}
.chip.neutral i{background:var(--sage)}
.dark .chip{color:#B4BFB8}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:12px!important}
.dark .eyebrow{color:#9AA79F}
.lead{font-size:24px;line-height:1.35;letter-spacing:-.01em;font-weight:400}
.large{font-family:var(--serif);font-weight:400;font-size:28px;line-height:1.22;letter-spacing:-.01em;margin-bottom:22px!important}
.sub{color:var(--muted);font-size:15px;margin:-10px 0 22px!important}
.statement{border-left:2px solid var(--wood);padding:4px 0 4px 20px;margin-top:26px!important;font-size:19px;line-height:1.4;max-width:1000px}
.statement.small{font-size:16px;margin-top:22px!important}
.split{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.li{padding:0 0 14px;margin-bottom:14px;border-bottom:1px solid var(--line)}
.li:last-child{border-bottom:0;margin-bottom:0}
.dark .li{border-color:var(--line-d)}
.li h3{margin-bottom:5px}
.li p{font-size:16px;color:var(--muted)}
.dark .li p{color:#B4BFB8}
.clean{padding-left:0;list-style:none}
.clean li{position:relative;padding-left:22px;margin-bottom:12px;font-size:18px;line-height:1.35}
.clean li::before{content:"";position:absolute;left:0;top:11px;width:10px;height:1px;background:var(--wood)}
figure img{display:block;width:100%;height:auto}
figcaption{font-size:12.5px;color:var(--muted);margin-top:10px;line-height:1.45}
.dark figcaption{color:#9AA79F}
.band{display:flex;gap:22px;align-items:flex-start;border-top:1px solid var(--line);margin-top:28px;padding-top:16px;font-size:15.5px;line-height:1.45;color:var(--muted)}
.band strong{color:var(--wood);white-space:nowrap;padding-top:3px}
.band.pkg{margin-top:22px}
.pkg-items{display:flex;gap:10px;flex-wrap:wrap}
.pkg-items b{font-weight:500;border:1px solid var(--line);padding:6px 12px;color:var(--ink);font-size:14.5px;background:#fff}
.stats{display:grid;grid-template-columns:repeat(4,1fr) auto;gap:32px;align-items:end;border-top:1px solid var(--line-d);padding-top:18px;margin-top:22px;flex:none}
.stat strong{display:block;font-family:var(--serif);font-weight:300;font-size:50px;line-height:1;letter-spacing:-.03em;color:var(--wood2)}
.light .stat strong{color:var(--wood)}
.stat span{display:block;font-size:14px;line-height:1.35;margin-top:8px;color:#B4BFB8}
.light .stat span{color:var(--muted)}
.stats-src{color:#7E8A83;text-align:right;font-size:10.5px}
.big-num{font-family:var(--serif);font-weight:300;font-size:64px;line-height:1;letter-spacing:-.03em;color:var(--wood);margin-bottom:14px!important}
.red{color:var(--red)}
.pos{color:#2E7D4F}.neg{color:var(--red)}
.dark .pos{color:#8FCB9F}
.sw{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin:0 6px 0 14px;background:var(--wood2)}
.sw.red{background:var(--red)}.sw.new{background:#8FCB9F}.sw.gone{background:transparent;border:1px dashed #9AA79F}
.sw.wood{background:var(--wood)}.sw.outline{background:transparent;border:1.5px solid var(--ink)}.sw.dot{border-radius:50%;background:var(--ink)}

/* --- portada / cierre --- */
.cover,.closing{padding:0}
.cover .s-head,.closing .s-head{position:absolute;left:64px;right:64px;top:44px;color:#C9D1CB}
.cover-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:60% 50%}
.cover-bg.dim{opacity:.5}
.cover-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(15,27,23,.96) 0%,rgba(15,27,23,.88) 38%,rgba(15,27,23,.35) 68%,rgba(15,27,23,.15) 100%),linear-gradient(0deg,rgba(15,27,23,.85) 0%,transparent 35%)}
.cover-shade.strong{background:linear-gradient(90deg,rgba(15,27,23,.97),rgba(15,27,23,.8))}
.cover .s-body,.closing .s-body{position:static}
.cover-copy{position:absolute;left:64px;top:150px;width:720px}
.cover .kick{color:#C9D1CB;margin-bottom:30px}
.cover h1{color:#F5F2EA;margin-bottom:30px}
.cover .lead{color:#D9DFD8;max-width:560px;font-size:21px}
.cover-stamp{position:absolute;left:64px;bottom:44px;display:flex;gap:0;border:1px solid var(--line-d);color:#C9D1CB}
.cover-stamp span{padding:9px 16px;border-right:1px solid var(--line-d)}
.cover-stamp span:last-child{border-right:0}
.cover-cap{position:absolute;right:64px;bottom:52px;color:#9AA79F;text-transform:none;letter-spacing:.02em}
.cover .cm,.closing .cm{color:#EDE9DF}
.close-copy{position:absolute;left:64px;top:130px;width:900px}
.closing h2{font-size:66px;color:#F5F2EA;max-width:900px;margin-bottom:30px!important}
.closing .lead{color:#D9DFD8;max-width:680px}
.actions{display:flex;gap:14px;margin-top:34px;align-items:center}
.primary{background:var(--paper);color:var(--ink);border:0;padding:14px 22px;font-weight:500}
.ghost-btn{background:transparent;border:1px solid var(--line-d);color:#EDE9DF;padding:13px 20px}
.end-note{margin-top:46px!important;color:#9AA79F;max-width:760px;line-height:1.7}

/* --- mapa --- */
.map{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:8px}
.map-card{text-align:left;background:var(--paper2);border:1px solid transparent;padding:24px 24px 20px;display:flex;flex-direction:column;gap:10px;min-height:200px;transition:background .2s,border-color .2s}
.map-card:hover{background:#fff;border-color:var(--line)}
.map-card .mono{color:var(--wood)}
.map-card strong{font-family:var(--serif);font-weight:400;font-size:30px;letter-spacing:-.02em;line-height:1}
.map-card em{font-style:normal;color:var(--muted);font-size:15.5px;flex:1}
.map-card small{color:var(--muted);font-size:10.5px}

/* --- tesis --- */
.thesis .s-body{display:flex;flex-direction:column}
.thesis-split{grid-template-columns:.8fr 1.2fr;gap:36px;align-items:center;flex:1;min-height:0}
.thesis .lead{margin-bottom:20px!important;color:#EDE9DF;font-size:22px}
.two-promises .li h3{color:var(--wood2);font-size:17px}
.two-promises .li p{font-size:15px}
.thesis-img img{max-height:350px;object-fit:contain;filter:drop-shadow(0 30px 40px rgba(0,0,0,.5))}

/* --- capítulo --- */
.divider .s-body{display:block}
.ghost{position:absolute;left:-14px;top:70px;font-family:var(--serif);font-weight:300;font-size:420px;line-height:1;letter-spacing:-.06em;color:transparent;-webkit-text-stroke:1px rgba(226,181,138,.28);user-select:none}
.div-copy{position:absolute;left:0;bottom:70px;width:560px}
.div-ch{color:var(--wood2);font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;margin-bottom:18px!important}
.divider h2{font-size:78px;margin-bottom:16px!important}
.div-q{font-family:var(--serif);font-style:italic;font-weight:300;font-size:30px;color:#D9DFD8;line-height:1.2;margin-bottom:26px!important}
.div-toc{font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:#9AA79F;line-height:1.9;text-transform:uppercase}
.div-img{position:absolute;right:-40px;top:40px;width:660px;opacity:.9}
.div-img img{filter:drop-shadow(0 30px 40px rgba(0,0,0,.5))}

/* --- problema --- */
.problem{grid-template-columns:1.15fr .85fr;gap:48px}
.sketch{background:#F3F4EB;border:1px solid var(--line);padding:6px}
.sketch figcaption{padding:10px 6px 4px}
.steps-v>div{display:grid;grid-template-columns:52px 1fr;gap:0 14px;padding:16px 0;border-top:1px solid var(--line)}
.steps-v>div:first-child{border-top:0;padding-top:4px}
.steps-v .mono{font-size:22px;font-family:var(--serif);font-weight:300;letter-spacing:0;line-height:1.1}
.steps-v h3{font-size:21px;margin-bottom:4px}
.steps-v p{grid-column:2;color:var(--muted);font-size:16px}

/* --- matriz --- */
.client{grid-template-columns:1.2fr .8fr;gap:44px;align-items:center}
.matrix{width:100%;display:block}
.matrix .axes line{stroke:var(--ink);stroke-width:1.2}
.matrix .axes text{font-family:var(--mono);font-size:10px;letter-spacing:.08em;fill:var(--muted)}
.matrix .zone{fill:rgba(184,112,63,.09);stroke:var(--wood);stroke-dasharray:4 4;stroke-width:1.2}
.matrix .zone.later{fill:transparent;stroke:var(--muted)}
.matrix .zone-l{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;fill:var(--wood)}
.matrix .zone-l.later{fill:var(--muted)}
.matrix .pt circle{fill:var(--muted)}
.matrix .pt.hi circle{fill:var(--wood)}
.matrix .pt text{font-size:13px;fill:var(--ink);font-weight:500}
.matrix .pt .sub{font-size:11px;fill:var(--muted);font-weight:400}

/* --- mvp --- */
.mvp{grid-template-columns:1.05fr .95fr;gap:52px}
.domain{position:relative;padding:34px 28px 30px;border:1px dashed var(--wood)}
.domain img{width:100%}
.domain .tag{position:absolute;background:var(--paper);color:var(--wood);padding:3px 8px;border:1px solid var(--wood);font-size:10px}
.domain .t1{left:-1px;top:-11px}.domain .t2{left:130px;top:-11px}.domain .t3{right:-1px;top:-11px}.domain .t4{left:-1px;bottom:-11px}.domain .t5{right:-1px;bottom:-11px}
.domain figcaption{position:absolute;left:28px;bottom:8px;font-size:11px}
.pills{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.pills li{border:1px solid var(--line);padding:7px 12px;font-size:14px;border-radius:2px;background:#fff}

/* --- capas --- */
.layers{display:grid;grid-template-columns:1fr 340px;gap:36px;align-items:start;height:100%}
.layers-stage{position:relative;height:400px}
.layers-stage img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:0;transition:opacity .5s ease}
.layers-stage img.on{opacity:1}
.layers-stage figcaption{position:absolute;left:0;bottom:-24px;font-size:10px}
.layers-list{list-style:none;padding:0;margin:0}
.layers-list button{width:100%;text-align:left;display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:start;padding:12px 14px;border:0;border-bottom:1px solid var(--line);background:transparent;border-left:2px solid transparent;transition:background .2s}
.layers-list button:hover{background:var(--paper2)}
.layers-list button[aria-pressed=true]{background:var(--paper2);border-left-color:var(--wood)}
.layers-list .mono{color:var(--wood);padding-top:3px}
.layers-list strong{display:block;font-size:17px}
.layers-list small{display:block;color:var(--muted);font-size:13px;margin-top:2px}
.layers-list button[aria-pressed=false] strong{color:var(--muted);font-weight:500}

/* --- rail (flujo) --- */
.rail{display:grid;grid-template-columns:repeat(5,1fr);gap:22px;margin-top:22px}
.rail>div{border-top:1px solid var(--ink);padding-top:16px;position:relative}
.rail>div::after{content:"";position:absolute;right:-16px;top:-3px;width:5px;height:5px;background:var(--wood);border-radius:50%}
.rail>div:last-child::after{display:none}
.rail .mono{color:var(--wood);display:block}
.rail svg{width:36px;height:36px;color:var(--ink);margin:22px 0 14px;display:block}
.rail h3{font-family:var(--serif);font-weight:400;font-size:28px;margin-bottom:8px}
.rail p{font-size:16px;color:var(--muted)}

/* --- ventana --- */
.win{display:grid;grid-template-columns:1.25fr .75fr;gap:40px;align-items:start}
.win-stage{position:relative}
.wall{width:100%;display:block}
.wall .pc{fill:var(--wood2);transition:fill .5s,width .9s cubic-bezier(.6,0,.2,1),transform .9s cubic-bezier(.6,0,.2,1),opacity .6s}
.wall .glass{fill:rgba(190,215,230,.10);stroke:rgba(190,215,230,.35);stroke-width:8;transition:width .9s cubic-bezier(.6,0,.2,1)}
.wall .new-b{opacity:0}
.wall .dim line{stroke:#9AA79F;stroke-width:8}
.wall .dim text{font-family:var(--mono);font-size:120px;fill:#C9D1CB;text-anchor:middle;letter-spacing:.06em}
.wall .dimB{opacity:0}
.wall .dim{transition:opacity .4s}
.wall .tag{font-family:var(--mono);font-size:105px;fill:#7E8A83;letter-spacing:.06em}
.wall.b #hdr,.wall.b #sill{width:1890px;fill:var(--red)}
.wall.b #glass{width:1800px}
.wall.b #rightJK{transform:translateX(600px)}
.wall.b #rightJK .pc{fill:var(--red)}
.wall.b .gone-b{opacity:0}
.wall.b .new-b{opacity:1;fill:#8FCB9F}
.wall.b .dimA{opacity:0}.wall.b .dimB{opacity:1}
.win-legend{display:flex;gap:18px;color:#9AA79F;font-size:10px;margin-top:10px}
.win-legend .sw{margin-left:0;width:10px;height:10px}
.win-log{background:var(--ink2);border:1px solid var(--line-d);padding:18px 20px;min-height:400px}
.win-log .head{display:grid;margin-bottom:14px;color:var(--wood2);font-size:10.5px}
.win-log .st{grid-area:1/1;transition:opacity .4s}
.win-log .stB,.win-log.b .stA{opacity:0}.win-log.b .stB{opacity:1}
.log{list-style:none;padding:0;font-size:14px;line-height:1.4}
.log li{padding:8px 0;border-top:1px solid var(--line-d);color:#D9DFD8;transition:opacity .5s,transform .5s}
.log li em{color:var(--wood2)}
.log li b{font-weight:600;color:#F5F2EA}
.log li.b{opacity:0;transform:translateY(6px)}
.win-log.b .log li.b{opacity:1;transform:none}
.win-log.b .log li.b:nth-child(3){transition-delay:.15s}.win-log.b .log li.b:nth-child(4){transition-delay:.3s}.win-log.b .log li.b:nth-child(5){transition-delay:.45s}.win-log.b .log li.b:nth-child(6){transition-delay:.6s}.win-log.b .log li.b:nth-child(7){transition-delay:.75s}.win-log.b .log li.b:nth-child(8){transition-delay:1s}.win-log.b .log li.b:nth-child(9){transition-delay:1.2s}
.log li.warn{color:#F1B08E}.log li.warn b{color:#F1B08E}
.log li.warn::before{content:"⚠ ";}
.log li.ok{color:#8FCB9F}

/* --- identidad --- */
.identity{grid-template-columns:.95fr 1.05fr;gap:56px}
.card-id{background:var(--ink);color:#EDE9DF;padding:28px 30px;text-transform:none;letter-spacing:0;font-size:14px;font-weight:400;position:relative}
.card-id::before{content:"ID ESTABLE";position:absolute;right:22px;top:20px;font-size:10px;letter-spacing:.1em;color:#7E8A83}
.card-id .id{font-size:21px;color:var(--wood2);margin-bottom:22px!important;padding-bottom:18px;border-bottom:1px solid var(--line-d);font-weight:500}
.card-id dl{display:grid;grid-template-columns:96px 1fr;gap:13px 16px}
.card-id dt{color:#7E8A83;text-transform:uppercase;font-size:10.5px;letter-spacing:.08em;padding-top:3px}
.card-id dd{margin:0;color:#EDE9DF}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;vertical-align:1px}
.dot.ok{background:#8FCB9F}

/* --- arquitectura --- */
.arch{display:grid;gap:12px}
.tier{display:grid;grid-template-columns:110px repeat(3,1fr);gap:12px;align-items:stretch}
.tier-l{align-self:center;color:var(--muted);font-size:10px}
.box{background:#fff;border:1px solid var(--line);padding:18px 20px;font-size:17px;line-height:1.3;font-weight:500;min-height:84px}
.box small{display:block;font-weight:400;color:var(--muted);font-size:13.5px;margin-top:6px}
.t-top .box{background:transparent;border-style:dashed}
.t-top .box.ai{border-color:var(--wood);color:var(--wood)}
.box.wide{grid-column:2 / 5;text-align:center;background:var(--paper2);font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;font-weight:500;padding:14px;min-height:0}
.t-core .box{min-height:110px}
.t-core .box{background:var(--ink);color:#EDE9DF;border-color:var(--ink)}
.t-core .box small{color:#B4BFB8}
.t-core .box.core{background:var(--moss);border-color:var(--moss)}
.t-core .tier-l{color:var(--wood)}

/* --- base Angus --- */
.base-split{grid-template-columns:1.05fr .95fr;gap:48px;align-items:center}
.base-figs{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:end}
.base-figs img{max-height:370px;object-fit:contain;filter:drop-shadow(0 20px 30px rgba(0,0,0,.5))}
.base-figs figcaption{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase}

/* --- competencia --- */
.comp{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:6px}
.comp-card{background:#fff;border:1px solid var(--line);padding:22px 20px 20px;min-height:380px;display:flex;flex-direction:column}
.comp-card.status{background:var(--paper2);border-style:dashed}
.comp-card h3{font-family:var(--serif);font-weight:400;font-size:24px;margin-bottom:14px;letter-spacing:-.01em}
.comp-card h3 a{text-decoration:none}
.comp-card h3 a:hover{color:var(--wood)}
.comp-card p{font-size:14.5px;color:var(--muted);line-height:1.4}
.comp-card .eyebrow{margin-top:auto;padding-top:18px;font-size:9.5px;margin-bottom:6px!important}
.comp-card .demo{color:var(--ink);font-weight:500}

/* --- ventaja --- */
.adv{grid-template-columns:1.25fr .75fr;gap:56px;align-items:start}
.pillars>div{display:grid;grid-template-columns:52px 1fr;gap:0 14px;padding:26px 0;border-top:1px solid var(--line)}
.pillars>div:first-child{border-top:0;padding-top:4px}
.pillars .mono{color:var(--wood);padding-top:8px}
.pillars h3{font-family:var(--serif);font-weight:400;font-size:27px;margin-bottom:6px;letter-spacing:-.01em}
.pillars p{grid-column:2;color:var(--muted);font-size:16.5px}
.callout{background:var(--paper2);padding:28px 30px}
.callout p{font-size:16px}
.callout .big-num{font-size:64px}
.callout .small{color:var(--muted);font-size:13.5px;margin-top:10px!important}
.callout.dark-c{background:var(--ink2);border:1px solid var(--line-d)}
.callout.dark-c .big-num{color:var(--wood2)}

/* --- escala --- */
.scale>div{display:grid;grid-template-columns:230px 1fr 220px;gap:24px;align-items:center;padding:11px 0;border-bottom:1px solid var(--line)}
.scale .lbl{color:var(--muted);text-transform:none;letter-spacing:.02em;font-size:13px}
.scale .dots{display:flex;flex-wrap:wrap;gap:4px;max-width:600px}
.scale .dots i{width:8px;height:8px;background:var(--wood);border-radius:50%;display:block}
.scale strong{font-family:var(--serif);font-weight:300;font-size:34px;letter-spacing:-.02em;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.scale+.band{margin-top:18px}

/* --- precios --- */
.pricing{display:grid;grid-template-columns:1.1fr 1.1fr 1.1fr .9fr;gap:14px}
.price{background:#fff;border:1px solid var(--line);padding:26px 24px 24px;position:relative;min-height:250px;display:flex;flex-direction:column}
.price.first{background:var(--ink);color:#EDE9DF;border-color:var(--ink)}
.price.first .eyebrow{color:#9AA79F}
.price.extra{background:transparent;border-style:dashed}
.amt{font-family:var(--serif);font-weight:300;font-size:54px;letter-spacing:-.03em;line-height:1;color:var(--wood);margin:6px 0 10px!important;white-space:nowrap}
.amt.sep{font-size:28px;line-height:1.05;white-space:normal;color:var(--ink);margin-top:14px!important;margin-bottom:22px!important}
.price.first .amt{color:var(--wood2)}
.amt small{font-family:var(--mono);font-size:12px;letter-spacing:.08em;vertical-align:28px;margin-right:6px;color:var(--muted)}
.per{color:var(--muted);margin-bottom:18px!important}
.price.first .per{color:#9AA79F}
.learn{font-size:15.5px;line-height:1.4;margin-top:auto!important}
.flag{position:absolute;right:16px;top:-12px;color:var(--paper);background:var(--wood);font-size:9.5px;padding:5px 9px}

/* --- piloto --- */
.metrics{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;gap:34px;margin-top:6px}
.metrics .stat strong{font-size:84px;color:var(--wood)}
.metrics .stat span{font-size:16px;color:var(--ink);margin-top:14px}
.pilot-l{margin-top:40px!important;padding-top:22px;border-top:1px solid var(--line)}
.pilot{display:grid;grid-template-columns:repeat(5,1fr);gap:18px}
.pilot>div{display:grid;gap:10px;position:relative;padding-right:10px}
.pilot>div:not(:last-child)::after{content:"→";position:absolute;right:-6px;top:0;color:var(--wood);font-size:14px}
.pilot b{color:var(--wood)}
.pilot span{font-size:15px;line-height:1.35}

/* --- embudo --- */
.funnel{width:100%;display:block;margin-top:10px}
.funnel .bar{fill:var(--wood)}
.funnel .link{fill:rgba(184,112,63,.18)}
.funnel .pct{font-family:var(--mono);font-size:12px;fill:var(--muted);letter-spacing:.06em}
.funnel .num{font-family:var(--serif);font-weight:300;font-size:46px;fill:var(--ink);letter-spacing:-.03em}
.funnel .lbl{font-size:13px;fill:var(--muted)}

/* --- presupuesto --- */
.budget{grid-template-columns:1.25fr .75fr;gap:56px;align-items:start}
.rng{display:grid;grid-template-columns:250px 1fr 120px;gap:16px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line);font-size:15px}
.track{position:relative;height:16px;background:var(--paper2)}
.track i{position:absolute;top:0;height:100%;background:var(--wood)}
.rv{color:var(--muted);text-align:right;text-transform:none;letter-spacing:0;font-size:12px}
.axis{display:grid;grid-template-columns:250px 1fr 120px;gap:16px;color:var(--muted);font-size:10px;margin-top:10px!important}
.axis span{grid-column:2;display:flex;justify-content:space-between}
.axis em{font-style:normal}
.total .hero{font-family:var(--serif);font-weight:300;font-size:74px;letter-spacing:-.04em;line-height:1;margin-bottom:18px!important}
.total .hero span{display:block;font-size:40px;color:var(--wood);margin-top:4px}
.total p{font-size:15px;color:var(--muted)}

/* --- años --- */
.years-split{grid-template-columns:1.15fr .85fr;gap:44px;align-items:center}
.years{width:100%;display:block}
.years .grid{stroke:var(--line);stroke-width:1}
.years .grid.zero{stroke:var(--ink);stroke-width:1.2}
.years .gl,.years .yr{font-family:var(--mono);font-size:10.5px;fill:var(--muted);letter-spacing:.06em}
.years .ing{fill:var(--wood)}
.years .fix{fill:transparent;stroke:var(--ink);stroke-width:1.4}
.years .vl{font-family:var(--mono);font-size:11px;fill:var(--ink)}
.years .vl.f{fill:var(--muted)}
.years polyline.res{fill:none;stroke:var(--ink);stroke-width:1.6;stroke-dasharray:4 4}
.years circle.res{stroke:var(--paper);stroke-width:2}
.years circle.neg{fill:var(--red)}.years circle.pos{fill:#2E7D4F}
.years .rl{font-family:var(--mono);font-size:12px;font-weight:600}
.years .rl.neg{fill:var(--red)}.years .rl.pos{fill:#2E7D4F}
.tbl{width:100%;border-collapse:collapse;font-size:15px}
.tbl th{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:right;padding:0 0 10px;border-bottom:1px solid var(--ink);font-weight:500}
.tbl th:first-child,.tbl td:first-child{text-align:left}
.tbl td{padding:11px 0;border-bottom:1px solid var(--line);text-align:right;font-variant-numeric:tabular-nums}
.tbl .tot td{font-weight:600;border-bottom:0}
.legend{margin-top:20px!important;color:var(--muted);font-size:10px}
.legend .sw{width:10px;height:10px;margin-left:0}

/* --- punto de equilibrio --- */
.be-split{grid-template-columns:1.15fr .85fr;gap:48px;align-items:center}
.be{width:100%;display:block}
.be .loss{fill:rgba(216,71,43,.08)}.be .gain{fill:rgba(184,112,63,.16)}
.be .grid{stroke:var(--line)}
.be .gl,.be .ax,.be .ll,.be .bl{font-family:var(--mono);font-size:10.5px;fill:var(--muted);letter-spacing:.06em}
.be .fixed{stroke:var(--ink);stroke-width:1.4;stroke-dasharray:5 4}
.be .contrib{stroke:var(--wood);stroke-width:2}
.be .ll.w{fill:var(--wood)}
.be .drop{stroke:var(--red);stroke-width:1;stroke-dasharray:3 3}
.be .pt{fill:var(--red);stroke:var(--paper);stroke-width:3}
.be .big{font-family:var(--serif);font-weight:300;font-size:48px;fill:var(--ink);letter-spacing:-.03em}
.be .bl{fill:var(--ink);font-size:9.5px}
.sens>div{display:flex;justify-content:space-between;align-items:baseline;padding:14px 0;border-bottom:1px solid var(--line);font-size:16px}
.sens b{font-family:var(--serif);font-weight:400;font-size:28px;letter-spacing:-.02em;font-variant-numeric:tabular-nums}

/* --- equipo --- */
.team{grid-template-columns:1.1fr .9fr}
.team .li{padding-bottom:12px;margin-bottom:12px}
.team .li h3{font-size:18px}
.team .li p{font-size:15px}
.cadence>div{display:grid;grid-template-columns:120px 1fr;gap:16px;padding:18px 0;border-top:1px solid var(--line);font-size:17px}
.cadence .mono{color:var(--wood);padding-top:3px}

/* --- roadmap --- */
.roadmap{margin-top:10px;--cols:1.55fr 1.55fr 1.55fr 1fr 1fr 1fr .62fr .62fr .62fr .62fr .62fr .62fr}
.months{display:grid;grid-template-columns:var(--cols);gap:8px;color:var(--muted);font-size:10px;padding-bottom:8px;border-bottom:1px solid var(--ink)}
.months span{border-left:1px solid var(--line);padding-left:6px}
.phases{display:grid;grid-template-columns:var(--cols);gap:8px;margin-top:14px}
.ph{background:#fff;border:1px solid var(--line);border-top:3px solid var(--wood);padding:16px 14px 14px;min-height:300px;display:flex;flex-direction:column}
.ph .range{color:var(--wood);font-size:9.5px;display:block;margin-bottom:10px}
.ph h3{font-family:var(--serif);font-weight:400;font-size:23px;margin-bottom:10px;letter-spacing:-.01em}
.ph p{font-size:14px;color:var(--muted);line-height:1.4}
.ph .gate{margin-top:auto;padding-top:14px;color:var(--ink);font-size:10.5px;text-transform:none;letter-spacing:.02em;line-height:1.5;border-top:1px dashed var(--line)}
.ph .gate::first-letter{color:var(--wood)}

/* --- señales --- */
.signals{gap:24px}
.go,.stop{padding:26px 28px;border:1px solid var(--line);min-height:240px}
.go{background:#fff}.stop{background:var(--paper2)}
.signals .clean li{font-size:19px;margin-bottom:14px}
.go .clean li::before{background:#2E7D4F}.stop .clean li::before{background:var(--red)}
.risks-l{margin-top:26px!important;margin-bottom:10px!important}
.risks{display:flex;flex-wrap:wrap;gap:8px;font-size:10.5px;color:var(--ink)}
.risks span{border:1px solid var(--line);padding:8px 12px;background:#fff}

/* --- inversión --- */
.invest-split{grid-template-columns:1.1fr .9fr;align-items:start}
.invest .lead{color:#EDE9DF;margin-bottom:22px!important}
.invest .paths .li h3{color:var(--wood2);font-size:17px}
.chain-l{margin-top:34px!important;padding-top:18px;border-top:1px solid var(--line-d)}
.chain{display:flex;flex-wrap:wrap;align-items:center;gap:8px;color:#C9D1CB;font-size:10.5px}
.chain span{border:1px solid var(--line-d);padding:8px 12px}
.chain span.now{background:var(--wood);border-color:var(--wood);color:var(--ink)}
.chain i{color:var(--wood2);font-style:normal}

/* --- semanas --- */
.weeks{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.weeks>div{border-top:1px solid var(--ink);padding-top:14px;display:flex;flex-direction:column;min-height:280px}
.weeks .mono{color:var(--wood)}
.weeks h3{font-family:var(--serif);font-weight:400;font-size:26px;margin:14px 0 10px;letter-spacing:-.01em}
.weeks p{font-size:15px;color:var(--muted);line-height:1.4}
.weeks .ev{margin-top:auto;padding-top:14px;border-top:1px dashed var(--line);color:var(--ink);font-size:14px}
.weeks .ev b{display:block;color:var(--muted);font-size:9.5px;margin-bottom:4px}

/* --- diálogos --- */
dialog{border:0;max-width:none;max-height:none;padding:0;color:var(--ink);background:var(--paper);box-shadow:0 30px 90px rgba(0,0,0,.6)}
dialog::backdrop{background:rgba(6,12,10,.75);backdrop-filter:blur(4px)}
.dialog-head{position:sticky;top:0;z-index:2;background:var(--paper);padding:18px 26px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}
.dialog-head strong{font-family:var(--serif);font-weight:400;font-size:22px}
.dialog-head button{background:transparent;border:1px solid var(--line);padding:8px 14px}
.index-dialog{width:min(900px,92vw);height:85vh}
.index-list{padding:18px;display:grid;grid-template-columns:1fr 1fr;gap:2px}
.index-list button{text-align:left;border:0;border-bottom:1px solid var(--line);padding:13px 12px;background:transparent;font-size:14.5px;display:grid;grid-template-columns:36px 1fr;gap:10px}
.index-list button:hover,.index-list button[aria-current=true]{background:var(--paper2)}
.index-list button span{color:var(--wood);font-family:var(--mono);font-size:11px;padding-top:3px}
.index-list button.div{font-family:var(--serif);font-size:17px;margin-top:8px}
.doc-dialog{width:min(1100px,95vw);height:92vh}
.document{max-width:900px;margin:0 auto;padding:40px 40px 80px}
.document h1{font-size:40px;margin-bottom:20px}
.document h2{font-size:30px;margin:44px 0 16px}
.document h3{font-size:22px;margin:24px 0 10px}
.document p,.document li{font-size:16.5px;line-height:1.65;margin-bottom:12px}
.document table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.45}
.document th,.document td{padding:10px 12px;border:1px solid var(--line);text-align:left;vertical-align:top}
.document th{background:var(--paper2);font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase}
.table-scroll{overflow:auto;margin:20px 0}
.document hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.document a{color:var(--wood)}
.toast{position:fixed;bottom:70px;left:50%;transform:translateX(-50%);background:var(--paper);color:var(--ink);padding:12px 18px;font-size:14px;z-index:20}

/* --- lectura --- */
.reading{overflow:auto}
.reading .stage{height:auto;display:block;padding:10px 20px}
.reading .slide{display:flex;flex-direction:column;transform:none!important;margin:24px auto;max-width:1280px;width:100%;height:auto;min-height:700px;overflow:visible}
.reading .cover,.reading .closing,.reading .divider{height:720px;min-height:0;overflow:hidden}
.reading .s-foot{position:static;margin-top:32px}
.reading .nav{position:sticky;bottom:0;background:#0B1310}
.reading .keyhint{display:none}
@keyframes appear{from{opacity:.5}to{opacity:1}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media(max-width:650px){.topbar{padding:0 10px;height:48px}.brand span{display:none}.top-actions button{padding:6px 8px;font-size:10px}#fullscreen{display:none}.stage{height:calc(100dvh - 96px);padding:0 6px}.nav{gap:6px}.nav-title{min-width:120px}.index-list{grid-template-columns:1fr}.document{padding:24px 18px}.reading .slide{padding:26px 22px;min-height:0;margin:14px 0}.reading .cover,.reading .closing,.reading .divider{height:auto;min-height:520px}.reading h1{font-size:44px}.reading h2,.reading .divider h2,.reading .closing h2{font-size:34px}.reading .split,.reading .map,.reading .rail,.reading .comp,.reading .pricing,.reading .metrics,.reading .weeks,.reading .layers,.reading .win,.reading .base-figs{grid-template-columns:1fr;gap:20px}.reading .tier{grid-template-columns:1fr}.reading .box.wide{grid-column:auto}.reading .phases{grid-template-columns:1fr}.reading .ph{grid-column:auto!important;min-height:0}.reading .months{display:none}.reading .ghost{font-size:200px;top:20px}.reading .div-copy{position:static;width:auto;margin-top:220px}.reading .div-img{display:none}.reading .cover,.reading .closing{padding:26px 22px}.reading .cover .s-body,.reading .closing .s-body{position:relative;z-index:1}.reading .cover-copy,.reading .close-copy{position:relative;z-index:2;left:auto;top:auto;width:auto;padding:40px 0 30px}.reading .cover-stamp,.reading .actions{position:relative;z-index:2;left:auto;bottom:auto}.reading .cover-stamp{position:static;flex-wrap:wrap;margin-top:20px;display:inline-flex}.reading .cover-cap{display:none}.reading .cover .s-head,.reading .closing .s-head{position:relative;left:auto;right:auto;top:auto;z-index:1}.reading .stats{grid-template-columns:1fr 1fr}.reading .scale>div{grid-template-columns:1fr;gap:8px}.reading .scale strong{text-align:left}.reading .rng,.reading .axis{grid-template-columns:1fr}.reading .rv{text-align:left}.reading .comp-card,.reading .weeks>div,.reading .map-card{min-height:0}.reading .divider{padding-bottom:40px}.reading .layers-stage{max-height:none}.reading .win-log{min-height:0}.reading .domain .tag{display:none}.reading .s-foot{flex-direction:column;align-items:flex-start;gap:10px}.reading .s-mark{display:none}}
@media print{@page{size:1280px 720px;margin:0}body{background:#fff;overflow:visible}.topbar,.nav,.progress,dialog,.toast,.keyhint{display:none!important}.stage,.reading .stage{display:block;height:auto;padding:0;overflow:visible}.slide,.slide.active,.reading .slide{display:flex!important;flex-direction:column;width:1280px!important;height:720px!important;min-height:720px!important;max-width:none!important;transform:none!important;margin:0!important;box-shadow:none;break-after:page;overflow:hidden!important;print-color-adjust:exact;-webkit-print-color-adjust:exact}.slide:last-child{break-after:auto}.reading .s-foot{position:absolute;margin:0}.layers-stage img{opacity:1!important}.layers-stage img:not(.on){display:none}}
`;

// ---------------------------------------------------------------- runtime del visor
const script = (tocText, rangeText, dividerIndex) => `(()=>{'use strict';
const TOC=${JSON.stringify(tocText)},RANGES=${JSON.stringify(rangeText)},DIV=${JSON.stringify(dividerIndex)};
document.querySelectorAll('[data-toc]').forEach(e=>e.textContent=TOC[e.dataset.toc]);
document.querySelectorAll('[data-range]').forEach(e=>e.textContent=RANGES[e.dataset.range]);
const slides=[...document.querySelectorAll('.slide')],count=slides.length;let current=0,reading=false;const $=id=>document.getElementById(id);
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function resize(){if(reading)return;const r=document.querySelector('.stage').getBoundingClientRect(),scale=Math.min((r.width-40)/1280,(r.height-16)/720,1.25);slides.forEach(s=>s.style.transform='scale('+Math.max(.1,scale)+')');}
function go(n,scroll=true){current=Math.max(0,Math.min(count-1,n));slides.forEach((s,i)=>{s.classList.toggle('active',i===current);s.setAttribute('aria-hidden',reading?'false':String(i!==current));});$('counter').textContent=String(current+1).padStart(2,'0')+' / '+count;$('navTitle').textContent=slides[current].dataset.title;$('progress').style.width=((current+1)/count*100)+'%';$('prev').disabled=current===0;$('next').disabled=current===count-1;$('live').textContent='Diapositiva '+(current+1)+' de '+count+': '+slides[current].dataset.title;document.querySelectorAll('[data-slide]').forEach(b=>b.setAttribute('aria-current',String(+b.dataset.slide===current)));try{history.replaceState(null,'','#'+(current+1));}catch(e){}if(reading&&scroll)slides[current].scrollIntoView({behavior:'smooth',block:'start'});resize();onChange();}
function doc(){$('docDialog').showModal();}
function toggleRead(){reading=!reading;document.body.classList.toggle('reading',reading);$('readingBtn').setAttribute('aria-pressed',String(reading));$('readingBtn').textContent=reading?'Diapositivas':'Lectura';go(current,false);if(reading)slides[current].scrollIntoView({block:'start'});else window.scrollTo(0,0);}
async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(e){const t=document.createElement('div');t.className='toast';t.textContent='Usá F11 para pantalla completa.';document.body.append(t);setTimeout(()=>t.remove(),3500);}}
/* capas interactivas */
const L=document.querySelector('[data-layers]');let lTimer=null,lUser=false,lIdx=0;
function setLayer(i){if(!L)return;lIdx=i;L.querySelectorAll('[data-layer]').forEach(im=>im.classList.toggle('on',+im.dataset.layer===i));L.querySelectorAll('[data-i]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.i===i)));}
if(L){L.querySelectorAll('[data-i]').forEach(b=>b.onclick=()=>{lUser=true;clearInterval(lTimer);setLayer(+b.dataset.i);});}
/* ventana animada */
const W=document.querySelector('[data-window]');let wTimer=null,wState=false;
function setWin(b){if(!W)return;wState=b;W.querySelector('.wall').classList.toggle('b',b);W.querySelector('.win-log').classList.toggle('b',b);}
function wCycle(){clearTimeout(wTimer);if(reduce)return void setWin(true);setWin(!wState);wTimer=setTimeout(wCycle,wState?5200:2600);}
if(W)W.querySelector('.win-stage').onclick=()=>{clearTimeout(wTimer);setWin(!wState);};
function onChange(){const s=slides[current];clearInterval(lTimer);clearTimeout(wTimer);
 if(L&&s.contains(L)&&!lUser&&!reduce){lTimer=setInterval(()=>setLayer((lIdx+1)%5),2400);}
 if(W&&s.contains(W)){setWin(false);wTimer=setTimeout(wCycle,1800);}}
$('prev').onclick=()=>go(current-1);$('next').onclick=()=>go(current+1);$('indexBtn').onclick=()=>$('indexDialog').showModal();$('docBtn').onclick=doc;$('readingBtn').onclick=toggleRead;$('fullscreen').onclick=fullscreen;
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
document.querySelectorAll('[data-slide]').forEach(b=>b.onclick=()=>{$('indexDialog').close();go(+b.dataset.slide);});
document.querySelectorAll('[data-chapter]').forEach(b=>{if(b.tagName==='BUTTON')b.onclick=()=>go(DIV[b.dataset.chapter]);});
document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>b.dataset.action==='doc'?doc():go(0));
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]')||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;if(e.target.closest('button,a')&&[' ','Enter'].includes(e.key))return;
 if(e.key==='ArrowRight'||e.key==='PageDown'||(e.key===' '&&!reading)){e.preventDefault();go(current+1);}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(current-1);}if(e.key==='Home'){e.preventDefault();go(0);}if(e.key==='End'){e.preventDefault();go(count-1);}if(e.key.toLowerCase()==='i')$('indexDialog').showModal();if(e.key.toLowerCase()==='f')fullscreen();});
let touch=null;const stage=document.querySelector('.stage');stage.addEventListener('touchstart',e=>{touch=[e.changedTouches[0].clientX,e.changedTouches[0].clientY];},{passive:true});stage.addEventListener('touchend',e=>{if(!touch||reading||e.target.closest('button,a'))return;const dx=e.changedTouches[0].clientX-touch[0],dy=e.changedTouches[0].clientY-touch[1];if(Math.abs(dx)>60&&Math.abs(dx)>Math.abs(dy)*1.5)go(current+(dx<0?1:-1));touch=null;},{passive:true});
window.addEventListener('resize',resize);window.addEventListener('hashchange',()=>{const n=parseInt(location.hash.slice(1),10);if(Number.isFinite(n))go(n-1);});
const initial=parseInt(location.hash.slice(1),10);go(Number.isFinite(initial)?initial-1:0);if(matchMedia('(max-width:650px)').matches)toggleRead();})();`;

module.exports = { esc, inline, markdown, prepareAssets, chip, row, stat, fig, wallSvg, css, script };
