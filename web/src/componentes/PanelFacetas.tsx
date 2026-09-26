import type { ClaveFaceta, FacetaCalculada } from "~/dominio/banco";

interface Props {
  readonly facetas: readonly FacetaCalculada[];
  readonly onAlternar: (clave: ClaveFaceta, valor: string) => void;
  readonly onLimpiar: (clave: ClaveFaceta) => void;
  readonly onExpandir: (clave: ClaveFaceta) => void;
}

export function PanelFacetas({ facetas, onAlternar, onLimpiar, onExpandir }: Props) {
  return (
    <div className="space-y-5 px-3.5 pt-3 pb-10">
      {facetas.map((f) => (
        <section key={f.clave} aria-label={f.titulo}>
          <h3 className="etiqueta-mono mb-1.5 flex justify-between">
            {f.titulo}
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
              className={`flex w-full cursor-pointer items-center gap-2 px-1 py-0.75 text-left text-sm leading-tight hover:bg-papel-2 ${v.cuenta || v.elegido ? "" : "opacity-40"}`}
            >
              <span
                className={`grid size-3.25 flex-none place-items-center border-[1.5px] border-tinta text-[10px] ${v.elegido ? "bg-tinta text-papel" : ""}`}
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
