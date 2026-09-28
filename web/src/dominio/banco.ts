import { correccionDe } from "./anexos";
import { nombreConvocatoria, nombreIdioma, normalizar, terminos, textoEn } from "./textos";
import type { Apartado, Pregunta } from "./tipos";

export const CLAVES_FACETA = [
  "region",
  "asignatura",
  "anio",
  "convocatoria",
  "idioma",
  "material",
  "correccion",
  "examen",
] as const;
export type ClaveFaceta = (typeof CLAVES_FACETA)[number];
export type Filtros = Readonly<Partial<Record<ClaveFaceta, readonly string[]>>>;

export interface DefinicionFaceta {
  readonly clave: ClaveFaceta;
  readonly titulo: string;
  readonly valores: (p: Pregunta) => readonly string[];
  readonly nombre?: (valor: string) => string;
  readonly orden?: (a: string, b: string) => number;
  readonly limite?: number;
}

interface DatosDeExamen {
  readonly asignatura: string;
  readonly region: string;
  readonly anio: number | null;
  readonly convocatoria: string;
}

export const nombreDeExamen = (e: DatosDeExamen): string =>
  `${e.asignatura} · ${e.region} · ${e.anio ?? "s. f."} ${nombreConvocatoria(e.convocatoria)}`;

export const nombreExamen = (p: Pregunta): string => nombreDeExamen(p.examen);

const textosDeApartados = (apartados: readonly Apartado[]): string[] =>
  apartados.flatMap((a) => [...Object.values(a.enunciado), ...textosDeApartados(a.apartados)]);

export function materiales(p: Pregunta): string[] {
  const todo = [...Object.values(p.enunciado), ...textosDeApartados(p.apartados)].join(" ");
  return [
    p.estimulos.some((e) => e.figuras.length > 0) && "Con figura",
    p.estimulos.some((e) => e.tipo === "texto") && "Con texto base",
    todo.includes("$") && "Con fórmulas",
    p.apartados.length > 0 && "Con apartados",
  ].filter((m): m is string => Boolean(m));
}

export const FACETAS: readonly DefinicionFaceta[] = [
  { clave: "region", titulo: "Región", valores: (p) => [p.examen.region] },
  { clave: "asignatura", titulo: "Asignatura", valores: (p) => [p.examen.asignatura] },
  {
    clave: "anio",
    titulo: "Año",
    valores: (p) => [String(p.examen.anio)],
    orden: (a, b) => b.localeCompare(a),
  },
  {
    clave: "convocatoria",
    titulo: "Convocatoria",
    valores: (p) => [p.examen.convocatoria],
    nombre: nombreConvocatoria,
  },
  { clave: "idioma", titulo: "Idioma", valores: (p) => p.idiomas, nombre: nombreIdioma },
  { clave: "material", titulo: "Material", valores: materiales },
  { clave: "correccion", titulo: "Corrección", valores: (p) => correccionDe(p.examen.anexos) },
  { clave: "examen", titulo: "Examen", valores: (p) => [nombreExamen(p)], limite: 8 },
];

export interface PreguntaIndexada {
  readonly pregunta: Pregunta;
  readonly texto: string;
  readonly facetas: Readonly<Record<ClaveFaceta, readonly string[]>>;
}

export function textoIndexable(p: Pregunta): string {
  const partes = [
    nombreExamen(p),
    ...Object.values(p.etiqueta),
    ...Object.values(p.enunciado),
    ...textosDeApartados(p.apartados),
    ...p.estimulos.flatMap((e) => [e.descripcion, ...Object.values(e.contenido)]),
    ...p.contexto.flatMap((c) => [...Object.values(c.etiqueta), ...Object.values(c.enunciado)]),
  ];
  return normalizar(partes.join(" ").replace(/\\[a-zA-Z]+|[{}$^_]/g, " "));
}

export const indexar = (preguntas: readonly Pregunta[]): PreguntaIndexada[] =>
  preguntas.map((pregunta) => ({
    pregunta,
    texto: textoIndexable(pregunta),
    facetas: Object.fromEntries(FACETAS.map((f) => [f.clave, f.valores(pregunta)])) as Record<
      ClaveFaceta,
      readonly string[]
    >,
  }));

export function cumple(
  p: PreguntaIndexada,
  filtros: Filtros,
  consulta: string,
  ignorar?: ClaveFaceta,
): boolean {
  for (const clave of CLAVES_FACETA) {
    const elegidos = filtros[clave];
    if (clave === ignorar || !elegidos?.length) continue;
    if (!p.facetas[clave].some((v) => elegidos.includes(v))) return false;
  }
  return terminos(consulta).every((t) => p.texto.includes(t));
}

export const filtrar = (preguntas: readonly PreguntaIndexada[], filtros: Filtros, consulta: string) =>
  preguntas.filter((p) => cumple(p, filtros, consulta));

export interface ValorFaceta {
  readonly valor: string;
  readonly nombre: string;
  readonly cuenta: number;
  readonly elegido: boolean;
}

export interface FacetaCalculada {
  readonly clave: ClaveFaceta;
  readonly titulo: string;
  readonly valores: readonly ValorFaceta[];
  readonly ocultos: number;
  readonly activa: boolean;
}

const LIMITE_POR_DEFECTO = 12;

/** Cuentas de cada faceta sobre las preguntas que cumplen todos los demás filtros (facetado disyuntivo). */
export function calcularFaceta(
  definicion: DefinicionFaceta,
  preguntas: readonly PreguntaIndexada[],
  filtros: Filtros,
  consulta: string,
  expandida: boolean,
): FacetaCalculada {
  const cuentas = new Map<string, number>();
  for (const p of preguntas)
    for (const v of p.facetas[definicion.clave]) if (!cuentas.has(v)) cuentas.set(v, 0);
  for (const p of preguntas) {
    if (!cumple(p, filtros, consulta, definicion.clave)) continue;
    for (const v of p.facetas[definicion.clave]) cuentas.set(v, (cuentas.get(v) ?? 0) + 1);
  }
  const elegidos = filtros[definicion.clave] ?? [];
  const porCuenta = (a: string, b: string) =>
    (cuentas.get(b) ?? 0) - (cuentas.get(a) ?? 0) || a.localeCompare(b, "es");
  const ordenados = [...cuentas.keys()].sort(definicion.orden ?? porCuenta);
  const limite = definicion.limite ?? LIMITE_POR_DEFECTO;
  const visibles = expandida ? ordenados : ordenados.filter((v, i) => i < limite || elegidos.includes(v));
  return {
    clave: definicion.clave,
    titulo: definicion.titulo,
    activa: elegidos.length > 0,
    ocultos: ordenados.length - visibles.length,
    valores: visibles.map((valor) => ({
      valor,
      nombre: definicion.nombre ? definicion.nombre(valor) : valor,
      cuenta: cuentas.get(valor) ?? 0,
      elegido: elegidos.includes(valor),
    })),
  };
}

export function alternar(filtros: Filtros, clave: ClaveFaceta, valor: string): Filtros {
  const actuales = filtros[clave] ?? [];
  const nuevos = actuales.includes(valor) ? actuales.filter((v) => v !== valor) : [...actuales, valor];
  return { ...filtros, [clave]: nuevos.length ? nuevos : undefined };
}

export const limpiar = (filtros: Filtros, clave: ClaveFaceta): Filtros => ({
  ...filtros,
  [clave]: undefined,
});

export function filtrosActivos(filtros: Filtros): { clave: ClaveFaceta; valor: string; nombre: string }[] {
  return FACETAS.flatMap((f) =>
    (filtros[f.clave] ?? []).map((valor) => ({
      clave: f.clave,
      valor,
      nombre: f.nombre ? f.nombre(valor) : valor,
    })),
  );
}

export function vecina(ids: readonly string[], actual: string | undefined, paso: 1 | -1): string | undefined {
  if (!ids.length) return undefined;
  const i = actual ? ids.indexOf(actual) : -1;
  if (i < 0) return ids[0];
  return ids[Math.min(ids.length - 1, Math.max(0, i + paso))];
}

export const numeroDeFiguras = (p: Pregunta): number => p.estimulos.reduce((n, e) => n + e.figuras.length, 0);

export function figurasDe<T extends { idioma: string }>(figuras: readonly T[], idioma: string): readonly T[] {
  const propias = figuras.filter((f) => f.idioma === idioma);
  return propias.length ? propias : figuras.slice(0, 1);
}

export interface Miga {
  readonly clave: string;
  readonly texto: string;
  readonly regla: string;
}

/** Ruta de la pregunta dentro del examen: el examen y los bloques u opciones que la contienen. */
export function migas(p: Pregunta, idioma: string): Miga[] {
  const textos = [nombreExamen(p), ...p.contexto.map((c) => textoEn(c.etiqueta, idioma))];
  return textos.map((texto, i) => ({
    clave: textos.slice(0, i + 1).join(" › "),
    texto,
    regla: i > 0 ? (p.contexto[i - 1]?.regla ?? "") : "",
  }));
}

export const claveApartado = (a: Apartado): string =>
  `${Object.values(a.etiqueta)[0] ?? ""}|${(Object.values(a.enunciado)[0] ?? "").slice(0, 60)}`;
