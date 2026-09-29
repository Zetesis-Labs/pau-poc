// @vitest-environment jsdom
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { resaltar } from "~/dominio/resaltado";
import { Markdown } from "./Markdown";

afterEach(cleanup);

describe("Markdown seguro", () => {
  it("elimina instrucciones ejecutables del texto extraído", () => {
    const { container } = render(
      <Markdown
        texto={
          '<img src="inexistente" onerror="alert(1)"><script>alert(2)</script><a href="javascript:alert(3)">enlace</a>'
        }
      />,
    );
    expect(container.querySelector("[onerror],script,[href^='javascript:']")).toBeNull();
    expect(container.textContent).toContain("enlace");
  });

  it.each([
    '<a href="java&#x73;cript:alert(1)">leer</a>',
    '<svg onload="alert(1)"><a href="javascript:alert(2)">leer</a></svg>',
    '<math><mtext><img src="x" onerror="alert(1)"></mtext></math>',
    '<iframe srcdoc="<script>alert(1)</script>"></iframe><object data="javascript:alert(1)"></object>',
    '<form><input name="__proto__" formaction="javascript:alert(1)"></form>',
    '<style>body { display:none }</style><p onclick="alert(1)">texto</p>',
    "[enlace](javascript:alert%281%29)",
    "$\\href{javascript:alert(1)}{x}$",
    '<a title="$x$" onclick="alert(1)">texto</a>',
  ])("bloquea variantes de contenido activo: %s", (texto) => {
    const { container } = render(<Markdown texto={texto} />);
    expect(container.querySelector("script,iframe,object,embed,form,input,style")).toBeNull();
    for (const elemento of container.querySelectorAll("*")) {
      for (const atributo of elemento.attributes) {
        expect(atributo.name).not.toMatch(/^on/i);
        if (["href", "src", "xlink:href"].includes(atributo.name))
          expect(atributo.value.replace(/\s/g, "")).not.toMatch(/^(javascript|vbscript|data):/i);
      }
    }
  });

  it("conserva tablas, formato, enlaces seguros y resaltado", () => {
    const { container } = render(
      <Markdown
        texto={"**Ácido** y [fuente](https://example.org)\n\n| Sustancia | pH |\n|---|---|\n| Ácido | 2 |"}
        resaltar={(html) => resaltar(html, "ácido")}
      />,
    );
    expect(container.querySelector("strong mark")?.textContent).toBe("Ácido");
    expect(container.querySelector("table td")?.textContent).toBe("Ácido");
    expect(container.querySelector("a")?.getAttribute("href")).toBe("https://example.org");
  });

  it("conserva KaTeX, MathML y el SVG de raíces y fórmulas químicas", () => {
    const { container } = render(
      <Markdown texto={"$\\sqrt[4]{x}+\\frac{a}{b}$\n\n$$\\ce{H2O -> H2 + O2}$$"} />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.querySelectorAll("math")).toHaveLength(2);
    expect(container.querySelector(".katex-display")).not.toBeNull();
    expect(container.querySelector("svg path")?.getAttribute("d")).toBeTruthy();
    expect(container.querySelector(".katex-html [style]")).not.toBeNull();
    expect(container.querySelector(".katex-error")).toBeNull();
  });

  it("sanea también el resultado del resaltador antes de insertarlo", () => {
    const { container } = render(
      <Markdown texto="texto" resaltar={() => '<mark>texto</mark><img src="x" onerror="alert(1)">'} />,
    );
    expect(container.querySelector("mark")?.textContent).toBe("texto");
    expect(container.querySelector("[onerror]")).toBeNull();
  });
});
