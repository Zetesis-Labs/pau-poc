import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { BotonTema } from "./BotonTema";

const pestana = "font-mono text-xs px-2 py-1 border-b-2 border-transparent text-suave hover:text-tinta";
const pestanaActiva = { className: "!border-rojo !text-tinta" };

export function Cabecera({ children }: { children?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b-[3px] border-double border-tinta px-4 py-2.5">
      <h1 className="font-titulo text-2xl leading-none font-extrabold tracking-tight whitespace-nowrap">
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
      <div className="flex min-w-0 flex-1 items-center gap-4 max-md:order-last max-md:basis-full">
        {children}
      </div>
      <BotonTema />
    </header>
  );
}
