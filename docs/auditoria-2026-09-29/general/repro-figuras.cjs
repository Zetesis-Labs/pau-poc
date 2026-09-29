// Reproduce el fallback usando el cuerpo real de la función y los datos publicados.
// No compila ni modifica la aplicación.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../../..');
const source = fs.readFileSync(path.join(root, 'web/src/dominio/banco.ts'), 'utf8');
const body = source.match(/export function figurasDe[^\n]+\{\n([\s\S]*?)\n\}/)[1];
const figurasDe = new Function('figuras', 'idioma', body);
const banco = JSON.parse(fs.readFileSync(path.join(root, 'datos/preguntas.json'), 'utf8'));
const values = [];
function walk(x) {
  if (Array.isArray(x)) return x.forEach(walk);
  if (!x || typeof x !== 'object') return;
  if (Array.isArray(x.figuras) && x.figuras.some(f => JSON.stringify(f).includes('3068d1110070_E2'))) {
    values.push({disponibles: x.figuras, mostradas_en_es: figurasDe(x.figuras, 'es')});
  }
  Object.values(x).forEach(walk);
}
walk(banco);
if (!values.length || values.some(v => v.disponibles.length !== 3 || v.mostradas_en_es.length !== 1)) {
  throw new Error('Los datos ya no reproducen el caso auditado');
}
fs.writeFileSync(path.join(__dirname, 'repro-figuras.json'), JSON.stringify(values, null, 2) + '\n');
console.log(`${values.length} referencias: tres páginas disponibles, una mostrada en es`);
