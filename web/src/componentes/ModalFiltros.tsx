import { useEffect, useMemo, useRef, useState } from "react";
import { PanelFacetas } from "~/componentes/PanelFacetas";
import {
  alternar,
  type ClaveFaceta,
  calcularFaceta,
  FACETAS,
  type Filtros,
  filtrar,
  filtrosActivos,
  limpiar,
  type PreguntaIndexada,
} from "~/dominio/banco";

interface Props {
  readonly abierto: boolean;
  readonly preguntas: readonly PreguntaIndexada[];
  readonly filtros: Filtros;
  readonly consulta: string;
  readonly onAplicar: (filtros: Filtros) => void;
  readonly onCerrar: () => void;
}

export function ModalFiltros({ abierto, preguntas, filtros, consulta, onAplicar, onCerrar }: Props) {
  const dialogo = useRef<HTMLDialogElement>(null);
  const focoAnterior = useRef<HTMLElement | null>(null);
  const [borrador, setBorrador] = useState<Filtros>(filtros);
  const [expandidas, setExpandidas] = useState<ReadonlySet<ClaveFaceta>>(new Set());

  useEffect(() => {
    const elemento = dialogo.current;
    if (!elemento) return;
    if (abierto) {
      if (!elemento.open) {
        focoAnterior.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        setBorrador(filtros);
        setExpandidas(new Set());
        elemento.showModal();
      }
    } else {
      if (elemento.open) elemento.close();
      focoAnterior.current?.focus();
      focoAnterior.current = null;
    }
  }, [abierto, filtros]);

  const facetas = useMemo(
    () =>
      FACETAS.map((faceta) =>
        calcularFaceta(faceta, preguntas, borrador, consulta, expandidas.has(faceta.clave)),
      ),
    [preguntas, borrador, consulta, expandidas],
  );
  const cuenta = useMemo(
    () => filtrar(preguntas, borrador, consulta).length,
    [preguntas, borrador, consulta],
  );
  const seleccionados = filtrosActivos(borrador).length;

  const aplicar = () => {
    onAplicar(borrador);
    onCerrar();
  };

  return (
    <dialog
      ref={dialogo}
      aria-labelledby="titulo-modal-filtros"
      onCancel={(evento) => {
        evento.preventDefault();
        onCerrar();
      }}
      onKeyDown={(evento) => {
        if (evento.key === "Escape") {
          evento.preventDefault();
          onCerrar();
        }
      }}
      onClick={(evento) => {
        if (evento.target === evento.currentTarget) onCerrar();
      }}
      className="m-auto h-[min(760px,88dvh)] w-[min(800px,calc(100vw-24px))] max-w-none overflow-hidden rounded-[28px] bg-papel p-0 text-tinta shadow-[0_24px_80px_rgba(20,16,10,0.35)] backdrop:bg-black/50 backdrop:backdrop-blur-[3px] open:grid open:grid-rows-[auto_minmax(0,1fr)_auto]"
    >
      <header className="flex items-start justify-between gap-5 px-5 pt-5 pb-4 sm:px-7 sm:pt-6">
        <div>
          <p className="etiqueta-mono mb-1 text-rojo">Explora el banco</p>
          <h2 id="titulo-modal-filtros" className="font-titulo text-[clamp(1.7rem,4vw,2.3rem)] leading-tight">
            Filtros
          </h2>
          <p className="mt-1 text-sm text-suave">Elige las preguntas que quieres consultar.</p>
        </div>
        <button
          type="button"
          aria-label="Cerrar filtros"
          onClick={onCerrar}
          className="grid size-9 shrink-0 cursor-pointer place-items-center rounded-full bg-papel-2 text-xl leading-none transition-colors hover:bg-papel-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rojo"
        >
          ×
        </button>
      </header>

      <div className="min-h-0 overflow-y-auto overscroll-contain px-4 pb-5 sm:px-6">
        <PanelFacetas
          facetas={facetas}
          enColumnas
          onAlternar={(clave, valor) => setBorrador((actual) => alternar(actual, clave, valor))}
          onLimpiar={(clave) => setBorrador((actual) => limpiar(actual, clave))}
          onExpandir={(clave) => setExpandidas((actual) => new Set([...actual, clave]))}
        />
      </div>

      <footer className="flex flex-wrap items-center gap-2 bg-papel px-5 py-4 shadow-[0_-10px_24px_rgba(20,16,10,0.06)] sm:px-7">
        <button
          type="button"
          onClick={() => setBorrador({})}
          disabled={!seleccionados}
          className="cursor-pointer rounded-full px-3 py-2 font-mono text-xs text-suave hover:bg-papel-2 hover:text-tinta disabled:cursor-default disabled:opacity-50"
        >
          Limpiar filtros{seleccionados > 0 ? ` (${seleccionados})` : ""}
        </button>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={onCerrar}
            className="cursor-pointer rounded-full px-3 py-2 text-sm text-suave hover:bg-papel-2 hover:text-tinta"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={aplicar}
            className="cursor-pointer rounded-full bg-tinta px-5 py-2.5 font-mono text-xs text-papel transition-colors hover:bg-rojo focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rojo"
          >
            Ver {cuenta} {cuenta === 1 ? "pregunta" : "preguntas"}
          </button>
        </div>
      </footer>
    </dialog>
  );
}
