// Levanta la API con uvicorn usando backend/.venv si existe; con --test corre pytest.
const { spawnSync } = require("node:child_process");
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

const r = spawnSync(python, args, { stdio: "inherit", cwd: backend });
process.exit(r.status ?? 1);
