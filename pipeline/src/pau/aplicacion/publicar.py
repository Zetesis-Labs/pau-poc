"""Escribe `datos/`: lo único del corpus que se versiona y que consume la web."""

import json
import shutil
from dataclasses import dataclass

from pau.aplicacion.anexos import anexos_de
from pau.aplicacion.banco import construir, registros
from pau.aplicacion.rutas import Rutas
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


def publicar(ejecucion: str, rutas: Rutas, lector: LectorPdf) -> Resumen:
    examenes = json.loads(rutas.examenes.read_text())
    anexos = anexos_de(examenes["documentos"], registros(rutas.ejecucion(ejecucion)), rutas, lector)
    publicacion = componer(examenes, construir(ejecucion, rutas, lector), ejecucion, anexos)
    destino = rutas.datos
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "figuras").mkdir(parents=True)
    (destino / "pdfs").mkdir()
    (destino / "catalogo.json").write_text(json.dumps(publicacion.catalogo, ensure_ascii=False))
    (destino / "preguntas.json").write_text(json.dumps(publicacion.preguntas, ensure_ascii=False))
    for figura in publicacion.figuras:
        shutil.copyfile(rutas.ejecucion(ejecucion) / "figuras" / figura, destino / "figuras" / figura)
    for publicado, original in publicacion.pdfs.items():
        shutil.copyfile(rutas.data / original, destino / publicado)
    return Resumen(
        documentos=len(publicacion.catalogo["documentos"]),
        procesados=sum(d["procesado"] for d in publicacion.catalogo["documentos"]),
        preguntas=len(publicacion.preguntas["preguntas"]),
        figuras=len(publicacion.figuras),
        pdfs=len(publicacion.pdfs),
        bytes={n: _tamano(destino / n) for n in ("catalogo.json", "preguntas.json", "figuras", "pdfs")},
    )
