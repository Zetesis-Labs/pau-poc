"""Parser puro de EHU: páginas anuales de exámenes de acceso."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pau.dominio.documento import Documento, anio_de, asignatura_canonica, convocatoria_de, limpiar, plano

FUENTE = "ehu"
INDICE = "https://www.ehu.eus/es/web/unibertsitaterako-sarbidea/pruebas-de-acceso/examenes-de-cursos-anteriores/bachillerato-y-ciclos-formativos-de-grado-superior"


def parse_indice(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    paginas = []
    for a in soup.select("a[href]"):
        url = urljoin(INDICE, a["href"]).split("?")[0]
        if re.search(r"/20\d\d$", url) and url.startswith(INDICE) or re.search(r"/(eau|pau)-20\d\d/examenes", url):
            paginas.append(url)
    return list(dict.fromkeys(paginas))


def _es_documento(url: str) -> bool:
    return "/documents/" in url


def _tipo(texto: str, url: str) -> str:
    t = plano(f"{texto} {url}")
    if "audio" in t or "ehutb" in t:
        return "audio"
    if "criterio" in t or "zuzentze" in t:
        return "criterios"
    if "solucion" in t or "ebazpen" in t:
        return "solucion"
    return "examen"


def _partir(texto: str) -> tuple[str, str, str]:
    partes = re.split(r"\s*-\s*(?=convocatoria)", texto, maxsplit=1, flags=re.I)
    return (partes[0], "-", partes[1]) if len(partes) == 2 else (texto, "", "")


def _formato_listado(contenido, pagina: str, anio: int | None) -> list[Documento]:
    documentos = []
    for a in contenido.select("li a[href]"):
        url = urljoin(pagina, a["href"])
        if not _es_documento(url):
            continue
        partes = a.select("span")
        texto = limpiar(partes[1].get_text() if len(partes) > 1 else a.get_text())
        materia, _, resto = _partir(texto)
        seccion = a.find_previous("h2")
        contexto = f"{resto} {limpiar(seccion.get_text()) if seccion else ''}"
        documentos.append(
            Documento(
                region="País Vasco",
                fuente=FUENTE,
                pagina=pagina,
                asignatura="General" if "criterio" in plano(materia) else asignatura_canonica(materia),
                anio=anio,
                convocatoria=convocatoria_de(resto or contexto),
                tipo=_tipo(f"{texto} {contexto}", url),
                url=url,
                titulo=texto,
            )
        )
    return documentos


def _formato_secciones(contenido, pagina: str, anio: int | None) -> list[Documento]:
    documentos = []
    for a in contenido.select("a[href]"):
        url = urljoin(pagina, a["href"])
        es_audio = "ehutb" in url
        if not (_es_documento(url) or es_audio):
            continue
        materia = a.find_previous(["h3", "h4"])
        seccion = a.find_previous("h2")
        texto = limpiar(a.get_text())
        nombre = limpiar(materia.get_text()) if materia else texto
        documentos.append(
            Documento(
                region="País Vasco",
                fuente=FUENTE,
                pagina=pagina,
                asignatura=asignatura_canonica(nombre),
                anio=anio,
                convocatoria=convocatoria_de(f"{limpiar(seccion.get_text()) if seccion else ''} {pagina}"),
                tipo=_tipo(texto, url),
                url=url,
                titulo=f"{nombre} — {texto}",
            )
        )
    return documentos


def parse_pagina(html: str, pagina: str) -> list[Documento]:
    soup = BeautifulSoup(html, "lxml")
    contenido = soup.select_one(".information-detail") or soup.select_one("#content") or soup
    anio = anio_de(pagina)
    if contenido.select("li a.bullet-pdf, li a[href*='/documents/']"):
        return _formato_listado(contenido, pagina, anio)
    return _formato_secciones(contenido, pagina, anio)
