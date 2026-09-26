"""Catálogo de documentos rastreados y decisiones puras de la descarga."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from pau.dominio.documento import Documento, ruta_local, url_descarga


@dataclass(frozen=True)
class Respuesta:
    estado: int
    url: str
    contenido: bytes
    tipo: str


FIRMAS = {b"%PDF": ".pdf", b"\xff\xd8\xff": ".jpg", b"\x89PNG": ".png"}


def deduplicar(documentos: list[Documento]) -> list[Documento]:
    unicos: dict[tuple[str, str], Documento] = {}
    for documento in documentos:
        unicos.setdefault((documento.fuente, documento.url), documento)
    return list(unicos.values())


def registro(documento: Documento, descargas: dict[str, dict]) -> dict:
    datos = documento.to_json()
    if datos["descargable"]:
        datos["archivo"] = ruta_local(documento)
        datos.update(descargas.get(documento.id, {}))
    return datos


def extension(contenido: bytes) -> str | None:
    cabecera = contenido[:1024].lstrip()
    return next((ext for firma, ext in FIRMAS.items() if cabecera.startswith(firma)), None)


def host(documento: Documento) -> str:
    return urlsplit(url_descarga(documento.url)).netloc


def evaluar_descarga(respuesta: Respuesta) -> tuple[str | None, str | None]:
    """(extensión con la que guardar, error). Exactamente uno de los dos es None."""
    if respuesta.estado in (401, 403) and "google.com" in respuesta.url:
        return None, "privado (requiere cuenta de Google con acceso)"
    if respuesta.estado >= 400:
        return None, f"HTTPStatusError: {respuesta.estado} en {respuesta.url}"
    ext = extension(respuesta.contenido)
    if ext is None:
        return None, f"formato no reconocido ({respuesta.tipo})"
    return ext, None
