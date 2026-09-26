import { describe, expect, it } from "vitest";
import {
  cumple,
  escribirFiltrosCatalogo,
  estadoDe,
  intensidad,
  kpis,
  leerFiltrosCatalogo,
  matriz,
  ordenar,
  paginar,
} from "./catalogo";
import { documento } from "./fixtures";

const docs = [
  documento({ id: "a", anio: 2024, procesado: true, pdf: "pdfs/a.pdf", bytes: 1000 }),
  documento({ id: "b", anio: 2023, tipo: "solucion", asignatura: "Física", bytes: 500 }),
  documento({ id: "c", anio: 2024, region: "País Vasco", error: "HTTP 404", descargable: false }),
  documento({ id: "d", anio: null, tipo: "video", formato: "youtube", asignatura: "Física" }),
];

describe("estadoDe", () => {
  it("distingue procesados, solo enlace y descargas fallidas", () => {
    expect(docs.map(estadoDe)).toEqual(["procesado", "enlace", "error", "enlace"]);
  });
});

describe("cumple", () => {
  it("filtra por campos, estado, tipos ocultos y texto sin tildes", () => {
    expect(docs.filter((d) => cumple(d, { anio: "2024" })).map((d) => d.id)).toEqual(["a", "c"]);
    expect(docs.filter((d) => cumple(d, { estado: "procesado" })).map((d) => d.id)).toEqual(["a"]);
    expect(docs.filter((d) => cumple(d, { ocultos: ["video", "solucion"] })).map((d) => d.id)).toEqual([
      "a",
      "c",
    ]);
    expect(docs.filter((d) => cumple(d, { texto: "fisica" })).map((d) => d.id)).toEqual(["b", "d"]);
  });
});

describe("kpis", () => {
  it("resume documentos, procesados, bytes, años y fallos", () => {
    expect(kpis(docs)).toEqual({
      documentos: 4,
      procesados: 1,
      bytesDescargados: 1500,
      soloEnlace: 1,
      asignaturas: 2,
      anios: [2023, 2024],
      fallidos: 1,
    });
    expect(kpis([]).anios).toBeNull();
  });
});

describe("matriz", () => {
  it("cuenta por asignatura y año ignorando los filtros de sus ejes", () => {
    const m = matriz(docs, { asignatura: "Física", anio: "2023", region: "Madrid" });
    expect(m.asignaturas).toEqual(["Física", "Matemáticas II"]);
    expect(m.anios).toEqual([2023, 2024]);
    expect(m.cuenta("Matemáticas II", 2024)).toBe(1);
    expect(m.cuenta("Física", 2023)).toBe(1);
    expect(m.maximo).toBe(1);
  });

  it("da más intensidad a más documentos y ninguna a cero", () => {
    expect(intensidad(0, 10)).toBe(0);
    expect(intensidad(10, 10)).toBe(100);
    expect(intensidad(1, 10)).toBeLessThan(intensidad(5, 10));
  });
});

describe("ordenar y paginar", () => {
  it("ordena por año descendente y deja los sin año al final", () => {
    expect(ordenar(docs).map((d) => d.id)).toEqual(["a", "c", "b", "d"]);
  });

  it("acota la página pedida al rango existente", () => {
    const numeros = Array.from({ length: 125 }, (_, i) => i);
    expect(paginar(numeros, 0, 60)).toMatchObject({ pagina: 0, paginas: 3 });
    expect(paginar(numeros, 9, 60).elementos).toEqual(numeros.slice(120));
    expect(paginar([], 3, 60)).toEqual({ elementos: [], pagina: 0, paginas: 1 });
  });
});

describe("URL del catálogo", () => {
  it("ida y vuelta conserva los filtros y descarta valores inválidos", () => {
    const filtros = {
      region: "Madrid",
      anio: "2024",
      estado: "procesado" as const,
      ocultos: ["video" as const],
      pagina: 2,
    };
    expect(leerFiltrosCatalogo(escribirFiltrosCatalogo(filtros))).toMatchObject(filtros);
    expect(leerFiltrosCatalogo({ estado: "raro", ocultos: "video|nada", pagina: "-1" })).toMatchObject({
      estado: undefined,
      ocultos: ["video"],
      pagina: undefined,
    });
  });
});
