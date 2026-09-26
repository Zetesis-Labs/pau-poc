/// <reference types="vite/client" />
import { createRootRouteWithContext, HeadContent, Outlet, Scripts } from "@tanstack/react-router";
import type { ReactNode } from "react";
import type { FuenteDatos } from "~/puertos/datos";
import type { LectorPdf } from "~/puertos/pdf";
import estilos from "~/styles.css?url";

export interface ContextoRouter {
  readonly datos: FuenteDatos;
  readonly pdf: LectorPdf;
}

const TEMA_INICIAL = `try{var t=localStorage.getItem("pau-tema");document.documentElement.dataset.tema=t||(matchMedia("(prefers-color-scheme: dark)").matches?"oscuro":"claro")}catch(e){}`;

export const Route = createRootRouteWithContext<ContextoRouter>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "PAU · banco de preguntas" },
      {
        name: "description",
        content: "Preguntas de la PAU extraídas de exámenes oficiales, con su PDF de origen.",
      },
    ],
    links: [
      { rel: "stylesheet", href: estilos },
      { rel: "icon", href: "data:," },
    ],
    scripts: [{ children: TEMA_INICIAL }],
  }),
  component: () => (
    <Documento>
      <Outlet />
    </Documento>
  ),
  notFoundComponent: () => <p className="p-10 text-center italic text-suave">Esta página no existe.</p>,
});

function Documento({ children }: { children: ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
