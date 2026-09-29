"""Vínculo de cada examen con su corrección: criterios y soluciones, sueltos o dentro del mismo PDF. Ver docs/datos.md."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal
from urllib.parse import unquote

from pau.dominio.fuentes.mundoestudiante import variante_de

TipoAnexo = Literal["criterios", "solucion"]
Origen = Literal["oficial", "academia"]
Acceso = Literal["publico", "privado", "roto"]
Encaje = Literal["exacta", "por_clave"]

TIPOS_EXAMEN = ("examen", "modelo")
TIPOS_ANEXO = ("criterios", "solucion")
FUENTES_CON_SOLUCION_OFICIAL = ("uc3m", "ehu", "umh")
VARIANTES_SIN_SIGNIFICADO = ("soluciones", "criterios")

CRITERIOS_EN_TEXTO = re.compile(
    r"criterios\s+espec[ií]ficos\s+de\s+correcci|criteris\s+espec[ií]fics\s+de\s+correcci|"
    r"soluciones\s+y\s+criterios|zuzentzeko\s+(?:eta\s+kalifikatzeko\s+)?irizpide",
    re.I,
)
SOLUCIONES_EN_TEXTO = re.compile(r"^\s*(?:soluci[oó]n(?:es)?|solucions?|ebazpen(?:ak)?)\s*$", re.I | re.M)


@dataclass(frozen=True)
class Incrustado:
    """Corrección que viene dentro del propio PDF del examen, a partir de `pagina`: criterios, solución o ambos."""

    contenido: tuple[TipoAnexo, ...]
    pagina: int

    @property
    def tipo(self) -> TipoAnexo:
        return self.contenido[0]


def origen(fuente: str, tipo: str) -> Origen:
    if tipo == "criterios" or fuente in FUENTES_CON_SOLUCION_OFICIAL:
        return "oficial"
    return "academia"


def acceso(documento: dict) -> Acceso:
    error = documento.get("error")
    if not error:
        return "publico"
    return "privado" if error.startswith("privado") else "roto"


def _variante(documento_o_variante: dict | str) -> str:
    if isinstance(documento_o_variante, str):
        v = documento_o_variante
    else:
        v = documento_o_variante.get("variante", "")
        if not v and documento_o_variante.get("fuente") == "mundoestudiante":
            nombre = unquote(documento_o_variante.get("url", "")).rsplit("/", 1)[-1].replace("+", " ")
            v = variante_de("", nombre)
    return "" if v in VARIANTES_SIN_SIGNIFICADO else v


def encaje(variante_examen: str, variante_anexo: str) -> Encaje | None:
    a, b = _variante(variante_examen), _variante(variante_anexo)
    if a == b:
        return "exacta"
    if not a or not b:
        return "por_clave"
    return None


def clave(documento: dict) -> tuple:
    return (documento["region"], documento["asignatura"], documento["anio"], documento["convocatoria"])


def _anexo_suelto(documento: dict, coincidencia: Encaje) -> dict:
    return {
        "id": documento["id"],
        "tipo": documento["tipo"],
        "contenido": [documento["tipo"]],
        "origen": origen(documento["fuente"], documento["tipo"]),
        "fuente": documento["fuente"],
        "acceso": acceso(documento),
        "coincidencia": coincidencia,
        "url": documento["url"],
        "titulo": documento.get("titulo", ""),
    }


def _anexo_incrustado(examen: dict, incrustado: Incrustado) -> dict:
    return {
        "tipo": incrustado.tipo,
        "contenido": list(incrustado.contenido),
        "origen": origen(examen["fuente"], incrustado.tipo),
        "fuente": examen["fuente"],
        "acceso": "publico",
        "coincidencia": "exacta",
        "incrustado": {"pagina": incrustado.pagina},
    }


def _orden(anexo: dict) -> tuple:
    return (
        "incrustado" not in anexo,
        anexo["origen"] != "oficial",
        anexo["tipo"] != "criterios",
        anexo["acceso"] != "publico",
        anexo.get("id", ""),
    )


def vincular(documentos: list[dict], incrustados: dict[str, Incrustado]) -> dict[str, list[dict]]:
    """Anexos de cada examen (solo los que tienen alguno), ordenados de más a menos fiable."""
    anexos_por_clave: dict[tuple, list[dict]] = defaultdict(list)
    for d in documentos:
        if d["tipo"] in TIPOS_ANEXO:
            anexos_por_clave[clave(d)].append(d)
    vinculos: dict[str, list[dict]] = {}
    for examen in documentos:
        if examen["tipo"] not in TIPOS_EXAMEN:
            continue
        propios = [_anexo_incrustado(examen, incrustados[examen["id"]])] if examen["id"] in incrustados else []
        for anexo in anexos_por_clave.get(clave(examen), []):
            coincidencia = encaje(_variante(examen), _variante(anexo))
            if coincidencia:
                propios.append(_anexo_suelto(anexo, coincidencia))
        if propios:
            vinculos[examen["id"]] = sorted(propios, key=_orden)
    return vinculos


def huerfanos(documentos: list[dict]) -> list[dict]:
    """Criterios y soluciones que no cuadran con ningún examen del catálogo."""
    vinculados = {a["id"] for anexos in vincular(documentos, {}).values() for a in anexos}
    return [d for d in documentos if d["tipo"] in TIPOS_ANEXO and d["id"] not in vinculados]


def incrustado_por_extraccion(otro_contenido: list[str], paginas_enunciado: list[int], textos_por_pagina: list[str]) -> Incrustado | None:
    """Con la extracción del modelo: la corrección empieza en la primera página no vacía tras el último enunciado
    (en un escaneado, sin capa de texto, en la siguiente sin más)."""
    tipos = [t for t in ("criterios", "soluciones") if t in otro_contenido]
    tras_enunciado = range(max(paginas_enunciado, default=0) + 1, len(textos_por_pagina) + 1)
    escaneado = not any(t.strip() for t in textos_por_pagina)
    primera = next((n for n in tras_enunciado if escaneado or textos_por_pagina[n - 1].strip()), None)
    if not tipos or primera is None:
        return None
    return Incrustado(tuple("criterios" if t == "criterios" else "solucion" for t in tipos), primera)


def incrustado_por_texto(textos_por_pagina: list[str]) -> Incrustado | None:
    """Sin extracción: la primera página, salvo la portada, con el título de unos criterios o unas soluciones."""
    for numero, texto in enumerate(textos_por_pagina[1:], start=2):
        if CRITERIOS_EN_TEXTO.search(texto):
            con_soluciones = any(SOLUCIONES_EN_TEXTO.search(t) for t in textos_por_pagina[numero - 1 :])
            return Incrustado(("criterios", "solucion") if con_soluciones else ("criterios",), numero)
        if SOLUCIONES_EN_TEXTO.search(texto):
            return Incrustado(("solucion",), numero)
    return None


def combinar(por_texto: dict[str, Incrustado], por_extraccion: dict[str, Incrustado]) -> dict[str, Incrustado]:
    """La página la da el título encontrado en el texto (la extracción no ve las hojas en blanco); el contenido, ambos."""
    combinados = {}
    for doc_id in por_texto.keys() | por_extraccion.keys():
        texto, extraccion = por_texto.get(doc_id), por_extraccion.get(doc_id)
        base = texto or extraccion
        contenido = tuple(t for t in ("criterios", "solucion") if any(t in i.contenido for i in (texto, extraccion) if i))
        combinados[doc_id] = Incrustado(contenido, base.pagina)
    return combinados
