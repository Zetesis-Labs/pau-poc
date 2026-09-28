import type { Anexo } from "./tipos";

const NOMBRE_FUENTE: Readonly<Record<string, string>> = {
  llibreta: "La Llibreta",
  mundoestudiante: "mundoestudiante",
  "selectividad.academy": "selectividad.academy",
  uc3m: "uc3m",
  ehu: "EHU",
  umh: "UMH",
};

export const nombreFuente = (fuente: string): string => NOMBRE_FUENTE[fuente] ?? fuente;

export function etiquetaAnexo(a: Anexo): string {
  if (a.contenido.includes("criterios") && a.contenido.includes("solucion"))
    return "Criterios y solución oficiales";
  if (a.tipo === "criterios") return "Criterios de corrección oficiales";
  return a.origen === "oficial" ? "Solución oficial" : `Solución de ${nombreFuente(a.fuente)}`;
}

/** Rótulo breve para listas donde no cabe la etiqueta completa. */
export function textoCorto(a: Anexo): string {
  if (a.contenido.includes("criterios") && a.contenido.includes("solucion")) return "Criterios + solución";
  if (a.tipo === "criterios") return "Criterios";
  return a.origen === "oficial" ? "Solución" : "Solución academia";
}

/** `pdf` es el documento publicado que hay que abrir en el visor; sin él, la página es del PDF del examen. */
export type Destino =
  | { readonly accion: "pagina"; readonly pdf?: string; readonly pagina: number; readonly nota: string }
  | { readonly accion: "enlace"; readonly href: string; readonly nota: string }
  | { readonly accion: "ninguna"; readonly nota: string };

/** Adónde lleva un anexo: a una página del PDF del examen, a su propio PDF publicado, a su origen o a ninguna parte. */
export function destinoAnexo(a: Anexo, examen: { readonly pdf?: string; readonly url: string }): Destino {
  if (a.incrustado) {
    const { pagina } = a.incrustado;
    return examen.pdf
      ? { accion: "pagina", pagina, nota: `en este PDF, p. ${pagina}` }
      : { accion: "enlace", href: examen.url, nota: `dentro del PDF del examen, p. ${pagina}` };
  }
  if (a.pdf) return { accion: "pagina", pdf: a.pdf, pagina: 1, nota: "" };
  if (a.acceso === "roto" || !a.url) return { accion: "ninguna", nota: "enlace roto" };
  return { accion: "enlace", href: a.url, nota: a.acceso === "privado" ? "requiere acceso" : "" };
}

const accesible = (a: Anexo) => a.acceso === "publico";

/** Qué corrección se puede consultar, para filtrar preguntas por criterios y por solución por separado. */
export function correccionDe(anexos: readonly Anexo[]): string[] {
  const contenido = new Set(anexos.filter(accesible).flatMap((a) => a.contenido));
  const valores = [
    contenido.has("criterios") && "Con criterios",
    contenido.has("solucion") && "Con solución",
  ];
  const presentes = valores.filter((v): v is string => Boolean(v));
  return presentes.length ? presentes : ["Sin corrección"];
}
