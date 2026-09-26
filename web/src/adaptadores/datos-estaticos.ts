import type { Banco, Catalogo } from "~/dominio/tipos";
import type { FuenteDatos } from "~/puertos/datos";

async function json<T>(url: string): Promise<T> {
  const respuesta = await fetch(url);
  if (!respuesta.ok) throw new Error(`No se pudo cargar ${url} (HTTP ${respuesta.status})`);
  return (await respuesta.json()) as T;
}

/** Lee el conjunto publicado servido como estáticos bajo `<base>datos/`. */
export function datosEstaticos(base: string): FuenteDatos {
  const raiz = `${base.replace(/\/?$/, "/")}datos/`;
  const recurso = (ruta: string) => `${raiz}${ruta.split("/").map(encodeURIComponent).join("/")}`;
  let banco: Promise<Banco> | undefined;
  let catalogo: Promise<Catalogo> | undefined;
  return {
    recurso,
    banco: () => {
      banco ??= json<Banco>(recurso("preguntas.json"));
      return banco;
    },
    catalogo: () => {
      catalogo ??= json<Catalogo>(recurso("catalogo.json"));
      return catalogo;
    },
  };
}
