"""Parser puro de UC3M: índice de materias y una página por materia."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from pau.dominio.documento import Documento, anio_de, asignatura_canonica, convocatoria_de, limpiar, plano

FUENTE = "uc3m"
INDICE = "https://www.uc3m.es/pruebasacceso/modelos-examenes&idioma=es"
MODELOS_VIGENTES = "1371318815066"


def parse_indice(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    central = soup.select_one(".contCentral") or soup
    materias: dict[str, str] = {}
    for a in central.select("a[href*='TextoMixta']"):
        texto = limpiar(a.get_text())
        if texto:
            materias.setdefault(urljoin(INDICE, a["href"]), texto)
    return [(texto, url) for url, texto in materias.items()]


def _texto_con_contexto(a) -> str:
    texto = limpiar(a.get_text())
    contenedor = a.find_parent("li") or a.find_parent("p")
    if contenedor is not None and not re.search(r"20\d\d", texto):
        return limpiar(contenedor.get_text())
    return texto


def _cabeceras(tabla) -> list[str]:
    return [limpiar(th.get_text()) for th in tabla.select("thead th")] or [
        limpiar(td.get_text()) for td in tabla.select("tr:first-child td")
    ]


def _tipo(texto: str, columna: str) -> str:
    t = plano(texto)
    if "criterio" in t:
        return "criterios"
    if "solucion" in t:
        return "solucion"
    if "modelo" in plano(columna) or "modelo" in t:
        return "modelo"
    return "examen"


def _variante(texto: str) -> str:
    resto = re.sub(r"20\d\d\s*-\s*20\d*", "", texto)
    for palabra in ("lunes", "martes", "coincidencias", "criterios", "soluciones"):
        if palabra in plano(resto):
            return palabra
    return ""


def parse_materia(html: str, pagina: str, nombre: str) -> list[Documento]:
    soup = BeautifulSoup(html, "lxml")
    central = soup.select_one(".contCentral") or soup
    documentos = []
    for tabla in central.select("table") or [central]:
        cabeceras = _cabeceras(tabla) if tabla.name == "table" else []
        for a in tabla.select("a[href]"):
            href = urljoin(pagina, a["href"])
            if "drive.google" not in href and not href.lower().endswith(".pdf"):
                continue
            texto = _texto_con_contexto(a)
            celda = a.find_parent("td")
            columna = ""
            if celda is not None and cabeceras:
                indice = len(celda.find_previous_siblings("td"))
                columna = cabeceras[indice] if indice < len(cabeceras) else ""
            es_modelos_vigentes = MODELOS_VIGENTES in pagina
            asignatura = asignatura_canonica(texto if es_modelos_vigentes else nombre)
            if es_modelos_vigentes:
                columna = "Modelos 2025-2026"
            documentos.append(
                Documento(
                    region="Madrid",
                    fuente=FUENTE,
                    pagina=pagina,
                    asignatura=asignatura,
                    anio=anio_de(texto) or anio_de(columna),
                    convocatoria=convocatoria_de(columna or texto),
                    tipo=_tipo(texto, columna),
                    url=href,
                    titulo=texto,
                    variante=_variante(texto),
                )
            )
    return documentos
