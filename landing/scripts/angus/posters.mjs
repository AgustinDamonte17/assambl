/**
 * Genera los posters estáticos del explode a partir del GLB real, renderizado por
 * el mismo visor de la página. Se usan mientras carga el 3D, ante errores de
 * WebGL/asset y como composición fija con prefers-reduced-motion.
 *
 * Uso (desde landing/, con la página servida):
 *   npm run build && npm start            # en otra terminal
 *   npm run posters                       # o: node scripts/angus/posters.mjs [url]
 *
 * Chromium: usa CHROMIUM_PATH si está definido; si no, el Chrome instalado.
 * Salida: public/models/angus-ranch-poster-{light,dark}-{assembled,exploded}.png
 */
import { chromium } from "playwright-core";
import { fileURLToPath } from "node:url";
import path from "node:path";

const url = process.argv[2] ?? "http://localhost:3000";
const out = path.resolve(
  fileURLToPath(import.meta.url),
  "../../../public/models",
);
const viewport = { width: 1600, height: 1000 };

const browser = await chromium.launch({
  ...(process.env.CHROMIUM_PATH
    ? { executablePath: process.env.CHROMIUM_PATH }
    : { channel: "chrome" }),
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});

for (const colorScheme of ["light", "dark"]) {
  const page = await browser.newPage({ viewport, colorScheme });
  await page.goto(url, { waitUntil: "networkidle" });
  await page.addStyleTag({
    content:
      "[data-explode-hud], nextjs-portal { visibility: hidden !important; }",
  });
  for (const [state, progress] of [
    ["assembled", 0],
    // Estructura elevada, sin techo ni envolvente (STEPS "06_Estructura"): al
    // final del recorrido solo queda el terreno.
    ["exploded", 0.6],
  ]) {
    await page.evaluate((p) => {
      const s = document.querySelector(".explode-track");
      const top = s.getBoundingClientRect().top + window.scrollY;
      window.scrollTo(0, top + p * (s.offsetHeight - window.innerHeight));
    }, progress);
    await page.waitForSelector('.explode-track[data-status="ready"]', {
      timeout: 60_000,
    });
    // El suavizado converge en ~1 s con GPU; con Chromium por software, más lento.
    await page.waitForTimeout(8000);
    const file = path.join(
      out,
      `angus-ranch-poster-${colorScheme}-${state}.png`,
    );
    await page.screenshot({ path: file });
    console.log(file);
  }
  await page.close();
}

await browser.close();
