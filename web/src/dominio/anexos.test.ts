import { describe, expect, it } from "vitest";
import { correccionDe, destinoAnexo, etiquetaAnexo } from "./anexos";
import type { Anexo } from "./tipos";

const incrustado: Anexo = {
  tipo: "criterios",
  origen: "oficial",
  fuente: "uc3m",
  acceso: "publico",
  coincidencia: "exacta",
  incrustado: { pagina: 3 },
};
const criteriosSueltos: Anexo = {
  tipo: "criterios",
  origen: "oficial",
  fuente: "llibreta",
  acceso: "publico",
  coincidencia: "exacta",
  id: "c1",
  url: "https://origen/criterios.pdf",
};
const academia: Anexo = {
  tipo: "solucion",
  origen: "academia",
  fuente: "mundoestudiante",
  acceso: "publico",
  coincidencia: "por_clave",
  id: "s1",
  url: "https://origen/solucion.pdf",
};
const privada: Anexo = { ...academia, fuente: "llibreta", acceso: "privado", id: "s2" };
const rota: Anexo = { ...academia, acceso: "roto", id: "s3" };

describe("etiquetaAnexo", () => {
  it("dice qué es y de quién", () => {
    expect(etiquetaAnexo(incrustado)).toBe("Criterios de corrección oficiales");
    expect(etiquetaAnexo({ ...academia, origen: "oficial", fuente: "ehu" })).toBe("Solución oficial");
    expect(etiquetaAnexo(academia)).toBe("Solución de mundoestudiante");
    expect(etiquetaAnexo(privada)).toBe("Solución de La Llibreta");
  });
});

describe("destinoAnexo", () => {
  const publicado = { pdf: "pdfs/ex.pdf", url: "https://origen/ex.pdf" };
  const soloOrigen = { url: "https://origen/ex.pdf" };

  it("lleva a la página del PDF publicado cuando la corrección va dentro", () => {
    expect(destinoAnexo(incrustado, publicado)).toEqual({
      accion: "pagina",
      pagina: 3,
      nota: "en este PDF, p. 3",
    });
  });

  it("sin PDF publicado enlaza al examen original indicando la página", () => {
    expect(destinoAnexo(incrustado, soloOrigen)).toEqual({
      accion: "enlace",
      href: "https://origen/ex.pdf",
      nota: "dentro del PDF del examen, p. 3",
    });
  });

  it("los anexos sueltos enlazan a su origen y avisan si son privados", () => {
    expect(destinoAnexo(criteriosSueltos, publicado)).toEqual({
      accion: "enlace",
      href: "https://origen/criterios.pdf",
      nota: "",
    });
    expect(destinoAnexo(privada, publicado)).toEqual({
      accion: "enlace",
      href: "https://origen/solucion.pdf",
      nota: "requiere acceso",
    });
  });

  it("no enlaza lo que está roto", () => {
    expect(destinoAnexo(rota, publicado)).toEqual({ accion: "ninguna", nota: "enlace roto" });
  });
});

describe("correccionDe", () => {
  it("resume lo mejor accesible", () => {
    expect(correccionDe([incrustado, academia])).toBe("Criterios oficiales");
    expect(correccionDe([{ ...academia, origen: "oficial", fuente: "ehu" }])).toBe("Solución oficial");
    expect(correccionDe([academia])).toBe("Solo de academia");
    expect(correccionDe([privada, rota])).toBe("Sin corrección accesible");
    expect(correccionDe([])).toBe("Sin corrección accesible");
  });
});
