import DOMPurify from "dompurify";
import { useMemo } from "react";
import { renderizar } from "~/dominio/markdown";

interface Props {
  readonly texto: string;
  readonly className?: string;
  readonly resaltar?: (html: string) => string;
}

export function Markdown({ texto, className = "prosa", resaltar }: Props) {
  const html = useMemo(() => {
    if (!DOMPurify.isSupported) return null;
    const base = renderizar(texto);
    return DOMPurify.sanitize(resaltar ? resaltar(base) : base, {
      FORBID_TAGS: ["style", "form", "input", "button", "textarea", "select", "option"],
    });
  }, [texto, resaltar]);
  if (html === null) return <div className={className}>{texto}</div>;
  // biome-ignore lint/security/noDangerouslySetInnerHtml: DOMPurify sanea el resultado final, incluidas fórmulas y resaltado.
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
