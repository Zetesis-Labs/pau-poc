"""Correcciones tipográficas sin ambigüedad, aplicadas tras la extracción. Funciones puras."""

import re

from pau.dominio.esquema import ExamenExtraido, Nodo, ReglaEleccion, Texto

MATEMATICAS = re.compile(r"\$\$.+?\$\$|(?<![\\$])\$(?!\$).+?(?<![\\$])\$", re.S)
GRADO_EN_FORMULA = re.compile(r"(?:\^\s*)?[º°](?!\})")
GRADO_EN_TEXTO = re.compile(r"(?<=\d)(\s?)º(?=\s?[CKF]\b)")
TRIGONOMETRIA = re.compile(r"\\(sen|tg|cotg|cosec|arcsen|arctg|arccotg|senh|tgh)(?![a-zA-Z])")


def _formula(tex: str) -> str:
    return TRIGONOMETRIA.sub(r"\\operatorname{\1}", GRADO_EN_FORMULA.sub(r"^{\\circ}", tex))


def normalizar_markdown(md: str) -> str:
    partes, ultimo = [], 0
    for m in MATEMATICAS.finditer(md):
        partes.append(GRADO_EN_TEXTO.sub(r"\1°", md[ultimo:m.start()]))
        partes.append(_formula(m.group(0)))
        ultimo = m.end()
    partes.append(GRADO_EN_TEXTO.sub(r"\1°", md[ultimo:]))
    return "".join(partes)


def _textos(textos: list[Texto]) -> tuple[list[Texto], int]:
    nuevos = [t.model_copy(update={"markdown": normalizar_markdown(t.markdown)}) for t in textos]
    return nuevos, sum(a.markdown != b.markdown for a, b in zip(textos, nuevos, strict=True))


REGLA_INFERIDA = "Regla «elegir 1» inferida en la normalización: {etiqueta} tiene {n} alternativas de tipo opción sin regla de elección."


def _regla_de_alternativas(n: int) -> ReglaEleccion:
    return ReglaEleccion(minimo=1, maximo=1, de=n, agregacion="suma", literal=[])


def inferir_reglas(examen: ExamenExtraido) -> tuple[ExamenExtraido, list[str]]:
    """Unas alternativas de tipo opción sin regla en su padre solo pueden significar «elegir una»."""
    hijos: dict[str | None, list[Nodo]] = {}
    for nodo in examen.nodos:
        hijos.setdefault(nodo.padre, []).append(nodo)
    notas, nodos = [], []
    for nodo in examen.nodos:
        opciones = [h for h in hijos.get(nodo.id, []) if h.tipo == "opcion"]
        if len(opciones) >= 2 and nodo.eleccion is None:
            nodo = nodo.model_copy(update={"eleccion": _regla_de_alternativas(len(opciones))})
            notas.append(REGLA_INFERIDA.format(etiqueta=nodo.etiqueta[0].markdown if nodo.etiqueta else nodo.id, n=len(opciones)))
        nodos.append(nodo)
    raiz = [n for n in hijos.get(None, []) if n.tipo == "opcion"]
    eleccion_raiz = examen.eleccion_raiz
    if len(raiz) >= 2 and eleccion_raiz is None:
        eleccion_raiz = _regla_de_alternativas(len(raiz))
        notas.append(REGLA_INFERIDA.format(etiqueta="el examen", n=len(raiz)))
    return examen.model_copy(update={"nodos": nodos, "eleccion_raiz": eleccion_raiz, "incidencias": [*examen.incidencias, *notas]}), notas


def normalizar(examen: ExamenExtraido) -> tuple[ExamenExtraido, int]:
    cambios = 0
    nodos = []
    for nodo in examen.nodos:
        enunciado, n = _textos(nodo.enunciado)
        cambios += n
        nodos.append(nodo.model_copy(update={"enunciado": enunciado}))
    estimulos = []
    for estimulo in examen.estimulos:
        contenido, n = _textos(estimulo.contenido)
        cambios += n
        estimulos.append(estimulo.model_copy(update={"contenido": contenido}))
    instrucciones, n = _textos(examen.instrucciones)
    cambios += n
    examen, notas = inferir_reglas(examen.model_copy(update={"nodos": nodos, "estimulos": estimulos, "instrucciones": instrucciones}))
    return examen, cambios + len(notas)
