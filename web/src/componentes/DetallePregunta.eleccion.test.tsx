// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { pregunta } from "~/dominio/fixtures";
import { DetallePregunta } from "./DetallePregunta";

afterEach(() => cleanup());

function mostrar(p: ReturnType<typeof pregunta>, idioma: string) {
  render(
    <DetallePregunta
      pregunta={p}
      idioma={idioma}
      recurso={(ruta) => `/datos/${ruta}`}
      onIdioma={vi.fn()}
      onAmpliar={vi.fn()}
      onCerrar={vi.fn()}
      onIrAPagina={vi.fn()}
    />,
  );
}

it("muestra la regla propia y su instrucción original incluso sin enunciado", () => {
  mostrar(
    pregunta({
      id: "cdd0f4f759e1:n2",
      enunciado: {},
      regla: "elegir 2 de 4",
      literalRegla: {
        es: "Defina DOS de los conceptos siguientes.",
        va: "Definiu DOS dels conceptes següents.",
      },
      idiomas: ["es", "va"],
      apartados: [
        {
          etiqueta: { es: "1" },
          enunciado: { es: "Afrancesados" },
          puntos: null,
          estimulos: [],
          regla: "",
          rubrica: null,
          solucion: null,
          apartados: [],
        },
      ],
    }),
    "es",
  );

  expect(screen.getByText("elegir 2 de 4")).toBeTruthy();
  expect(screen.getByText("Defina DOS de los conceptos siguientes.")).toBeTruthy();
  expect(screen.getByText("Afrancesados")).toBeTruthy();
});

it("mantiene visible la instrucción en el idioma elegido", () => {
  mostrar(
    pregunta({
      id: "cdd0f4f759e1:n2",
      regla: "elegir 2 de 4",
      literalRegla: {
        es: "Defina DOS de los conceptos siguientes.",
        va: "Definiu DOS dels conceptes següents.",
      },
      idiomas: ["es", "va"],
    }),
    "va",
  );

  expect(screen.getByText("Definiu DOS dels conceptes següents.")).toBeTruthy();
});

it("muestra la regla aunque la extracción no incluya literal", () => {
  mostrar(pregunta({ id: "sin-literal:n1", regla: "elegir 1 de 2" }), "es");

  expect(screen.getByText("elegir 1 de 2")).toBeTruthy();
});

it("abre una pregunta del banco anterior sin campo de regla propia", () => {
  mostrar(pregunta({ id: "anterior:n1" }), "es");

  expect(screen.getByRole("heading", { name: "1" })).toBeTruthy();
  expect(screen.queryByText("Regla de la pregunta")).toBeNull();
});
