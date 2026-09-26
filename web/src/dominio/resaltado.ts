import { normalizar, terminos } from "./textos";

const LONGITUD_MINIMA = 3;

/** Marca con <mark> la primera aparición de cada término en los nodos de texto del HTML, sin tocar etiquetas. */
export function resaltar(html: string, consulta: string): string {
  const buscados = terminos(consulta).filter((t) => t.length >= LONGITUD_MINIMA);
  if (!buscados.length) return html;
  return html.replace(/>([^<]+)</g, (_, texto: string) => {
    let salida = texto;
    for (const termino of buscados) {
      const i = normalizar(salida).indexOf(termino);
      if (i >= 0)
        salida = `${salida.slice(0, i)}<mark>${salida.slice(i, i + termino.length)}</mark>${salida.slice(i + termino.length)}`;
    }
    return `>${salida}<`;
  });
}
