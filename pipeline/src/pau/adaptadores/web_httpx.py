"""Web sobre httpx: certificados del sistema, caché de HTML en disco y reintentos ante cortes de transporte."""

import hashlib
import ssl
import time
from pathlib import Path

import httpx
import truststore

from pau.dominio.catalogo import Respuesta

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
INTENTOS = 4


class WebHttpx:
    def __init__(self, cache: Path, pausa: float = 0.3, sin_red: bool = False):
        self._cliente = httpx.Client(
            headers={"User-Agent": UA},
            follow_redirects=True,
            timeout=60,
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        )
        self._cache = cache
        self._pausa = pausa
        self._sin_red = sin_red
        cache.mkdir(parents=True, exist_ok=True)

    def texto(self, url: str) -> str:
        destino = self._cache / hashlib.sha1(url.encode()).hexdigest()
        if destino.exists():
            return destino.read_text()
        if self._sin_red:
            raise LookupError(f"sin caché para {url}")
        respuesta = self._cliente.get(url)
        respuesta.raise_for_status()
        time.sleep(self._pausa)
        destino.write_text(respuesta.text)
        return respuesta.text

    def descargar(self, url: str) -> Respuesta:
        for intento in range(INTENTOS):
            try:
                r = self._cliente.get(url)
                return Respuesta(r.status_code, str(r.url), r.content, r.headers.get("content-type", "?"))
            except httpx.TransportError:
                if intento == INTENTOS - 1:
                    raise
                time.sleep(2 * (intento + 1))
        raise AssertionError("inalcanzable")
