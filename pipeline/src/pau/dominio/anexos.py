"""Vínculo de cada examen con su corrección: criterios y soluciones, sueltos o dentro del mismo PDF. Ver docs/datos.md."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

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
    """Corrección que viene dentro del propio PDF del examen, a partir de `pagina`."""

    tipo: TipoAnexo
    pagina: int


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
    v = documento_o_variante if isinstance(documento_o_variante, str) else documento_o_variante.get("variante", "")
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
            coincidencia = encaje(examen.get("variante", ""), anexo.get("variante", ""))
            if coincidencia:
                propios.append(_anexo_suelto(anexo, coincidencia))
        if propios:
            vinculos[examen["id"]] = sorted(propios, key=_orden)
    return vinculos


def huerfanos(documentos: list[dict]) -> list[dict]:
    """Criterios y soluciones que no cuadran con ningún examen del catálogo."""
    vinculados = {a["id"] for anexos in vincular(documentos, {}).values() for a in anexos}
    return [d for d in documentos if d["tipo"] in TIPOS_ANEXO and d["id"] not in vinculados]


def incrustado_por_extraccion(otro_contenido: list[str], paginas_enunciado: list[int], paginas: int) -> Incrustado | None:
    """Con la extracción del modelo: la corrección empieza en la primera página tras el último enunciado."""
    tipos = [t for t in ("criterios", "soluciones") if t in otro_contenido]
    primera = max(paginas_enunciado, default=0) + 1
    if not tipos or primera > paginas:
        return None
    return Incrustado("criterios" if "criterios" in tipos else "solucion", primera)


def incrustado_por_texto(textos_por_pagina: list[str]) -> Incrustado | None:
    """Sin extracción: la primera página, salvo la portada, con el título de unos criterios o unas soluciones."""
    for numero, texto in enumerate(textos_por_pagina[1:], start=2):
        if CRITERIOS_EN_TEXTO.search(texto):
            return Incrustado("criterios", numero)
        if SOLUCIONES_EN_TEXTO.search(texto):
            return Incrustado("solucion", numero)
    return None
