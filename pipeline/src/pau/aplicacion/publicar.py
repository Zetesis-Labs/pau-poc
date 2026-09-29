"""Escribe `datos/`: lo único del corpus que se versiona y que consume la web."""

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from pau.aplicacion.anexos import anexos_de
from pau.aplicacion.banco import RUBRICAS, SOLUCIONES, construir, registros
from pau.aplicacion.rutas import Rutas
from pau.aplicacion.verificacion import exigir_conservacion
from pau.dominio.publicacion import publicar as componer
from pau.puertos import LectorPdf


@dataclass(frozen=True)
class Resumen:
    documentos: int
    procesados: int
    preguntas: int
    figuras: int
    pdfs: int
    bytes: dict[str, int]


def _tamano(ruta) -> int:
    return sum(p.stat().st_size for p in ruta.rglob("*") if p.is_file()) if ruta.is_dir() else ruta.stat().st_size


def publicar(ejecucion: str, rutas: Rutas, lector: LectorPdf, rubricas: str = RUBRICAS, soluciones: str = SOLUCIONES) -> Resumen:
    exigir_conservacion(ejecucion, rutas, rubricas, soluciones)
    examenes = json.loads(rutas.examenes.read_text())
    anexos = anexos_de(examenes["documentos"], registros(rutas.ejecucion(ejecucion)), rutas, lector)
    publicacion = componer(examenes, construir(ejecucion, rutas, lector, rubricas, soluciones), ejecucion, anexos)
    with TemporaryDirectory(prefix=".pau-publicacion-", dir=rutas.raiz) as temporal:
        destino = Path(temporal) / "datos"
        (destino / "figuras").mkdir(parents=True)
        (destino / "pdfs").mkdir()
        (destino / "catalogo.json").write_text(json.dumps(publicacion.catalogo, ensure_ascii=False))
        (destino / "preguntas.json").write_text(json.dumps(publicacion.preguntas, ensure_ascii=False))
        for figura in publicacion.figuras:
            shutil.copyfile(rutas.ejecucion(ejecucion) / "figuras" / figura, destino / "figuras" / figura)
        for publicado, original in publicacion.pdfs.items():
            shutil.copyfile(rutas.data / original, destino / publicado)
        resumen = Resumen(
            documentos=len(publicacion.catalogo["documentos"]),
            procesados=sum(d["procesado"] for d in publicacion.catalogo["documentos"]),
            preguntas=len(publicacion.preguntas["preguntas"]),
            figuras=len(publicacion.figuras),
            pdfs=len(publicacion.pdfs),
            bytes={n: _tamano(destino / n) for n in ("catalogo.json", "preguntas.json", "figuras", "pdfs")},
        )
        anterior = Path(temporal).with_name(Path(temporal).name + "-anterior")
        if rutas.datos.exists():
            rutas.datos.rename(anterior)
        try:
            destino.rename(rutas.datos)
        except OSError:
            if anterior.exists():
                anterior.rename(rutas.datos)
            raise
        if anterior.exists():
            try:
                shutil.rmtree(anterior)
            except OSError:
                print(f"Publicación instalada; no se pudo retirar el respaldo {anterior}", file=sys.stderr)
        return resumen
