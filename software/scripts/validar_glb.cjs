// Valida un .glb con el validador oficial de Khronos.
//   node scripts/validar_glb.cjs backend/cache/salidas/terreno_ejemplo.glb
// Requiere: npm install --no-save gltf-validator

const fs = require("fs");
const path = require("path");
const validador = require("gltf-validator");

const archivo = process.argv[2];
if (!archivo) {
  console.error("Uso: node scripts/validar_glb.cjs <archivo.glb>");
  process.exit(2);
}

const datos = new Uint8Array(fs.readFileSync(archivo));
validador
  .validateBytes(datos, { uri: path.basename(archivo) })
  .then((informe) => {
    const { numErrors, numWarnings, numInfos, numHints } = informe.issues;
    console.log(`validador ${informe.validatorVersion} — ${path.basename(archivo)}`);
    console.log(`errores ${numErrors}  advertencias ${numWarnings}  info ${numInfos}  sugerencias ${numHints}`);
    for (const m of informe.issues.messages) {
      console.log(`  [${m.severity}] ${m.code} ${m.pointer || ""} — ${m.message}`);
    }
    console.log("resumen:", JSON.stringify(informe.info, null, 2));
    process.exit(numErrors > 0 ? 1 : 0);
  })
  .catch((e) => {
    console.error("falló la validación:", e);
    process.exit(3);
  });
