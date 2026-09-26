"""Selección estratificada de exámenes para extraer: la muestra inicial y los lotes siguientes."""

import random
from collections import defaultdict
from collections.abc import Callable

FUENTES_OFICIALES = ("uc3m", "ehu", "umh", "llibreta")
MAX_PAGINAS = 25
ESCANEADO = 200
TAMANO_MUESTRA = 50
TRONCALES_POR_CELDA = 3
OTRAS_POR_CELDA = 2
TRONCALES = {
    "Matemáticas II", "Matemáticas Aplicadas a las CCSS II", "Física", "Química", "Biología",
    "Historia de España", "Lengua Castellana y Literatura II", "Inglés", "Historia de la Filosofía",
    "Historia del Arte", "Geografía", "Dibujo Técnico II", "Economía de la Empresa",
}
ESPECIALES: list[tuple[str, Callable[[dict], bool]]] = [
    ("escaneado", lambda d: d["texto_por_pagina"] < ESCANEADO),
    ("escaneado-2", lambda d: d["texto_por_pagina"] < ESCANEADO and d["fuente"] in ("umh", "llibreta")),
    ("dibujo", lambda d: "Dibujo" in d["asignatura"]),
    ("musica", lambda d: "Music" in d["asignatura"] or "Análisis Musical" in d["asignatura"]),
    ("lengua-cooficial", lambda d: d["asignatura"] in ("Valenciano", "Lengua Vasca y Literatura II")),
    ("comentario-texto", lambda d: d["asignatura"] in ("Lengua Castellana y Literatura II", "Historia de la Filosofía")),
]


def epoca(anio: int | None) -> str:
    if anio is None or anio <= 2019:
        return "hasta-2019"
    return "2020-2024" if anio <= 2024 else "pau-2025"


def clave_examen(d: dict) -> tuple:
    return (d["region"], d["asignatura"], d["anio"], d["convocatoria"], d["tipo"], d.get("variante", ""))


def es_candidato(d: dict) -> bool:
    return d["tipo"] in ("examen", "modelo") and bool(d.get("bytes")) and d.get("archivo", "").endswith(".pdf") and d["fuente"] in FUENTES_OFICIALES


def medible(paginas: int) -> bool:
    return 0 < paginas <= MAX_PAGINAS


def _celdas(candidatos: list[dict]) -> dict[tuple, list[dict]]:
    celdas: dict[tuple, list[dict]] = defaultdict(list)
    for d in candidatos:
        celdas[(d["region"], epoca(d["anio"]))].append(d)
    return celdas


def elegir(candidatos: list[dict], total: int, escaneados: int, azar: random.Random) -> list[dict]:
    """Lote de exámenes nuevos: algunos escaneados y el resto repartido por región y época, equilibrando asignaturas."""
    celdas = _celdas(candidatos)
    lote, usados, por_asignatura = [], set(), defaultdict(int)

    def tomar(d: dict, estrato: str) -> None:
        lote.append({**d, "estrato": estrato})
        usados.add(clave_examen(d))
        por_asignatura[d["asignatura"]] += 1

    escaneos = [c for c in candidatos if c["texto_por_pagina"] < ESCANEADO]
    for d in azar.sample(escaneos, k=min(escaneados, len(escaneos))):
        tomar(d, "especial · escaneado")
    ronda = 0
    while len(lote) < total and ronda < 50:
        ronda += 1
        for celda in sorted(celdas):
            libres = [d for d in celdas[celda] if clave_examen(d) not in usados]
            if not libres or len(lote) >= total:
                continue
            minimo = min(por_asignatura[d["asignatura"]] for d in libres)
            tomar(azar.choice([d for d in libres if por_asignatura[d["asignatura"]] == minimo]), f"{celda[0]} · {celda[1]}")
    return lote


def elegir_diverso(documentos: list[dict], n: int, ya: set[str], asignaturas_usadas: dict[str, int], azar: random.Random) -> list[dict]:
    por_asignatura: dict[str, list[dict]] = defaultdict(list)
    for d in documentos:
        if d["id"] not in ya:
            por_asignatura[d["asignatura"]].append(d)
    elegidos = []
    while len(elegidos) < n and por_asignatura:
        asignatura = min(por_asignatura, key=lambda a: (asignaturas_usadas[a], azar.random()))
        d = azar.choice(por_asignatura.pop(asignatura))
        elegidos.append(d)
        asignaturas_usadas[asignatura] += 1
    return elegidos


def muestra(medidos: list[dict], azar: random.Random) -> list[dict]:
    """Muestra inicial: troncales y otras por celda región × época, casos especiales y relleno hasta el tamaño fijado."""
    asignaturas_usadas: dict[str, int] = defaultdict(int)
    elegida, ya = [], set()
    celdas = _celdas(medidos)
    for celda in sorted(celdas):
        troncales = [d for d in celdas[celda] if d["asignatura"] in TRONCALES]
        elegidos = elegir_diverso(troncales, TRONCALES_POR_CELDA, ya, asignaturas_usadas, azar)
        ya.update(d["id"] for d in elegidos)
        elegidos += elegir_diverso(celdas[celda], OTRAS_POR_CELDA, ya, asignaturas_usadas, azar)
        for d in elegidos:
            elegida.append({**d, "estrato": f"{celda[0]} · {celda[1]}"})
            ya.add(d["id"])
    for nombre, criterio in ESPECIALES:
        if not any(criterio(d) for d in elegida if d["estrato"] != f"especial · {nombre}") or nombre.endswith("-2"):
            pool = [d for d in medidos if criterio(d) and d["id"] not in ya]
            if pool:
                d = azar.choice(pool)
                elegida.append({**d, "estrato": f"especial · {nombre}"})
                ya.add(d["id"])
    for d in elegir_diverso(medidos, TAMANO_MUESTRA - len(elegida), ya, asignaturas_usadas, azar):
        elegida.append({**d, "estrato": "relleno"})
        ya.add(d["id"])
    return elegida
