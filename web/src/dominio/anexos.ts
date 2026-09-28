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
  if (a.tipo === "criterios") return "Criterios de corrección oficiales";
  return a.origen === "oficial" ? "Solución oficial" : `Solución de ${nombreFuente(a.fuente)}`;
}

export type Destino =
  | { readonly accion: "pagina"; readonly pagina: number; readonly nota: string }
  | { readonly accion: "enlace"; readonly href: string; readonly nota: string }
  | { readonly accion: "ninguna"; readonly nota: string };

/** Adónde lleva un anexo: a una página del PDF que ya se ve, a su origen o a ninguna parte si el enlace está roto. */
export function destinoAnexo(a: Anexo, examen: { readonly pdf?: string; readonly url: string }): Destino {
  if (a.incrustado) {
    const { pagina } = a.incrustado;
    return examen.pdf
      ? { accion: "pagina", pagina, nota: `en este PDF, p. ${pagina}` }
      : { accion: "enlace", href: examen.url, nota: `dentro del PDF del examen, p. ${pagina}` };
  }
  if (a.acceso === "roto" || !a.url) return { accion: "ninguna", nota: "enlace roto" };
  return { accion: "enlace", href: a.url, nota: a.acceso === "privado" ? "requiere acceso" : "" };
}

const accesible = (a: Anexo) => a.acceso === "publico";

/** La mejor corrección que se puede consultar, para filtrar preguntas por ella. */
export function correccionDe(anexos: readonly Anexo[]): string {
  const disponibles = anexos.filter(accesible);
  if (disponibles.some((a) => a.origen === "oficial" && a.tipo === "criterios")) return "Criterios oficiales";
  if (disponibles.some((a) => a.origen === "oficial")) return "Solución oficial";
  if (disponibles.length) return "Solo de academia";
  return "Sin corrección accesible";
}
