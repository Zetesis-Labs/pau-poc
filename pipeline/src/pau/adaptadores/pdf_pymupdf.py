"""LectorPdf sobre PyMuPDF."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pymupdf

from pau.dominio.geometria import Bloque, Caja, GeometriaPagina
from pau.puertos import Imagen

MUESTRAS_GRISES = 20000


def _caja(rect: pymupdf.Rect) -> Caja:
    return Caja(rect.x0, rect.y0, rect.x1, rect.y1)


def _grises(pixmap: pymupdf.Pixmap) -> bytes:
    gris = pymupdf.Pixmap(pymupdf.csGRAY, pixmap) if pixmap.n > 1 else pixmap
    return bytes(gris.samples[:: max(1, len(gris.samples) // MUESTRAS_GRISES)])


class DocumentoPymupdf:
    def __init__(self, documento: pymupdf.Document):
        self._documento = documento

    @property
    def paginas(self) -> int:
        return self._documento.page_count

    def _pagina(self, numero: int) -> pymupdf.Page:
        return self._documento[numero - 1]

    def rect(self, pagina: int) -> Caja:
        return _caja(self._pagina(pagina).rect)

    def bloques(self, pagina: int) -> list[Bloque]:
        return [Bloque(Caja(*b[:4]), b[4], b[6] == 0) for b in self._pagina(pagina).get_text("blocks")]

    def texto(self, pagina: int) -> str:
        return self._pagina(pagina).get_text()

    def geometria(self, pagina: int) -> GeometriaPagina:
        p = self._pagina(pagina)
        return GeometriaPagina(
            rect=_caja(p.rect),
            imagenes=[Caja(*i["bbox"]) for i in p.get_image_info()],
            dibujos=[_caja(r) for r in p.cluster_drawings()],
            bloques=self.bloques(pagina),
        )

    def buscar(self, pagina: int, texto: str) -> list[Caja]:
        return [_caja(r) for r in self._pagina(pagina).search_for(texto)]

    def renderizar(self, pagina: int, caja: Caja, dpi: int) -> Imagen:
        pixmap = self._pagina(pagina).get_pixmap(dpi=dpi, clip=pymupdf.Rect(*caja.tupla()))
        return Imagen(pixmap.tobytes("png"), pixmap.width, pixmap.height, _grises(pixmap))

    def caracteres_por_pagina(self) -> int:
        texto = "".join(p.get_text() for p in self._documento)
        return len(texto.strip()) // max(self.paginas, 1)


class LectorPymupdf:
    @contextmanager
    def abrir(self, ruta: Path) -> Iterator[DocumentoPymupdf]:
        with pymupdf.open(ruta) as documento:
            yield DocumentoPymupdf(documento)

    def paginas_desde(self, ruta: Path, desde: int) -> bytes:
        with pymupdf.open(ruta) as documento:
            if desde > 1:
                documento.select(list(range(desde - 1, documento.page_count)))
            return documento.tobytes(garbage=3, deflate=True)
