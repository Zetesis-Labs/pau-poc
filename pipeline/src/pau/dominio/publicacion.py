"""Conjunto publicado (`datos/`): qué documentos, preguntas, figuras y PDFs salen del corpus. Ver docs/datos.md."""

from dataclasses import dataclass

from pau.dominio.banco import ruta_pdf, sin_campos_internos
from pau.dominio.rubrica import es_pdf_local

CAMPOS_CATALOGO = (
    "id", "region", "fuente", "pagina", "asignatura", "anio", "convocatoria", "tipo",
    "titulo", "variante", "formato", "url", "descargable", "bytes", "error",
)


@dataclass(frozen=True)
class Publicacion:
    catalogo: dict
    preguntas: dict
    pdfs: dict[str, str]
    """ruta publicada (pdfs/<id>.pdf) → ruta del PDF original dentro de data/"""
    figuras: list[str]
    """nombres de archivo de las figuras referenciadas"""


def anexo_publicado(anexo: dict, documentos: dict[str, dict]) -> dict:
    """Los anexos sueltos, públicos y descargados en PDF de un examen procesado se publican en `pdfs/`; el resto solo se enlaza."""
    publicable = "incrustado" not in anexo and anexo["acceso"] == "publico" and es_pdf_local(documentos.get(anexo.get("id", "")))
    return {**anexo, "pdf": ruta_pdf(anexo["id"])} if publicable else anexo


def pdfs_referenciados(valor) -> set[str]:
    if isinstance(valor, dict):
        propio = {valor["pdf"]} if "pdf" in valor else set()
        return propio.union(*(pdfs_referenciados(v) for v in valor.values()))
    if isinstance(valor, list):
        return set().union(*(pdfs_referenciados(v) for v in valor))
    return set()


def documento_publicado(documento: dict, procesados: set[str], anexos: dict[str, list[dict]]) -> dict:
    publicado = {k: documento[k] for k in CAMPOS_CATALOGO if k in documento}
    publicado["procesado"] = documento["id"] in procesados
    if publicado["procesado"]:
        publicado["pdf"] = ruta_pdf(documento["id"])
    if documento["id"] in anexos:
        publicado["anexos"] = anexos[documento["id"]]
    return publicado


def pregunta_publicada(pregunta: dict, anexos: dict[str, list[dict]]) -> dict:
    publicada = sin_campos_internos(pregunta)
    return {**publicada, "examen": {**publicada["examen"], "anexos": anexos.get(publicada["examen"]["id"], [])}}


def figuras_referenciadas(preguntas: list[dict]) -> list[str]:
    return sorted({f["src"].removeprefix("figuras/") for p in preguntas for e in p["estimulos"] for f in e["figuras"]})


def publicar(examenes: dict, preguntas: list[dict], ejecucion: str, anexos: dict[str, list[dict]]) -> Publicacion:
    """`preguntas` son las del banco ya ancladas, con sus campos internos (`_archivo`); `anexos`, la corrección de cada examen."""
    procesados = {p["examen"]["id"] for p in preguntas}
    por_id = {d["id"]: d for d in examenes["documentos"]}
    anexos = {doc_id: [anexo_publicado(a, por_id) for a in lista] if doc_id in procesados else lista for doc_id, lista in anexos.items()}
    catalogo = {
        "generado": examenes["generado"],
        "fuentes": examenes["fuentes"],
        "documentos": [documento_publicado(d, procesados, anexos) for d in examenes["documentos"]],
    }
    publicadas = {"ejecucion": ejecucion, "preguntas": [pregunta_publicada(p, anexos) for p in preguntas]}
    originales = {ruta_pdf(d["id"]): d.get("archivo") for d in examenes["documentos"]} | {p["examen"]["pdf"]: p["_archivo"] for p in preguntas}
    return Publicacion(
        catalogo=catalogo,
        preguntas=publicadas,
        pdfs={ruta: originales[ruta] for ruta in sorted(pdfs_referenciados([catalogo, publicadas]))},
        figuras=figuras_referenciadas(preguntas),
    )
