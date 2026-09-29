import { useEffect, useId, useMemo, useRef, useState } from "react";
import { destinoAnexo, etiquetaAnexo } from "~/dominio/anexos";
import { etiquetaSolucion } from "~/dominio/rubrica";
import { idiomaPreferido } from "~/dominio/textos";
import type { Anexo, Apartado, Pregunta, Solucion } from "~/dominio/tipos";
import type { LectorPdf } from "~/puertos/pdf";
import { type Salto, VisorPdf } from "./VisorPdf";

type Grupo = "examen" | "criterios" | "soluciones";
type Destino = ReturnType<typeof destinoAnexo>;

interface Documento {
  readonly id: string;
  readonly grupo: Grupo;
  readonly titulo: string;
  readonly destino: Destino;
  readonly pdf?: string;
}

interface Props {
  readonly pregunta: Pregunta;
  readonly idioma: string;
  readonly recurso: (ruta: string) => string;
  readonly lector: LectorPdf;
  readonly salto?: Salto;
}

const GRUPOS: readonly { id: Grupo; titulo: string; vacio: string }[] = [
  { id: "examen", titulo: "Examen", vacio: "El PDF del examen no está disponible." },
  { id: "criterios", titulo: "Criterios", vacio: "No hay criterios vinculados a este examen." },
  { id: "soluciones", titulo: "Soluciones", vacio: "No hay soluciones vinculadas a este examen." },
];

function paginasDe(pregunta: Pregunta, idioma: string, tipo: "rubrica" | "solucion"): number[] {
  const paginas: number[] = [];
  const incluir = (apartados: readonly Apartado[]) => {
    for (const apartado of apartados) {
      const pagina = apartado[tipo]?.paginas[idioma];
      if (pagina) paginas.push(pagina);
      incluir(apartado.apartados);
    }
  };
  const principal = pregunta[tipo]?.paginas[idioma];
  if (principal) paginas.push(principal);
  incluir(pregunta.apartados);
  return paginas;
}

function solucionesDe(pregunta: Pregunta): Solucion[] {
  const soluciones: Solucion[] = [];
  if (pregunta.solucion) soluciones.push(pregunta.solucion);
  const incluir = (apartados: readonly Apartado[]) => {
    for (const apartado of apartados) {
      if (apartado.solucion) soluciones.push(apartado.solucion);
      incluir(apartado.apartados);
    }
  };
  incluir(pregunta.apartados);
  return soluciones;
}

function documentosDe(pregunta: Pregunta, idioma: string): Documento[] {
  const examen = pregunta.examen;
  const documentos: Documento[] = [
    {
      id: "examen",
      grupo: "examen",
      titulo: "PDF del examen",
      destino: { accion: "pagina", pdf: examen.pdf, pagina: pregunta.paginas[idioma] ?? 1, nota: "" },
      pdf: examen.pdf,
    },
  ];
  examen.anexos.forEach((anexo: Anexo, indice) => {
    const destino = destinoAnexo(anexo, examen);
    for (const grupo of ["criterios", "soluciones"] as const) {
      const contenido = grupo === "criterios" ? "criterios" : "solucion";
      if (!anexo.contenido.includes(contenido)) continue;
      documentos.push({
        id: `${grupo}-${anexo.id ?? `${anexo.incrustado?.pagina ?? "anexo"}-${indice}`}`,
        grupo,
        titulo: etiquetaAnexo(anexo),
        destino,
        pdf: destino.accion === "pagina" ? (destino.pdf ?? examen.pdf) : undefined,
      });
    }
  });

  if (!documentos.some((d) => d.grupo === "criterios") && pregunta.fuenteRubrica) {
    const fuente = pregunta.fuenteRubrica;
    const pagina = paginasDe(pregunta, idioma, "rubrica")[0] ?? 1;
    const destino: Destino = fuente.incrustado
      ? { accion: "pagina", pagina, nota: `en este PDF, p. ${pagina}` }
      : fuente.pdf
        ? { accion: "pagina", pdf: fuente.pdf, pagina, nota: "" }
        : { accion: "enlace", href: fuente.url, nota: "" };
    documentos.push({
      id: "fuente-rubrica",
      grupo: "criterios",
      titulo: "Criterios de corrección",
      destino,
      pdf: destino.accion === "pagina" ? (destino.pdf ?? examen.pdf) : undefined,
    });
  }

  const solucionesYaSituadas = new Set<number>();
  solucionesDe(pregunta).forEach((solucion, indice) => {
    const pagina = solucion.paginas[idiomaPreferido(Object.keys(solucion.paginas), idioma)] ?? 1;
    const destino: Destino = solucion.incrustado
      ? { accion: "pagina", pagina, nota: `en este PDF, p. ${pagina}` }
      : solucion.pdf
        ? { accion: "pagina", pdf: solucion.pdf, pagina, nota: "" }
        : solucion.url
          ? { accion: "enlace", href: solucion.url, nota: "" }
          : { accion: "ninguna", nota: "documento no disponible" };
    const pdf = destino.accion === "pagina" ? (destino.pdf ?? examen.pdf) : undefined;
    const titulo = etiquetaSolucion(solucion);
    const indiceExistente = documentos.findIndex(
      (documento) =>
        documento.grupo === "soluciones" &&
        ((pdf && documento.pdf === pdf) ||
          (destino.accion === "enlace" &&
            documento.destino.accion === "enlace" &&
            documento.destino.href === destino.href)),
    );
    const existente = documentos[indiceExistente];
    if (existente) {
      if (!solucionesYaSituadas.has(indiceExistente)) {
        documentos[indiceExistente] = { ...existente, titulo, destino, pdf };
        solucionesYaSituadas.add(indiceExistente);
      }
      return;
    }
    documentos.push({
      id: `fuente-solucion-${indice}`,
      grupo: "soluciones",
      titulo,
      destino,
      pdf,
    });
    solucionesYaSituadas.add(documentos.length - 1);
  });
  return documentos;
}

function documentoDelSalto(
  documentos: readonly Documento[],
  pregunta: Pregunta,
  idioma: string,
  salto: Salto,
) {
  const pdf = salto.pdf ?? pregunta.examen.pdf;
  const candidatos = documentos.filter(
    (documento) => documento.destino.accion === "pagina" && documento.pdf === pdf,
  );
  const tipo =
    salto.grupo ??
    (paginasDe(pregunta, idioma, "rubrica").includes(salto.pagina)
      ? "criterios"
      : paginasDe(pregunta, idioma, "solucion").includes(salto.pagina)
        ? "soluciones"
        : undefined);
  if (tipo) {
    const candidato = candidatos.find((documento) => documento.grupo === tipo);
    if (candidato) return candidato;
  }
  if (salto.pdf) {
    const propio = candidatos.find((documento) => documento.grupo !== "examen");
    if (propio) return propio;
  }
  const incrustado = candidatos
    .filter(
      (documento) =>
        documento.grupo !== "examen" &&
        documento.destino.accion === "pagina" &&
        !documento.destino.pdf &&
        documento.destino.pagina <= salto.pagina,
    )
    .sort((a, b) =>
      a.destino.accion === "pagina" && b.destino.accion === "pagina"
        ? b.destino.pagina - a.destino.pagina
        : 0,
    )[0];
  return incrustado ?? candidatos[0] ?? documentos[0];
}

export function DocumentosPregunta({ pregunta, idioma, recurso, lector, salto }: Props) {
  const id = useId();
  const documentos = useMemo(() => documentosDe(pregunta, idioma), [pregunta, idioma]);
  const saltosIniciales = useMemo(() => {
    const saltos = new Map<string, Salto>();
    for (const documento of documentos) {
      if (documento.destino.accion === "pagina")
        saltos.set(documento.id, { pagina: documento.destino.pagina, vez: 0 });
    }
    return saltos;
  }, [documentos]);
  const [activo, setActivo] = useState<Grupo | null>(null);
  const [seleccionado, setSeleccionado] = useState<string>();
  const [saltoAplicado, setSaltoAplicado] = useState<Salto>();
  const secciones = useRef<Record<Grupo, HTMLDivElement | null>>({
    examen: null,
    criterios: null,
    soluciones: null,
  });

  useEffect(() => {
    if (!salto) return;
    const documento = documentoDelSalto(documentos, pregunta, idioma, salto);
    if (!documento) return;
    setActivo(documento.grupo);
    setSeleccionado(documento.id);
    setSaltoAplicado(salto);
  }, [salto, pregunta, idioma, documentos]);

  useEffect(() => {
    if (saltoAplicado && activo) {
      secciones.current[activo]?.scrollIntoView?.({ behavior: "auto", block: "start" });
    }
  }, [activo, saltoAplicado]);

  return (
    <section aria-label="Documentos originales" className="mt-8 space-y-2.5 pb-5">
      <p className="etiqueta-mono px-1">Documentos originales</p>
      {GRUPOS.map((grupo) => {
        const lista = documentos.filter((documento) => documento.grupo === grupo.id);
        const abierto = activo === grupo.id;
        const elegido = lista.find((documento) => documento.id === seleccionado) ?? lista[0];
        return (
          <div
            key={grupo.id}
            ref={(elemento) => {
              secciones.current[grupo.id] = elemento;
            }}
            className="overflow-hidden rounded-2xl border border-regla bg-papel-2"
          >
            <h3>
              <button
                type="button"
                aria-label={grupo.titulo}
                aria-expanded={abierto}
                aria-controls={`${id}-${grupo.id}`}
                className="flex w-full cursor-pointer items-center px-5 py-4 text-left font-titulo text-lg font-semibold text-tinta hover:text-rojo"
                onClick={() => {
                  setActivo(abierto ? null : grupo.id);
                  setSeleccionado(lista[0]?.id);
                  setSaltoAplicado(undefined);
                }}
              >
                <span aria-hidden className="mr-3 font-mono text-sm text-rojo">
                  {abierto ? "−" : "+"}
                </span>
                {grupo.titulo}
                <span className="ml-3 font-mono text-[11px] font-normal text-suave">
                  {lista.length
                    ? `${lista.length} ${lista.length === 1 ? "documento" : "documentos"}`
                    : "sin documento"}
                </span>
              </button>
            </h3>
            <div
              id={`${id}-${grupo.id}`}
              hidden={!abierto}
              className="border-t border-regla px-3 pb-3 pt-3 sm:px-4 sm:pb-4"
            >
              {abierto && (
                <>
                  {!elegido && <p className="px-2 py-4 text-sm text-suave">{grupo.vacio}</p>}
                  {lista.length > 1 && (
                    <nav aria-label={`Documentos de ${grupo.titulo}`} className="mb-3 flex flex-wrap gap-1.5">
                      {lista.map((documento) => (
                        <button
                          type="button"
                          key={documento.id}
                          aria-pressed={elegido?.id === documento.id}
                          onClick={() => {
                            setSeleccionado(documento.id);
                            setSaltoAplicado(undefined);
                          }}
                          className={`cursor-pointer rounded-full border px-3 py-1 font-mono text-[11px] ${elegido?.id === documento.id ? "border-tinta bg-tinta text-papel" : "border-regla bg-papel text-suave hover:border-tinta hover:text-tinta"}`}
                        >
                          {documento.titulo}
                        </button>
                      ))}
                    </nav>
                  )}
                  {elegido?.destino.accion === "pagina" && elegido.pdf && (
                    <VisorPdf
                      key={elegido.id}
                      lector={lector}
                      url={recurso(elegido.pdf)}
                      ancla={grupo.id === "examen" ? pregunta.anclas[idioma] : undefined}
                      salto={saltoAplicado ?? saltosIniciales.get(elegido.id)}
                    />
                  )}
                  {elegido?.destino.accion === "enlace" && (
                    <p className="px-2 py-4 text-sm text-suave">
                      <a
                        href={elegido.destino.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-tinta underline underline-offset-2 hover:text-rojo"
                      >
                        Abrir {elegido.titulo.toLowerCase()} en el origen ↗
                      </a>
                      {elegido.destino.nota && (
                        <span className="ml-2 font-mono text-xs">{elegido.destino.nota}</span>
                      )}
                    </p>
                  )}
                  {elegido?.destino.accion === "ninguna" && (
                    <p className="px-2 py-4 font-mono text-xs text-suave">
                      {elegido.titulo}: {elegido.destino.nota}.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </section>
  );
}
