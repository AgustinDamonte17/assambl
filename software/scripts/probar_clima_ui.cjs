// Prueba acotada del panel de clima, para no repetir todo el recorrido.
//   node scripts/probar_clima_ui.cjs

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");

const BASE = process.env.BASE_UI || "http://localhost:5173";
const SALIDA = path.join(__dirname, "..", "backend", "cache", "salidas", "ui");
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

async function principal() {
  fs.mkdirSync(SALIDA, { recursive: true });
  const navegador = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"] });
  const pagina = await navegador.newPage();
  await pagina.setViewport({ width: 1600, height: 950 });

  pagina.on("console", (m) => console.log(`[consola ${m.type()}]`, m.text()));
  pagina.on("pageerror", (e) => console.log("[pageerror]", e.message));
  pagina.on("requestfailed", (r) => console.log("[request falló]", r.url(), r.failure()?.errorText));
  pagina.on("response", (r) => {
    if (r.url().includes("/api/")) console.log(`[api ${r.status()}]`, r.url());
  });

  await pagina.goto(BASE, { waitUntil: "networkidle2" });
  // Se siembra un proyecto con ubicación para entrar directo al paso de clima.
  await pagina.evaluate(() => {
    const p = JSON.parse(localStorage.getItem("assambl.proyecto"));
    p.terreno.ubicacion = { lat: -31.42, lon: -64.19, direccion: null, fuente: "prueba", fecha: null };
    p.terreno.sistema_local = {
      origen_lat: -31.42,
      origen_lon: -64.19,
      norte: "+Y",
      unidades: "m",
      proyeccion: "equirrectangular local",
      cota_origen_msnm: null,
    };
    localStorage.setItem("assambl.proyecto", JSON.stringify(p));
  });
  await pagina.reload({ waitUntil: "networkidle2" });

  await pagina.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find((x) => x.textContent.includes("Clima") && !x.disabled);
    b.click();
  });

  try {
    await pagina.waitForFunction(() => document.body.innerText.includes("Rosa de vientos"), { timeout: 120000 });
    console.log("\nel panel de clima cargó bien");
  } catch {
    console.log("\nno cargó. Panel:\n", await pagina.evaluate(() => document.querySelector("aside")?.innerText));
  }
  await esperar(1500);
  await pagina.screenshot({ path: path.join(SALIDA, "6_clima.png") });
  await pagina.evaluate(() => document.querySelector("aside").scrollTo(0, 1500));
  await esperar(600);
  await pagina.screenshot({ path: path.join(SALIDA, "7_viento.png") });
  await navegador.close();
}

principal().catch((e) => {
  console.error("falló:", e);
  process.exit(1);
});
