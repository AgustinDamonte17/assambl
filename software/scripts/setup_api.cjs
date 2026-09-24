// Crea backend/.venv e instala requirements.txt. Idempotente.
const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");

const backend = path.join(__dirname, "..", "backend");
const venv = path.join(backend, ".venv");
const isWin = process.platform === "win32";
const venvPython = path.join(venv, isWin ? "Scripts" : "bin", isWin ? "python.exe" : "python");

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd: backend, shell: false });
  if (r.status !== 0) {
    console.error(`Falló: ${cmd} ${args.join(" ")}`);
    process.exit(r.status ?? 1);
  }
}

if (!existsSync(venvPython)) {
  const base = process.env.PYTHON || (isWin ? "python" : "python3");
  console.log(`Creando entorno virtual en ${venv} con ${base}`);
  run(base, ["-m", "venv", venv]);
}
run(venvPython, ["-m", "pip", "install", "--upgrade", "pip", "--quiet"]);
run(venvPython, ["-m", "pip", "install", "-r", "requirements.txt", "--quiet"]);
console.log("Backend listo.");
