// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { pregunta } from "~/dominio/fixtures";
import type { DocumentoPdf, LectorPdf } from "~/puertos/pdf";
import { DetallePregunta } from "./DetallePregunta";
import { DocumentosPregunta } from "./DocumentosPregunta";
import { VisorPdf } from "./VisorPdf";

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(private readonly callback: ResizeObserverCallback) {}
      observe() {
        this.callback(
          [{ contentRect: { width: 600 } } as ResizeObserverEntry],
          this as unknown as ResizeObserver,
        );
      }
      disconnect() {}
      unobserve() {}
    },
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function lectorFalso() {
  const pintar = vi.fn(async (): Promise<{ ancho: number; alto: number }> => ({ ancho: 572, alto: 800 }));
  const abrir = vi.fn(async (_url: string): Promise<DocumentoPdf> => ({ paginas: 12, pintar }));
  return { lector: { abrir } satisfies LectorPdf, abrir, pintar };
}

const recurso = (ruta: string) => `/datos/${ruta}`;
const acordeon = (titulo: string) => screen.getByRole("button", { name: titulo });

describe("DocumentosPregunta", () => {
  it("mantiene los tres PDF colapsados sin cargar ninguno", () => {
    const { lector, abrir } = lectorFalso();
    render(
      <DocumentosPregunta pregunta={pregunta({ id: "p1" })} idioma="es" recurso={recurso} lector={lector} />,
    );
    expect(acordeon("Examen").getAttribute("aria-expanded")).toBe("false");
    expect(acordeon("Criterios").getAttribute("aria-expanded")).toBe("false");
    expect(acordeon("Soluciones").getAttribute("aria-expanded")).toBe("false");
    expect(abrir).not.toHaveBeenCalled();
  });

  it("abre sólo el PDF elegido y conserva los enlaces sin insertarlos en el visor", async () => {
    const { lector, abrir } = lectorFalso();
    const p = pregunta({
      id: "p1",
      examen: {
        ...pregunta({ id: "base" }).examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "c1",
            pdf: "pdfs/c1.pdf",
            url: "https://origen/c1.pdf",
          },
          {
            tipo: "solucion",
            contenido: ["solucion"],
            origen: "academia",
            fuente: "llibreta",
            acceso: "privado",
            coincidencia: "exacta",
            id: "s1",
            url: "https://origen/s1",
          },
        ],
      },
    });
    render(<DocumentosPregunta pregunta={p} idioma="es" recurso={recurso} lector={lector} />);
    fireEvent.click(acordeon("Criterios"));
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/c1.pdf"));
    fireEvent.click(acordeon("Soluciones"));
    expect(
      screen
        .getByText(/Abrir solución de la llibreta en el origen/)
        .closest("a")
        ?.getAttribute("href"),
    ).toBe("https://origen/s1");
    expect(abrir).toHaveBeenCalledTimes(1);
  });

  it("salta al anexo y a su página aunque el acordeón esté cerrado", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "c1",
            pdf: "pdfs/c1.pdf",
            url: "https://origen/c1.pdf",
          },
        ],
      },
    });
    const { rerender } = render(
      <DocumentosPregunta pregunta={p} idioma="es" recurso={recurso} lector={lector} />,
    );
    rerender(
      <DocumentosPregunta
        pregunta={p}
        idioma="es"
        recurso={recurso}
        lector={lector}
        salto={{ pagina: 4, pdf: "pdfs/c1.pdf", vez: 1 }}
      />,
    );
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/c1.pdf"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(4, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
    expect(acordeon("Criterios").getAttribute("aria-expanded")).toBe("true");
  });

  it("abre una corrección incrustada en su primera página y dirige los saltos de solución", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      solucion: {
        texto: { es: "Resultado" },
        origen: "oficial",
        fuente: "uc3m",
        incrustado: true,
        paginas: { es: 6 },
      },
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios", "solucion"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            incrustado: { pagina: 4 },
          },
        ],
      },
    });
    const { rerender } = render(
      <DocumentosPregunta pregunta={p} idioma="es" recurso={recurso} lector={lector} />,
    );
    fireEvent.click(acordeon("Criterios"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(4, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
    expect(abrir).toHaveBeenCalledWith("/datos/pdfs/ex1.pdf");
    rerender(
      <DocumentosPregunta
        pregunta={p}
        idioma="es"
        recurso={recurso}
        lector={lector}
        salto={{ pagina: 6, vez: 2 }}
      />,
    );
    await waitFor(() => expect(acordeon("Soluciones").getAttribute("aria-expanded")).toBe("true"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(6, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
  });

  it("un salto sin PDF ignora el anexo local aunque coincida su página de solución", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      solucion: {
        texto: { es: "Resultado" },
        origen: "oficial",
        fuente: "uc3m",
        incrustado: false,
        pdf: "pdfs/solucion.pdf",
        paginas: { es: 2 },
      },
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "solucion",
            contenido: ["solucion"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "s1",
            pdf: "pdfs/solucion.pdf",
          },
          {
            tipo: "criterios",
            contenido: ["criterios"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            incrustado: { pagina: 2 },
          },
        ],
      },
    });
    render(
      <DocumentosPregunta
        pregunta={p}
        idioma="es"
        recurso={recurso}
        lector={lector}
        salto={{ pagina: 2, vez: 1 }}
      />,
    );
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/ex1.pdf"));
    expect(abrir).not.toHaveBeenCalledWith("/datos/pdfs/solucion.pdf");
    expect(acordeon("Criterios").getAttribute("aria-expanded")).toBe("true");
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(2, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
  });

  it("encuentra soluciones de apartados con PDF propio sin solución en el nodo raíz", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const apartado = (pdf: string, pagina: number) => ({
      etiqueta: { es: "a" },
      enunciado: { es: "Enunciado" },
      puntos: 1,
      estimulos: [],
      regla: "",
      rubrica: null,
      solucion: {
        texto: { es: "Resultado" },
        origen: "oficial" as const,
        fuente: "uc3m",
        incrustado: false,
        pdf,
        paginas: { es: pagina },
      },
      apartados: [],
    });
    const p = pregunta({
      id: "p1",
      apartados: [apartado("pdfs/a.pdf", 2), apartado("pdfs/b.pdf", 5)],
    });
    render(
      <DocumentosPregunta
        pregunta={p}
        idioma="es"
        recurso={recurso}
        lector={lector}
        salto={{ pagina: 5, pdf: "pdfs/b.pdf", vez: 1 }}
      />,
    );
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/b.pdf"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(5, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
    expect(acordeon("Soluciones").getAttribute("aria-expanded")).toBe("true");
    expect(acordeon("Soluciones").textContent).toContain("2 documentos");
  });

  it("muestra en Soluciones la respuesta de un apartado hallada en criterios y abre su página en el idioma elegido", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "c1",
            pdf: "pdfs/criterios.pdf",
          },
        ],
      },
      apartados: [
        {
          etiqueta: { es: "a" },
          enunciado: { es: "Enunciado" },
          puntos: 1,
          estimulos: [],
          regla: "",
          rubrica: null,
          solucion: {
            texto: { es: "Resultado", va: "Emaitza" },
            origen: "oficial",
            fuente: "uc3m",
            extraccion: "rubrica",
            incrustado: false,
            pdf: "pdfs/criterios.pdf",
            paginas: { es: 6, va: 8 },
          },
          apartados: [],
        },
      ],
    });
    render(<DocumentosPregunta pregunta={p} idioma="va" recurso={recurso} lector={lector} />);
    fireEvent.click(acordeon("Soluciones"));
    expect(acordeon("Soluciones").textContent).toContain("1 documento");
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/criterios.pdf"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(8, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
  });

  it("deduplica un anexo que ya incluye solución y prioriza la página extraída", async () => {
    const { lector, abrir, pintar } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios", "solucion"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "c1",
            pdf: "pdfs/criterios.pdf",
          },
        ],
      },
      solucion: {
        texto: { es: "Resultado" },
        origen: "oficial",
        fuente: "uc3m",
        extraccion: "rubrica",
        incrustado: false,
        pdf: "pdfs/criterios.pdf",
        paginas: { es: 9 },
      },
    });
    render(<DocumentosPregunta pregunta={p} idioma="es" recurso={recurso} lector={lector} />);
    fireEvent.click(acordeon("Soluciones"));
    expect(acordeon("Soluciones").textContent).toContain("1 documento");
    await waitFor(() => expect(abrir).toHaveBeenCalledWith("/datos/pdfs/criterios.pdf"));
    await waitFor(() =>
      expect(pintar).toHaveBeenCalledWith(9, expect.any(HTMLCanvasElement), 572, expect.any(AbortSignal)),
    );
  });

  it("abre el grupo solicitado por criterios o respuesta aunque compartan PDF y página", async () => {
    const { lector } = lectorFalso();
    const base = pregunta({ id: "base" });
    const p = pregunta({
      id: "p1",
      examen: {
        ...base.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios", "solucion"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            id: "c1",
            pdf: "pdfs/criterios.pdf",
          },
        ],
      },
      fuenteRubrica: {
        tipo: "criterios",
        incrustado: false,
        url: "https://origen/criterios.pdf",
        pdf: "pdfs/criterios.pdf",
      },
      rubrica: { puntos: 1, criterios: { es: "Criterio" }, desglose: [], paginas: { es: 9 } },
      solucion: {
        texto: { es: "Respuesta" },
        origen: "oficial",
        fuente: "uc3m",
        extraccion: "rubrica",
        incrustado: false,
        pdf: "pdfs/criterios.pdf",
        paginas: { es: 9 },
      },
    });
    function Vista() {
      const [salto, setSalto] = useState<{
        pagina: number;
        pdf?: string;
        grupo?: "criterios" | "soluciones";
        vez: number;
      }>();
      return (
        <DetallePregunta
          pregunta={p}
          idioma="es"
          recurso={recurso}
          onIdioma={vi.fn()}
          onAmpliar={vi.fn()}
          onCerrar={vi.fn()}
          onIrAPagina={(pagina, pdf, grupo) =>
            setSalto((previo) => ({ pagina, pdf, grupo, vez: (previo?.vez ?? 0) + 1 }))
          }
        >
          <DocumentosPregunta pregunta={p} idioma="es" recurso={recurso} lector={lector} salto={salto} />
        </DetallePregunta>
      );
    }
    render(<Vista />);
    fireEvent.click(screen.getByText(/Cómo se corrige/));
    fireEvent.click(screen.getByText(/Ver la solución/));
    const [criterios, solucion] = screen.getAllByRole("button", { name: /ver en el PDF, p. 9/ });
    if (!criterios || !solucion) throw new Error("Faltan los enlaces de criterios y solución");
    fireEvent.click(criterios);
    await waitFor(() => expect(acordeon("Criterios").getAttribute("aria-expanded")).toBe("true"));
    fireEvent.click(solucion);
    await waitFor(() => expect(acordeon("Soluciones").getAttribute("aria-expanded")).toBe("true"));
  });
});

describe("VisorPdf", () => {
  it("navega con flechas sólo cuando el foco está en el visor", async () => {
    const { lector } = lectorFalso();
    const { container } = render(<VisorPdf lector={lector} url="/examen.pdf" />);
    await waitFor(() => expect(screen.getByText("página 1 de 12")).toBeTruthy());
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByText("página 1 de 12")).toBeTruthy();
    const visor = container.querySelector('[aria-label="Visor del PDF"]');
    expect(visor).toBeTruthy();
    expect(visor?.hasAttribute("data-visor-pdf")).toBe(true);
    fireEvent.keyDown(screen.getByTitle("Página siguiente (→)"), { key: "ArrowRight" });
    expect(screen.getByText("página 2 de 12")).toBeTruthy();
  });

  it("cancela un render al cambiar de página y al desmontarse", async () => {
    const pendientes: Array<{ signal: AbortSignal | undefined; resolver: () => void }> = [];
    const pintar: DocumentoPdf["pintar"] = (_pagina, _lienzo, _ancho, signal) =>
      new Promise((resolve) => {
        pendientes.push({ signal, resolver: () => resolve({ ancho: 572, alto: 800 }) });
      });
    const lector: LectorPdf = { abrir: async () => ({ paginas: 5, pintar }) };
    const { unmount } = render(<VisorPdf lector={lector} url="/examen.pdf" />);
    await waitFor(() => expect(pendientes).toHaveLength(1));
    fireEvent.click(screen.getByTitle("Página siguiente (→)"));
    await waitFor(() => expect(pendientes).toHaveLength(2));
    expect(pendientes[0]?.signal?.aborted).toBe(true);
    unmount();
    expect(pendientes[1]?.signal?.aborted).toBe(true);
    await act(async () => {
      for (const pendiente of pendientes) pendiente.resolver();
    });
  });
});
