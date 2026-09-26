import { useMemo } from "react";
import { renderizar } from "~/dominio/markdown";

interface Props {
  readonly texto: string;
  readonly className?: string;
  readonly resaltar?: (html: string) => string;
}

export function Markdown({ texto, className = "prosa", resaltar }: Props) {
  const html = useMemo(() => {
    const base = renderizar(texto);
    return resaltar ? resaltar(base) : base;
  }, [texto, resaltar]);
  // biome-ignore lint/security/noDangerouslySetInnerHtml: HTML generado por marked y KaTeX a partir del conjunto publicado.
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
