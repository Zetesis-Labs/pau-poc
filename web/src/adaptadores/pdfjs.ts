import type { DocumentoPdf, LectorPdf } from "~/puertos/pdf";

type Pdfjs = typeof import("pdfjs-dist");

let modulo: Promise<Pdfjs> | undefined;

function cargarPdfjs(): Promise<Pdfjs> {
  modulo ??= Promise.all([import("pdfjs-dist"), import("pdfjs-dist/build/pdf.worker.min.mjs?url")]).then(
    ([pdfjs, worker]) => {
      pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
      return pdfjs;
    },
  );
  return modulo;
}

/** Lector de PDF con PDF.js; se carga bajo demanda y guarda los documentos abiertos. */
export function lectorPdfjs(): LectorPdf {
  const abiertos = new Map<string, Promise<DocumentoPdf>>();
  const renders = new WeakMap<HTMLCanvasElement, Promise<void>>();
  const abrir = async (url: string): Promise<DocumentoPdf> => {
    const pdfjs = await cargarPdfjs();
    const documento = await pdfjs.getDocument({ url }).promise;
    return {
      paginas: documento.numPages,
      async pintar(numero, lienzo, anchoCss, signal) {
        const anterior = renders.get(lienzo);
        const actual = async () => {
          await anterior?.catch(() => undefined);
          signal?.throwIfAborted();
          const pagina = await documento.getPage(numero);
          signal?.throwIfAborted();
          const base = pagina.getViewport({ scale: 1 });
          const escala = anchoCss / base.width;
          const vista = pagina.getViewport({ scale: escala * (window.devicePixelRatio || 1) });
          lienzo.width = vista.width;
          lienzo.height = vista.height;
          const tarea = pagina.render({ canvas: lienzo, viewport: vista });
          const cancelar = () => tarea.cancel();
          signal?.addEventListener("abort", cancelar, { once: true });
          try {
            if (signal?.aborted) tarea.cancel();
            await tarea.promise;
            signal?.throwIfAborted();
            return { ancho: anchoCss, alto: base.height * escala };
          } finally {
            signal?.removeEventListener("abort", cancelar);
          }
        };
        const resultado = actual();
        renders.set(
          lienzo,
          resultado.then(
            () => undefined,
            () => undefined,
          ),
        );
        return resultado;
      },
    };
  };
  return {
    abrir(url) {
      let documento = abiertos.get(url);
      if (!documento) {
        documento = abrir(url);
        documento.catch(() => abiertos.delete(url));
        abiertos.set(url, documento);
      }
      return documento;
    },
  };
}
