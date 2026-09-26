"""Geometría de página y ajuste de los recortes de figuras que propone el modelo a piezas reales del PDF."""

from __future__ import annotations

from dataclasses import dataclass, field

from pau.dominio.esquema import ExamenExtraido, Recorte

AREA_MINIMA = 0.005
AREA_MAXIMA = 0.9
DESVIACION_MINIMA = 4.0
TIPOS_VISUALES = ("figura", "grafica", "mapa", "partitura", "tabla", "otro")
HOLGURA_VERTICAL = 0.12
HOLGURA_HORIZONTAL = 0.06
CONTENCION_MINIMA = 0.5
PROPORCION_TAMANO = 3.0
DISTANCIA_ETIQUETA = 12
LONGITUD_ETIQUETA = 30
AREA_CANDIDATO_MAXIMA = 0.6
MARGEN = 4
MARGEN_SIN_GEOMETRIA = 0.02
SOLAPE_AJENO = 0.3
DUPLICADO = 0.9
MARGEN_PAGINA = 0.05


@dataclass(frozen=True)
class Caja:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def ancho(self) -> float:
        return self.x1 - self.x0

    @property
    def alto(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return max(self.ancho, 0) * max(self.alto, 0)

    @property
    def vacia(self) -> bool:
        return self.x0 >= self.x1 or self.y0 >= self.y1

    @property
    def centro(self) -> tuple[float, float]:
        return (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2

    def __and__(self, otra: Caja) -> Caja:
        return Caja(max(self.x0, otra.x0), max(self.y0, otra.y0), min(self.x1, otra.x1), min(self.y1, otra.y1))

    def __or__(self, otra: Caja) -> Caja:
        return Caja(min(self.x0, otra.x0), min(self.y0, otra.y0), max(self.x1, otra.x1), max(self.y1, otra.y1))

    def expandir(self, dx: float, dy: float | None = None) -> Caja:
        dy = dx if dy is None else dy
        return Caja(self.x0 - dx, self.y0 - dy, self.x1 + dx, self.y1 + dy)

    def intersecta(self, otra: Caja) -> bool:
        return not (self & otra).vacia

    def tupla(self) -> tuple[float, float, float, float]:
        return self.x0, self.y0, self.x1, self.y1


@dataclass(frozen=True)
class Bloque:
    caja: Caja
    texto: str
    es_texto: bool = True


@dataclass(frozen=True)
class GeometriaPagina:
    """Lo que el PDF sabe de una página: su tamaño, imágenes incrustadas, grupos de dibujos vectoriales y bloques (de texto o de imagen)."""

    rect: Caja
    imagenes: list[Caja] = field(default_factory=list)
    dibujos: list[Caja] = field(default_factory=list)
    bloques: list[Bloque] = field(default_factory=list)


@dataclass(frozen=True)
class RecortePlanificado:
    estimulo: str
    idioma: str
    pagina: int
    numero: int
    problemas: tuple[str, ...]
    caja: Caja | None = None
    metodo: str | None = None


def problemas(recorte: Recorte) -> list[str]:
    coordenadas = (recorte.x0, recorte.y0, recorte.x1, recorte.y1)
    if any(c < 0 or c > 1 for c in coordenadas):
        return ["fuera-de-rango"]
    if recorte.x1 <= recorte.x0 or recorte.y1 <= recorte.y0:
        return ["invertido"]
    area = (recorte.x1 - recorte.x0) * (recorte.y1 - recorte.y0)
    if area < AREA_MINIMA:
        return ["diminuto"]
    if area > AREA_MAXIMA:
        return ["casi-pagina"]
    return []


def rectangulo(recorte: Recorte, pagina: Caja) -> Caja:
    return Caja(
        pagina.x0 + recorte.x0 * pagina.ancho,
        pagina.y0 + recorte.y0 * pagina.alto,
        pagina.x0 + recorte.x1 * pagina.ancho,
        pagina.y0 + recorte.y1 * pagina.alto,
    )


def fusionar_contiguos(cajas: list[Caja]) -> list[Caja]:
    grupos = list(cajas)
    cambiado = True
    while cambiado:
        cambiado = False
        for i in range(len(grupos)):
            for j in range(i + 1, len(grupos)):
                if grupos[i].expandir(3).intersecta(grupos[j]):
                    grupos[i] = grupos[i] | grupos[j]
                    grupos.pop(j)
                    cambiado = True
                    break
            if cambiado:
                break
    return grupos


def candidatos(imagenes: list[Caja], dibujos: list[Caja], pagina: Caja) -> list[Caja]:
    utiles = [c & pagina for c in [*imagenes, *dibujos]]
    utiles = [c for c in utiles if AREA_MINIMA * pagina.area <= c.area <= AREA_CANDIDATO_MAXIMA * pagina.area]
    return fusionar_contiguos(utiles)


def _distancia(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def ajustar(aproximado: Caja, opciones: list[Caja], textos: list[Bloque], pagina: Caja, ajenas: list[Caja] = ()) -> tuple[Caja, str]:
    """Ajusta la caja aproximada del modelo a una pieza real del PDF, sin invadir las figuras de otros estímulos de la misma página."""
    zona = aproximado.expandir(HOLGURA_HORIZONTAL * pagina.ancho, HOLGURA_VERTICAL * pagina.alto)
    area = aproximado.area
    parecidos = [
        c for c in opciones
        if (c & zona).area >= CONTENCION_MINIMA * c.area and area / PROPORCION_TAMANO <= c.area <= area * PROPORCION_TAMANO
        and not any((c & otra).area > SOLAPE_AJENO * otra.area for otra in ajenas)
    ]
    if not parecidos:
        return aproximado.expandir(MARGEN_SIN_GEOMETRIA * pagina.alto) & pagina, "modelo"
    base = min(parecidos, key=lambda c: _distancia(c.centro, aproximado.centro))
    entorno = base.expandir(DISTANCIA_ETIQUETA)
    union = base
    for bloque in textos:
        if entorno.intersecta(bloque.caja) and len(bloque.texto.strip()) <= LONGITUD_ETIQUETA:
            union = union | bloque.caja
    return union.expandir(MARGEN) & pagina, "pdf"


def es_etiqueta(bloque: Bloque, pagina: Caja) -> bool:
    limpio = bloque.texto.strip()
    en_margen = bloque.caja.y1 < pagina.y0 + MARGEN_PAGINA * pagina.alto or bloque.caja.y0 > pagina.y1 - MARGEN_PAGINA * pagina.alto
    return bool(limpio) and not (limpio.isdigit() and en_margen)


def opciones_de(geometria: GeometriaPagina) -> tuple[list[Caja], list[Bloque]]:
    textos = [b for b in geometria.bloques if b.es_texto and es_etiqueta(b, geometria.rect)]
    return candidatos(geometria.imagenes, geometria.dibujos, geometria.rect), textos


def en_blanco(muestras: bytes) -> bool:
    """Muestras de gris (0-255) de un recorte: casi sin variación = recorte vacío."""
    if not muestras:
        return True
    media = sum(muestras) / len(muestras)
    varianza = sum((m - media) ** 2 for m in muestras) / len(muestras)
    return varianza ** 0.5 < DESVIACION_MINIMA


def paginas_con_recortes(examen: ExamenExtraido) -> set[int]:
    return {r.pagina for e in examen.estimulos for r in e.recortes}


def planificar_recortes(examen: ExamenExtraido, paginas: dict[int, GeometriaPagina]) -> list[RecortePlanificado]:
    """Decide la caja final de cada recorte; `paginas` trae la geometría de las páginas existentes del PDF."""
    cajas_por_pagina: dict[int, list[tuple[str, Caja]]] = {}
    for estimulo in examen.estimulos:
        for recorte in estimulo.recortes:
            if recorte.pagina in paginas and not problemas(recorte):
                cajas_por_pagina.setdefault(recorte.pagina, []).append((estimulo.id, rectangulo(recorte, paginas[recorte.pagina].rect)))
    plan = []
    for estimulo in examen.estimulos:
        vistos: list[tuple[int, Caja]] = []
        for n, recorte in enumerate(estimulo.recortes, 1):
            fallos = problemas(recorte)
            if recorte.pagina not in paginas:
                fallos.append("pagina-inexistente")
            if fallos:
                plan.append(RecortePlanificado(estimulo.id, recorte.idioma, recorte.pagina, n, tuple(fallos)))
                continue
            geometria = paginas[recorte.pagina]
            opciones, textos = opciones_de(geometria)
            ajenas = [c for e, c in cajas_por_pagina.get(recorte.pagina, []) if e != estimulo.id]
            caja, metodo = ajustar(rectangulo(recorte, geometria.rect), opciones, textos, geometria.rect, ajenas)
            if any(p == recorte.pagina and (caja & r).area >= DUPLICADO * caja.area for p, r in vistos):
                continue
            vistos.append((recorte.pagina, caja))
            plan.append(RecortePlanificado(estimulo.id, recorte.idioma, recorte.pagina, n, (), caja, metodo))
    return plan


def nombre_figura(prefijo: str, recorte: RecortePlanificado) -> str:
    return f"{prefijo}_{recorte.estimulo}_{recorte.idioma}_{recorte.numero}.png"


def sin_recorte(examen: ExamenExtraido) -> list[str]:
    return [e.id for e in examen.estimulos if e.tipo in TIPOS_VISUALES and not e.contenido and not e.recortes]


def hallazgos_de_recortes(figuras: list[dict], examen: ExamenExtraido) -> list[dict]:
    return [
        {"regla": f"recorte-{p}", "grave": False, "detalle": f"{f['estimulo']} {f['idioma']} p.{f['pagina']}"}
        for f in figuras for p in f["problemas"]
    ] + [{"regla": "figura-sin-recorte", "grave": False, "detalle": e} for e in sin_recorte(examen)]
