"""Recorre las seis fuentes y compone el catálogo."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from pau.dominio.catalogo import deduplicar, registro
from pau.dominio.documento import Documento, asignatura_canonica
from pau.dominio.fuentes import academy, ehu, llibreta, mundoestudiante, uc3m, umh
from pau.puertos import Web


def _academy(web: Web) -> list[Documento]:
    return academy.parse(web.texto(academy.DATOS))


def _ehu(web: Web) -> list[Documento]:
    return [d for pagina in ehu.parse_indice(web.texto(ehu.INDICE)) for d in ehu.parse_pagina(web.texto(pagina), pagina)]


def _llibreta(web: Web) -> list[Documento]:
    return [d for materia in llibreta.parse_indice(web.texto(llibreta.INDICE)) for d in llibreta.parse_materia(web.texto(materia), materia)]


def _mundoestudiante(web: Web) -> list[Documento]:
    return mundoestudiante.parse(web.texto(mundoestudiante.PAGINA))


def _uc3m(web: Web) -> list[Documento]:
    return [d for nombre, url in uc3m.parse_indice(web.texto(uc3m.INDICE)) for d in uc3m.parse_materia(web.texto(url), url, nombre)]


def _umh(web: Web) -> list[Documento]:
    documentos = []
    for materia in umh.parse_indice(web.texto(umh.BASE)):
        nombre, convocatorias = umh.parse_materia(web.texto(materia), materia)
        asignatura = asignatura_canonica(nombre)
        for etiqueta, url in convocatorias:
            documentos += umh.parse_convocatoria(web.texto(url), url, asignatura, etiqueta)
    return documentos


FUENTES = {
    uc3m.FUENTE: (_uc3m, {"region": "Madrid", "url": uc3m.INDICE}),
    mundoestudiante.FUENTE: (_mundoestudiante, {"region": "Madrid", "url": mundoestudiante.PAGINA}),
    umh.FUENTE: (_umh, {"region": "Comunidad Valenciana", "url": umh.BASE}),
    llibreta.FUENTE: (_llibreta, {"region": "Comunidad Valenciana", "url": llibreta.INDICE}),
    ehu.FUENTE: (_ehu, {"region": "País Vasco", "url": ehu.INDICE}),
    academy.FUENTE: (_academy, {"region": "País Vasco", "url": academy.INDICE}),
}


def rastrear(web: Web, nombres: list[str]) -> list[Documento]:
    documentos = []
    for nombre in nombres:
        encontrados = FUENTES[nombre][0](web)
        print(f"{nombre}: {len(encontrados)} enlaces", file=sys.stderr)
        documentos += encontrados
    return deduplicar(documentos)


def descargas_previas(ruta: Path) -> dict[str, dict]:
    """Resultados de descarga de un catálogo anterior, para no perderlos al volver a rastrear."""
    if not ruta.exists():
        return {}
    campos = ("archivo", "bytes", "error")
    return {d["id"]: {k: d[k] for k in campos if k in d} for d in json.loads(ruta.read_text())["documentos"]}


def catalogo(documentos: list[Documento], nombres: list[str], descargas: dict[str, dict]) -> dict:
    return {
        "generado": datetime.now(UTC).isoformat(timespec="seconds"),
        "fuentes": {nombre: FUENTES[nombre][1] for nombre in nombres},
        "documentos": [registro(d, descargas) for d in documentos],
    }
