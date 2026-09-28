import { memo, useCallback } from "react";
import { numeroDeFiguras } from "~/dominio/banco";
import { resaltar } from "~/dominio/resaltado";
import { origenesDeSolucion, tieneRubrica } from "~/dominio/rubrica";
import { idiomaPreferido, textoEn } from "~/dominio/textos";
import type { Pregunta } from "~/dominio/tipos";
import { Markdown } from "./Markdown";

interface Props {
  readonly pregunta: Pregunta;
  readonly seleccionada: boolean;
  readonly idioma?: string;
  readonly consulta: string;
  readonly onElegir: (id: string) => void;
}

const marca =
  "font-mono text-[10px] leading-none font-medium uppercase tracking-[0.08em] px-1.25 py-0.75 border";

export const TarjetaPregunta = memo(function TarjetaPregunta({
  pregunta: p,
  seleccionada,
  idioma,
  consulta,
  onElegir,
}: Props) {
  const lengua = idiomaPreferido(p.idiomas, idioma);
  const figuras = numeroDeFiguras(p);
  const resumen =
    textoEn(p.enunciado, lengua) || textoEn(p.apartados[0]?.enunciado, lengua) || "*Sin enunciado propio*";
  const marcar = useCallback((html: string) => resaltar(html, consulta), [consulta]);
  return (
    <button
      type="button"
      data-id={p.id}
      aria-current={seleccionada}
      onClick={() => onElegir(p.id)}
      className={`block w-full cursor-pointer border-b border-regla px-3.5 pt-2.75 pb-3 text-left hover:bg-papel-2 ${seleccionada ? "bg-papel-3 shadow-[inset_4px_0_0_var(--rojo)]" : ""}`}
    >
      <div className="flex justify-between gap-2 font-mono text-[11px] text-suave">
        <span>{p.examen.asignatura}</span>
        <span className="whitespace-nowrap">
          {p.examen.region} · {p.examen.anio}
        </span>
      </div>
      <div className="mt-0.75 mb-1 font-titulo text-base leading-tight font-semibold">
        {textoEn(p.etiqueta, lengua)}
      </div>
      <Markdown texto={resumen} resaltar={marcar} className="resumen line-clamp-3 text-sm" />
      <div className="mt-1.5 flex flex-wrap gap-1.25">
        {p.puntos !== null && <span className={`${marca} border-current text-verde`}>{p.puntos} p.</span>}
        {p.apartados.length > 0 && (
          <span className={`${marca} border-regla text-suave`}>{p.apartados.length} apartados</span>
        )}
        {figuras > 0 && (
          <span className={`${marca} border-current text-azul`}>
            {figuras} figura{figuras > 1 ? "s" : ""}
          </span>
        )}
        {tieneRubrica(p) && <span className={`${marca} border-current text-verde`}>rúbrica</span>}
        {origenesDeSolucion(p).size > 0 && (
          <span className={`${marca} border-current text-azul`}>solución</span>
        )}
        {p.idiomas.length > 1 && (
          <span className={`${marca} border-regla text-suave`}>{p.idiomas.join(" · ")}</span>
        )}
      </div>
    </button>
  );
});
