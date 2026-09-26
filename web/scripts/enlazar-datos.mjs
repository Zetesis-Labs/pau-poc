import { cpSync, existsSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const origen = process.env.DATOS ? resolve(process.env.DATOS) : resolve(aqui, "../../datos");
const destino = resolve(aqui, "../public/datos");

if (!existsSync(resolve(origen, "preguntas.json"))) {
  console.error(`Falta ${origen}/preguntas.json: ejecuta antes \`pau publicar\` en pipeline/.`);
  process.exit(1);
}
rmSync(destino, { recursive: true, force: true });
cpSync(origen, destino, { recursive: true });
console.log(`datos copiados a ${destino}`);
