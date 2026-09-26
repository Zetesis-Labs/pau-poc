import type { Convocatoria, Textos } from "./tipos";

export const NOMBRE_IDIOMA: Readonly<Record<string, string>> = {
  es: "castellano",
  va: "valenciano",
  ca: "catalán",
  eu: "euskera",
  en: "inglés",
  fr: "francés",
  de: "alemán",
  it: "italiano",
  pt: "portugués",
  la: "latín",
  grc: "griego",
};

export const NOMBRE_CONVOCATORIA: Readonly<Record<Convocatoria, string>> = {
  ordinaria: "Ordinaria",
  extraordinaria: "Extraordinaria",
  modelo: "Modelo",
  reserva: "Reserva",
  otra: "Otra",
};

export const nombreIdioma = (codigo: string): string => NOMBRE_IDIOMA[codigo] ?? codigo;

export const nombreConvocatoria = (valor: string): string =>
  NOMBRE_CONVOCATORIA[valor as Convocatoria] ?? valor;

export function textoEn(textos: Textos | undefined, idioma: string): string {
  if (!textos) return "";
  return textos[idioma] ?? textos.es ?? Object.values(textos)[0] ?? "";
}

export function idiomaPreferido(disponibles: readonly string[], elegido: string | undefined): string {
  if (elegido && disponibles.includes(elegido)) return elegido;
  if (disponibles.includes("es")) return "es";
  return disponibles[0] ?? "es";
}

export const normalizar = (texto: string): string =>
  texto
    .normalize("NFD")
    .replace(/\p{Mn}/gu, "")
    .toLowerCase();

export const terminos = (consulta: string): string[] => normalizar(consulta).split(/\s+/).filter(Boolean);
