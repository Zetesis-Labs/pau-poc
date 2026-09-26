import type { Ancla } from "./tipos";

export interface Franja {
  readonly top: number;
  readonly alto: number;
}

const ALTO_MINIMO = 0.02;
const ALTO_SIN_FIN = 0.05;
const MARGEN_PX = 4;
const AIRE_SUPERIOR_PX = 60;

/** Banda resaltada de la pregunta sobre una página renderizada a `altoPx` píxeles, o null si no hay ancla en esa página. */
export function franjaEn(ancla: Ancla | undefined, pagina: number, altoPx: number): Franja | null {
  if (!ancla || ancla.pagina !== pagina || ancla.y0 === null) return null;
  const fin = ancla.y1 ?? ancla.y0 + ALTO_SIN_FIN;
  return {
    top: ancla.y0 * altoPx - MARGEN_PX,
    alto: Math.max(ALTO_MINIMO, fin - ancla.y0) * altoPx + 2 * MARGEN_PX,
  };
}

export const desplazamientoPara = (franja: Franja | null): number =>
  franja ? Math.max(0, franja.top - AIRE_SUPERIOR_PX) : 0;

export const paginaAcotada = (pagina: number, total: number): number =>
  Math.min(Math.max(1, pagina), Math.max(1, total));
