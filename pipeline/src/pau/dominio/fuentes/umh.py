"""Parser puro de Banc de la Selectivitat (UMH): materias, convocatorias y PDFs."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pau.dominio.documento import Documento, anio_de, convocatoria_de, limpiar, plano

FUENTE = "umh"
BASE = "https://bancdelaselectivitat.umh.es/examenes-resueltos/"


def _normalizar(url: str) -> str:
    return url.replace("http://", "https://").rstrip("/") + "/"


def _contenido(soup):
    return soup.select_one("#left-area") or soup.select_one("article") or soup


def _es_hija(url: str, padre: str) -> bool:
    return url.startswith(padre) and url != padre and "/examenes-resueltos/http" not in url


def parse_indice(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    materias = []
    for a in soup.select("a[href]"):
        url = _normalizar(urljoin(BASE, a["href"]))
        resto = url.removeprefix(BASE).strip("/")
        if _es_hija(url, BASE) and resto and "/" not in resto:
            materias.append(url)
    return list(dict.fromkeys(materias))


def parse_materia(html: str, pagina: str) -> tuple[str, list[tuple[str, str]]]:
    soup = BeautifulSoup(html, "lxml")
    titulo = soup.select_one("h1")
    nombre = limpiar(titulo.get_text()) if titulo else pagina.rstrip("/").rsplit("/", 1)[-1]
    convocatorias: dict[str, str] = {}
    for a in soup.select("a[href]"):
        url = _normalizar(urljoin(pagina, a["href"]))
        etiqueta = limpiar(a.get_text())
        if _es_hija(url, pagina) and etiqueta:
            convocatorias.setdefault(url, etiqueta)
    return nombre, [(etiqueta, url) for url, etiqueta in convocatorias.items()]


def _tipo_pdf(texto: str, url: str) -> str:
    t = plano(f"{texto} {url}")
    if "criteri" in t:
        return "criterios"
    if "soluc" in t or "resuel" in t or "sol-" in t:
        return "solucion"
    return "examen"


def _anio_corto(pagina: str) -> int | None:
    sufijo = re.search(r"-(\d\d)/?$", pagina)
    return 2000 + int(sufijo.group(1)) if sufijo else None


def parse_convocatoria(html: str, pagina: str, asignatura: str, etiqueta: str) -> list[Documento]:
    soup = BeautifulSoup(html, "lxml")
    contenido = _contenido(soup)
    titulo = soup.select_one("h1")
    respaldo = " ".join([limpiar(titulo.get_text()) if titulo else "", *(limpiar(a.get_text()) for a in contenido.select("a[href$='.pdf']"))])
    anio = anio_de(etiqueta) or anio_de(pagina) or _anio_corto(pagina)
    convocatoria = convocatoria_de(etiqueta)
    if convocatoria == "otra":
        convocatoria = convocatoria_de(f"{respaldo} {pagina}")
    comunes = dict(region="Comunidad Valenciana", fuente=FUENTE, pagina=pagina, asignatura=asignatura, anio=anio, convocatoria=convocatoria)
    documentos = []
    vistos = set()
    for a in contenido.select("a[href]"):
        url = urljoin(pagina, a["href"])
        if not url.lower().split("?")[0].endswith(".pdf") or url in vistos:
            continue
        vistos.add(url)
        texto = limpiar(a.get_text()) or url.rsplit("/", 1)[-1]
        documentos.append(Documento(**comunes, tipo=_tipo_pdf(texto, url), url=url, titulo=texto))
    for iframe in contenido.select("iframe[src*='youtube']"):
        url = iframe["src"].split("?")[0]
        if url in vistos:
            continue
        vistos.add(url)
        titulo = limpiar(iframe.get("title", "")) or "Vídeo con la resolución"
        documentos.append(Documento(**comunes, tipo="video", url=url, titulo=titulo))
    return documentos
