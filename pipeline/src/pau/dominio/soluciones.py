"""Soluciones: la respuesta de cada nodo del examen, oficial si la hay y de academia si no.

Etapa aparte de la rúbrica: las respuestas pueden venir de otros documentos (solucionarios, academias) y su
cobertura se mide por separado. Siempre se guarda de dónde sale cada respuesta.
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from pau.dominio.banco import ruta_pdf
from pau.dominio.esquema import ExamenExtraido, Idioma, Pagina, Texto
from pau.dominio.normalizar import normalizar_markdown
from pau.dominio.rubrica import CONTROL, es_pdf_local
from pau.dominio.validar import FORMULA, ComprobarKatex, Hallazgo, errores_katex

VERSION_SOLUCIONES = "s1"
TIPOS_RESPONDIBLES = ("pregunta", "apartado")

OrigenSolucion = Literal["oficial", "academia"]


class EntradaSolucion(BaseModel):
    nodo: str = Field(description="id del nodo del examen (n1, n2…) tal como aparece en el árbol que se te da.")
    respuesta: list[Texto] = Field(description="La respuesta o resolución de ese nodo, literal, en Markdown, por idioma.")
    paginas: list[Pagina] = Field(description="Página del PDF recibido donde está esta respuesta, una por idioma.")


class SolucionExtraida(BaseModel):
    contiene_soluciones: bool = Field(description="false si el documento no trae respuestas de este examen.")
    idiomas: list[Idioma]
    entradas: list[EntradaSolucion]
    sin_correspondencia: list[str] = Field(description="Respuestas que no has podido asociar a ningún nodo del árbol: su etiqueta y por qué.")
    incidencias: list[str] = Field(description="Dudas, contradicciones, erratas, partes ilegibles. Vacío si nada.")


@dataclass(frozen=True)
class FuenteSolucion:
    archivo: str
    desde: int
    anexo: dict


def _utilizables(anexos: list[dict], origen: OrigenSolucion) -> list[dict]:
    return [a for a in anexos if a["origen"] == origen and a["acceso"] == "publico"]


def fuente_de_solucion(examen: dict, anexos: list[dict], documentos: dict[str, dict], origen: OrigenSolucion) -> FuenteSolucion | None:
    """El mejor documento de ese origen con las respuestas: lo incrustado, luego solucionarios, luego criterios; la variante exacta antes."""
    candidatos = _utilizables(anexos, origen)
    for a in candidatos:
        if "incrustado" in a:
            return FuenteSolucion(examen["archivo"], a["incrustado"]["pagina"], a)
    sueltos = [a for a in candidatos if "incrustado" not in a and es_pdf_local(documentos.get(a.get("id", "")))]
    sueltos.sort(key=lambda a: (a["tipo"] != "solucion", a["coincidencia"] != "exacta"))
    return FuenteSolucion(documentos[sueltos[0]["id"]]["archivo"], 1, sueltos[0]) if sueltos else None


def _cubiertos(examen: ExamenExtraido, con_entrada: set[str]) -> set[str]:
    padre = {n.id: n.padre for n in examen.nodos}
    cubiertos = set()
    for n in examen.nodos:
        actual = n.id
        while actual:
            if actual in con_entrada:
                cubiertos.add(n.id)
                break
            actual = padre.get(actual)
    return cubiertos


def sin_respuesta(examen: ExamenExtraido, con_entrada: set[str]) -> list[str]:
    """Preguntas y apartados sin subdivisiones que no tienen respuesta propia ni de un nodo que los contenga."""
    con_hijos = {n.padre for n in examen.nodos}
    hojas = [n.id for n in examen.nodos if n.tipo in TIPOS_RESPONDIBLES and n.id not in con_hijos]
    cubiertos = _cubiertos(examen, con_entrada)
    return [h for h in hojas if h not in cubiertos]


def _limpios(textos: list[Texto]) -> list[Texto]:
    return [t.model_copy(update={"markdown": normalizar_markdown(CONTROL.sub("", t.markdown))}) for t in textos]


def normalizar_soluciones(solucion: SolucionExtraida, desde: int) -> SolucionExtraida:
    """Limpia el texto y pasa las páginas del recorte enviado al modelo a la numeración del PDF original."""
    entradas = [
        e.model_copy(update={
            "respuesta": _limpios(e.respuesta),
            "paginas": [p.model_copy(update={"pagina": p.pagina + desde - 1}) for p in e.paginas],
        })
        for e in solucion.entradas
    ]
    return solucion.model_copy(update={"entradas": entradas})


def validar_soluciones(solucion: SolucionExtraida, examen: ExamenExtraido, comprobar_katex: ComprobarKatex) -> list[Hallazgo]:
    if not solucion.contiene_soluciones:
        return [Hallazgo("sin-soluciones", False, "el documento no trae respuestas de este examen")]
    nodos = {n.id for n in examen.nodos}
    hallazgos, vistos = [], set()
    for e in solucion.entradas:
        if e.nodo not in nodos:
            hallazgos.append(Hallazgo("nodo-inexistente", True, e.nodo))
            continue
        if e.nodo in vistos:
            hallazgos.append(Hallazgo("nodo-repetido", False, e.nodo))
        vistos.add(e.nodo)
    huecos = sin_respuesta(examen, {e.nodo for e in solucion.entradas if e.respuesta})
    if huecos:
        hallazgos.append(Hallazgo("nodos-sin-respuesta", False, ", ".join(huecos)))
    formulas = [
        {"tex": (m.group(1) or m.group(2)).strip(), "bloque": m.group(1) is not None}
        for e in solucion.entradas for t in e.respuesta for m in FORMULA.finditer(t.markdown)
    ]
    return hallazgos + errores_katex(formulas, comprobar_katex)


def _por_idioma(textos: list[dict]) -> dict[str, str]:
    return {t["idioma"]: t["markdown"] for t in textos}


def _de_registro(registro: dict | None) -> dict[str, dict]:
    if not registro or not registro["resultado"]["contiene_soluciones"]:
        return {}
    anexo = registro["fuente"]["anexo"]
    procedencia = {"origen": anexo["origen"], "fuente": anexo["fuente"], "incrustado": "incrustado" in anexo}
    if not procedencia["incrustado"]:
        procedencia.update(url=anexo["url"], pdf=ruta_pdf(anexo["id"]))
    por_nodo = {}
    for e in registro["resultado"]["entradas"]:
        if e["respuesta"] and e["nodo"] not in por_nodo:
            por_nodo[e["nodo"]] = {"texto": _por_idioma(e["respuesta"]), **procedencia, "paginas": {p["idioma"]: p["pagina"] for p in e["paginas"]}}
    return por_nodo


def soluciones_por_nodo(oficial: dict | None, academia: dict | None) -> dict[str, dict]:
    """Respuesta publicable de cada nodo: la oficial y, donde no la hay, la de academia."""
    return {**_de_registro(academia), **_de_registro(oficial)}
