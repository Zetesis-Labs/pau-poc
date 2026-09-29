import type { ReactNode } from "react";
import { claveApartado, figurasDe, migas } from "~/dominio/banco";
import { nombreIdioma, textoEn } from "~/dominio/textos";
import type { Apartado, Estimulo, FuenteRubrica, Pregunta } from "~/dominio/tipos";
import { Markdown } from "./Markdown";
import { RubricaNodo } from "./RubricaNodo";
import { SolucionNodo } from "./SolucionNodo";

interface Props {
  readonly children?: ReactNode;
  readonly pregunta: Pregunta;
  readonly idioma: string;
  readonly recurso: (ruta: string) => string;
  readonly onIdioma: (idioma: string) => void;
  readonly onAmpliar: (src: string) => void;
  readonly onCerrar: () => void;
  readonly onIrAPagina: (pagina: number, pdf?: string, grupo?: "criterios" | "soluciones") => void;
}

const LARGO_PLEGADO = 900;

export function DetallePregunta({
  children,
  pregunta: p,
  idioma,
  recurso,
  onIdioma,
  onAmpliar,
  onCerrar,
  onIrAPagina,
}: Props) {
  const introduccion = p.contexto.map((c) => textoEn(c.enunciado, idioma)).filter(Boolean);
  const literalRegla = textoEn(p.literalRegla, idioma);
  return (
    <article className="h-full overflow-y-auto px-8 pt-7 pb-12 max-md:px-5">
      <div className="mx-auto max-w-225">
        <button
          type="button"
          onClick={onCerrar}
          className="sticky top-0 z-2 mb-3 hidden cursor-pointer rounded-full bg-papel-2 px-3 py-2 font-mono text-[11px] max-md:inline-block"
        >
          ← volver a la lista
        </button>
        <nav aria-label="Ubicación en el examen" className="mb-1.5 font-mono text-xs text-suave">
          {migas(p, idioma).map((m, i) => (
            <span key={m.clave}>
              {i > 0 && " › "}
              {m.texto}
              {m.regla && <span className="text-azul"> ({m.regla})</span>}
            </span>
          ))}
          {p.reglaExamen && <span className="text-azul"> · examen: {p.reglaExamen}</span>}
        </nav>
        <h2 className="mb-1 font-titulo text-3xl leading-tight font-semibold">
          {textoEn(p.etiqueta, idioma)}
        </h2>
        <div className="mb-3.5 flex flex-wrap gap-x-3.5 gap-y-1 font-mono text-xs text-suave">
          {p.puntos !== null && <span>{p.puntos} puntos</span>}
          <span>{p.examen.fuente}</span>
          <a href={p.examen.url} target="_blank" rel="noopener" className="underline">
            origen ↗
          </a>
        </div>
        {p.idiomas.length > 1 && (
          <fieldset className="mb-6 inline-flex gap-1 rounded-full bg-papel-3/60 p-1">
            <legend className="sr-only">Idioma</legend>
            {p.idiomas.map((i) => (
              <button
                type="button"
                key={i}
                aria-pressed={i === idioma}
                onClick={() => onIdioma(i)}
                className={`cursor-pointer rounded-full px-3.5 py-1.5 font-mono text-xs font-medium ${i === idioma ? "bg-tinta text-papel" : ""}`}
              >
                {nombreIdioma(i)}
              </button>
            ))}
          </fieldset>
        )}
        {introduccion.length > 0 && (
          <div className="mb-3.5 border-l-[3px] border-azul py-0.5 pl-3 text-sm text-suave">
            {introduccion.map((texto) => (
              <Markdown key={texto} texto={texto} />
            ))}
          </div>
        )}
        {(p.regla || literalRegla) && (
          <div className="mb-4 border-l-[3px] border-azul py-0.5 pl-3">
            <div className="font-mono text-xs text-azul">Regla de la pregunta</div>
            {p.regla && <div className="font-mono text-sm text-azul">{p.regla}</div>}
            {literalRegla && <Markdown texto={literalRegla} />}
          </div>
        )}
        <Markdown texto={textoEn(p.enunciado, idioma)} />
        {p.rubrica && (
          <RubricaNodo
            rubrica={p.rubrica}
            puntosEnunciado={p.puntos}
            idioma={idioma}
            fuente={p.fuenteRubrica}
            onIrAPagina={onIrAPagina}
          />
        )}
        {p.solucion && <SolucionNodo solucion={p.solucion} idioma={idioma} onIrAPagina={onIrAPagina} />}
        {p.estimulos.map((e) => (
          <BloqueEstimulo key={e.id} estimulo={e} idioma={idioma} recurso={recurso} onAmpliar={onAmpliar} />
        ))}
        <Apartados lista={p.apartados} idioma={idioma} fuente={p.fuenteRubrica} onIrAPagina={onIrAPagina} />
        {textoEn(p.criteriosGenerales, idioma) && (
          <details className="mt-8 rounded-2xl bg-papel-2 p-5">
            <summary className="cursor-pointer font-titulo text-lg">
              Criterios generales de corrección
            </summary>
            <Markdown texto={textoEn(p.criteriosGenerales, idioma)} />
          </details>
        )}
        {children}
      </div>
    </article>
  );
}

function BloqueEstimulo({
  estimulo: e,
  idioma,
  recurso,
  onAmpliar,
}: {
  estimulo: Estimulo;
  idioma: string;
  recurso: (ruta: string) => string;
  onAmpliar: (src: string) => void;
}) {
  const contenido = textoEn(e.contenido, idioma);
  const largo = contenido.length > LARGO_PLEGADO;
  return (
    <details className="my-6 rounded-2xl bg-papel-2 px-5 py-4" open={!largo}>
      <summary className="etiqueta-mono cursor-pointer">
        {e.id} · {e.tipo}
        {largo && " · desplegar"}
      </summary>
      {figurasDe(e.figuras, idioma).map((f) => (
        <figure key={f.src} className="my-4 flex justify-center">
          <button type="button" className="cursor-zoom-in" onClick={() => onAmpliar(recurso(f.src))}>
            <img
              src={recurso(f.src)}
              alt={e.descripcion}
              loading="lazy"
              className="block max-h-[560px] max-w-full rounded-xl bg-white object-contain"
            />
          </button>
        </figure>
      ))}
      {(!e.figuras.length || !contenido) && (
        <Markdown texto={e.descripcion} className="prosa my-2 text-sm text-suave italic" />
      )}
      {contenido && <Markdown texto={contenido} />}
    </details>
  );
}

interface PropsApartados {
  readonly lista: readonly Apartado[];
  readonly idioma: string;
  readonly fuente: FuenteRubrica | null;
  readonly onIrAPagina: (pagina: number, pdf?: string, grupo?: "criterios" | "soluciones") => void;
}

function Apartados({ lista, idioma, fuente, onIrAPagina }: PropsApartados) {
  if (!lista.length) return null;
  return (
    <ol className="mt-3 col-span-full">
      {lista.map((a) => (
        <li
          key={claveApartado(a)}
          className="grid grid-cols-[38px_minmax(0,1fr)_auto] gap-1.5 border-t border-regla/60 py-4"
        >
          <span className="font-titulo text-base font-semibold">{textoEn(a.etiqueta, idioma)}</span>
          <div>
            <Markdown texto={textoEn(a.enunciado, idioma)} />
            {a.regla && <div className="font-mono text-xs text-azul">{a.regla}</div>}
            {a.rubrica && (
              <RubricaNodo
                rubrica={a.rubrica}
                puntosEnunciado={a.puntos}
                idioma={idioma}
                fuente={fuente}
                onIrAPagina={onIrAPagina}
              />
            )}
            {a.solucion && <SolucionNodo solucion={a.solucion} idioma={idioma} onIrAPagina={onIrAPagina} />}
          </div>
          <span className="pt-0.75 font-mono text-xs whitespace-nowrap text-verde">
            {a.puntos !== null ? `${a.puntos} p.` : ""}
          </span>
          {a.apartados.length > 0 && (
            <div className="col-start-2 col-end-4">
              <Apartados lista={a.apartados} idioma={idioma} fuente={fuente} onIrAPagina={onIrAPagina} />
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}
