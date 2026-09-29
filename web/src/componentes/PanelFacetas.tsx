import type { ClaveFaceta, FacetaCalculada } from "~/dominio/banco";

interface Props {
  readonly facetas: readonly FacetaCalculada[];
  readonly onAlternar: (clave: ClaveFaceta, valor: string) => void;
  readonly onLimpiar: (clave: ClaveFaceta) => void;
  readonly onExpandir: (clave: ClaveFaceta) => void;
  readonly enColumnas?: boolean;
}

export function PanelFacetas({ facetas, onAlternar, onLimpiar, onExpandir, enColumnas = false }: Props) {
  return (
    <div
      className={
        enColumnas ? "grid grid-cols-1 items-start gap-3 md:grid-cols-2" : "space-y-5 px-3.5 pt-3 pb-10"
      }
    >
      {facetas.map((f) => (
        <section
          key={f.clave}
          aria-label={f.titulo}
          className={enColumnas ? "min-w-0 rounded-[20px] bg-papel-2/50 px-4 py-3.5" : undefined}
        >
          <h3 className="etiqueta-mono mb-2 flex items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              {f.titulo}
              {f.activa && (
                <span
                  className="grid min-w-5 place-items-center rounded-full bg-rojo px-1.5 py-0.5 text-[10px] leading-none text-papel"
                  title={`${f.valores.filter((valor) => valor.elegido).length} seleccionados`}
                >
                  {f.valores.filter((valor) => valor.elegido).length}
                </span>
              )}
            </span>
            {f.activa && (
              <button
                type="button"
                className="cursor-pointer tracking-normal text-rojo normal-case"
                onClick={() => onLimpiar(f.clave)}
              >
                quitar
              </button>
            )}
          </h3>
          {f.valores.map((v) => (
            <button
              type="button"
              key={v.valor}
              aria-pressed={v.elegido}
              onClick={() => onAlternar(f.clave, v.valor)}
              className={`flex w-full cursor-pointer items-center gap-2 rounded-lg px-1.5 py-1 text-left text-sm leading-tight hover:bg-papel-3/60 ${v.cuenta || v.elegido ? "" : "opacity-40"}`}
            >
              <span
                className={`grid size-3.25 flex-none place-items-center rounded-[4px] border-[1.5px] border-tinta text-[10px] ${v.elegido ? "bg-tinta text-papel" : ""}`}
              >
                {v.elegido ? "✓" : ""}
              </span>
              <span className="flex-1">{v.nombre}</span>
              <span className="font-mono text-[11px] text-suave">{v.cuenta}</span>
            </button>
          ))}
          {f.ocultos > 0 && (
            <button
              type="button"
              className="cursor-pointer p-1 font-mono text-[11px] text-suave hover:text-tinta"
              onClick={() => onExpandir(f.clave)}
            >
              ver {f.ocultos} más
            </button>
          )}
        </section>
      ))}
    </div>
  );
}
