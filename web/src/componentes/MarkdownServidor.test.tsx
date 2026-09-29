import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Markdown } from "./Markdown";

describe("Markdown sin DOM disponible", () => {
  it("presenta texto escapado cuando no puede sanear HTML", () => {
    const html = renderToStaticMarkup(<Markdown texto={'<img src="x" onerror="alert(1)">'} />);
    expect(html).toContain("&lt;img");
    expect(html).not.toContain("<img");
  });
});
