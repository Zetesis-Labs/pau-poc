import { describe, expect, it } from "vitest";
import { pregunta } from "./fixtures";
import {
  destinoRubrica,
  destinoSolucion,
  discrepanciaDePuntos,
  etiquetaSolucion,
  tieneRubrica,
  valoresCorreccion,
} from "./rubrica";
import type { Apartado, Rubrica, Solucion } from "./tipos";

const rubrica: Rubrica = {
  puntos: 0.75,
  criterios: { es: "Planteamiento" },
  desglose: [],
  paginas: { es: 6, va: 12 },
};

const academia: Solucion = {
  texto: { es: "b = 3" },
  origen: "academia",
  fuente: "mundoestudiante",
  incrustado: false,
  url: "https://me/sol.pdf",
  paginas: { es: 2 },
};
const oficial: Solucion = {
  texto: { es: "a = 1" },
  origen: "oficial",
  fuente: "uc3m",
  incrustado: true,
  paginas: { es: 7 },
};

const apartado = (r: Rubrica | null, hijos: Apartado[] = [], solucion: Solucion | null = null): Apartado => ({
  etiqueta: { es: "a)" },
  enunciado: { es: "..." },
  puntos: 1,
  estimulos: [],
  regla: "",
  rubrica: r,
  solucion,
  apartados: hijos,
});

describe("tieneRubrica", () => {
  it("mira la pregunta y todos sus apartados, a cualquier profundidad", () => {
    expect(tieneRubrica(pregunta({ id: "a" }))).toBe(false);
    expect(tieneRubrica(pregunta({ id: "b", rubrica }))).toBe(true);
    expect(tieneRubrica(pregunta({ id: "c", apartados: [apartado(null, [apartado(rubrica)])] }))).toBe(true);
  });
});

describe("discrepanciaDePuntos", () => {
  it("avisa cuando los criterios puntúan distinto que el enunciado", () => {
    expect(discrepanciaDePuntos(1, rubrica)).toBe("los criterios dan 0,75 puntos; el enunciado, 1");
    expect(discrepanciaDePuntos(0.75, rubrica)).toBeNull();
    expect(discrepanciaDePuntos(null, rubrica)).toBeNull();
    expect(discrepanciaDePuntos(1, { ...rubrica, puntos: null })).toBeNull();
  });
});

describe("destinoRubrica", () => {
  it("salta a la página del PDF si los criterios van dentro, en el idioma que se lee", () => {
    expect(destinoRubrica(rubrica, { tipo: "criterios", incrustado: true }, "va")).toEqual({
      accion: "pagina",
      pagina: 12,
    });
    expect(destinoRubrica(rubrica, { tipo: "criterios", incrustado: true }, "eu")).toEqual({
      accion: "pagina",
      pagina: 6,
    });
  });

  it("enlaza a la página del documento de criterios si es aparte", () => {
    expect(
      destinoRubrica(rubrica, { tipo: "criterios", incrustado: false, url: "https://gva/c.pdf" }, "es"),
    ).toEqual({
      accion: "enlace",
      href: "https://gva/c.pdf#page=6",
    });
  });

  it("sin página conocida no lleva a ninguna parte", () => {
    expect(
      destinoRubrica({ ...rubrica, paginas: {} }, { tipo: "criterios", incrustado: true }, "es"),
    ).toBeNull();
    expect(destinoRubrica(rubrica, null, "es")).toBeNull();
  });
});

describe("soluciones", () => {
  it("lleva a su página: la del PDF que se ve o la del documento de la academia", () => {
    expect(destinoSolucion(oficial, "es")).toEqual({ accion: "pagina", pagina: 7 });
    expect(destinoSolucion(academia, "es")).toEqual({ accion: "enlace", href: "https://me/sol.pdf#page=2" });
  });

  it("dice de dónde sale", () => {
    expect(etiquetaSolucion(oficial)).toBe("solución oficial");
    expect(etiquetaSolucion(academia)).toBe("solución de mundoestudiante (academia)");
  });
});

describe("valoresCorreccion", () => {
  it("refleja lo que se puede consultar en la pregunta", () => {
    const completa = pregunta({
      id: "x",
      rubrica,
      apartados: [apartado(null, [], oficial), apartado(null, [], academia)],
      examen: {
        ...pregunta({ id: "y" }).examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            incrustado: { pagina: 5 },
          },
        ],
      },
    });
    expect(valoresCorreccion(completa)).toEqual([
      "Con criterios",
      "Con rúbrica",
      "Con solución oficial",
      "Con solución de academia",
    ]);
    expect(valoresCorreccion(pregunta({ id: "z", solucion: academia }))).toEqual([
      "Con solución de academia",
    ]);
    expect(valoresCorreccion(pregunta({ id: "w" }))).toEqual(["Sin corrección"]);
  });
});
