// Levanta la API con uvicorn usando backend/.venv si existe; con --test corre pytest.
const { spawn, spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");

const backend = path.join(__dirname, "..", "backend");
const isWin = process.platform === "win32";
const venvPython = path.join(backend, ".venv", isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python");
const python = existsSync(venvPython) ? venvPython : process.env.PYTHON || (isWin ? "python" : "python3");

const test = process.argv.includes("--test");
const recarga = process.env.API_RELOAD !== "0"; // API_RELOAD=0 desactiva la recarga automática
const args = test
  ? ["-m", "pytest", "-q"]
  : ["-m", "uvicorn", "api.main:app", ...(recarga ? ["--reload"] : []), "--port", process.env.API_PORT || "8765"];

if (test || !isWin) {
  const r = spawnSync(python, args, { stdio: "inherit", cwd: backend });
  process.exit(r.status ?? 1);
}

// En Windows, uvicorn reinicia el servidor mandándole Ctrl+C, y ese Ctrl+C le llega a todo lo que
// comparte la consola: la web y este mismo script. Por eso la API corre en una consola propia
// (oculta), y al terminar se la cierra junto con sus procesos hijos.
const api = spawn(python, args, { stdio: "inherit", cwd: backend, detached: true, windowsHide: true });
let cerrando = false;
const cerrar = () => {
  if (cerrando || api.exitCode !== null) return;
  cerrando = true;
  spawnSync("taskkill", ["/pid", String(api.pid), "/T", "/F"], { stdio: "ignore" });
};
for (const senal of ["SIGINT", "SIGTERM", "SIGBREAK", "SIGHUP"]) {
  process.on(senal, () => {
    cerrar();
    process.exit(0);
  });
}
process.on("exit", cerrar);
api.on("exit", (codigo) => process.exit(codigo ?? 1));
