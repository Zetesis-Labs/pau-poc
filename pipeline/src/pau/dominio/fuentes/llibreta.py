"""Parser puro de Acadèmia La Llibreta: una página por materia."""

from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup

from pau.dominio.documento import Documento, anio_de, asignatura_canonica, convocatoria_de, limpiar, plano

FUENTE = "llibreta"
INDICE = "https://academialallibreta.es/examenes-y-soluciones-selectividad-pau/"


def parse_indice(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    materias = []
    for a in soup.select("a[href]"):
        url = urljoin(INDICE, a["href"])
        resto = url.removeprefix(INDICE).strip("/")
        if url.startswith(INDICE) and resto and "/" not in resto and resto != "feed":
            materias.append(INDICE + resto + "/")
    return list(dict.fromkeys(materias))


def _tipo(a, texto: str) -> str:
    clases = " ".join(a.get("class", []))
    t = plano(texto)
    if "youtube" in a.get("href", "") or "video" in t:
        return "video"
    if "--crit" in clases or "criterio" in t:
        return "criterios"
    if "--sol" in clases or "solucion" in t:
        return "solucion"
    if "--model" in clases or "modelo" in t:
        return "modelo"
    return "examen"


def _variante(texto: str, url: str) -> str:
    t = plano(f"{texto} {unquote(url)}")
    for marca, variante in (("dana", "DANA"), ("2a convocatoria", "2ª convocatoria"), ("julio-2", "2ª convocatoria"), ("opcion a", "Opción A"), ("opcion b", "Opción B"), (" cv", "CV")):
        if marca in t:
            return variante
    return ""


def parse_materia(html: str, pagina: str) -> list[Documento]:
    soup = BeautifulSoup(html, "lxml")
    slug = pagina.rstrip("/").rsplit("/", 1)[-1]
    asignatura = asignatura_canonica(slug.replace("-", " "))
    documentos = []
    for caja in soup.select(".ll-exam-call-box"):
        cabecera = caja.find("h4")
        convocatoria_texto = limpiar(cabecera.get_text()) if cabecera else ""
        panel = caja.find_parent(attrs={"data-year-panel": True})
        anio = int(panel["data-year-panel"]) if panel else anio_de(convocatoria_texto)
        for a in caja.select("a[href]"):
            texto = limpiar(a.get_text())
            url = urljoin(pagina, a["href"])
            documentos.append(
                Documento(
                    region="Comunidad Valenciana",
                    fuente=FUENTE,
                    pagina=pagina,
                    asignatura=asignatura,
                    anio=anio,
                    convocatoria=convocatoria_de(convocatoria_texto),
                    tipo=_tipo(a, texto),
                    url=url,
                    titulo=f"{convocatoria_texto} — {texto}",
                    variante=_variante(f"{convocatoria_texto} {texto}", url),
                )
            )
    return documentos
