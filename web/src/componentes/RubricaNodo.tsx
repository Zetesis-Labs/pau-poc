import { destinoRubrica, discrepanciaDePuntos } from "~/dominio/rubrica";
import { textoEn } from "~/dominio/textos";
import type { FuenteRubrica, Rubrica } from "~/dominio/tipos";
import { Markdown } from "./Markdown";

interface Props {
  readonly rubrica: Rubrica;
  readonly puntosEnunciado: number | null;
  readonly idioma: string;
  readonly fuente: FuenteRubrica | null;
  readonly onIrAPagina: (pagina: number) => void;
}

const numero = (n: number) => n.toLocaleString("es", { maximumFractionDigits: 2 });

export function RubricaNodo({ rubrica, puntosEnunciado, idioma, fuente, onIrAPagina }: Props) {
  const criterios = textoEn(rubrica.criterios, idioma);
  const discrepancia = discrepanciaDePuntos(puntosEnunciado, rubrica);
  const destino = destinoRubrica(rubrica, fuente, idioma);
  return (
    <details className="group mt-1.5 min-w-0 overflow-x-auto border-l-2 border-verde pl-3">
      <summary className="etiqueta-mono cursor-pointer text-verde! select-none">
        Cómo se corrige{rubrica.puntos !== null ? ` · ${numero(rubrica.puntos)} p.` : ""}
      </summary>
      {discrepancia && <p className="mt-1 font-mono text-[11px] text-rojo">Atención: {discrepancia}.</p>}
      {criterios && <Markdown texto={criterios} className="prosa text-[15px]" />}
      {rubrica.desglose.length > 0 && (
        <ul className="my-1.5 space-y-0.5 text-sm">
          {rubrica.desglose.map((t) => (
            <li key={`${t.puntos}-${textoEn(t.descripcion, idioma)}`} className="flex items-baseline gap-2">
              <span className="font-mono text-xs whitespace-nowrap text-verde">{numero(t.puntos)} p.</span>
              <Markdown texto={textoEn(t.descripcion, idioma)} className="resumen" />
            </li>
          ))}
        </ul>
      )}
      {destino?.accion === "pagina" && (
        <button
          type="button"
          className="font-mono text-[11px] text-suave underline"
          onClick={() => onIrAPagina(destino.pagina)}
        >
          ver en el PDF, p. {destino.pagina} →
        </button>
      )}
      {destino?.accion === "enlace" && (
        <a
          className="font-mono text-[11px] text-suave underline"
          href={destino.href}
          target="_blank"
          rel="noopener"
        >
          ver en los criterios oficiales ↗
        </a>
      )}
    </details>
  );
}
