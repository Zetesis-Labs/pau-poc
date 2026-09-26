import type { Banco, Catalogo } from "~/dominio/tipos";

export interface FuenteDatos {
  banco(): Promise<Banco>;
  catalogo(): Promise<Catalogo>;
  /** URL pública de un recurso de `datos/` (figura o PDF) a partir de su ruta relativa. */
  recurso(ruta: string): string;
}
