"""Conjunto publicado (`datos/`): qué documentos, preguntas, figuras y PDFs salen del corpus. Ver docs/datos.md."""

from dataclasses import dataclass

from pau.dominio.banco import ruta_pdf, sin_campos_internos

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
    archivos = {p["examen"]["id"]: p["_archivo"] for p in preguntas}
    return Publicacion(
        catalogo={
            "generado": examenes["generado"],
            "fuentes": examenes["fuentes"],
            "documentos": [documento_publicado(d, procesados, anexos) for d in examenes["documentos"]],
        },
        preguntas={"ejecucion": ejecucion, "preguntas": [pregunta_publicada(p, anexos) for p in preguntas]},
        pdfs={ruta_pdf(doc_id): archivo for doc_id, archivo in sorted(archivos.items())},
        figuras=figuras_referenciadas(preguntas),
    )
