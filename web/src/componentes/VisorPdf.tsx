import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { desplazamientoPara, franjaEn, paginaAcotada } from "~/dominio/franja";
import type { Ancla } from "~/dominio/tipos";
import type { DocumentoPdf, LectorPdf } from "~/puertos/pdf";

export interface Salto {
  readonly pagina: number;
  readonly pdf?: string;
  readonly grupo?: "criterios" | "soluciones";
  readonly vez: number;
}

interface Props {
  readonly lector: LectorPdf;
  readonly url: string;
  readonly ancla?: Ancla;
  readonly salto?: Salto;
  readonly onVolver?: () => void;
}

type Carga =
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string }
  | { estado: "listo"; documento: DocumentoPdf };

const RELLENO = 28;
const boton =
  "cursor-pointer rounded-lg border border-regla bg-papel px-2 py-1 text-tinta hover:border-tinta disabled:cursor-default disabled:opacity-35";

export function VisorPdf({ lector, url, ancla, salto, onVolver }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: "cargando" });
  const [pagina, setPagina] = useState(salto?.pagina ?? ancla?.pagina ?? 1);
  const [alto, setAlto] = useState(0);
  const [ancho, setAncho] = useState(0);
  const [pintada, setPintada] = useState(false);
  const [errorPintura, setErrorPintura] = useState<string>();
  const hoja = useRef<HTMLDivElement>(null);
  const lienzo = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    setPagina(salto?.pagina ?? ancla?.pagina ?? 1);
  }, [salto, ancla?.pagina]);

  useEffect(() => {
    let vigente = true;
    setCarga({ estado: "cargando" });
    lector.abrir(url).then(
      (documento) => {
        if (vigente) setCarga({ estado: "listo", documento });
      },
      (error: unknown) => {
        if (vigente)
          setCarga({ estado: "error", mensaje: error instanceof Error ? error.message : String(error) });
      },
    );
    return () => {
      vigente = false;
    };
  }, [lector, url]);

  useEffect(() => {
    const elemento = hoja.current;
    if (!elemento) return;
    const observador = new ResizeObserver(([entrada]) => {
      if (entrada) setAncho(Math.max(300, Math.floor(entrada.contentRect.width) - RELLENO));
    });
    observador.observe(elemento);
    return () => observador.disconnect();
  }, []);

  const total = carga.estado === "listo" ? carga.documento.paginas : 0;
  const paginaVisible = paginaAcotada(pagina, total);

  useEffect(() => {
    if (carga.estado !== "listo" || !lienzo.current || !ancho) return;
    const controlador = new AbortController();
    setPintada(false);
    setAlto(0);
    setErrorPintura(undefined);
    carga.documento.pintar(paginaVisible, lienzo.current, ancho, controlador.signal).then(
      (medidas) => {
        if (controlador.signal.aborted) return;
        setAlto(medidas.alto);
        setPintada(true);
        if (hoja.current)
          hoja.current.scrollTop = desplazamientoPara(franjaEn(ancla, paginaVisible, medidas.alto));
      },
      (error: unknown) => {
        if (!controlador.signal.aborted) {
          setErrorPintura(error instanceof Error ? error.message : String(error));
        }
      },
    );
    return () => controlador.abort();
  }, [carga, paginaVisible, ancho, ancla]);

  const franja = pintada && alto ? franjaEn(ancla, paginaVisible, alto) : null;
  const navegarConFlechas = (ev: KeyboardEvent<HTMLButtonElement | HTMLAnchorElement>) => {
    if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") {
      ev.preventDefault();
      setPagina((actual) => paginaAcotada(actual + (ev.key === "ArrowRight" ? 1 : -1), total));
    }
  };

  return (
    <section
      aria-label="Visor del PDF"
      data-visor-pdf
      className="flex h-[min(70vh,720px)] min-h-[400px] min-w-0 flex-col overflow-hidden rounded-xl border border-regla bg-papel-2"
    >
      <div className="flex flex-wrap items-center gap-2 border-b border-regla px-3 py-2 font-mono text-xs text-suave">
        {onVolver && (
          <button type="button" className={boton} onClick={onVolver} onKeyDown={navegarConFlechas}>
            ← volver al examen
          </button>
        )}
        <button
          type="button"
          className={boton}
          disabled={paginaVisible <= 1}
          onClick={() => setPagina(paginaVisible - 1)}
          onKeyDown={navegarConFlechas}
          title="Página anterior (←)"
        >
          ←
        </button>
        <span>{total ? `página ${paginaVisible} de ${total}` : "…"}</span>
        <button
          type="button"
          className={boton}
          disabled={!total || paginaVisible >= total}
          onClick={() => setPagina(paginaVisible + 1)}
          onKeyDown={navegarConFlechas}
          title="Página siguiente (→)"
        >
          →
        </button>
        <a
          className="ml-auto text-tinta underline underline-offset-2 hover:text-rojo"
          href={`${url}#page=${paginaVisible}`}
          target="_blank"
          rel="noopener noreferrer"
          onKeyDown={navegarConFlechas}
        >
          abrir en esta página ↗
        </a>
      </div>
      <div ref={hoja} className="min-h-0 flex-1 overflow-auto p-3.5">
        {carga.estado === "error" && (
          <p role="alert" className="p-8 text-center font-mono text-xs text-suave">
            No se pudo cargar el PDF ({carga.mensaje}).
          </p>
        )}
        {carga.estado === "cargando" && (
          <p className="p-8 text-center font-mono text-xs text-suave">Cargando PDF…</p>
        )}
        {errorPintura && (
          <p role="alert" className="p-8 text-center font-mono text-xs text-suave">
            No se pudo mostrar esta página ({errorPintura}).
          </p>
        )}
        <div
          className="relative mx-auto bg-white shadow-[0_8px_30px_-12px_rgba(0,0,0,.35)]"
          style={{
            width: ancho || undefined,
            visibility: carga.estado === "listo" && pintada ? "visible" : "hidden",
          }}
        >
          <canvas ref={lienzo} className="block w-full" />
          {franja && (
            <div
              data-testid="franja"
              className="pointer-events-none absolute inset-x-0 border-y-2 border-rojo bg-resalte transition-[top,height] duration-250"
              style={{ top: franja.top, height: franja.alto }}
            />
          )}
        </div>
      </div>
    </section>
  );
}
