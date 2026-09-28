export type Textos = Readonly<Record<string, string>>;

export type Convocatoria = "ordinaria" | "extraordinaria" | "modelo" | "reserva" | "otra";
export type TipoDocumento = "examen" | "modelo" | "criterios" | "solucion" | "video" | "audio";
export type Formato = "pdf" | "drive" | "gdoc" | "youtube" | "audio" | "web" | "carpeta";

export interface Anexo {
  readonly tipo: "criterios" | "solucion";
  readonly contenido: readonly ("criterios" | "solucion")[];
  readonly origen: "oficial" | "academia";
  readonly fuente: string;
  readonly acceso: "publico" | "privado" | "roto";
  readonly coincidencia: "exacta" | "por_clave";
  readonly id?: string;
  readonly url?: string;
  readonly titulo?: string;
  readonly incrustado?: { readonly pagina: number };
}

export interface Documento {
  readonly id: string;
  readonly region: string;
  readonly fuente: string;
  readonly pagina: string;
  readonly asignatura: string;
  readonly anio: number | null;
  readonly convocatoria: Convocatoria;
  readonly tipo: TipoDocumento;
  readonly titulo: string;
  readonly variante: string;
  readonly formato: Formato;
  readonly url: string;
  readonly descargable: boolean;
  readonly bytes?: number;
  readonly error?: string;
  readonly procesado: boolean;
  readonly pdf?: string;
  readonly anexos?: readonly Anexo[];
}

export interface Catalogo {
  readonly generado: string;
  readonly fuentes: Readonly<Record<string, { readonly region: string; readonly url: string }>>;
  readonly documentos: readonly Documento[];
}

export interface Figura {
  readonly src: string;
  readonly idioma: string;
}

export interface Estimulo {
  readonly id: string;
  readonly tipo: string;
  readonly descripcion: string;
  readonly contenido: Textos;
  readonly figuras: readonly Figura[];
}

export interface Tramo {
  readonly descripcion: Textos;
  readonly puntos: number;
}

export interface Rubrica {
  readonly puntos: number | null;
  readonly criterios: Textos;
  readonly desglose: readonly Tramo[];
  readonly paginas: Readonly<Record<string, number>>;
}

export interface Solucion {
  readonly texto: Textos;
  readonly origen: "oficial" | "academia";
  readonly fuente: string;
  readonly incrustado: boolean;
  readonly url?: string;
  readonly paginas: Readonly<Record<string, number>>;
}

export type FuenteRubrica =
  | { readonly tipo: "criterios" | "solucion"; readonly incrustado: true }
  | { readonly tipo: "criterios" | "solucion"; readonly incrustado: false; readonly url: string };

export interface Apartado {
  readonly etiqueta: Textos;
  readonly enunciado: Textos;
  readonly puntos: number | null;
  readonly estimulos: readonly string[];
  readonly regla: string;
  readonly rubrica: Rubrica | null;
  readonly solucion: Solucion | null;
  readonly apartados: readonly Apartado[];
}

export interface Contexto {
  readonly etiqueta: Textos;
  readonly tipo: "bloque" | "opcion" | "pregunta";
  readonly enunciado: Textos;
  readonly regla: string;
  readonly sintetico: boolean;
}

export interface Ancla {
  readonly pagina: number;
  readonly y0: number | null;
  readonly y1: number | null;
}

export interface ExamenDePregunta {
  readonly id: string;
  readonly region: string;
  readonly asignatura: string;
  readonly anio: number;
  readonly convocatoria: Convocatoria;
  readonly tipo: TipoDocumento;
  readonly fuente: string;
  readonly url: string;
  readonly pdf: string;
  readonly anexos: readonly Anexo[];
}

export interface Pregunta {
  readonly id: string;
  readonly examen: ExamenDePregunta;
  readonly reglaExamen: string;
  readonly contexto: readonly Contexto[];
  readonly etiqueta: Textos;
  readonly enunciado: Textos;
  readonly puntos: number | null;
  readonly rubrica: Rubrica | null;
  readonly solucion: Solucion | null;
  readonly criteriosGenerales: Textos;
  readonly fuenteRubrica: FuenteRubrica | null;
  readonly apartados: readonly Apartado[];
  readonly idiomas: readonly string[];
  readonly estimulos: readonly Estimulo[];
  readonly paginas: Readonly<Record<string, number>>;
  readonly anclas: Readonly<Record<string, Ancla>>;
}

export interface Banco {
  readonly ejecucion: string;
  readonly preguntas: readonly Pregunta[];
}
