import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Cabecera } from "~/componentes/Cabecera";
import { DetallePregunta } from "~/componentes/DetallePregunta";
import { Cargando, ErrorDeCarga } from "~/componentes/Estados";
import { PanelFacetas } from "~/componentes/PanelFacetas";
import { TarjetaPregunta } from "~/componentes/TarjetaPregunta";
import { type Salto, VisorPdf } from "~/componentes/VisorPdf";
import { Zoom } from "~/componentes/Zoom";
import {
  alternar,
  type ClaveFaceta,
  calcularFaceta,
  FACETAS,
  filtrar,
  filtrosActivos,
  indexar,
  limpiar,
  vecina,
} from "~/dominio/banco";
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
  const [expandidas, setExpandidas] = useState<ReadonlySet<ClaveFaceta>>(new Set());
  const [facetasAbiertas, setFacetasAbiertas] = useState(false);
  const [detalleAbierto, setDetalleAbierto] = useState(false);
  const [ampliada, setAmpliada] = useState<string | null>(null);
  const [salto, setSalto] = useState<Salto & { readonly pregunta: string }>();
  const [consulta, setConsulta] = useState(estado.consulta);
  const buscador = useRef<HTMLInputElement>(null);
  const lista = useRef<HTMLElement>(null);

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
  const facetas = useMemo(
    () =>
      FACETAS.map((f) =>
        calcularFaceta(f, preguntas, estado.filtros, estado.consulta, expandidas.has(f.clave)),
      ),
    [preguntas, estado.filtros, estado.consulta, expandidas],
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
      const escribiendo = ev.target instanceof HTMLElement && ev.target.matches("input, textarea");
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
  const ancla = seleccionada
    ? (seleccionada.anclas[idioma] ?? Object.values(seleccionada.anclas)[0])
    : undefined;
  const activos = filtrosActivos(estado.filtros);

  return (
    <div className="grid h-dvh grid-cols-[250px_380px_1fr] grid-rows-[auto_1fr] overflow-hidden max-[1100px]:grid-cols-[330px_1fr] max-md:grid-cols-1">
      <div className="col-span-full">
        <Cabecera>
          <button
            type="button"
            onClick={() => setFacetasAbiertas(!facetasAbiertas)}
            className="hidden cursor-pointer border-[1.5px] border-tinta px-2 py-1 font-mono text-xs max-[1100px]:inline-block"
          >
            Filtros
          </button>
          <label className="relative max-w-140 flex-1">
            <span className="sr-only">Buscar</span>
            <span aria-hidden className="absolute top-1.25 left-2.5 text-lg text-suave">
              ⌕
            </span>
            <input
              ref={buscador}
              type="search"
              value={consulta}
              onChange={(ev) => setConsulta(ev.target.value)}
              placeholder="Buscar en enunciados, apartados y textos…"
              autoComplete="off"
              className="w-full border-[1.5px] border-tinta bg-papel py-1.75 pr-2.5 pl-8 text-[15px] outline-none focus:border-rojo"
            />
            <kbd className="absolute top-2 right-2 max-md:hidden">/</kbd>
          </label>
          <span className="font-mono text-[11px] whitespace-nowrap text-suave max-[1300px]:hidden">
            <kbd>↑</kbd>
            <kbd>↓</kbd> navegar · <kbd>←</kbd>
            <kbd>→</kbd> página del PDF
          </span>
        </Cabecera>
      </div>

      <aside
        aria-label="Filtros"
        className={`overflow-y-auto border-r-[1.5px] border-tinta max-[1100px]:fixed max-[1100px]:inset-y-0 max-[1100px]:top-14 max-[1100px]:left-0 max-[1100px]:z-5 max-[1100px]:w-70 max-[1100px]:bg-papel max-[1100px]:shadow-[10px_0_30px_-10px_rgba(0,0,0,.4)] ${facetasAbiertas ? "" : "max-[1100px]:hidden"}`}
      >
        <PanelFacetas
          facetas={facetas}
          onAlternar={(clave, valor) =>
            actualizar((e) => ({ ...e, filtros: alternar(e.filtros, clave, valor) }))
          }
          onLimpiar={(clave) => actualizar((e) => ({ ...e, filtros: limpiar(e.filtros, clave) }))}
          onExpandir={(clave) => setExpandidas(new Set([...expandidas, clave]))}
        />
      </aside>

      <section
        ref={lista}
        aria-label="Preguntas"
        className="overflow-y-auto border-r-[1.5px] border-tinta max-md:border-r-0"
      >
        <div className="sticky top-0 z-1 flex justify-between gap-2 border-b border-regla bg-papel px-3.5 py-2 font-mono text-xs text-suave">
          <span className="whitespace-nowrap" aria-live="polite">
            {visibles.length} de {preguntas.length} preguntas
          </span>
          <span className="flex flex-wrap justify-end gap-1">
            {activos.map((a) => (
              <button
                type="button"
                key={`${a.clave}:${a.valor}`}
                title="Quitar filtro"
                onClick={() => actualizar((e) => ({ ...e, filtros: alternar(e.filtros, a.clave, a.valor) }))}
                className="cursor-pointer border border-tinta px-1.5 text-[11px] text-tinta hover:border-rojo hover:bg-rojo hover:text-papel"
              >
                {a.nombre} ×
              </button>
            ))}
          </span>
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
        className={`grid overflow-hidden min-[1500px]:grid-cols-2 max-[1500px]:grid-rows-[minmax(0,1.1fr)_minmax(0,1fr)] max-md:fixed max-md:inset-0 max-md:z-6 max-md:bg-papel ${detalleAbierto ? "" : "max-md:hidden"}`}
      >
        {seleccionada ? (
          <>
            <DetallePregunta
              pregunta={seleccionada}
              idioma={idioma}
              recurso={datos.recurso}
              onIdioma={(lang) => actualizar((e) => ({ ...e, idioma: lang }))}
              onAmpliar={setAmpliada}
              onCerrar={() => setDetalleAbierto(false)}
              onIrAPagina={(pagina) =>
                setSalto({ pregunta: seleccionada.id, pagina, vez: (salto?.vez ?? 0) + 1 })
              }
            />
            <VisorPdf
              lector={pdf}
              url={datos.recurso(seleccionada.examen.pdf)}
              ancla={ancla}
              salto={salto?.pregunta === seleccionada.id ? salto : undefined}
            />
          </>
        ) : (
          <p className="col-span-full px-5 py-10 text-center text-suave italic">
            Elige una pregunta de la lista.
          </p>
        )}
      </main>
      <Zoom src={ampliada} onCerrar={() => setAmpliada(null)} />
    </div>
  );
}
