"""Métricas de una extracción y su parecido con una ejecución de referencia."""

import re
import unicodedata
from difflib import SequenceMatcher
from statistics import mean

FORMULA = re.compile(r"\$\$.+?\$\$|(?<![\\$])\$(?!\$).+?(?<![\\$])\$", re.S)


def _plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", sin_tildes).strip()


def _etiqueta(nodo: dict) -> str:
    valor = nodo["etiqueta"]
    texto = valor if isinstance(valor, str) else next((t["markdown"] for t in valor if t["idioma"] == "es"), valor[0]["markdown"] if valor else "")
    return re.sub(r"[^a-z0-9]", "", _plano(texto))


def _texto(textos: list[dict], idioma: str) -> str:
    elegido = next((t for t in textos if t["idioma"] == idioma), textos[0] if textos else None)
    return _plano(elegido["markdown"]) if elegido else ""


def rutas(resultado: dict) -> dict[tuple, dict]:
    por_id = {n["id"]: n for n in resultado["nodos"]}

    def ruta(nodo: dict) -> tuple:
        partes = []
        while nodo:
            partes.append((nodo["tipo"], nodo["orden"]))
            nodo = por_id.get(nodo["padre"])
        return tuple(reversed(partes))

    return {ruta(n): n for n in resultado["nodos"]}


def metricas(registro: dict) -> dict:
    res = registro["resultado"]
    textos = [t["markdown"] for n in res["nodos"] for t in n["enunciado"]]
    return {
        "preguntas": sum(n["tipo"] == "pregunta" for n in res["nodos"]),
        "apartados": sum(n["tipo"] == "apartado" for n in res["nodos"]),
        "con_puntos": sum(n["puntos"] is not None for n in res["nodos"]),
        "reglas": sum(n["eleccion"] is not None for n in res["nodos"]) + (res["eleccion_raiz"] is not None),
        "formulas": sum(len(FORMULA.findall(t)) for t in textos),
        "idiomas": ",".join(sorted(res["idiomas"])),
        "graves": [h["regla"] for h in registro["hallazgos"] if h["grave"]],
        "incidencias": len(res["incidencias"]),
    }


def similitud(referencia: dict, candidato: dict) -> tuple[float, float]:
    ref, cand = rutas(referencia["resultado"]), rutas(candidato["resultado"])
    idioma = "es" if "es" in referencia["resultado"]["idiomas"] else referencia["resultado"]["idiomas"][0]
    comunes = [r for r in ref if r in cand]
    ratios = [
        SequenceMatcher(None, _texto(ref[r]["enunciado"], idioma), _texto(cand[r]["enunciado"], idioma)).ratio()
        for r in comunes
        if _texto(ref[r]["enunciado"], idioma)
    ]
    return len(comunes) / max(len(ref), 1), mean(ratios) if ratios else 0.0
