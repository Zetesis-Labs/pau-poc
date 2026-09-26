import { describe, expect, it } from "vitest";
import { desplazamientoPara, franjaEn, paginaAcotada } from "./franja";

describe("franjaEn", () => {
  const ancla = { pagina: 2, y0: 0.25, y1: 0.5 };

  it("convierte fracciones de página a píxeles con margen", () => {
    expect(franjaEn(ancla, 2, 1000)).toEqual({ top: 246, alto: 258 });
  });

  it("no pinta nada en otra página o sin posición", () => {
    expect(franjaEn(ancla, 1, 1000)).toBeNull();
    expect(franjaEn({ pagina: 2, y0: null, y1: null }, 2, 1000)).toBeNull();
    expect(franjaEn(undefined, 2, 1000)).toBeNull();
  });

  it("sin final conocido usa una altura por defecto", () => {
    expect(franjaEn({ pagina: 1, y0: 0.1, y1: null }, 1, 1000)?.alto).toBeCloseTo(58);
  });

  it("deja aire encima al desplazarse y nunca negativo", () => {
    expect(desplazamientoPara({ top: 246, alto: 10 })).toBe(186);
    expect(desplazamientoPara({ top: 20, alto: 10 })).toBe(0);
    expect(desplazamientoPara(null)).toBe(0);
  });

  it("acota la página al documento", () => {
    expect(paginaAcotada(0, 5)).toBe(1);
    expect(paginaAcotada(9, 5)).toBe(5);
    expect(paginaAcotada(3, 0)).toBe(1);
  });
});
