"""Recupera respuestas literales de rúbricas ya extraídas para nodos sin solución.

Es un filtro de publicación, no una validación académica. Las excepciones conocidas
proceden de docs/auditoria-2026-09-29/rubricas/informe.md.
"""

from collections import Counter

from pau.dominio.banco import ruta_pdf

TIPOS_RESPONDIBLES = frozenset({"pregunta", "apartado", "opcion"})
FUENTES_DE_ORIGEN_DUDOSO = frozenset({"c4afc8d9c75a", "361720afddf5"})
DOCUMENTOS_DE_CORRESPONDENCIA_DUDOSA = {
    "5091bd5d23ad": "correspondencia-parcial",
    "ab690a84e30c": "baremo-distinto",
}
NODOS_DE_PAGINA_INCORRECTA = {
    ("9c4cbc92103b", "n21"): "idioma-pagina-incorrectos",
    ("9c4cbc92103b", "n25"): "idioma-pagina-incorrectos",
    ("3c134e1125e6", "n9"): "pagina-incorrecta",
    ("cdd0f4f759e1", "n9"): "pagina-incorrecta",
}


def _motivo_fuente(registro: dict, rubrica: dict) -> str | None:
    fuente = rubrica.get("fuente") or {}
    anexo = fuente.get("anexo") or {}
    doc_id = registro.get("documento", {}).get("id")
    if rubrica.get("documento") != doc_id:
        return "documento-distinto"
    if not rubrica.get("resultado", {}).get("contiene_criterios"):
        return "sin-criterios"
    if anexo.get("id") in FUENTES_DE_ORIGEN_DUDOSO:
        return "origen-no-acreditado"
    if doc_id in DOCUMENTOS_DE_CORRESPONDENCIA_DUDOSA:
        return DOCUMENTOS_DE_CORRESPONDENCIA_DUDOSA[doc_id]
    if anexo.get("acceso") != "publico":
        return "fuente-no-publica"
    if anexo.get("origen") not in {"oficial", "academia"}:
        return "origen-no-admitido"
    if not anexo.get("fuente"):
        return "fuente-incompleta"
    incrustado = "incrustado" in anexo
    if incrustado:
        if not fuente.get("archivo") or fuente["archivo"] != registro.get("documento", {}).get("archivo"):
            return "incrustado-ajeno"
        pagina = anexo["incrustado"].get("pagina") if isinstance(anexo["incrustado"], dict) else None
        if type(pagina) is not int or pagina < 1 or pagina != fuente.get("desde"):
            return "fuente-incompleta"
    else:
        if not all(anexo.get(c) for c in ("id", "url")) or not fuente.get("archivo"):
            return "fuente-incompleta"
        if anexo.get("coincidencia") != "exacta":
            return "coincidencia-no-exacta"
    desde = fuente.get("desde")
    if type(desde) is not int or desde < 1:
        return "fuente-incompleta"
    return None


def _motivo_respuesta(entrada: dict, desde: int) -> str | None:
    respuesta = entrada.get("respuesta")
    if not isinstance(respuesta, list) or any(not isinstance(t, dict) or not isinstance(t.get("markdown"), str) or not t["markdown"].strip() for t in respuesta):
        return "respuesta-vacia"
    idiomas = [t.get("idioma") for t in respuesta]
    if any(not idioma for idioma in idiomas) or len(idiomas) != len(set(idiomas)):
        return "idioma-repetido"
    paginas = entrada.get("paginas")
    if not isinstance(paginas, list) or any(not isinstance(p, dict) for p in paginas):
        return "idiomas-paginas-distintos"
    idiomas_pagina = [p.get("idioma") for p in paginas]
    if len(idiomas_pagina) != len(set(idiomas_pagina)) or not set(idiomas).issubset(idiomas_pagina):
        return "idiomas-paginas-distintos"
    if any(type(p.get("pagina")) is not int or p["pagina"] < desde for p in paginas):
        return "pagina-fuera-de-fuente"
    return None


def _ancestro_con_solucion(nodo: str, nodos: dict[str, dict], soluciones: dict[str, dict]) -> bool:
    vistos = set()
    actual = nodos[nodo].get("padre")
    while actual and actual not in vistos:
        if actual in soluciones:
            return True
        vistos.add(actual)
        actual = nodos.get(actual, {}).get("padre")
    return False


def recuperar_respuestas(registro: dict, rubrica: dict | None, soluciones: dict[str, dict]) -> tuple[dict[str, dict], list[dict]]:
    """Conserva soluciones y añade respuestas r2 verificables, con una razón por entrada descartada.

    La entrada y la salida son datos JSON del pipeline. El filtro comprueba
    estructura y procedencia declarada; no comprueba el PDF ni la veracidad del texto.
    """
    combinadas = dict(soluciones)
    exclusiones: list[dict] = []
    if rubrica is None:
        return combinadas, exclusiones
    entradas = rubrica.get("resultado", {}).get("entradas", [])
    nodos = {n["id"]: n for n in registro.get("resultado", {}).get("nodos", [])}
    repetidos = Counter(e.get("nodo") for e in entradas)
    fuente = rubrica.get("fuente") or {}
    anexo = fuente.get("anexo") or {}
    doc_id = registro.get("documento", {}).get("id")
    motivo_fuente = _motivo_fuente(registro, rubrica)
    for entrada in entradas:
        if not entrada.get("respuesta"):
            continue
        nodo = entrada.get("nodo")
        motivo = (
            "solucion-existente" if nodo in soluciones else
            "ancestro-con-solucion" if nodo in nodos and _ancestro_con_solucion(nodo, nodos, soluciones) else
            "nodo-repetido" if repetidos[nodo] > 1 else
            "nodo-inexistente" if nodo not in nodos else
            "tipo-no-respondible" if nodos[nodo].get("tipo") not in TIPOS_RESPONDIBLES else
            NODOS_DE_PAGINA_INCORRECTA.get((doc_id, nodo)) or
            motivo_fuente or _motivo_respuesta(entrada, fuente.get("desde", 1))
        )
        if motivo:
            exclusiones.append({"etapa": "respuesta-rubrica", "nodo": nodo, "motivo": motivo})
            continue
        incrustado = "incrustado" in anexo
        procedencia = {"origen": anexo["origen"], "fuente": anexo["fuente"], "incrustado": incrustado}
        if not incrustado:
            procedencia.update(url=anexo["url"], pdf=ruta_pdf(anexo["id"]))
        idiomas_respuesta = {t["idioma"] for t in entrada["respuesta"]}
        combinadas[nodo] = {
            "texto": {t["idioma"]: t["markdown"] for t in entrada["respuesta"]},
            **procedencia,
            "paginas": {p["idioma"]: p["pagina"] for p in entrada["paginas"] if p["idioma"] in idiomas_respuesta},
            "extraccion": "rubrica",
        }
    return combinadas, exclusiones
