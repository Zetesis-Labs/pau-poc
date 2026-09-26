"""Validaciones deterministas de un examen extraído. Funciones puras: la comprobación de KaTeX se inyecta."""

import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from pau.dominio.esquema import ExamenExtraido, Nodo, ReglaEleccion

TOLERANCIA = 0.01
TIPOS_CON_ENUNCIADO = ("pregunta", "apartado")
FORMULA = re.compile(r"\$\$(.+?)\$\$|(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$", re.S)


@dataclass(frozen=True)
class Hallazgo:
    regla: str
    grave: bool
    detalle: str


def _etiqueta(nodo: Nodo) -> str:
    return nodo.etiqueta[0].markdown if nodo.etiqueta else nodo.id


def _hijos(nodos: list[Nodo]) -> dict[str | None, list[Nodo]]:
    arbol: dict[str | None, list[Nodo]] = defaultdict(list)
    for nodo in nodos:
        arbol[nodo.padre].append(nodo)
    for hermanos in arbol.values():
        hermanos.sort(key=lambda n: n.orden)
    return arbol


def estructura(examen: ExamenExtraido) -> list[Hallazgo]:
    hallazgos = []
    ids = Counter(n.id for n in examen.nodos)
    for repetido in (i for i, c in ids.items() if c > 1):
        hallazgos.append(Hallazgo("id-duplicado", True, repetido))
    conocidos = set(ids)
    for nodo in examen.nodos:
        if nodo.padre is not None and nodo.padre not in conocidos:
            hallazgos.append(Hallazgo("padre-inexistente", True, f"{nodo.id} → {nodo.padre}"))
    padres = {n.id: n.padre for n in examen.nodos}
    for nodo in examen.nodos:
        visto, actual = set(), nodo.id
        while actual is not None and actual not in visto:
            visto.add(actual)
            actual = padres.get(actual)
        if actual is not None:
            hallazgos.append(Hallazgo("ciclo", True, nodo.id))
    if not any(n.tipo == "pregunta" for n in examen.nodos):
        hallazgos.append(Hallazgo("sin-preguntas", True, ""))
    por_id = {n.id: n for n in examen.nodos}
    for nodo in examen.nodos:
        padre = por_id.get(nodo.padre)
        if nodo.tipo == "pregunta" and padre is not None and padre.tipo == "pregunta":
            hallazgos.append(Hallazgo("pregunta-dentro-de-pregunta", True, f"{nodo.id} en {padre.id}"))
    hijos = _hijos(examen.nodos)
    for padre_id, hermanos in hijos.items():
        regla = examen.eleccion_raiz if padre_id is None else por_id[padre_id].eleccion if padre_id in por_id else None
        if sum(h.tipo == "opcion" for h in hermanos) >= 2 and regla is None:
            hallazgos.append(Hallazgo("opciones-sin-regla", True, str(padre_id)))
    return hallazgos


def contenido(examen: ExamenExtraido) -> list[Hallazgo]:
    hallazgos = []
    estimulos = {e.id for e in examen.estimulos}
    arbol = _hijos(examen.nodos)
    for nodo in examen.nodos:
        vacio = not any(t.markdown.strip() for t in nodo.enunciado)
        if vacio and nodo.tipo in TIPOS_CON_ENUNCIADO and not arbol.get(nodo.id) and not nodo.estimulos:
            hallazgos.append(Hallazgo("enunciado-vacio", True, f"{nodo.id} ({_etiqueta(nodo)})"))
        for ref in nodo.estimulos:
            if ref not in estimulos:
                hallazgos.append(Hallazgo("estimulo-inexistente", True, f"{nodo.id} → {ref}"))
    idiomas_nodos = {t.idioma for n in examen.nodos for t in n.enunciado}
    for idioma in set(examen.idiomas) - idiomas_nodos:
        hallazgos.append(Hallazgo("idioma-sin-textos", False, idioma))
    if len(examen.idiomas) > 1:
        preguntas = [n for n in examen.nodos if n.tipo in TIPOS_CON_ENUNCIADO and n.enunciado]
        cojas = [n.id for n in preguntas if len({t.idioma for t in n.enunciado}) < len(set(examen.idiomas) & idiomas_nodos)]
        if cojas:
            hallazgos.append(Hallazgo("version-linguistica-incompleta", False, f"{len(cojas)}/{len(preguntas)} nodos"))
    return hallazgos


def numeracion(examen: ExamenExtraido) -> list[Hallazgo]:
    hallazgos = []
    for padre, hermanos in _hijos(examen.nodos).items():
        ordenes = [n.orden for n in hermanos]
        if ordenes != list(range(1, len(hermanos) + 1)):
            hallazgos.append(Hallazgo("orden-no-consecutivo", False, f"hijos de {padre}: {ordenes}"))
    return hallazgos


def _maximo(regla: ReglaEleccion | None, valores: list[float]) -> float:
    elegidos = sorted(valores, reverse=True)[: regla.maximo] if regla and regla.maximo else valores
    if regla and regla.agregacion == "media" and elegidos:
        return sum(elegidos) / len(elegidos)
    return sum(elegidos)


def _puntos(nodo_id: str | None, arbol: dict, regla: ReglaEleccion | None, propios: float | None, hallazgos: list[Hallazgo]) -> float | None:
    hijos = arbol.get(nodo_id, [])
    valores = [_puntos(h.id, arbol, h.eleccion, h.puntos, hallazgos) for h in hijos]
    if hijos and all(v is not None for v in valores):
        calculado = _maximo(regla, valores)
        if propios is not None and abs(calculado - propios) > TOLERANCIA:
            hallazgos.append(Hallazgo("puntos-no-cuadran", True, f"{nodo_id}: declarado {propios}, hijos {calculado:g}"))
        return propios if propios is not None else calculado
    return propios


def puntuacion(examen: ExamenExtraido) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    if not any(n.puntos is not None for n in examen.nodos):
        return [Hallazgo("sin-puntuaciones", False, "")]
    total = _puntos(None, _hijos(examen.nodos), examen.eleccion_raiz, None, hallazgos)
    esperado = examen.puntuacion_total or 10
    if total is None:
        hallazgos.append(Hallazgo("total-incalculable", False, "faltan puntos en algún nodo"))
    elif abs(total - esperado) > TOLERANCIA:
        elegidas = examen.eleccion_raiz.maximo if examen.eleccion_raiz and examen.eleccion_raiz.maximo else None
        if elegidas and abs(total - esperado * elegidas) <= TOLERANCIA:
            hallazgos.append(Hallazgo("media-implicita", False, f"{elegidas} preguntas de {esperado:g}: la nota sería la media"))
        else:
            hallazgos.append(Hallazgo("total-distinto", True, f"calculado {total:g}, esperado {esperado:g}"))
    for regla in [examen.eleccion_raiz, *(n.eleccion for n in examen.nodos)]:
        if regla and regla.de and ((regla.maximo or 0) > regla.de or (regla.minimo or 0) > (regla.maximo or regla.de)):
            hallazgos.append(Hallazgo("eleccion-imposible", True, f"{regla.minimo}–{regla.maximo} de {regla.de}"))
    return hallazgos


def paginas(examen: ExamenExtraido) -> list[Hallazgo]:
    idiomas = set(examen.idiomas)
    faltan = [n.id for n in examen.nodos if n.tipo == "pregunta" and {p.idioma for p in n.paginas} < idiomas]
    return [Hallazgo("pagina-sin-idioma", False, f"{len(faltan)} preguntas")] if faltan and len(idiomas) > 1 else []


DATOS = re.compile(r"(?:^|\s|\*)Datos?\s*[:.]", re.I)
QUIMICA_SUELTA = re.compile(r"(?<![\w$\\{])(?=[A-Za-z0-9]*\d)(?:[A-Z][a-z]?\d{0,3}){2,}(?![\w}])")
FLECHA = re.compile(r"[→⇌⟶⇄]")
NOTA_MEDIA = re.compile(r"\bmedia\b|divide(?:n|rá)? entre|mitjana|batez beste", re.I)
COMA_DECIMAL = re.compile(r"(?<![{\d])\d+,\d")


def _fuera_de_formulas(md: str) -> str:
    return FORMULA.sub(" ", md)


def _es(textos: list) -> str:
    return next((t.markdown for t in textos if t.idioma == "es"), textos[0].markdown if textos else "")


def calidad(examen: ExamenExtraido) -> list[Hallazgo]:
    hallazgos = []
    arbol = _hijos(examen.nodos)
    for nodo in examen.nodos:
        texto = _es(nodo.enunciado)
        if nodo.tipo == "apartado" and DATOS.search(texto):
            hallazgos.append(Hallazgo("datos-en-apartado", False, f"{nodo.id} ({_etiqueta(nodo)})"))
        if re.match(r"\W*Datos?\b", texto, re.I) and not arbol.get(nodo.id):
            hallazgos.append(Hallazgo("nodo-solo-datos", False, nodo.id))
    textos = [t.markdown for n in examen.nodos for t in n.enunciado] + [t.markdown for e in examen.estimulos for t in e.contenido]
    sueltas = sorted({m.group(0) for t in textos for m in QUIMICA_SUELTA.finditer(_fuera_de_formulas(t))})
    if sueltas:
        hallazgos.append(Hallazgo("quimica-fuera-de-ce", False, ", ".join(sueltas[:8])))
    flechas = sum(len(FLECHA.findall(_fuera_de_formulas(t))) for t in textos)
    if flechas:
        hallazgos.append(Hallazgo("flecha-fuera-de-formula", False, str(flechas)))
    comas = [f["tex"] for f in formulas(examen) if COMA_DECIMAL.search(f["tex"]) and "(" not in f["tex"]]
    if comas:
        hallazgos.append(Hallazgo("coma-decimal-sin-llaves", False, f"{len(comas)}: {comas[0][:40]}"))
    reglas = [examen.eleccion_raiz, *(n.eleccion for n in examen.nodos)]
    instrucciones = " ".join([t.markdown for t in examen.instrucciones] + [t.markdown for r in reglas if r for t in r.literal])
    if NOTA_MEDIA.search(instrucciones) and not any(r and r.agregacion == "media" for r in reglas):
        hallazgos.append(Hallazgo("media-no-detectada", False, NOTA_MEDIA.search(instrucciones).group(0)))
    return hallazgos


def formulas(examen: ExamenExtraido) -> list[dict]:
    textos = [t.markdown for n in examen.nodos for t in n.enunciado]
    textos += [t.markdown for e in examen.estimulos for t in e.contenido]
    return [
        {"tex": (m.group(1) or m.group(2)).strip(), "bloque": m.group(1) is not None}
        for texto in textos
        for m in FORMULA.finditer(texto)
    ]


ComprobarKatex = Callable[[list[dict]], list[str | None]]
"""Recibe fórmulas {tex, bloque} y devuelve, para cada una, el error de KaTeX o None."""


def errores_katex(lista: list[dict], comprobar: ComprobarKatex) -> list[Hallazgo]:
    if not lista:
        return []
    return [
        Hallazgo("latex-invalido", True, f"{f['tex'][:80]} — {error}")
        for f, error in zip(lista, comprobar(lista), strict=True)
        if error
    ]


def validar(examen: ExamenExtraido, comprobar_katex: ComprobarKatex) -> list[Hallazgo]:
    if not examen.es_examen:
        return [Hallazgo("no-es-examen", True, "")]
    return [
        *estructura(examen),
        *contenido(examen),
        *numeracion(examen),
        *paginas(examen),
        *calidad(examen),
        *puntuacion(examen),
        *errores_katex(formulas(examen), comprobar_katex),
    ]
