// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SolucionNodo } from "./SolucionNodo";

afterEach(cleanup);

describe("SolucionNodo", () => {
  it("identifica una respuesta extraída de criterios oficiales sin atribuirle validación académica", () => {
    const onIrAPagina = vi.fn();
    render(
      <SolucionNodo
        solucion={{
          texto: { es: "La respuesta es 42" },
          origen: "oficial",
          fuente: "uc3m",
          extraccion: "rubrica",
          incrustado: false,
          pdf: "pdfs/criterios.pdf",
          paginas: { es: 7 },
        }}
        idioma="es"
        onIrAPagina={onIrAPagina}
      />,
    );
    expect(screen.getByText(/Respuesta en los criterios oficiales/)).toBeTruthy();
    expect(screen.queryByText(/validada/)).toBeNull();
    fireEvent.click(screen.getByText(/Respuesta en los criterios oficiales/));
    expect(screen.getByText("La respuesta es 42")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /ver en el PDF, p. 7/ }));
    expect(onIrAPagina).toHaveBeenCalledWith(7, "pdfs/criterios.pdf", "soluciones");
  });

  it("identifica una respuesta extraída de criterios de academia por su fuente", () => {
    render(
      <SolucionNodo
        solucion={{
          texto: { es: "Respuesta" },
          origen: "academia",
          fuente: "llibreta",
          extraccion: "rubrica",
          incrustado: false,
          paginas: { es: 3 },
        }}
        idioma="es"
        onIrAPagina={vi.fn()}
      />,
    );
    expect(screen.getByText(/Respuesta en los criterios de La Llibreta/)).toBeTruthy();
    expect(screen.getByText(/Redacción de la academia, no del tribunal/)).toBeTruthy();
  });
});
