const katex = require("katex");
require("katex/contrib/mhchem");

const entrada = JSON.parse(require("fs").readFileSync(0, "utf8"));
const errores = entrada.map((formula) => {
  try {
    katex.renderToString(formula.tex, { displayMode: formula.bloque, throwOnError: true, strict: "ignore" });
    return null;
  } catch (error) {
    return error.message.slice(0, 200);
  }
});
process.stdout.write(JSON.stringify(errores));
