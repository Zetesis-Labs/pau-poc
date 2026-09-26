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
  const abrir = async (url: string): Promise<DocumentoPdf> => {
    const pdfjs = await cargarPdfjs();
    const documento = await pdfjs.getDocument({ url }).promise;
    return {
      paginas: documento.numPages,
      async pintar(numero, lienzo, anchoCss) {
        const pagina = await documento.getPage(numero);
        const base = pagina.getViewport({ scale: 1 });
        const escala = anchoCss / base.width;
        const vista = pagina.getViewport({ scale: escala * (window.devicePixelRatio || 1) });
        lienzo.width = vista.width;
        lienzo.height = vista.height;
        await pagina.render({ canvas: lienzo, viewport: vista }).promise;
        return { ancho: anchoCss, alto: base.height * escala };
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
