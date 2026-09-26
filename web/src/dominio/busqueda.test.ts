import { describe, expect, it } from "vitest";
import { escribirEstado, leerEstado, validarBusqueda } from "./busqueda";

describe("URL del banco", () => {
  it("ida y vuelta conserva consulta, selección, idioma y filtros", () => {
    const estado = {
      consulta: "ácido",
      seleccion: "ex1:n3",
      idioma: "va",
      filtros: { region: ["Madrid", "País Vasco"], anio: ["2024"] },
    };
    expect(leerEstado(validarBusqueda(escribirEstado(estado)))).toEqual(estado);
  });

  it("descarta parámetros desconocidos o vacíos y acepta años numéricos", () => {
    expect(validarBusqueda({ q: "", foo: "x", anio: 2024, region: "Madrid|" })).toEqual({
      anio: "2024",
      region: "Madrid|",
    });
    expect(leerEstado({ region: "Madrid|" }).filtros).toEqual({ region: ["Madrid"] });
  });

  it("no escribe claves vacías", () => {
    expect(escribirEstado({ consulta: "", filtros: { region: [] } })).toEqual({});
  });
});
