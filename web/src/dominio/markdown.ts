import katex from "katex";
import "katex/contrib/mhchem";
import { Marked } from "marked";

const FORMULA = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;
const HUECO = /\uE000(\d+)\uE001/g;
const marked = new Marked({ gfm: true, breaks: false });

const escapar = (texto: string): string =>
  texto.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] ?? c);

function formula(tex: string, bloque: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode: bloque,
      throwOnError: false,
      output: "htmlAndMathml",
      trust: false,
    });
  } catch {
    return escapar(tex);
  }
}

/** Convierte Markdown/LaTeX en HTML sin sanear; el componente Markdown protege la inserción en el DOM. */
export function renderizar(md: string): string {
  const formulas: { tex: string; bloque: boolean }[] = [];
  const protegido = md.replace(FORMULA, (_, bloque: string | undefined, linea: string | undefined) => {
    formulas.push({ tex: bloque ?? linea ?? "", bloque: bloque !== undefined });
    return `\uE000${formulas.length - 1}\uE001`;
  });
  const html = marked.parse(protegido, { async: false });
  return html.replace(HUECO, (_, i: string) => {
    const f = formulas[Number(i)];
    return f ? formula(f.tex, f.bloque) : "";
  });
}
