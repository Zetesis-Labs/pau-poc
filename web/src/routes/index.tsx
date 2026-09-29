import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Cabecera } from "~/componentes/Cabecera";
import { DetallePregunta } from "~/componentes/DetallePregunta";
import { DocumentosPregunta } from "~/componentes/DocumentosPregunta";
import { Cargando, ErrorDeCarga } from "~/componentes/Estados";
import { ModalFiltros } from "~/componentes/ModalFiltros";
import { TarjetaPregunta } from "~/componentes/TarjetaPregunta";
import type { Salto } from "~/componentes/VisorPdf";
import { Zoom } from "~/componentes/Zoom";
import { alternar, filtrar, filtrosActivos, indexar, vecina } from "~/dominio/banco";
import { type EstadoBanco, escribirEstado, leerEstado, validarBusqueda } from "~/dominio/busqueda";
import { idiomaPreferido } from "~/dominio/textos";

export const Route = createFileRoute("/")({
  validateSearch: validarBusqueda,
  ssr: false,
  loader: async ({ context }) => indexar((await context.datos.banco()).preguntas),
  pendingComponent: () => <Cargando que="el banco de preguntas" />,
  errorComponent: ({ error }) => <ErrorDeCarga error={error} />,
  component: Banco,
});

const ESPERA_BUSQUEDA_MS = 150;
const ANCHO_MOVIL = 768;

function Banco() {
  const preguntas = Route.useLoaderData();
  const { datos, pdf } = Route.useRouteContext();
  const busqueda = Route.useSearch();
  const navegar = Route.useNavigate();
  const estado = useMemo(() => leerEstado(busqueda), [busqueda]);
  const [facetasAbiertas, setFacetasAbiertas] = useState(false);
  const [detalleAbierto, setDetalleAbierto] = useState(false);
  const [ampliada, setAmpliada] = useState<string | null>(null);
  const [salto, setSalto] = useState<Salto & { readonly pregunta: string; readonly pdf?: string }>();
  const [consulta, setConsulta] = useState(estado.consulta);
  const buscador = useRef<HTMLInputElement>(null);
  const lista = useRef<HTMLElement>(null);
  const detalle = useRef<HTMLElement>(null);

  const actualizar = useCallback(
    (cambio: (e: EstadoBanco) => EstadoBanco) =>
      navegar({ search: (previa) => escribirEstado(cambio(leerEstado(previa))), replace: true }),
    [navegar],
  );

  useEffect(() => {
    if (consulta === estado.consulta) return;
    const temporizador = setTimeout(() => actualizar((e) => ({ ...e, consulta })), ESPERA_BUSQUEDA_MS);
    return () => clearTimeout(temporizador);
  }, [consulta, estado.consulta, actualizar]);

  const visibles = useMemo(
    () => filtrar(preguntas, estado.filtros, estado.consulta),
    [preguntas, estado.filtros, estado.consulta],
  );
  const seleccionada = visibles.find((p) => p.pregunta.id === estado.seleccion)?.pregunta;
  const ids = useMemo(() => visibles.map((p) => p.pregunta.id), [visibles]);

  const elegir = useCallback(
    (id: string) => {
      setDetalleAbierto(true);
      actualizar((e) => ({ ...e, seleccion: id }));
    },
    [actualizar],
  );

  useEffect(() => {
    if (!detalleAbierto || window.innerWidth >= ANCHO_MOVIL) return;
    detalle.current?.querySelector("article")?.scrollTo({ top: 0 });
    detalle.current?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
  }, [detalleAbierto]);

  useEffect(() => {
    if (!seleccionada && ids[0] && window.innerWidth > ANCHO_MOVIL)
      actualizar((e) => ({ ...e, seleccion: ids[0] }));
  }, [seleccionada, ids, actualizar]);

  useEffect(() => {
    if (!seleccionada) return;
    lista.current
      ?.querySelector(`[data-id="${CSS.escape(seleccionada.id)}"]`)
      ?.scrollIntoView({ block: "nearest" });
  }, [seleccionada]);

  useEffect(() => {
    const teclas = (ev: KeyboardEvent) => {
      if (document.querySelector("dialog[open]")) return;
      const escribiendo =
        ev.target instanceof HTMLElement &&
        ev.target.closest(
          "input, textarea, select, button, a, summary, [contenteditable], [data-visor-pdf]",
        ) !== null;
      if (ev.key === "/" && !escribiendo) {
        ev.preventDefault();
        buscador.current?.focus();
      } else if (ev.key === "Escape" && escribiendo) {
        buscador.current?.blur();
      } else if (!escribiendo && ["ArrowDown", "ArrowUp", "j", "k"].includes(ev.key)) {
        ev.preventDefault();
        const siguiente = vecina(ids, estado.seleccion, ev.key === "ArrowDown" || ev.key === "j" ? 1 : -1);
        if (siguiente) actualizar((e) => ({ ...e, seleccion: siguiente }));
      }
    };
    window.addEventListener("keydown", teclas);
    return () => window.removeEventListener("keydown", teclas);
  }, [ids, estado.seleccion, actualizar]);

  const idioma = seleccionada ? idiomaPreferido(seleccionada.idiomas, estado.idioma) : "es";
  const activos = filtrosActivos(estado.filtros);

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <Cabecera>
        <label className="relative min-w-0 flex-1">
          <span className="sr-only">Buscar preguntas</span>
          <span aria-hidden="true" className="absolute top-2 left-4 text-lg text-suave">
            ⌕
          </span>
          <input
            ref={buscador}
            type="search"
            value={consulta}
            onChange={(ev) => setConsulta(ev.target.value)}
            placeholder="Buscar preguntas…"
            autoComplete="off"
            className="w-full rounded-full border border-regla bg-papel-2 py-2.5 pr-8 pl-10 text-[15px] outline-none focus:border-rojo"
          />
        </label>
        <button
          type="button"
          onClick={() => setFacetasAbiertas(true)}
          aria-haspopup="dialog"
          aria-expanded={facetasAbiertas}
          className="flex shrink-0 cursor-pointer items-center gap-2 rounded-full border border-regla px-4 py-2.5 font-mono text-xs hover:bg-papel-2"
        >
          Filtros{" "}
          {activos.length > 0 && (
            <span className="rounded-full bg-rojo px-1.5 text-papel">{activos.length}</span>
          )}
        </button>
      </Cabecera>
      <div className="grid min-h-0 flex-1 grid-cols-[340px_minmax(0,1fr)] gap-5 px-5 pb-5 max-lg:grid-cols-[300px_minmax(0,1fr)] max-md:grid-cols-1 max-md:px-3 max-md:pb-3">
        <section
          ref={lista}
          aria-label="Preguntas"
          className="min-h-0 overflow-y-auto rounded-3xl bg-papel-2/50 p-2"
        >
          <div className="sticky top-0 z-1 rounded-2xl bg-papel px-3 py-3 font-mono text-xs text-suave">
            <span aria-live="polite">
              {visibles.length} de {preguntas.length} preguntas
            </span>
            {activos.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {activos.map((a) => (
                  <button
                    type="button"
                    key={`${a.clave}:${a.valor}`}
                    aria-label={`Quitar filtro ${a.nombre}`}
                    onClick={() =>
                      actualizar((e) => ({ ...e, filtros: alternar(e.filtros, a.clave, a.valor) }))
                    }
                    className="cursor-pointer rounded-full bg-papel-2 px-2.5 py-1 text-[11px] text-tinta hover:bg-papel-3"
                  >
                    {a.nombre} ×
                  </button>
                ))}
              </div>
            )}
          </div>
          {visibles.length ? (
            visibles.map(({ pregunta }) => (
              <TarjetaPregunta
                key={pregunta.id}
                pregunta={pregunta}
                seleccionada={pregunta.id === seleccionada?.id}
                idioma={estado.idioma}
                consulta={estado.consulta}
                onElegir={elegir}
              />
            ))
          ) : (
            <p className="px-5 py-10 text-center text-suave italic">Ninguna pregunta cumple estos filtros.</p>
          )}
        </section>
        <main
          ref={detalle}
          className={`min-h-0 min-w-0 overflow-hidden rounded-3xl bg-papel-2/40 max-md:fixed max-md:inset-0 max-md:z-6 max-md:rounded-none max-md:bg-papel ${detalleAbierto ? "" : "max-md:hidden"}`}
        >
          {seleccionada ? (
            <DetallePregunta
              key={seleccionada.id}
              pregunta={seleccionada}
              idioma={idioma}
              recurso={datos.recurso}
              onIdioma={(lang) => actualizar((e) => ({ ...e, idioma: lang }))}
              onAmpliar={setAmpliada}
              onCerrar={() => setDetalleAbierto(false)}
              onIrAPagina={(pagina, documento, grupo) =>
                setSalto((previo) => ({
                  pregunta: seleccionada.id,
                  pagina,
                  pdf: documento,
                  grupo,
                  vez: (previo?.vez ?? 0) + 1,
                }))
              }
            >
              <DocumentosPregunta
                pregunta={seleccionada}
                idioma={idioma}
                recurso={datos.recurso}
                lector={pdf}
                salto={salto?.pregunta === seleccionada.id ? salto : undefined}
              />
            </DetallePregunta>
          ) : (
            <p className="px-5 py-16 text-center text-suave italic">Elige una pregunta de la lista.</p>
          )}
        </main>
      </div>
      <ModalFiltros
        abierto={facetasAbiertas}
        preguntas={preguntas}
        filtros={estado.filtros}
        consulta={estado.consulta}
        onAplicar={(filtros) => actualizar((e) => ({ ...e, filtros }))}
        onCerrar={() => setFacetasAbiertas(false)}
      />
      <Zoom src={ampliada} onCerrar={() => setAmpliada(null)} />
    </div>
  );
}
