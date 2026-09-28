import { describe, expect, it } from "vitest";
import {
  alternar,
  calcularFaceta,
  claveApartado,
  FACETAS,
  type Filtros,
  figurasDe,
  filtrar,
  filtrosActivos,
  indexar,
  limpiar,
  materiales,
  migas,
  vecina,
} from "./banco";
import { pregunta } from "./fixtures";

const faceta = (clave: string) => {
  const f = FACETAS.find((d) => d.clave === clave);
  if (!f) throw new Error(clave);
  return f;
};

const madrid = pregunta({ id: "m" });
const valencia = pregunta({
  id: "v",
  examen: { ...madrid.examen, id: "ex2", region: "Comunidad Valenciana", asignatura: "Química" },
  idiomas: ["es", "va"],
  enunciado: { es: "Ajusta la reacción del ácido.", va: "Ajusteu la reacció de l'àcid." },
});
const vasca = pregunta({
  id: "e",
  examen: { ...madrid.examen, id: "ex3", region: "País Vasco", anio: 2021 },
  idiomas: ["eu", "es"],
});
const indice = indexar([madrid, valencia, vasca]);

describe("filtrar", () => {
  it("combina valores de una faceta con O y facetas distintas con Y", () => {
    const filtros: Filtros = { region: ["Madrid", "País Vasco"], anio: ["2024"] };
    expect(filtrar(indice, filtros, "").map((p) => p.pregunta.id)).toEqual(["m"]);
  });

  it("busca todos los términos sin distinguir tildes ni mayúsculas", () => {
    expect(filtrar(indice, {}, "ACIDO reaccion").map((p) => p.pregunta.id)).toEqual(["v"]);
    expect(filtrar(indice, {}, "acido integral")).toEqual([]);
  });

  it("encuentra el texto en cualquier idioma de la pregunta", () => {
    expect(filtrar(indice, {}, "reacció").map((p) => p.pregunta.id)).toEqual(["v"]);
  });

  it("ignora los comandos de LaTeX al indexar", () => {
    const fraccion = indexar([pregunta({ id: "f", enunciado: { es: "Simplifica $\\frac{a}{b}$" } })]);
    expect(filtrar(fraccion, {}, "frac")).toEqual([]);
    expect(filtrar(fraccion, {}, "simplifica")).toHaveLength(1);
  });
});

describe("calcularFaceta", () => {
  it("cuenta cada faceta sin aplicar su propio filtro (facetado disyuntivo)", () => {
    const region = calcularFaceta(faceta("region"), indice, { region: ["Madrid"] }, "", false);
    expect(Object.fromEntries(region.valores.map((v) => [v.valor, [v.cuenta, v.elegido]]))).toEqual({
      Madrid: [1, true],
      "Comunidad Valenciana": [1, false],
      "País Vasco": [1, false],
    });
    expect(region.activa).toBe(true);
  });

  it("aplica los filtros de las demás facetas y conserva los valores sin resultados", () => {
    const region = calcularFaceta(faceta("region"), indice, { anio: ["2021"] }, "", false);
    expect(region.valores.find((v) => v.valor === "Madrid")?.cuenta).toBe(0);
    expect(region.valores.find((v) => v.valor === "País Vasco")?.cuenta).toBe(1);
  });

  it("ordena los años de más reciente a más antiguo", () => {
    expect(calcularFaceta(faceta("anio"), indice, {}, "", false).valores.map((v) => v.valor)).toEqual([
      "2024",
      "2021",
    ]);
  });

  it("traduce los códigos de idioma", () => {
    const nombres = calcularFaceta(faceta("idioma"), indice, {}, "", false).valores.map((v) => v.nombre);
    expect(nombres).toContain("euskera");
    expect(nombres).toContain("valenciano");
  });

  it("recorta a su límite salvo los valores elegidos, y dice cuántos oculta", () => {
    const muchas = indexar(
      Array.from({ length: 15 }, (_, i) =>
        pregunta({ id: `p${i}`, examen: { ...madrid.examen, asignatura: `A${String(i).padStart(2, "0")}` } }),
      ),
    );
    const recortada = calcularFaceta(faceta("asignatura"), muchas, { asignatura: ["A14"] }, "", false);
    expect(recortada.valores).toHaveLength(13);
    expect(recortada.valores.some((v) => v.valor === "A14")).toBe(true);
    expect(recortada.ocultos).toBe(2);
    expect(calcularFaceta(faceta("asignatura"), muchas, {}, "", true).ocultos).toBe(0);
  });
});

describe("faceta de corrección", () => {
  it("permite filtrar por criterios y por solución por separado", () => {
    const conCriterios = pregunta({
      id: "c",
      examen: {
        ...madrid.examen,
        anexos: [
          {
            tipo: "criterios",
            contenido: ["criterios", "solucion"],
            origen: "oficial",
            fuente: "uc3m",
            acceso: "publico",
            coincidencia: "exacta",
            incrustado: { pagina: 3 },
          },
        ],
      },
    });
    const valores = calcularFaceta(
      faceta("correccion"),
      indexar([madrid, conCriterios]),
      {},
      "",
      false,
    ).valores;
    expect(Object.fromEntries(valores.map((v) => [v.valor, v.cuenta]))).toEqual({
      "Con criterios": 1,
      "Con solución": 1,
      "Sin corrección": 1,
    });
  });
});

describe("alternar y limpiar", () => {
  it("añade y quita valores, y deja la faceta vacía como sin filtro", () => {
    const con = alternar({}, "region", "Madrid");
    expect(con.region).toEqual(["Madrid"]);
    expect(alternar(con, "region", "Madrid").region).toBeUndefined();
    expect(limpiar({ region: ["Madrid"], anio: ["2024"] }, "region")).toEqual({
      region: undefined,
      anio: ["2024"],
    });
  });

  it("lista los filtros activos con su nombre legible", () => {
    expect(filtrosActivos({ convocatoria: ["extraordinaria"] })).toEqual([
      { clave: "convocatoria", valor: "extraordinaria", nombre: "Extraordinaria" },
    ]);
  });
});

describe("vecina", () => {
  it("se mueve por la lista sin salirse de los extremos", () => {
    expect(vecina(["a", "b", "c"], "b", 1)).toBe("c");
    expect(vecina(["a", "b", "c"], "c", 1)).toBe("c");
    expect(vecina(["a", "b", "c"], "a", -1)).toBe("a");
  });

  it("empieza por la primera si no hay selección o ya no es visible", () => {
    expect(vecina(["a", "b"], undefined, 1)).toBe("a");
    expect(vecina(["a", "b"], "z", -1)).toBe("a");
    expect(vecina([], "a", 1)).toBeUndefined();
  });
});

describe("materiales", () => {
  it("detecta figuras, texto base, fórmulas y apartados", () => {
    const completa = pregunta({
      id: "x",
      estimulos: [
        {
          id: "E1",
          tipo: "figura",
          descripcion: "",
          contenido: {},
          figuras: [{ src: "figuras/a.png", idioma: "es" }],
        },
        { id: "E2", tipo: "texto", descripcion: "", contenido: { es: "Texto" }, figuras: [] },
      ],
      apartados: [
        {
          etiqueta: { es: "a)" },
          enunciado: { es: "Sin fórmula" },
          puntos: 1,
          estimulos: [],
          regla: "",
          apartados: [],
        },
      ],
    });
    expect(materiales(completa)).toEqual(["Con figura", "Con texto base", "Con fórmulas", "Con apartados"]);
    expect(materiales(pregunta({ id: "y", enunciado: { es: "Comenta el texto." } }))).toEqual([]);
  });
});

describe("migas", () => {
  it("encadena examen, bloques y reglas con claves únicas", () => {
    const p = pregunta({
      id: "c",
      contexto: [
        {
          etiqueta: { es: "Opción A" },
          tipo: "opcion",
          enunciado: {},
          regla: "elegir 1 de 2",
          sintetico: false,
        },
        { etiqueta: { es: "Bloque 1" }, tipo: "bloque", enunciado: {}, regla: "", sintetico: true },
      ],
    });
    const resultado = migas(p, "es");
    expect(resultado.map((m) => m.texto)).toEqual([
      "Matemáticas II · Madrid · 2024 Ordinaria",
      "Opción A",
      "Bloque 1",
    ]);
    expect(resultado.map((m) => m.regla)).toEqual(["", "elegir 1 de 2", ""]);
    expect(new Set(resultado.map((m) => m.clave)).size).toBe(3);
  });
});

describe("figurasDe", () => {
  it("prefiere las figuras del idioma elegido y si no hay usa la primera", () => {
    const figuras = [
      { src: "a_va.png", idioma: "va" },
      { src: "a_es.png", idioma: "es" },
    ];
    expect(figurasDe(figuras, "es")).toEqual([{ src: "a_es.png", idioma: "es" }]);
    expect(figurasDe(figuras, "eu")).toEqual([{ src: "a_va.png", idioma: "va" }]);
  });
});

describe("claveApartado", () => {
  it("distingue apartados con la misma etiqueta y distinto enunciado", () => {
    const base = { puntos: null, estimulos: [], regla: "", apartados: [] };
    expect(claveApartado({ ...base, etiqueta: { es: "a)" }, enunciado: { es: "Uno" } })).not.toBe(
      claveApartado({ ...base, etiqueta: { es: "a)" }, enunciado: { es: "Dos" } }),
    );
  });
});
