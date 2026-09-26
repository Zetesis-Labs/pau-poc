import { createRouter, parseSearchWith, stringifySearchWith } from "@tanstack/react-router";
import { datosEstaticos } from "./adaptadores/datos-estaticos";
import { lectorPdfjs } from "./adaptadores/pdfjs";
import { routeTree } from "./routeTree.gen";

export function getRouter() {
  return createRouter({
    routeTree,
    context: { datos: datosEstaticos(import.meta.env.BASE_URL), pdf: lectorPdfjs() },
    scrollRestoration: true,
    defaultPreload: "intent",
    parseSearch: parseSearchWith((valor) => valor),
    stringifySearch: stringifySearchWith(String),
  });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>;
  }
}
