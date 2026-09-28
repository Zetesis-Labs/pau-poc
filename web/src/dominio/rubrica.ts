import { correccionDe, nombreFuente } from "./anexos";
import { idiomaPreferido } from "./textos";
import type { Apartado, FuenteRubrica, Pregunta, Rubrica, Solucion } from "./tipos";

const nodos = (apartados: readonly Apartado[]): Apartado[] =>
  apartados.flatMap((a) => [a, ...nodos(a.apartados)]);

const todos = (p: Pregunta) => [p, ...nodos(p.apartados)];

export const tieneRubrica = (p: Pregunta): boolean => todos(p).some((n) => n.rubrica !== null);

export const origenesDeSolucion = (p: Pregunta): Set<Solucion["origen"]> =>
  new Set(todos(p).flatMap((n) => (n.solucion ? [n.solucion.origen] : [])));

/** Valores de la faceta Corrección: lo que se puede consultar de verdad en la pregunta. */
export function valoresCorreccion(p: Pregunta): string[] {
  const origenes = origenesDeSolucion(p);
  const valores = [
    correccionDe(p.examen.anexos).includes("Con criterios") && "Con criterios",
    tieneRubrica(p) && "Con rúbrica",
    origenes.has("oficial") && "Con solución oficial",
    origenes.has("academia") && "Con solución de academia",
  ].filter((v): v is string => Boolean(v));
  return valores.length ? valores : ["Sin corrección"];
}

const TOLERANCIA = 0.01;
const numero = (n: number) => n.toLocaleString("es", { maximumFractionDigits: 2 });

export function discrepanciaDePuntos(enunciado: number | null, rubrica: Rubrica): string | null {
  if (enunciado === null || rubrica.puntos === null || Math.abs(enunciado - rubrica.puntos) <= TOLERANCIA)
    return null;
  return `los criterios dan ${numero(rubrica.puntos)} puntos; el enunciado, ${numero(enunciado)}`;
}

export type DestinoOriginal =
  | { readonly accion: "pagina"; readonly pdf?: string; readonly pagina: number }
  | { readonly accion: "enlace"; readonly href: string };

interface Documento {
  readonly incrustado: boolean;
  readonly url?: string;
  readonly pdf?: string;
}

/** Dónde ver algo en su documento original: una página del PDF del examen, la de su PDF publicado o la del enlazado. */
function destinoEnOriginal(
  paginas: Readonly<Record<string, number>>,
  { incrustado, url, pdf }: Documento,
  idioma: string,
): DestinoOriginal | null {
  const pagina = paginas[idiomaPreferido(Object.keys(paginas), idioma)];
  if (pagina === undefined) return null;
  if (incrustado) return { accion: "pagina", pagina };
  if (pdf) return { accion: "pagina", pdf, pagina };
  return url ? { accion: "enlace", href: `${url}#page=${pagina}` } : null;
}

export const destinoRubrica = (rubrica: Rubrica, fuente: FuenteRubrica | null, idioma: string) =>
  fuente ? destinoEnOriginal(rubrica.paginas, fuente, idioma) : null;

export const destinoSolucion = (solucion: Solucion, idioma: string) =>
  destinoEnOriginal(solucion.paginas, solucion, idioma);

export const etiquetaSolucion = (s: Solucion): string =>
  s.origen === "oficial" ? "solución oficial" : `solución de ${nombreFuente(s.fuente)} (academia)`;
