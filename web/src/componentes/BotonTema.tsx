export function BotonTema() {
  const alternar = () => {
    const raiz = document.documentElement;
    raiz.dataset.tema = raiz.dataset.tema === "oscuro" ? "claro" : "oscuro";
    try {
      localStorage.setItem("pau-tema", raiz.dataset.tema);
    } catch {
      // Sin almacenamiento el tema solo dura la visita.
    }
  };
  return (
    <button
      type="button"
      onClick={alternar}
      title="Cambiar tema"
      className="cursor-pointer border-[1.5px] border-tinta px-2.5 py-1 font-mono text-xs hover:bg-tinta hover:text-papel"
    >
      ◐
    </button>
  );
}
