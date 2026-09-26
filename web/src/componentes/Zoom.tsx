import { useEffect } from "react";

export function Zoom({ src, onCerrar }: { src: string | null; onCerrar: () => void }) {
  useEffect(() => {
    if (!src) return;
    const cerrarConEscape = (ev: KeyboardEvent) => ev.key === "Escape" && onCerrar();
    window.addEventListener("keydown", cerrarConEscape);
    return () => window.removeEventListener("keydown", cerrarConEscape);
  }, [src, onCerrar]);
  if (!src) return null;
  return (
    <button
      type="button"
      onClick={onCerrar}
      aria-label="Cerrar imagen ampliada"
      className="fixed inset-0 z-10 grid cursor-zoom-out place-items-center bg-black/80 p-8"
    >
      <img src={src} alt="" className="max-h-full max-w-full bg-white" />
    </button>
  );
}
