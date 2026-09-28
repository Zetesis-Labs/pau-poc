import type { Documento, Pregunta } from "./tipos";

export function pregunta(cambios: Partial<Pregunta> & { id: string }): Pregunta {
  return {
    examen: {
      id: "ex1",
      region: "Madrid",
      asignatura: "Matemáticas II",
      anio: 2024,
      convocatoria: "ordinaria",
      tipo: "examen",
      fuente: "uc3m",
      url: "https://origen/ex1.pdf",
      pdf: "pdfs/ex1.pdf",
      anexos: [],
    },
    reglaExamen: "",
    contexto: [],
    etiqueta: { es: "1" },
    enunciado: { es: "Calcula la integral $\\int_0^1 x\\,dx$." },
    puntos: 2.5,
    apartados: [],
    idiomas: ["es"],
    estimulos: [],
    paginas: { es: 1 },
    anclas: { es: { pagina: 1, y0: 0.2, y1: 0.4 } },
    ...cambios,
  };
}

export function documento(cambios: Partial<Documento> & { id: string }): Documento {
  return {
    region: "Madrid",
    fuente: "uc3m",
    pagina: "https://origen",
    asignatura: "Matemáticas II",
    anio: 2024,
    convocatoria: "ordinaria",
    tipo: "examen",
    titulo: "Examen",
    variante: "",
    formato: "pdf",
    url: "https://origen/doc.pdf",
    descargable: true,
    procesado: false,
    ...cambios,
  };
}
