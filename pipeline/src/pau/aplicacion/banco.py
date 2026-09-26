"""Construye el banco de preguntas de una ejecución y ancla cada pregunta a su franja del PDF."""

import json
from pathlib import Path

from pau.aplicacion.rutas import Rutas
from pau.dominio.banco import fin_de_contenido, franjas, inicio_en_pagina, preguntas_de
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


def construir(ejecucion: str, rutas: Rutas, lector: LectorPdf) -> list[dict]:
    """Preguntas ancladas, aún con los campos internos (`_archivo`…) que necesita la publicación."""
    preguntas = [p for r in registros(rutas.ejecucion(ejecucion)) for p in preguntas_de(r)]
    por_pdf: dict[str, list[dict]] = {}
    for p in preguntas:
        por_pdf.setdefault(p["_archivo"], []).append(p)
    for archivo, grupo in por_pdf.items():
        _anclar_pdf(grupo, rutas.data / archivo, lector)
    return preguntas


def ancladas(preguntas: list[dict]) -> int:
    return sum(any(a["y0"] is not None for a in p["anclas"].values()) for p in preguntas)
