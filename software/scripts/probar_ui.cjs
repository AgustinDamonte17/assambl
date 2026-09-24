// Recorre la interfaz en un navegador headless y guarda capturas.
//   npm install --no-save puppeteer
//   node scripts/probar_ui.cjs
//
// Verifica el camino completo: ubicación → lote → modelo 3D → clima.

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");

const BASE = process.env.BASE_UI || "http://localhost:5173";
const SALIDA = path.join(__dirname, "..", "backend", "cache", "salidas", "ui");
const LAT = -31.42;
const LON = -64.19;

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

async function escribirCampo(pagina, selector, valor) {
  const el = await pagina.waitForSelector(selector);
  await el.focus();
  await pagina.evaluate((e) => {
    e.value = "";
  }, el);
  await el.type(String(valor));
  await pagina.keyboard.press("Tab");
}

// React escucha el setter nativo del input, así que no alcanza con asignar value.
async function mover(pagina, selector, valor) {
  await pagina.waitForSelector(selector);
  await pagina.evaluate(
    (s, v) => {
      const r = document.querySelector(s);
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set.call(r, v);
      r.dispatchEvent(new Event("input", { bubbles: true }));
      r.dispatchEvent(new Event("change", { bubbles: true }));
    },
    selector,
    valor,
  );
}

async function clickPorTexto(pagina, texto) {
  const encontrado = await pagina.evaluate((t) => {
    const b = [...document.querySelectorAll("button")].find((x) => x.textContent.trim().includes(t) && !x.disabled);
    if (b) b.click();
    return !!b;
  }, texto);
  if (!encontrado) throw new Error(`No se encontró un botón habilitado con el texto "${texto}"`);
}

async function principal() {
  fs.mkdirSync(SALIDA, { recursive: true });
  const navegador = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  });
  const pagina = await navegador.newPage();
  await pagina.setViewport({ width: 1600, height: 950 });

  const errores = [];
  pagina.on("console", (m) => m.type() === "error" && errores.push(m.text()));
  pagina.on("pageerror", (e) => errores.push(`pageerror: ${e.message}`));

  await pagina.goto(BASE, { waitUntil: "networkidle2" });
  await pagina.evaluate(() => localStorage.clear());
  await pagina.reload({ waitUntil: "networkidle2" });

  // 1 · Ubicación
  const campos = await pagina.$$("input[inputmode='decimal']");
  await escribirCampo(pagina, "input[inputmode='decimal']", LAT);
  await campos[1].focus();
  await pagina.evaluate((e) => (e.value = ""), campos[1]);
  await campos[1].type(String(LON));
  await pagina.keyboard.press("Tab");
  await esperar(2500);
  await pagina.screenshot({ path: path.join(SALIDA, "1_ubicacion.png") });

  await clickPorTexto(pagina, "Generar escena 3D");
  // innerText devuelve el texto ya transformado por CSS: los títulos van en
  // mayúsculas, así que las búsquedas se hacen sin distinguir may/min.
  await pagina.waitForFunction(() => /posts del relieve/i.test(document.body.innerText), { timeout: 180000 });
  await esperar(1500);
  await pagina.screenshot({ path: path.join(SALIDA, "2_relieve.png") });

  const resumen = await pagina.evaluate(() => {
    const filas = [...document.querySelectorAll("aside div")]
      .filter((d) => d.children.length === 2 && d.className.includes("justify-between"))
      .map((d) => `${d.children[0].innerText.trim()}: ${d.children[1].innerText.trim()}`);
    // La naturaleza que declara cada fuente, no la palabra suelta en la página: el
    // texto explicativo también dice «provisional» cuando el relieve es real.
    return { filas, provisional: filas.some((f) => /:\s*provisional$/i.test(f)) };
  });
  console.log("relieve:");
  for (const f of resumen.filas) console.log("  " + f);
  console.log("  escena provisional:", resumen.provisional);

  // 2 · Lote
  await clickPorTexto(pagina, "Siguiente: lote");
  await esperar(1200);
  await clickPorTexto(pagina, "Crear");
  await esperar(2500);
  await pagina.screenshot({ path: path.join(SALIDA, "3_lote.png") });
  const reglas = await pagina.evaluate(() =>
    [...document.querySelectorAll("li")].map((l) => l.innerText.replace(/\n/g, " | ")).filter((t) => /^R01\./.test(t)),
  );
  console.log("\nreglas R01:");
  for (const r of reglas) console.log("  " + r);

  // 3 · Modelo 3D
  await clickPorTexto(pagina, "Siguiente: modelo 3D");
  await pagina.waitForFunction(() => document.querySelector("canvas") !== null, { timeout: 30000 });
  await esperar(6000);
  await pagina.screenshot({ path: path.join(SALIDA, "4_modelo_mediodia.png") });

  // Mover el sol a la tarde con el control horario.
  await mover(pagina, "input[type='range'][max='24']", "17.5");
  await esperar(2500);
  await pagina.screenshot({ path: path.join(SALIDA, "5_modelo_tarde.png") });

  // Entorno completo a media mañana: con el sol a media altura se leen las laderas.
  await mover(pagina, "input[type='range'][max='24']", "9.5");
  await clickPorTexto(pagina, "Todo");
  await esperar(2500);
  await pagina.screenshot({ path: path.join(SALIDA, "5b_modelo_entorno.png") });

  const sol = await pagina.evaluate(() => {
    const t = document.body.innerText.split("\n");
    return t.filter((l) => /amanece|atardece|Azimut|Altura sobre|Mediodía solar|Duración/i.test(l)).map((l) => l.trim());
  });
  console.log("\nsol:", sol.join(" · "));

  // 4 · Clima
  await clickPorTexto(pagina, "Clima");
  try {
    await pagina.waitForFunction(() => /rosa de vientos/i.test(document.body.innerText), { timeout: 300000 });
  } catch (e) {
    await pagina.screenshot({ path: path.join(SALIDA, "x_clima_fallo.png") });
    const panel = await pagina.evaluate(() => document.querySelector("aside")?.innerText ?? "(sin panel)");
    console.error("el panel de clima no cargó. Contenido del panel:\n", panel);
    throw e;
  }
  await esperar(2000);
  await pagina.screenshot({ path: path.join(SALIDA, "6_clima.png"), fullPage: false });
  await pagina.evaluate(() => document.querySelector("aside").scrollTo(0, 1400));
  await esperar(800);
  await pagina.screenshot({ path: path.join(SALIDA, "7_viento.png") });

  const clima = await pagina.evaluate(() =>
    document.body.innerText
      .split("\n")
      .filter((l) => /Grados-día|Período|Series horarias|Calmas|Dirección dominante|Elevación de la celda/i.test(l))
      .map((l) => l.trim()),
  );
  console.log("\nclima:", clima.join(" · "));

  console.log("\nerrores de consola:", errores.length ? errores : "ninguno");
  console.log("capturas en", SALIDA);
  await navegador.close();
  if (errores.length) process.exit(1);
}

principal().catch((e) => {
  console.error("falló:", e.message);
  process.exit(1);
});
