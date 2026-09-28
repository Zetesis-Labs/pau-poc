import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Cabecera } from "~/componentes/Cabecera";
import { Cargando, ErrorDeCarga } from "~/componentes/Estados";
import { destinoAnexo, etiquetaAnexo, textoCorto } from "~/dominio/anexos";
import { nombreDeExamen } from "~/dominio/banco";
import {
  cumple,
  type Estado,
  escribirFiltrosCatalogo,
  estadoDe,
  type FiltrosCatalogo,
  formatoBytes,
  intensidad,
  kpis,
  leerFiltrosCatalogo,
  matriz,
  NOMBRE_ESTADO,
  NOMBRE_TIPO,
  ordenar,
  paginar,
  TIPOS,
  unicos,
} from "~/dominio/catalogo";
import { nombreConvocatoria } from "~/dominio/textos";
import type { Documento } from "~/dominio/tipos";

export const Route = createFileRoute("/catalogo")({
  validateSearch: (crudo) => escribirFiltrosCatalogo(leerFiltrosCatalogo(crudo)),
  ssr: false,
  loader: ({ context }) => context.datos.catalogo(),
  pendingComponent: () => <Cargando que="el catálogo" />,
  errorComponent: ({ error }) => <ErrorDeCarga error={error} />,
  head: () => ({ meta: [{ title: "PAU · catálogo de exámenes" }] }),
  component: VistaCatalogo,
});

const POR_PAGINA = 60;
const control =
  "w-full border-[1.5px] border-tinta bg-papel px-2.5 py-1.75 font-serif text-sm normal-case tracking-normal text-tinta";
const botonMono =
  "cursor-pointer border-[1.5px] border-tinta px-2.5 py-1.5 font-mono text-xs uppercase tracking-wider hover:bg-tinta hover:text-papel disabled:opacity-35 disabled:hover:bg-transparent disabled:hover:text-tinta";

function VistaCatalogo() {
  const catalogo = Route.useLoaderData();
  const { datos } = Route.useRouteContext();
  const filtros = leerFiltrosCatalogo(Route.useSearch());
  const navegar = Route.useNavigate();
  const docs = catalogo.documentos;
  const lista = useRef<HTMLDivElement>(null);
  const [texto, setTexto] = useState(filtros.texto ?? "");

  const cambiar = (cambio: Partial<FiltrosCatalogo>) =>
    navegar({
      search: (previa) =>
        escribirFiltrosCatalogo({ ...leerFiltrosCatalogo(previa), pagina: undefined, ...cambio }),
      replace: true,
    });

  useEffect(() => {
    if (texto === (filtros.texto ?? "")) return;
    const t = setTimeout(() => cambiar({ texto }), 150);
    return () => clearTimeout(t);
  });

  const filtrados = useMemo(() => docs.filter((d) => cumple(d, filtros)), [docs, filtros]);
  const resumen = kpis(filtrados);
  const cobertura = useMemo(() => matriz(docs, filtros), [docs, filtros]);
  const pagina = paginar(ordenar(filtrados), (filtros.pagina ?? 1) - 1, POR_PAGINA);

  const selectores: {
    campo: "region" | "asignatura" | "anio" | "convocatoria" | "fuente";
    titulo: string;
    valores: string[];
    nombre?: (v: string) => string;
  }[] = [
    { campo: "region", titulo: "Región", valores: unicos(docs.map((d) => d.region)) },
    { campo: "asignatura", titulo: "Asignatura", valores: unicos(docs.map((d) => d.asignatura)) },
    {
      campo: "anio",
      titulo: "Año",
      valores: unicos(docs.flatMap((d) => (d.anio ? [String(d.anio)] : []))).reverse(),
    },
    {
      campo: "convocatoria",
      titulo: "Convocatoria",
      valores: unicos(docs.map((d) => d.convocatoria)),
      nombre: nombreConvocatoria,
    },
    { campo: "fuente", titulo: "Fuente", valores: unicos(docs.map((d) => d.fuente)) },
  ];

  const exportar = () => {
    const blob = new Blob([JSON.stringify(filtrados, null, 1)], { type: "application/json" });
    const enlace = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(blob),
      download: "catalogo-filtrado.json",
    });
    enlace.click();
    URL.revokeObjectURL(enlace.href);
  };

  return (
    <div className="min-h-dvh bg-[repeating-linear-gradient(to_bottom,transparent_0_31px,color-mix(in_srgb,var(--regla)_45%,transparent)_31px_32px)]">
      <Cabecera />
      <main className="mx-auto max-w-[1320px] px-6 pt-10 pb-20 max-md:px-4">
        <header className="grid grid-cols-[1fr_auto] items-end gap-6 border-b-[3px] border-double border-tinta pb-5 max-md:grid-cols-1">
          <div>
            <span className="mb-3.5 inline-block -rotate-3 border-[1.5px] border-rojo px-2.5 py-1.5 font-mono text-[11px] tracking-[0.18em] text-rojo uppercase">
              Archivo · Pruebas de acceso
            </span>
            <h1 className="m-0 font-titulo text-[clamp(44px,7vw,92px)] leading-[.9] font-extrabold tracking-[-0.03em]">
              Exámenes <em className="font-light text-rojo">PAU</em>
            </h1>
            <p className="mt-2.5 max-w-[60ch] text-suave">
              Madrid, Comunidad Valenciana y País Vasco: enunciados, soluciones, criterios y modelos de seis
              fuentes. Solo los exámenes procesados tienen su PDF aquí; el resto enlaza a su origen. Generado
              el {new Date(catalogo.generado).toLocaleString("es")}.
            </p>
          </div>
          <button type="button" className={botonMono} onClick={exportar} title="Descargar el JSON filtrado">
            JSON filtrado
          </button>
        </header>

        <dl className="my-7 grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] border-[1.5px] border-tinta bg-papel">
          {[
            [resumen.documentos.toLocaleString("es"), "documentos"],
            [resumen.procesados.toLocaleString("es"), "con preguntas extraídas"],
            [formatoBytes(resumen.bytesDescargados), "descargado en origen"],
            [resumen.soloEnlace.toLocaleString("es"), "solo enlace"],
            [String(resumen.asignaturas), "asignaturas"],
            [resumen.anios ? `${resumen.anios[0]}–${String(resumen.anios[1]).slice(2)}` : "—", "años"],
            [String(resumen.fallidos), "descargas fallidas"],
          ].map(([valor, etiqueta]) => (
            <div key={etiqueta} className="border-r border-regla px-4.5 py-4 last:border-r-0">
              <dd
                className={`font-titulo text-[34px] leading-none font-semibold tabular-nums ${etiqueta === "descargas fallidas" && resumen.fallidos ? "text-rojo" : ""}`}
              >
                {valor}
              </dd>
              <dt className="font-mono text-[11px] tracking-widest text-suave uppercase">{etiqueta}</dt>
            </div>
          ))}
        </dl>

        <div className="mb-3.5 grid grid-cols-[2fr_repeat(6,minmax(0,1fr))] gap-2.5 max-lg:grid-cols-2">
          <label className="etiqueta-mono flex flex-col gap-1 max-lg:col-span-full">
            Buscar
            <input
              type="search"
              className={control}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="asignatura, título, variante…"
            />
          </label>
          {selectores.map((s) => (
            <label key={s.campo} className="etiqueta-mono flex min-w-0 flex-col gap-1">
              {s.titulo}
              <select
                className={control}
                value={filtros[s.campo] ?? ""}
                onChange={(e) => cambiar({ [s.campo]: e.target.value || undefined })}
              >
                <option value="">Todos</option>
                {s.valores.map((v) => (
                  <option key={v} value={v}>
                    {s.nombre ? s.nombre(v) : v}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <label className="etiqueta-mono flex min-w-0 flex-col gap-1">
            Estado
            <select
              className={control}
              value={filtros.estado ?? ""}
              onChange={(e) => cambiar({ estado: (e.target.value || undefined) as Estado | undefined })}
            >
              <option value="">Todos</option>
              {(Object.keys(NOMBRE_ESTADO) as Estado[]).map((e) => (
                <option key={e} value={e}>
                  {NOMBRE_ESTADO[e]}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mb-6 flex flex-wrap gap-1.5">
          {TIPOS.map((t) => {
            const oculto = filtros.ocultos?.includes(t) ?? false;
            return (
              <button
                type="button"
                key={t}
                aria-pressed={!oculto}
                onClick={() =>
                  cambiar({
                    ocultos: oculto
                      ? filtros.ocultos?.filter((o) => o !== t)
                      : [...(filtros.ocultos ?? []), t],
                  })
                }
                className={`cursor-pointer border px-2 py-0.75 font-mono text-xs ${oculto ? "border-dashed border-suave" : "border-tinta bg-tinta text-papel"}`}
              >
                {NOMBRE_TIPO[t]} <span>{docs.filter((d) => d.tipo === t).length}</span>
              </button>
            );
          })}
        </div>

        <section className="mt-8">
          <h2 className="font-titulo text-[26px] font-semibold">
            Cobertura
            <small className="ml-2.5 font-mono text-xs font-normal text-suave">
              {cobertura.asignaturas.length} asignaturas × {cobertura.anios.length} años · máx.{" "}
              {cobertura.maximo}
            </small>
          </h2>
          <p className="mb-3.5 text-sm text-suave">
            Documentos por asignatura y año con los filtros actuales. Pulsa una celda para ver sus documentos.
          </p>
          <div className="overflow-x-auto border-[1.5px] border-tinta bg-papel">
            <table className="w-full border-collapse font-mono text-xs">
              <thead>
                <tr>
                  <th className="sticky left-0 bg-papel-2" />
                  {cobertura.anios.map((a) => (
                    <th
                      key={a}
                      className="sticky top-0 border border-regla bg-papel-2 px-1 py-1.5 font-medium"
                    >
                      '{String(a).slice(2)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cobertura.asignaturas.map((asignatura) => (
                  <tr key={asignatura}>
                    <th className="sticky left-0 border border-regla bg-papel px-2.5 py-1 text-left font-serif text-[13px] font-semibold whitespace-nowrap">
                      {asignatura}
                    </th>
                    {cobertura.anios.map((anio) => {
                      const n = cobertura.cuenta(asignatura, anio);
                      const p = intensidad(n, cobertura.maximo);
                      const elegida = filtros.asignatura === asignatura && filtros.anio === String(anio);
                      return (
                        <td key={anio} className="border border-regla p-0">
                          <button
                            type="button"
                            title={`${asignatura} · ${anio}: ${n}`}
                            onClick={() => {
                              cambiar(
                                elegida
                                  ? { asignatura: undefined, anio: undefined }
                                  : { asignatura, anio: String(anio) },
                              );
                              lista.current?.scrollIntoView({ behavior: "smooth" });
                            }}
                            className={`h-7 w-full min-w-8.5 cursor-pointer text-[11px] hover:outline-2 hover:-outline-offset-2 hover:outline-rojo ${elegida ? "outline-2 -outline-offset-2 outline-rojo" : ""}`}
                            style={{
                              background: n
                                ? `color-mix(in srgb, var(--tinta) ${p}%, var(--papel-2))`
                                : "transparent",
                              color: n / cobertura.maximo > 0.45 ? "var(--papel)" : "var(--tinta)",
                            }}
                          >
                            {n || ""}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-8" ref={lista}>
          <h2 className="font-titulo text-[26px] font-semibold">
            Documentos
            <small className="ml-2.5 font-mono text-xs font-normal text-suave">
              {filtrados.length.toLocaleString("es")} resultados
            </small>
          </h2>
          <div className="border-t-[1.5px] border-tinta">
            {pagina.elementos.length ? (
              pagina.elementos.map((d) => <Fila key={d.id} documento={d} recurso={datos.recurso} />)
            ) : (
              <p className="p-10 text-center text-suave italic">Ningún documento con estos filtros.</p>
            )}
          </div>
          {pagina.paginas > 1 && (
            <nav className="mt-4.5 flex items-center justify-center gap-2.5 font-mono text-sm">
              <button
                type="button"
                className={botonMono}
                disabled={pagina.pagina === 0}
                onClick={() => cambiar({ pagina: pagina.pagina })}
              >
                ← anterior
              </button>
              <span>
                {pagina.pagina + 1} / {pagina.paginas}
              </span>
              <button
                type="button"
                className={botonMono}
                disabled={pagina.pagina >= pagina.paginas - 1}
                onClick={() => cambiar({ pagina: pagina.pagina + 2 })}
              >
                siguiente →
              </button>
            </nav>
          )}
        </section>
      </main>
    </div>
  );
}

const COLOR_TIPO: Record<string, string> = {
  examen: "text-tinta",
  solucion: "text-verde",
  criterios: "text-azul",
  modelo: "text-rojo",
  video: "text-suave border-dashed",
  audio: "text-suave border-dashed",
};

const NOMBRE_FORMATO: Record<string, string> = {
  youtube: "YouTube",
  audio: "Audio",
  web: "Página",
  drive: "Drive",
  gdoc: "Google Doc",
};

function Fila({ documento: d, recurso }: { documento: Documento; recurso: (ruta: string) => string }) {
  const enlace =
    "font-mono text-xs font-medium whitespace-nowrap border-b-[1.5px] border-rojo pb-px hover:text-rojo";
  return (
    <div className="grid grid-cols-[64px_1fr_auto] items-center gap-4 border-b border-regla px-1 py-3 hover:bg-papel-2/70 max-md:grid-cols-[48px_1fr]">
      <div className="font-titulo text-[22px] leading-none font-semibold tabular-nums">{d.anio ?? "—"}</div>
      <div>
        <div className="font-semibold">
          {d.asignatura}{" "}
          <span
            className={`border border-current px-1.5 py-1 font-mono text-[10px] leading-none font-medium tracking-[0.12em] uppercase ${COLOR_TIPO[d.tipo] ?? ""}`}
          >
            {NOMBRE_TIPO[d.tipo] ?? d.tipo}
          </span>
        </div>
        <div className="mt-0.5 flex flex-wrap gap-x-3 gap-y-1 font-mono text-xs text-suave">
          <span>{d.region}</span>
          <span>{nombreConvocatoria(d.convocatoria)}</span>
          {d.variante && <span>{d.variante}</span>}
          <span>{d.fuente}</span>
          <span>{d.titulo}</span>
          {d.bytes ? <span>{(d.bytes / 1024).toFixed(0)} KB</span> : null}
        </div>
      </div>
      <div className="flex flex-wrap justify-end gap-2 max-md:col-start-2 max-md:justify-start">
        {d.procesado && (
          <Link className={enlace} to="/" search={{ examen: nombreDeExamen(d) }}>
            Preguntas
          </Link>
        )}
        {d.pdf && (
          <a className={enlace} href={recurso(d.pdf)} target="_blank" rel="noopener">
            PDF
          </a>
        )}
        {(d.anexos ?? []).map((a) => {
          const destino = destinoAnexo(a, d);
          const titulo = [etiquetaAnexo(a), destino.nota].filter(Boolean).join(" · ");
          const texto = textoCorto(a);
          if (destino.accion === "ninguna") return null;
          const href =
            destino.accion === "enlace" ? destino.href : `${recurso(d.pdf ?? "")}#page=${destino.pagina}`;
          return (
            <a
              key={a.id ?? "incrustado"}
              className={enlace}
              href={href}
              target="_blank"
              rel="noopener"
              title={titulo}
            >
              {texto}
              {a.acceso === "privado" ? " (privada)" : ""}
            </a>
          );
        })}
        <a className={enlace} href={d.url} target="_blank" rel="noopener">
          {NOMBRE_FORMATO[d.formato] ?? "Original"}
        </a>
        {estadoDe(d) === "error" && (
          <span className="font-mono text-xs text-rojo" title={d.error}>
            ✗ roto
          </span>
        )}
      </div>
    </div>
  );
}
