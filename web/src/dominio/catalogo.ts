import { normalizar } from "./textos";
import type { Documento, TipoDocumento } from "./tipos";

export const TIPOS: readonly TipoDocumento[] = [
  "examen",
  "solucion",
  "criterios",
  "modelo",
  "video",
  "audio",
];

export const NOMBRE_TIPO: Readonly<Record<TipoDocumento, string>> = {
  examen: "Examen",
  solucion: "Solución",
  criterios: "Criterios",
  modelo: "Modelo",
  video: "Vídeo",
  audio: "Audio",
};

export type Estado = "procesado" | "enlace" | "error";

export const NOMBRE_ESTADO: Readonly<Record<Estado, string>> = {
  procesado: "Con preguntas extraídas",
  enlace: "Solo enlace de origen",
  error: "Descarga fallida",
};

export interface FiltrosCatalogo {
  readonly texto?: string;
  readonly region?: string;
  readonly asignatura?: string;
  readonly anio?: string;
  readonly convocatoria?: string;
  readonly fuente?: string;
  readonly estado?: Estado;
  readonly ocultos?: readonly TipoDocumento[];
  readonly pagina?: number;
}

export const estadoDe = (d: Documento): Estado => (d.error ? "error" : d.procesado ? "procesado" : "enlace");

type CampoSelector = "region" | "asignatura" | "anio" | "convocatoria" | "fuente";

export function cumple(d: Documento, f: FiltrosCatalogo, ignorar: readonly CampoSelector[] = []): boolean {
  const distinto = (campo: CampoSelector, valor: string) =>
    !ignorar.includes(campo) && f[campo] !== undefined && f[campo] !== valor;
  if (distinto("region", d.region) || distinto("asignatura", d.asignatura)) return false;
  if (distinto("anio", String(d.anio ?? "")) || distinto("convocatoria", d.convocatoria)) return false;
  if (distinto("fuente", d.fuente)) return false;
  if (f.estado && estadoDe(d) !== f.estado) return false;
  if (f.ocultos?.includes(d.tipo)) return false;
  if (f.texto) {
    const buscado = normalizar(f.texto);
    const texto = normalizar(
      `${d.asignatura} ${d.titulo} ${d.variante} ${d.fuente} ${d.region} ${d.anio ?? ""}`,
    );
    if (!texto.includes(buscado)) return false;
  }
  return true;
}

export const unicos = <T extends string | number>(valores: readonly T[]): T[] =>
  [...new Set(valores)].sort((a, b) => String(a).localeCompare(String(b), "es"));

export interface Kpis {
  readonly documentos: number;
  readonly procesados: number;
  readonly bytesDescargados: number;
  readonly soloEnlace: number;
  readonly asignaturas: number;
  readonly anios: readonly [number, number] | null;
  readonly fallidos: number;
}

export function kpis(docs: readonly Documento[]): Kpis {
  const anios = docs.map((d) => d.anio).filter((a): a is number => a !== null);
  return {
    documentos: docs.length,
    procesados: docs.filter((d) => d.procesado).length,
    bytesDescargados: docs.reduce((s, d) => s + (d.bytes ?? 0), 0),
    soloEnlace: docs.filter((d) => !d.descargable).length,
    asignaturas: new Set(docs.map((d) => d.asignatura)).size,
    anios: anios.length ? [Math.min(...anios), Math.max(...anios)] : null,
    fallidos: docs.filter((d) => d.error).length,
  };
}

export interface Matriz {
  readonly asignaturas: readonly string[];
  readonly anios: readonly number[];
  readonly cuenta: (asignatura: string, anio: number) => number;
  readonly maximo: number;
}

/** Cobertura asignatura × año con todos los filtros salvo los de asignatura y año, que son los ejes. */
export function matriz(docs: readonly Documento[], f: FiltrosCatalogo): Matriz {
  const universo = docs.filter((d) => cumple(d, f, ["asignatura", "anio"]));
  const cuentas = new Map<string, number>();
  for (const d of universo) {
    const clave = `${d.asignatura}|${d.anio}`;
    cuentas.set(clave, (cuentas.get(clave) ?? 0) + 1);
  }
  return {
    asignaturas: unicos(universo.map((d) => d.asignatura)),
    anios: unicos(universo.map((d) => d.anio).filter((a): a is number => a !== null)),
    cuenta: (asignatura, anio) => cuentas.get(`${asignatura}|${anio}`) ?? 0,
    maximo: Math.max(1, ...cuentas.values()),
  };
}

export const intensidad = (n: number, maximo: number): number =>
  n ? Math.round(18 + 82 * Math.sqrt(n / maximo)) : 0;

export function ordenar(docs: readonly Documento[]): Documento[] {
  return [...docs].sort(
    (a, b) =>
      (b.anio ?? 0) - (a.anio ?? 0) ||
      a.region.localeCompare(b.region) ||
      a.asignatura.localeCompare(b.asignatura, "es") ||
      a.convocatoria.localeCompare(b.convocatoria) ||
      TIPOS.indexOf(a.tipo) - TIPOS.indexOf(b.tipo),
  );
}

export interface Pagina<T> {
  readonly elementos: readonly T[];
  readonly pagina: number;
  readonly paginas: number;
}

export function paginar<T>(elementos: readonly T[], pagina: number, porPagina: number): Pagina<T> {
  const paginas = Math.max(1, Math.ceil(elementos.length / porPagina));
  const actual = Math.min(Math.max(0, pagina), paginas - 1);
  return {
    elementos: elementos.slice(actual * porPagina, (actual + 1) * porPagina),
    pagina: actual,
    paginas,
  };
}

export function formatoBytes(bytes: number): string {
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(2)} GB` : `${(bytes / 1e6).toFixed(0)} MB`;
}

const ESTADOS: readonly Estado[] = ["procesado", "enlace", "error"];
const esTipo = (v: string): v is TipoDocumento => (TIPOS as readonly string[]).includes(v);
const texto = (v: unknown) =>
  typeof v === "string" && v ? v : typeof v === "number" ? String(v) : undefined;

export function leerFiltrosCatalogo(crudo: Record<string, unknown>): FiltrosCatalogo {
  const estado = texto(crudo.estado);
  const ocultos = texto(crudo.ocultos)?.split("|").filter(esTipo);
  const pagina = Number(crudo.pagina);
  return {
    texto: texto(crudo.texto),
    region: texto(crudo.region),
    asignatura: texto(crudo.asignatura),
    anio: texto(crudo.anio),
    convocatoria: texto(crudo.convocatoria),
    fuente: texto(crudo.fuente),
    estado: ESTADOS.find((e) => e === estado),
    ocultos: ocultos?.length ? ocultos : undefined,
    pagina: Number.isInteger(pagina) && pagina > 0 ? pagina : undefined,
  };
}

export function escribirFiltrosCatalogo(f: FiltrosCatalogo): Record<string, string | number | undefined> {
  return {
    ...f,
    texto: f.texto || undefined,
    ocultos: f.ocultos?.length ? f.ocultos.join("|") : undefined,
    pagina: f.pagina || undefined,
  };
}
