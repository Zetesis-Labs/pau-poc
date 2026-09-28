"""Aplana las extracciones en un banco de preguntas y decide la franja de cada pregunta en su página."""

import re
from collections.abc import Callable

from pau.dominio.geometria import Bloque, Caja
from pau.dominio.rubrica import rubricas_por_nodo

FORMULA = re.compile(r"\$\$(.+?)\$\$|\$([^$]+)\$", re.S)
FORMULA_TRIVIAL = re.compile(r"[\w\s.,:;+\-−=%()/·']*")
MARKDOWN = re.compile(r"[*_#>`|\\]")
PUNTUACION_FINAL = ".,;:"
PALABRAS_ANCLA = 6
CERCANIA_ETIQUETA = 0.12
CERCANIA_APARTADO = 0.2
SEPARACION_MINIMA = 0.005
ALTO_MINIMO = 0.05
CAMPOS_EXAMEN = ("id", "region", "asignatura", "anio", "convocatoria", "tipo", "fuente", "url")

Buscar = Callable[[str], list[Caja]]


def ruta_pdf(doc_id: str) -> str:
    return f"pdfs/{doc_id}.pdf"


def ruta_figura(archivo: str) -> str:
    return f"figuras/{archivo}"


def _por_idioma(textos: list[dict]) -> dict[str, str]:
    return {t["idioma"]: t["markdown"] for t in textos}


def _hijos(nodos: list[dict]) -> dict[str | None, list[dict]]:
    arbol: dict[str | None, list[dict]] = {}
    for nodo in nodos:
        arbol.setdefault(nodo["padre"], []).append(nodo)
    for hermanos in arbol.values():
        hermanos.sort(key=lambda n: n["orden"])
    return arbol


def regla(eleccion: dict | None) -> str:
    if not eleccion:
        return ""
    if eleccion["minimo"] == eleccion["maximo"] and eleccion["maximo"]:
        cuantos = str(eleccion["maximo"])
    else:
        cuantos = f"{eleccion['minimo'] or 0}–{eleccion['maximo'] or '?'}"
    media = " (nota media)" if eleccion["agregacion"] == "media" else ""
    return f"elegir {cuantos} de {eleccion['de'] or '?'}{media}"


def _apartados(nodo: dict, arbol: dict, rubricas: dict[str, dict], soluciones: dict[str, dict]) -> list[dict]:
    return [
        {
            "etiqueta": _por_idioma(h["etiqueta"]),
            "enunciado": _por_idioma(h["enunciado"]),
            "puntos": h["puntos"],
            "estimulos": h["estimulos"],
            "regla": regla(h["eleccion"]),
            "rubrica": rubricas.get(h["id"]),
            "solucion": soluciones.get(h["id"]),
            "apartados": _apartados(h, arbol, rubricas, soluciones),
        }
        for h in arbol.get(nodo["id"], [])
    ]


def fuente_publicada(fuente: dict) -> dict:
    anexo = fuente["anexo"]
    publicada = {"tipo": anexo["tipo"], "incrustado": "incrustado" in anexo}
    return publicada if publicada["incrustado"] else {**publicada, "url": anexo["url"], "pdf": ruta_pdf(anexo["id"])}


def _estimulos_usados(nodo: dict, arbol: dict, ancestros: list[dict]) -> list[str]:
    ids = [e for a in ancestros for e in a["estimulos"]] + list(nodo["estimulos"])
    pendientes = list(arbol.get(nodo["id"], []))
    while pendientes:
        hijo = pendientes.pop()
        ids += hijo["estimulos"]
        pendientes += arbol.get(hijo["id"], [])
    return list(dict.fromkeys(ids))


def _formula_plana(decimal: str) -> Callable[[re.Match], str]:
    """Las fórmulas triviales ($1$, $2{,}5$, $x$) se leen en el PDF como texto; las demás no se pueden buscar."""
    def plana(m: re.Match) -> str:
        tex = (m.group(1) or m.group(2)).replace("{,}", decimal).replace("{.}", decimal).strip()
        return tex if "\\" not in tex and FORMULA_TRIVIAL.fullmatch(tex) else " "
    return plana


def texto_plano(md: str, decimal: str = ",") -> str:
    palabras = MARKDOWN.sub(" ", FORMULA.sub(_formula_plana(decimal), md)).split()
    return " ".join(p for p in palabras if any(c.isalnum() for c in p))


def _sin_formulas(md: str) -> str:
    return re.sub(r"\s+", " ", MARKDOWN.sub(" ", FORMULA.sub(" ", md))).strip()


def variantes(md: str) -> list[str]:
    """Formas de buscar un texto en el PDF, de la más fiel a la más tolerante: el PDF puede escribir los decimales con punto."""
    return list(dict.fromkeys(v for v in (texto_plano(md, ","), texto_plano(md, "."), _sin_formulas(md)) if v))


def _enunciado_de_anclaje(nodo: dict, arbol: dict, idioma: str) -> str:
    propio = _por_idioma(nodo["enunciado"]).get(idioma, "")
    if len(texto_plano(propio).split()) >= 3:
        return propio
    hijos = arbol.get(nodo["id"], [])
    return _por_idioma(hijos[0]["enunciado"]).get(idioma, "") if hijos else propio


def _ancestros(nodo: dict, por_id: dict) -> list[dict]:
    """Del más externo al padre inmediato."""
    lista, actual = [], por_id.get(nodo["padre"])
    while actual:
        lista.insert(0, actual)
        actual = por_id.get(actual["padre"])
    return lista


def unidades(nodos: list[dict], por_id: dict) -> list[dict]:
    """Preguntas del banco: las `pregunta` más externas; si el modelo no tipó ninguna, las alternativas que no agrupan otras."""
    preguntas = [n for n in nodos if n["tipo"] == "pregunta" and not any(a["tipo"] == "pregunta" for a in _ancestros(n, por_id))]
    if preguntas:
        return preguntas
    con_hijos_estructurales = {n["padre"] for n in nodos if n["tipo"] in ("opcion", "pregunta", "bloque")}
    return [n for n in nodos if n["tipo"] == "opcion" and n["id"] not in con_hijos_estructurales]


def preguntas_de(registro: dict, rubrica: dict | None = None, soluciones: dict[str, dict] | None = None) -> list[dict]:
    """Preguntas de un registro de extracción, con la rúbrica y la solución de cada nodo si las hay.

    Los campos con `_` son internos del anclaje y no se publican.
    """
    soluciones = soluciones or {}
    res, doc = registro["resultado"], registro["documento"]
    con_rubrica = bool(rubrica and rubrica["resultado"]["contiene_criterios"])
    rubricas, generales = rubricas_por_nodo(rubrica["resultado"]) if con_rubrica else ({}, {})
    por_id = {n["id"]: n for n in res["nodos"]}
    arbol = _hijos(res["nodos"])
    estimulos = {e["id"]: e for e in res["estimulos"]}
    figuras = [f for f in registro.get("figuras", []) if f.get("archivo")]
    salida = []
    for nodo in unidades(res["nodos"], por_id):
        ancestros = _ancestros(nodo, por_id)
        usados = _estimulos_usados(nodo, arbol, ancestros)
        salida.append({
            "id": f"{doc['id']}:{nodo['id']}",
            "examen": {**{k: doc[k] for k in CAMPOS_EXAMEN}, "pdf": ruta_pdf(doc["id"])},
            "reglaExamen": regla(res["eleccion_raiz"]),
            "contexto": [
                {"etiqueta": _por_idioma(a["etiqueta"]), "tipo": a["tipo"], "enunciado": _por_idioma(a["enunciado"]), "regla": regla(a["eleccion"]), "sintetico": a.get("sintetico", False)}
                for a in ancestros
            ],
            "etiqueta": _por_idioma(nodo["etiqueta"]),
            "enunciado": _por_idioma(nodo["enunciado"]),
            "puntos": nodo["puntos"],
            "rubrica": rubricas.get(nodo["id"]),
            "solucion": soluciones.get(nodo["id"]),
            "criteriosGenerales": generales,
            "fuenteRubrica": fuente_publicada(rubrica["fuente"]) if con_rubrica else None,
            "apartados": _apartados(nodo, arbol, rubricas, soluciones),
            "idiomas": sorted({t["idioma"] for t in nodo["enunciado"]} or set(res["idiomas"])),
            "estimulos": [
                {
                    "id": e,
                    "tipo": estimulos[e]["tipo"],
                    "descripcion": estimulos[e]["descripcion"],
                    "contenido": _por_idioma(estimulos[e]["contenido"]),
                    "figuras": [{"src": ruta_figura(f["archivo"]), "idioma": f["idioma"]} for f in figuras if f["estimulo"] == e],
                }
                for e in usados if e in estimulos
            ],
            "paginas": {p["idioma"]: p["pagina"] for p in nodo["paginas"]},
            "_archivo": doc["archivo"],
            "_ancla": {p["idioma"]: variantes(_enunciado_de_anclaje(nodo, arbol, p["idioma"])) for p in nodo["paginas"]},
            "_primerApartado": {
                p["idioma"]: variantes(_por_idioma(arbol[nodo["id"]][0]["enunciado"]).get(p["idioma"], "")) if arbol.get(nodo["id"]) else []
                for p in nodo["paginas"]
            },
            "_etiquetaPlana": {p["idioma"]: texto_plano(_por_idioma(nodo["etiqueta"]).get(p["idioma"], "")) for p in nodo["paginas"]},
        })
    return salida


def sin_campos_internos(pregunta: dict) -> dict:
    return {k: v for k, v in pregunta.items() if not k.startswith("_")}


def apariciones(buscar: Buscar, texto: str, minimo: int = 3) -> list[Caja]:
    """Busca el texto por sus primeras palabras, acortando la búsqueda hasta encontrarlo; la puntuación final no cuenta."""
    palabras = texto.split()
    for n in (PALABRAS_ANCLA, 4, 3, 2, 1):
        if n < minimo or len(palabras) < n:
            continue
        encontrados = buscar(" ".join(palabras[:n]).rstrip(PUNTUACION_FINAL))
        if encontrados:
            return encontrados
    return []


def primeras_apariciones(buscar: Buscar, alternativas: list[str], minimo: int = 3) -> list[Caja]:
    return next((encontrados for texto in alternativas if (encontrados := apariciones(buscar, texto, minimo))), [])


def desambiguar(enunciados: list[Caja], apartados: list[Caja], alto: float) -> list[Caja]:
    """Si el enunciado aparece varias veces (por ejemplo en un índice), elige la aparición seguida de su primer apartado."""
    if len(enunciados) < 2:
        return enunciados
    distancias = [(min((a.y0 - e.y0 for a in apartados if 0 < a.y0 - e.y0 <= CERCANIA_APARTADO * alto), default=None), e) for e in enunciados]
    seguidos = [(d, e) for d, e in distancias if d is not None]
    return [min(seguidos, key=lambda x: x[0])[1]] if seguidos else enunciados[-1:]


def inicio(enunciados: list[Caja], etiquetas: list[Caja], alto: float) -> float | None:
    """Inicio de la pregunta: la etiqueta inmediatamente encima de su enunciado, o el enunciado si no hay etiqueta cerca."""
    if enunciados:
        base = enunciados[0].y0
        encima = [e.y0 for e in etiquetas if 0 <= base - e.y0 <= CERCANIA_ETIQUETA * alto]
        return (max(encima) if encima else base) / alto
    return etiquetas[-1].y0 / alto if etiquetas else None


def inicio_en_pagina(pregunta: dict, idioma: str, buscar: Buscar, alto: float) -> float | None:
    etiqueta = pregunta["_etiquetaPlana"].get(idioma, "")
    etiquetas = apariciones(buscar, etiqueta, minimo=1) if len(etiqueta) > 3 else []
    enunciados = desambiguar(
        primeras_apariciones(buscar, pregunta["_ancla"].get(idioma, [])),
        primeras_apariciones(buscar, pregunta["_primerApartado"].get(idioma, [])),
        alto,
    )
    return inicio(enunciados, etiquetas, alto)


def fin_de_contenido(bloques: list[Bloque], alto: float) -> float:
    utiles = [b for b in bloques if b.texto.strip() and not b.texto.strip().isdigit()]
    return min(1.0, max((b.caja.y1 for b in utiles), default=alto) / alto + 0.01)


def franjas(inicios: list[float], limite: float) -> list[float]:
    """Final de cada pregunta de una página: el inicio de la siguiente estrictamente por debajo, o el final del contenido."""
    finales = []
    for y in inicios:
        posteriores = [otro for otro in inicios if otro > y + SEPARACION_MINIMA]
        finales.append(round(min(posteriores) if posteriores else max(limite, y + ALTO_MINIMO), 4))
    return finales
