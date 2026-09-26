import { describe, expect, it } from "vitest";
import { renderizar } from "./markdown";
import { resaltar } from "./resaltado";

describe("renderizar", () => {
  it("renderiza fórmulas en línea y en bloque con KaTeX", () => {
    const html = renderizar("Sea $x^2$ y\n\n$$\\int_0^1 f$$");
    expect(html.match(/class="katex"/g)).toHaveLength(2);
    expect(html).toContain("katex-display");
  });

  it("no deja que markdown altere los subrayados y asteriscos de las fórmulas", () => {
    const html = renderizar("$a_1 * b_2 * c_3$");
    expect(html).not.toContain("<em>");
    expect(html).toContain("katex");
  });

  it("entiende mhchem", () => {
    expect(renderizar("$\\ce{H2O -> H2 + O2}$")).not.toContain("katex-error");
  });

  it("mantiene tablas de markdown", () => {
    expect(renderizar("| a | b |\n|---|---|\n| 1 | 2 |")).toContain("<table>");
  });

  it("no rompe con LaTeX inválido", () => {
    expect(() => renderizar("$\\frac{a$")).not.toThrow();
  });
});

describe("resaltar", () => {
  it("marca términos en el texto sin tocar etiquetas ni distinguir tildes", () => {
    expect(resaltar('<p class="acido">El ácido</p>', "acido")).toBe(
      '<p class="acido">El <mark>ácido</mark></p>',
    );
  });

  it("ignora términos cortos", () => {
    expect(resaltar("<p>de la</p>", "de la")).toBe("<p>de la</p>");
  });
});
