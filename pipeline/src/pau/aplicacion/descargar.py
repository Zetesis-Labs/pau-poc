"""Descarga los documentos descargables del catálogo, con un tope de conexiones por servidor."""

import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pau.dominio.catalogo import evaluar_descarga, host
from pau.dominio.documento import Documento, ruta_local, url_descarga
from pau.puertos import Web


def _existente(destino: Path) -> Path | None:
    if not destino.parent.exists():
        return None
    return next((p for p in destino.parent.glob(destino.stem + ".*") if p.stat().st_size > 0), None)


def _resultado(ruta: Path, data: Path) -> dict:
    return {"archivo": str(ruta.relative_to(data)), "bytes": ruta.stat().st_size}


def descargar(documento: Documento, web: Web, data: Path) -> dict:
    destino = data / ruta_local(documento)
    existente = _existente(destino)
    if existente:
        return _resultado(existente, data)
    try:
        respuesta = web.descargar(url_descarga(documento.url))
    except Exception as error:
        return {"error": f"{type(error).__name__}: {error}"[:300]}
    ext, error = evaluar_descarga(respuesta)
    if error:
        return {"error": error}
    destino = destino.with_suffix(ext)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(respuesta.contenido)
    return _resultado(destino, data)


def descargar_todo(documentos: list[Documento], web: Web, data: Path, hilos_por_host: int) -> dict[str, dict]:
    pendientes = [d for d in documentos if url_descarga(d.url)]
    grupos: dict[str, list[Documento]] = defaultdict(list)
    for documento in pendientes:
        grupos[host(documento)].append(documento)
    semaforos = {h: threading.Semaphore(hilos_por_host) for h in grupos}

    def con_tope(documento: Documento, semaforo: threading.Semaphore) -> dict:
        with semaforo:
            return descargar(documento, web, data)

    resultados: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, hilos_por_host * len(grupos))) as pool:
        futuros = {pool.submit(con_tope, d, semaforos[h]): d for h, docs in grupos.items() for d in docs}
        for n, futuro in enumerate(as_completed(futuros), 1):
            documento = futuros[futuro]
            resultados[documento.id] = futuro.result()
            if "error" in resultados[documento.id]:
                print(f"  ✗ {documento.url} → {resultados[documento.id]['error']}", file=sys.stderr)
            if n % 100 == 0:
                print(f"  {n}/{len(pendientes)} descargas", file=sys.stderr)
    return resultados
