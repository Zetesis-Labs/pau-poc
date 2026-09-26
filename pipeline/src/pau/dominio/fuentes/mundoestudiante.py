"""Parser puro de mundoestudiante: una sola página con todos los enlaces de Madrid."""

import re
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from pau.dominio.documento import Documento, anio_de, asignatura_canonica, convocatoria_de, limpiar, plano

FUENTE = "mundoestudiante"
PAGINA = "https://mundoestudiante.com/examenes-resueltos/selectividad/madrid/"


def _materia(a) -> str:
    columna = a.find_parent(class_="gb-block-layout-column-inner")
    etiqueta = columna.find("p") if columna else None
    if etiqueta and limpiar(etiqueta.get_text()):
        return limpiar(etiqueta.get_text())
    nombre = unquote(a["href"]).rsplit("/", 1)[-1].replace("+", " ")
    return nombre.split("Madrid", 1)[-1]


def _tipo(texto: str, url: str) -> str:
    t = plano(f"{texto} {unquote(url)}")
    if "solucion" in t:
        return "solucion"
    if "criterio" in t:
        return "criterios"
    if "modelo" in t:
        return "modelo"
    return "examen"


def _variante(texto: str, nombre_fichero: str) -> str:
    opcion = re.search(r"opcion[ _]([ab])\b", plano(f"{texto} {nombre_fichero}"))
    if opcion:
        return f"Opción {opcion.group(1).upper()}"
    return "V2" if " V2" in nombre_fichero else ""


def parse(html: str) -> list[Documento]:
    soup = BeautifulSoup(html, "lxml")
    documentos = []
    for a in soup.select("a[href]"):
        url = urljoin(PAGINA, a["href"])
        if not url.lower().split("?")[0].endswith(".pdf"):
            continue
        cabecera = a.find_previous("h3")
        contexto = limpiar(cabecera.get_text()) if cabecera else ""
        nombre_fichero = unquote(url).rsplit("/", 1)[-1].replace("+", " ")
        materia = _materia(a)
        texto = limpiar(a.get_text())
        documentos.append(
            Documento(
                region="Madrid",
                fuente=FUENTE,
                pagina=PAGINA,
                asignatura=asignatura_canonica(materia),
                anio=anio_de(contexto) or anio_de(nombre_fichero),
                convocatoria=convocatoria_de(f"{contexto} {nombre_fichero}"),
                tipo=_tipo(texto, url),
                url=url,
                titulo=f"{materia} — {texto} ({contexto})",
                variante=_variante(texto, nombre_fichero),
            )
        )
    return documentos
