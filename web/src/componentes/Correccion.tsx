import { destinoAnexo, etiquetaAnexo } from "~/dominio/anexos";
import type { Anexo } from "~/dominio/tipos";
import { Markdown } from "./Markdown";

interface Props {
  readonly anexos: readonly Anexo[];
  readonly examen: { readonly pdf?: string; readonly url: string };
  readonly generales: string;
  readonly onIrAPagina: (pagina: number, pdf?: string) => void;
}

const claveAnexo = (a: Anexo) => a.id ?? `incrustado-${a.incrustado?.pagina}`;
const enlace =
  "cursor-pointer text-left underline decoration-rojo decoration-[1.5px] underline-offset-2 hover:text-rojo";

export function Correccion({ anexos, examen, generales, onIrAPagina }: Props) {
  return (
    <section aria-label="Corrección del examen" className="mb-3.5 border-l-[3px] border-verde py-0.5 pl-3">
      <h3 className="etiqueta-mono mb-1">Corrección</h3>
      {anexos.length === 0 ? (
        <p className="text-sm text-suave italic">Sin criterios ni solución vinculados a este examen.</p>
      ) : (
        <ul className="space-y-0.5 text-sm">
          {anexos.map((a) => {
            const destino = destinoAnexo(a, examen);
            const etiqueta = etiquetaAnexo(a);
            return (
              <li key={claveAnexo(a)} className="flex flex-wrap items-baseline gap-x-2">
                {destino.accion === "pagina" && (
                  <button
                    type="button"
                    className={enlace}
                    onClick={() => onIrAPagina(destino.pagina, destino.pdf)}
                  >
                    {etiqueta} →
                  </button>
                )}
                {destino.accion === "enlace" && (
                  <a className={enlace} href={destino.href} target="_blank" rel="noopener">
                    {etiqueta} ↗
                  </a>
                )}
                {destino.accion === "ninguna" && <span className="text-suave line-through">{etiqueta}</span>}
                {destino.nota && <span className="font-mono text-[11px] text-suave">{destino.nota}</span>}
              </li>
            );
          })}
        </ul>
      )}
      {generales && (
        <details className="mt-1">
          <summary className="cursor-pointer font-mono text-[11px] text-suave select-none">
            Criterios generales del examen
          </summary>
          <Markdown texto={generales} className="prosa text-sm" />
        </details>
      )}
    </section>
  );
}
