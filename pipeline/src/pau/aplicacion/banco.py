"""Construye el banco de preguntas de una ejecución y ancla cada pregunta a su franja del PDF."""

import json
from pathlib import Path

from pau.aplicacion.rutas import Rutas
from pau.dominio.banco import fin_de_contenido, franjas, inicio_en_pagina, preguntas_de
from pau.dominio.soluciones import soluciones_por_nodo
from pau.puertos import LectorPdf


def registros(carpeta: Path) -> list[dict]:
    lista = [json.loads(r.read_text()) for r in sorted(carpeta.glob("*.json")) if r.name != "preguntas.json"]
    return [r for r in lista if "resultado" in r and r["resultado"]["es_examen"]]


def _anclar_pdf(grupo: list[dict], pdf: Path, lector: LectorPdf) -> None:
    with lector.abrir(pdf) as documento:
        inicios: dict[tuple[int, str], list[tuple[float, dict]]] = {}
        for p in grupo:
            p["anclas"] = {}
            for idioma, numero in p["paginas"].items():
                if not 1 <= numero <= documento.paginas:
                    continue
                alto = documento.rect(numero).alto
                y = inicio_en_pagina(p, idioma, lambda texto, n=numero: documento.buscar(n, texto), alto)
                p["anclas"][idioma] = {"pagina": numero, "y0": round(y, 4) if y is not None else None, "y1": None}
                if y is not None:
                    inicios.setdefault((numero, idioma), []).append((y, p))
        for (numero, idioma), lista in inicios.items():
            lista.sort(key=lambda x: x[0])
            limite = fin_de_contenido(documento.bloques(numero), documento.rect(numero).alto)
            for (_, p), y1 in zip(lista, franjas([y for y, _ in lista], limite), strict=True):
                p["anclas"][idioma]["y1"] = y1


RUBRICAS = "gpt-6-luna__r2"
SOLUCIONES = "gpt-6-luna__s1"


def registro_de(carpeta: Path, doc_id: str) -> dict | None:
    ruta = carpeta / f"{doc_id}.json"
    if not ruta.exists():
        return None
    salida = json.loads(ruta.read_text())
    return salida if "resultado" in salida else None


def construir(ejecucion: str, rutas: Rutas, lector: LectorPdf, rubricas: str = RUBRICAS, soluciones: str = SOLUCIONES) -> list[dict]:
    """Preguntas ancladas, con su rúbrica y su solución, aún con los campos internos (`_archivo`…) que necesita la publicación."""
    base = rutas.ejecucion(ejecucion)
    preguntas = []
    for r in registros(base):
        doc_id = r["documento"]["id"]
        por_nodo = soluciones_por_nodo(
            registro_de(base / "soluciones" / soluciones / "oficial", doc_id),
            registro_de(base / "soluciones" / soluciones / "academia", doc_id),
        )
        preguntas += preguntas_de(r, registro_de(base / "rubricas" / rubricas, doc_id), por_nodo)
    por_pdf: dict[str, list[dict]] = {}
    for p in preguntas:
        por_pdf.setdefault(p["_archivo"], []).append(p)
    for archivo, grupo in por_pdf.items():
        _anclar_pdf(grupo, rutas.data / archivo, lector)
    return preguntas


def ancladas(preguntas: list[dict]) -> int:
    return sum(any(a["y0"] is not None for a in p["anclas"].values()) for p in preguntas)
