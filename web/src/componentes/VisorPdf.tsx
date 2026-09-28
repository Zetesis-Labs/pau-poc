import { useEffect, useRef, useState } from "react";
import { desplazamientoPara, franjaEn, paginaAcotada } from "~/dominio/franja";
import type { Ancla } from "~/dominio/tipos";
import type { DocumentoPdf, LectorPdf } from "~/puertos/pdf";

export interface Salto {
  readonly pagina: number;
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
  "cursor-pointer border border-tinta bg-papel px-2 py-0.5 disabled:cursor-default disabled:opacity-35";

export function VisorPdf({ lector, url, ancla, salto, onVolver }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: "cargando" });
  const [pagina, setPagina] = useState(ancla?.pagina ?? 1);
  const [alto, setAlto] = useState(0);
  const [ancho, setAncho] = useState(0);
  const hoja = useRef<HTMLDivElement>(null);
  const lienzo = useRef<HTMLCanvasElement>(null);

  useEffect(() => setPagina(ancla?.pagina ?? 1), [ancla]);

  useEffect(() => {
    if (salto) setPagina(salto.pagina);
  }, [salto]);

  useEffect(() => {
    let vigente = true;
    setCarga({ estado: "cargando" });
    lector.abrir(url).then(
      (documento) => vigente && setCarga({ estado: "listo", documento }),
      (error: unknown) =>
        vigente &&
        setCarga({ estado: "error", mensaje: error instanceof Error ? error.message : String(error) }),
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

  useEffect(() => {
    if (carga.estado !== "listo" || !lienzo.current || !ancho) return;
    let vigente = true;
    carga.documento.pintar(paginaAcotada(pagina, total), lienzo.current, ancho).then((r) => {
      if (!vigente) return;
      setAlto(r.alto);
      if (hoja.current) hoja.current.scrollTop = desplazamientoPara(franjaEn(ancla, pagina, r.alto));
    });
    return () => {
      vigente = false;
    };
  }, [carga, pagina, ancho, ancla, total]);

  useEffect(() => {
    const teclas = (ev: KeyboardEvent) => {
      if (ev.target instanceof HTMLElement && ev.target.matches("input, textarea")) return;
      if (ev.key === "ArrowLeft") setPagina((p) => paginaAcotada(p - 1, total));
      if (ev.key === "ArrowRight") setPagina((p) => paginaAcotada(p + 1, total));
    };
    window.addEventListener("keydown", teclas);
    return () => window.removeEventListener("keydown", teclas);
  }, [total]);

  const franja = alto ? franjaEn(ancla, pagina, alto) : null;

  return (
    <div className="flex min-h-0 flex-col bg-papel-2">
      <div className="flex items-center gap-2 border-b border-regla px-3 py-2 font-mono text-xs text-suave">
        {onVolver && (
          <button type="button" className={`${boton} text-tinta`} onClick={onVolver}>
            ← volver al examen
          </button>
        )}
        <button
          type="button"
          className={boton}
          disabled={pagina <= 1}
          onClick={() => setPagina(pagina - 1)}
          title="Página anterior (←)"
        >
          ←
        </button>
        <span>{total ? `página ${pagina} de ${total}` : "…"}</span>
        <button
          type="button"
          className={boton}
          disabled={!total || pagina >= total}
          onClick={() => setPagina(pagina + 1)}
          title="Página siguiente (→)"
        >
          →
        </button>
        <a
          className="ml-auto text-tinta underline"
          href={`${url}#page=${pagina}`}
          target="_blank"
          rel="noopener"
        >
          abrir en esta página ↗
        </a>
      </div>
      <div ref={hoja} className="flex-1 overflow-auto p-3.5">
        {carga.estado === "error" && (
          <p className="p-8 text-center font-mono text-xs text-suave">
            No se pudo cargar el PDF ({carga.mensaje}).
          </p>
        )}
        {carga.estado === "cargando" && (
          <p className="p-8 text-center font-mono text-xs text-suave">Cargando PDF…</p>
        )}
        <div
          className="relative mx-auto bg-white shadow-[0_8px_30px_-12px_rgba(0,0,0,.35)]"
          style={{ width: ancho || undefined, display: carga.estado === "listo" ? undefined : "none" }}
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
    </div>
  );
}
