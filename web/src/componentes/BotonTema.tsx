import { useEffect, useState } from "react";

type Preferencia = "sistema" | "claro" | "oscuro";

export function BotonTema() {
  const [preferencia, setPreferencia] = useState<Preferencia | null>(null);

  useEffect(() => {
    let elegida: Preferencia = "sistema";
    try {
      const guardada = localStorage.getItem("pau-tema");
      if (guardada === "claro" || guardada === "oscuro") elegida = guardada;
    } catch {
      // La preferencia del navegador funciona también sin almacenamiento.
    }
    setPreferencia(elegida);
  }, []);

  useEffect(() => {
    if (!preferencia) return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const aplicar = () => {
      document.documentElement.dataset.tema =
        preferencia === "sistema" ? (media.matches ? "oscuro" : "claro") : preferencia;
    };
    aplicar();
    media.addEventListener("change", aplicar);
    return () => media.removeEventListener("change", aplicar);
  }, [preferencia]);

  const cambiar = (valor: string) => {
    if (valor !== "sistema" && valor !== "claro" && valor !== "oscuro") return;
    setPreferencia(valor);
    try {
      if (valor === "sistema") localStorage.removeItem("pau-tema");
      else localStorage.setItem("pau-tema", valor);
    } catch {
      // Sin almacenamiento la elección se mantiene durante esta visita.
    }
  };

  return (
    <label className="flex items-center gap-1.5 rounded-full bg-papel-2 px-3 py-2 font-mono text-xs text-suave max-md:px-2 max-md:text-[10px]">
      <span aria-hidden="true">◐</span>
      <span className="sr-only">Tema</span>
      <select
        value={preferencia ?? "sistema"}
        onChange={(event) => cambiar(event.target.value)}
        className="min-w-0 cursor-pointer bg-transparent text-tinta"
      >
        <option value="sistema">Sistema</option>
        <option value="claro">Claro</option>
        <option value="oscuro">Oscuro</option>
      </select>
    </label>
  );
}
