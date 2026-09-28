"""Puertos: lo que el núcleo y los casos de uso necesitan del mundo exterior."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

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
    id: str = ""


@dataclass(frozen=True)
class Salida:
    """Respuesta estructurada del modelo en el formato pedido."""

    resultado: BaseModel | None
    uso: dict | None
    estado: str
    detalle: str = ""
    id: str = ""


class Extractor(Protocol):
    def extraer(self, pdf: bytes, nombre: str, contexto: str, instrucciones: str, modelo: str, esfuerzo: str) -> Extraccion: ...

    def estructurar(
        self, pdf: bytes, nombre: str, contexto: str, instrucciones: str, modelo: str, esfuerzo: str, formato: type[BaseModel],
    ) -> Salida: ...


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

    def paginas_desde(self, ruta: Path, desde: int) -> bytes:
        """Un PDF nuevo con las páginas de `ruta` a partir de `desde` (1 = todas)."""
        ...


class ComprobadorKatex(Protocol):
    def __call__(self, formulas: list[dict]) -> list[str | None]: ...
