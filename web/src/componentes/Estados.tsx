export const Cargando = ({ que }: { que: string }) => (
  <p className="p-10 text-center font-mono text-xs text-suave">Cargando {que}…</p>
);

export const ErrorDeCarga = ({ error }: { error: unknown }) => (
  <div className="m-8 border-2 border-rojo p-5">
    <b>No se pudieron cargar los datos.</b>
    <p className="font-mono text-sm">{error instanceof Error ? error.message : String(error)}</p>
  </div>
);
