"""Rúbrica de corrección: qué valora el corrector en cada nodo del examen, extraída de los criterios oficiales.

Es una etapa aparte de la extracción del enunciado: recibe el árbol ya extraído y solo asocia a sus nodos lo que
dicen los criterios. Así los puntos del enunciado y los de los criterios se pueden contrastar en vez de mezclarse.
"""

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field

from pau.dominio.esquema import ExamenExtraido, Idioma, Pagina, Texto
from pau.dominio.normalizar import normalizar_markdown
from pau.dominio.validar import FORMULA, ComprobarKatex, Hallazgo, errores_katex

VERSION_RUBRICA = "r1"
TOLERANCIA = 0.01
LARGO_ENUNCIADO = 160
CONTROL = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class Tramo(BaseModel):
    descripcion: list[Texto] = Field(description="Qué se puntúa en este tramo, literal, por idioma.")
    puntos: float = Field(description="Puntos que da este tramo según los criterios.")


class EntradaRubrica(BaseModel):
    nodo: str = Field(description="id del nodo del examen (n1, n2…) tal como aparece en el árbol que se te da.")
    puntos: float | None = Field(description="Puntuación máxima que los criterios dan a este nodo; null si no la dan.")
    criterios: list[Texto] = Field(description="Qué valora el corrector en este nodo, literal, en Markdown, por idioma.")
    desglose: list[Tramo] = Field(description="Reparto de los puntos dentro del nodo si los criterios lo detallan; vacío si no.")
    respuesta: list[Texto] = Field(description="Respuesta o solución que dan los criterios para este nodo, literal; vacío si no la dan.")
    paginas: list[Pagina] = Field(description="Página del PDF recibido donde están estos criterios, una por idioma.")


class RubricaExtraida(BaseModel):
    contiene_criterios: bool = Field(description="false si el documento no trae criterios ni soluciones de este examen.")
    idiomas: list[Idioma]
    generales: list[Texto] = Field(description="Criterios que valen para todo el examen (presentación, ortografía, penalizaciones…), literales.")
    entradas: list[EntradaRubrica]
    sin_correspondencia: list[str] = Field(description="Criterios que no has podido asociar a ningún nodo del árbol: su etiqueta y por qué.")
    incidencias: list[str] = Field(description="Dudas, contradicciones entre criterios y enunciado, erratas. Vacío si nada.")


@dataclass(frozen=True)
class FuenteRubrica:
    archivo: str
    """Ruta del PDF dentro de data/."""
    desde: int
    """Primera página que se envía al modelo (1 = el documento entero)."""
    anexo: dict


def es_pdf_local(documento: dict | None) -> bool:
    return bool(documento and documento.get("bytes") and documento.get("archivo", "").endswith(".pdf"))


def fuente_de_rubrica(examen: dict, anexos: list[dict], documentos: dict[str, dict]) -> FuenteRubrica | None:
    """El mejor documento oficial y legible con la corrección de un examen: la incrustada, luego criterios, luego soluciones."""
    oficiales = [a for a in anexos if a["origen"] == "oficial" and a["acceso"] == "publico"]
    for a in oficiales:
        if "incrustado" in a:
            return FuenteRubrica(examen["archivo"], a["incrustado"]["pagina"], a)
    sueltos = [a for a in oficiales if "incrustado" not in a and es_pdf_local(documentos.get(a.get("id", "")))]
    sueltos.sort(key=lambda a: (a["tipo"] != "criterios", a["coincidencia"] != "exacta"))
    if not sueltos:
        return None
    return FuenteRubrica(documentos[sueltos[0]["id"]]["archivo"], 1, sueltos[0])


def _primero(textos: list[Texto]) -> str:
    return textos[0].markdown if textos else ""


def _recortado(texto: str) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= LARGO_ENUNCIADO else plano[: LARGO_ENUNCIADO - 1] + "…"


def arbol_para_el_modelo(examen: ExamenExtraido) -> str:
    """El árbol ya extraído, una línea por nodo, para que el modelo asocie cada criterio a su id."""
    lineas = ["id | padre | tipo | etiqueta | puntos | enunciado"]
    for n in examen.nodos:
        puntos = "-" if n.puntos is None else str(n.puntos)
        lineas.append(f"{n.id} | {n.padre or '-'} | {n.tipo} | {_primero(n.etiqueta)} | {puntos} | {_recortado(_primero(n.enunciado))}")
    return "\n".join(lineas)


def paginas_originales(rubrica: RubricaExtraida, desde: int) -> RubricaExtraida:
    """El modelo numera las páginas del recorte que recibe; se pasan a la numeración del PDF original."""
    if desde == 1:
        return rubrica
    desplazar = lambda paginas: [p.model_copy(update={"pagina": p.pagina + desde - 1}) for p in paginas]  # noqa: E731
    return rubrica.model_copy(update={"entradas": [e.model_copy(update={"paginas": desplazar(e.paginas)}) for e in rubrica.entradas]})


def _limpios(textos: list[Texto]) -> list[Texto]:
    return [t.model_copy(update={"markdown": normalizar_markdown(CONTROL.sub("", t.markdown))}) for t in textos]


def normalizar_rubrica(rubrica: RubricaExtraida) -> RubricaExtraida:
    """Quita caracteres de control (secuencias ANSI que a veces cuela el modelo) y aplica las correcciones tipográficas del enunciado."""
    entradas = [
        e.model_copy(update={
            "criterios": _limpios(e.criterios),
            "respuesta": _limpios(e.respuesta),
            "desglose": [t.model_copy(update={"descripcion": _limpios(t.descripcion)}) for t in e.desglose],
        })
        for e in rubrica.entradas
    ]
    return rubrica.model_copy(update={"generales": _limpios(rubrica.generales), "entradas": entradas})


def _formulas(rubrica: RubricaExtraida) -> list[dict]:
    textos = [t.markdown for t in rubrica.generales]
    for e in rubrica.entradas:
        textos += [t.markdown for t in (*e.criterios, *e.respuesta)]
        textos += [t.markdown for tramo in e.desglose for t in tramo.descripcion]
    return [{"tex": (m.group(1) or m.group(2)).strip(), "bloque": m.group(1) is not None} for texto in textos for m in FORMULA.finditer(texto)]


def _cubiertos(examen: ExamenExtraido, con_entrada: set[str]) -> set[str]:
    """Un nodo está cubierto si tiene entrada él, algún antepasado o algún descendiente."""
    padre = {n.id: n.padre for n in examen.nodos}
    cubiertos = set()
    for nodo_id in con_entrada:
        actual = nodo_id
        while actual:
            cubiertos.add(actual)
            actual = padre.get(actual)
    hijos: dict[str | None, list[str]] = {}
    for n in examen.nodos:
        hijos.setdefault(n.padre, []).append(n.id)
    pendientes = list(con_entrada)
    while pendientes:
        actual = pendientes.pop()
        cubiertos.add(actual)
        pendientes += hijos.get(actual, [])
    return cubiertos


def validar_rubrica(rubrica: RubricaExtraida, examen: ExamenExtraido, comprobar_katex: ComprobarKatex) -> list[Hallazgo]:
    if not rubrica.contiene_criterios:
        return [Hallazgo("sin-criterios", False, "el documento no trae criterios de este examen")]
    nodos = {n.id: n for n in examen.nodos}
    hallazgos, vistos = [], set()
    for e in rubrica.entradas:
        if e.nodo not in nodos:
            hallazgos.append(Hallazgo("nodo-inexistente", True, e.nodo))
            continue
        if e.nodo in vistos:
            hallazgos.append(Hallazgo("nodo-repetido", False, e.nodo))
        vistos.add(e.nodo)
        esperado = nodos[e.nodo].puntos
        if e.puntos is not None and esperado is not None and abs(e.puntos - esperado) > TOLERANCIA:
            hallazgos.append(Hallazgo("puntos-distintos", False, f"{e.nodo}: enunciado {esperado}, criterios {e.puntos}"))
        suma = sum(t.puntos for t in e.desglose)
        if e.desglose and e.puntos is not None and abs(suma - e.puntos) > TOLERANCIA:
            hallazgos.append(Hallazgo("desglose-no-suma", False, f"{e.nodo}: {suma} de {e.puntos}"))
    puntuados = {n.id for n in examen.nodos if n.puntos is not None}
    huecos = sorted(puntuados - _cubiertos(examen, vistos))
    if huecos:
        hallazgos.append(Hallazgo("nodos-sin-rubrica", False, ", ".join(huecos)))
    return hallazgos + errores_katex(_formulas(rubrica), comprobar_katex)


def _por_idioma(textos: list[dict]) -> dict[str, str]:
    return {t["idioma"]: t["markdown"] for t in textos}


def rubricas_por_nodo(resultado: dict) -> tuple[dict[str, dict], dict[str, str]]:
    """Rúbrica publicable de cada nodo y criterios generales del examen. La respuesta se publica desde la fase de soluciones."""
    por_nodo = {}
    for e in resultado["entradas"]:
        por_nodo.setdefault(e["nodo"], {
            "puntos": e["puntos"],
            "criterios": _por_idioma(e["criterios"]),
            "desglose": [{"descripcion": _por_idioma(t["descripcion"]), "puntos": t["puntos"]} for t in e["desglose"]],
            "paginas": {p["idioma"]: p["pagina"] for p in e["paginas"]},
        })
    return por_nodo, _por_idioma(resultado["generales"])
