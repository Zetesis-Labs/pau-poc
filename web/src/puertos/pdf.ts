export interface PaginaRenderizada {
  readonly ancho: number;
  readonly alto: number;
}

export interface DocumentoPdf {
  readonly paginas: number;
  /** Pinta la página en el lienzo con `anchoCss` píxeles de ancho visibles y devuelve el tamaño en píxeles CSS. */
  pintar(pagina: number, lienzo: HTMLCanvasElement, anchoCss: number): Promise<PaginaRenderizada>;
}

export interface LectorPdf {
  abrir(url: string): Promise<DocumentoPdf>;
}
