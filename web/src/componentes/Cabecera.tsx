import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { BotonTema } from "./BotonTema";

const pestana =
  "font-mono text-xs px-3 py-2 rounded-full text-suave hover:text-tinta hover:bg-papel-2 max-md:px-2 max-md:text-[10px]";
const pestanaActiva = { className: "bg-papel-3/70 !text-tinta" };

export function Cabecera({ children }: { children?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-center gap-x-5 gap-y-3 px-6 py-5 max-md:px-4 max-md:py-3 max-md:gap-x-2">
      <h1 className="font-titulo text-2xl leading-none font-extrabold tracking-tight whitespace-nowrap max-md:text-xl">
        PAU <em className="font-normal text-rojo">poc</em>
      </h1>
      <nav className="flex flex-1 gap-1 md:flex-none">
        <Link
          to="/"
          className={pestana}
          activeProps={pestanaActiva}
          activeOptions={{ exact: true, includeSearch: false }}
        >
          Preguntas
        </Link>
        <Link
          to="/catalogo"
          className={pestana}
          activeProps={pestanaActiva}
          activeOptions={{ includeSearch: false }}
        >
          Catálogo
        </Link>
      </nav>
      <div className="flex min-w-0 flex-1 items-center gap-2 max-md:order-last max-md:basis-full">
        {children}
      </div>
      <BotonTema />
    </header>
  );
}
