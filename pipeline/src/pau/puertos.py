"""Puertos: lo que el núcleo y los casos de uso necesitan del mundo exterior."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pau.dominio.catalogo import Respuesta
from pau.dominio.esquema import ExamenExtraido
from pau.dominio.geometria import Bloque, Caja, GeometriaPagina


class Web(Protocol):
    def texto(self, url: str) -> str: ...

    def descargar(self, url: str) -> Respuesta: ...


@dataclass(frozen=True)
class Extraccion:
    examen: ExamenExtraido | None
    uso: dict | None
    estado: str
    detalle: str = ""


class Extractor(Protocol):
    def extraer(self, pdf: bytes, nombre: str, contexto: str, instrucciones: str, modelo: str, esfuerzo: str) -> Extraccion: ...


@dataclass(frozen=True)
class Imagen:
    png: bytes
    ancho: int
    alto: int
    grises: bytes
    """Muestra de píxeles en escala de grises, para detectar recortes en blanco."""


class DocumentoPdf(Protocol):
    @property
    def paginas(self) -> int: ...

    def rect(self, pagina: int) -> Caja: ...

    def bloques(self, pagina: int) -> list[Bloque]: ...

    def texto(self, pagina: int) -> str: ...

    def geometria(self, pagina: int) -> GeometriaPagina: ...

    def buscar(self, pagina: int, texto: str) -> list[Caja]: ...

    def renderizar(self, pagina: int, caja: Caja, dpi: int) -> Imagen: ...

    def caracteres_por_pagina(self) -> int: ...


class LectorPdf(Protocol):
    def abrir(self, ruta: Path) -> AbstractContextManager[DocumentoPdf]: ...


class ComprobadorKatex(Protocol):
    def __call__(self, formulas: list[dict]) -> list[str | None]: ...
