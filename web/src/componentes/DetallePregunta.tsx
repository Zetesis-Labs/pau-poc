import { claveApartado, figurasDe, migas } from "~/dominio/banco";
import { nombreIdioma, textoEn } from "~/dominio/textos";
import type { Apartado, Estimulo, FuenteRubrica, Pregunta } from "~/dominio/tipos";
import { Correccion } from "./Correccion";
import { Markdown } from "./Markdown";
import { RubricaNodo } from "./RubricaNodo";
import { SolucionNodo } from "./SolucionNodo";

interface Props {
  readonly pregunta: Pregunta;
  readonly idioma: string;
  readonly recurso: (ruta: string) => string;
  readonly onIdioma: (idioma: string) => void;
  readonly onAmpliar: (src: string) => void;
  readonly onCerrar: () => void;
  readonly onIrAPagina: (pagina: number) => void;
}

const LARGO_PLEGADO = 900;

export function DetallePregunta({
  pregunta: p,
  idioma,
  recurso,
  onIdioma,
  onAmpliar,
  onCerrar,
  onIrAPagina,
}: Props) {
  const introduccion = p.contexto.map((c) => textoEn(c.enunciado, idioma)).filter(Boolean);
  return (
    <article className="overflow-y-auto border-tinta px-6.5 pt-4.5 pb-16 max-[1500px]:border-b-[1.5px] min-[1500px]:border-r-[1.5px] max-md:px-4">
      <button
        type="button"
        onClick={onCerrar}
        className="mb-2.5 hidden cursor-pointer border border-tinta px-1.5 font-mono text-[11px] max-md:inline-block"
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
      <h2 className="mb-1 font-titulo text-3xl leading-tight font-semibold">{textoEn(p.etiqueta, idioma)}</h2>
      <div className="mb-3.5 flex flex-wrap gap-x-3.5 gap-y-1 font-mono text-xs text-suave">
        {p.puntos !== null && <span>{p.puntos} puntos</span>}
        <span>{p.examen.fuente}</span>
        <a href={p.examen.url} target="_blank" rel="noopener" className="underline">
          origen ↗
        </a>
      </div>
      <Correccion
        anexos={p.examen.anexos}
        examen={p.examen}
        generales={textoEn(p.criteriosGenerales, idioma)}
        onIrAPagina={onIrAPagina}
      />
      {p.idiomas.length > 1 && (
        <fieldset className="mb-3.5 inline-flex border-[1.5px] border-tinta">
          <legend className="sr-only">Idioma</legend>
          {p.idiomas.map((i) => (
            <button
              type="button"
              key={i}
              aria-pressed={i === idioma}
              onClick={() => onIdioma(i)}
              className={`cursor-pointer px-2.5 py-0.75 font-mono text-xs font-medium ${i === idioma ? "bg-tinta text-papel" : ""}`}
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
    <details className="my-3 border border-regla bg-papel-2 px-3.5 py-2.5" open={!largo}>
      <summary className="etiqueta-mono cursor-pointer">
        {e.id} · {e.tipo}
        {largo && " · desplegar"}
      </summary>
      {figurasDe(e.figuras, idioma).map((f) => (
        <figure key={f.src} className="my-2">
          <button type="button" className="cursor-zoom-in" onClick={() => onAmpliar(recurso(f.src))}>
            <img
              src={recurso(f.src)}
              alt={e.descripcion}
              loading="lazy"
              className="block max-h-[520px] max-w-full border border-regla bg-white"
            />
          </button>
        </figure>
      ))}
      {(!e.figuras.length || !contenido) && (
        <Markdown texto={e.descripcion} className="prosa my-1.5 text-suave italic" />
      )}
      {contenido && <Markdown texto={contenido} />}
    </details>
  );
}

interface PropsApartados {
  readonly lista: readonly Apartado[];
  readonly idioma: string;
  readonly fuente: FuenteRubrica | null;
  readonly onIrAPagina: (pagina: number) => void;
}

function Apartados({ lista, idioma, fuente, onIrAPagina }: PropsApartados) {
  if (!lista.length) return null;
  return (
    <ol className="mt-3 col-span-full">
      {lista.map((a) => (
        <li
          key={claveApartado(a)}
          className="grid grid-cols-[38px_minmax(0,1fr)_auto] gap-1.5 border-t border-dashed border-regla py-2"
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
