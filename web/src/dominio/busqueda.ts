import { CLAVES_FACETA, type ClaveFaceta, type Filtros } from "./banco";

export type BusquedaUrl = { q?: string; p?: string; lang?: string } & Partial<Record<ClaveFaceta, string>>;

export interface EstadoBanco {
  readonly consulta: string;
  readonly seleccion?: string;
  readonly idioma?: string;
  readonly filtros: Filtros;
}

const SEPARADOR = "|";

const cadena = (valor: unknown): string | undefined =>
  typeof valor === "string" && valor.length > 0
    ? valor
    : typeof valor === "number"
      ? String(valor)
      : undefined;

/** Normaliza los parámetros crudos de la URL del banco; lo que no se entiende se descarta. */
export function validarBusqueda(crudo: Record<string, unknown>): BusquedaUrl {
  const salida: BusquedaUrl = { q: cadena(crudo.q), p: cadena(crudo.p), lang: cadena(crudo.lang) };
  for (const clave of CLAVES_FACETA) salida[clave] = cadena(crudo[clave]);
  return quitarVacios(salida);
}

export function leerEstado(b: BusquedaUrl): EstadoBanco {
  const filtros: Partial<Record<ClaveFaceta, readonly string[]>> = {};
  for (const clave of CLAVES_FACETA) {
    const valores = b[clave]?.split(SEPARADOR).filter(Boolean);
    if (valores?.length) filtros[clave] = valores;
  }
  return { consulta: b.q ?? "", seleccion: b.p, idioma: b.lang, filtros };
}

export function escribirEstado(e: EstadoBanco): BusquedaUrl {
  const salida: BusquedaUrl = { q: e.consulta || undefined, p: e.seleccion, lang: e.idioma };
  for (const clave of CLAVES_FACETA) {
    const valores = e.filtros[clave];
    salida[clave] = valores?.length ? valores.join(SEPARADOR) : undefined;
  }
  return quitarVacios(salida);
}

function quitarVacios<T extends object>(objeto: T): T {
  return Object.fromEntries(Object.entries(objeto).filter(([, v]) => v !== undefined)) as T;
}
