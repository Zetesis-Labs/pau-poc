import { destinoSolucion, etiquetaSolucion } from "~/dominio/rubrica";
import { textoEn } from "~/dominio/textos";
import type { Solucion } from "~/dominio/tipos";
import { Markdown } from "./Markdown";

interface Props {
  readonly solucion: Solucion;
  readonly idioma: string;
  readonly onIrAPagina: (pagina: number, pdf?: string) => void;
}

export function SolucionNodo({ solucion, idioma, onIrAPagina }: Props) {
  const destino = destinoSolucion(solucion, idioma);
  const deAcademia = solucion.origen === "academia";
  return (
    <details
      className={`mt-1.5 min-w-0 overflow-x-auto border-l-2 pl-3 ${deAcademia ? "border-azul" : "border-verde"}`}
    >
      <summary
        className={`etiqueta-mono cursor-pointer select-none ${deAcademia ? "text-azul!" : "text-verde!"}`}
      >
        Ver la solución · {etiquetaSolucion(solucion)}
      </summary>
      <Markdown texto={textoEn(solucion.texto, idioma)} className="prosa text-[15px]" />
      {deAcademia && (
        <p className="font-mono text-[11px] text-suave">
          Redacción de la academia, no del tribunal: puede no coincidir con los criterios oficiales.
        </p>
      )}
      {destino?.accion === "pagina" && (
        <button
          type="button"
          className="font-mono text-[11px] text-suave underline"
          onClick={() => onIrAPagina(destino.pagina, destino.pdf)}
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
          ver en el documento original ↗
        </a>
      )}
    </details>
  );
}
