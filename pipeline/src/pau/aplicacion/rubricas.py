"""Extrae la rúbrica de corrección de cada examen procesado a partir de sus criterios o soluciones oficiales."""

import json
import time
from dataclasses import asdict
from pathlib import Path

from pau.aplicacion.anexos import anexos_de
from pau.aplicacion.banco import registros
from pau.aplicacion.extraer import Parametros, contexto
from pau.aplicacion.pasadas import ejecutar, resumen
from pau.aplicacion.rutas import Rutas
from pau.dominio.esquema import ExamenExtraido
from pau.dominio.rubrica import (
    VERSION_RUBRICA,
    FuenteRubrica,
    RubricaExtraida,
    arbol_para_el_modelo,
    fuente_de_rubrica,
    normalizar_rubrica,
    paginas_originales,
    validar_rubrica,
)
from pau.puertos import ComprobadorKatex, Extractor, LectorPdf


def carpeta(rutas: Rutas, ejecucion: str, parametros: Parametros) -> Path:
    return rutas.ejecucion(ejecucion) / "rubricas" / parametros.ejecucion


def contexto_rubrica(registro: dict, examen: ExamenExtraido) -> str:
    return (
        f"{contexto(registro['documento'])}\n\n"
        "Árbol del examen (una línea por nodo; usa estos ids):\n"
        f"{arbol_para_el_modelo(examen)}\n\n"
        "Numera las páginas del PDF que recibes empezando en 1."
    )


def extraer_rubrica(
    registro: dict, fuente: FuenteRubrica, parametros: Parametros, rutas: Rutas,
    extractor: Extractor, lector: LectorPdf, comprobar_katex: ComprobadorKatex,
) -> dict:
    inicio = time.monotonic()
    examen = ExamenExtraido(**registro["resultado"])
    salida = {
        "documento": registro["documento"]["id"],
        "fuente": {"archivo": fuente.archivo, "desde": fuente.desde, "anexo": fuente.anexo},
        "modelo": parametros.modelo,
        "esfuerzo": parametros.esfuerzo,
        "prompt": parametros.prompt,
        "esquema": VERSION_RUBRICA,
    }
    try:
        respuesta = extractor.estructurar(
            lector.paginas_desde(rutas.data / fuente.archivo, fuente.desde), Path(fuente.archivo).name,
            contexto_rubrica(registro, examen), (rutas.prompts / f"{parametros.prompt}.md").read_text(),
            parametros.modelo, parametros.esfuerzo, RubricaExtraida,
        )
    except Exception as error:
        return {**salida, "error": f"{type(error).__name__}: {error}"[:500], "segundos": round(time.monotonic() - inicio, 1)}
    salida.update(segundos=round(time.monotonic() - inicio, 1), uso=respuesta.uso, estado=respuesta.estado)
    if respuesta.resultado is None:
        return {**salida, "error": f"sin salida parseada (estado {respuesta.estado}, {respuesta.detalle})"}
    rubrica = normalizar_rubrica(paginas_originales(respuesta.resultado, fuente.desde))
    salida["resultado"] = rubrica.model_dump()
    salida["hallazgos"] = [asdict(h) for h in validar_rubrica(rubrica, examen, comprobar_katex)]
    return salida


def tareas(ejecucion: str, rutas: Rutas, lector: LectorPdf) -> tuple[list[tuple[dict, FuenteRubrica]], int]:
    """Exámenes procesados con una fuente oficial de corrección, y cuántos no la tienen."""
    documentos = json.loads(rutas.examenes.read_text())["documentos"]
    por_id = {d["id"]: d for d in documentos}
    procesados = registros(rutas.ejecucion(ejecucion))
    anexos = anexos_de(documentos, procesados, rutas, lector)
    con_fuente = []
    for r in procesados:
        doc_id = r["documento"]["id"]
        fuente = fuente_de_rubrica(por_id[doc_id], anexos.get(doc_id, []), por_id)
        if fuente:
            con_fuente.append((r, fuente))
    return con_fuente, len(procesados) - len(con_fuente)


def extraer_rubricas(
    ejecucion: str, parametros: Parametros, rutas: Rutas, extractor: Extractor, lector: LectorPdf,
    comprobar_katex: ComprobadorKatex, hilos: int, rehacer: bool, ids: list[str] | None = None, limite: int | None = None,
) -> None:
    lista, sin_fuente = tareas(ejecucion, rutas, lector)
    if ids:
        lista = [(r, f) for r, f in lista if r["documento"]["id"] in ids]
    ejecutar(
        lista[:limite],
        lambda r, f: extraer_rubrica(r, f, parametros, rutas, extractor, lector, comprobar_katex),
        carpeta(rutas, ejecucion, parametros), hilos, rehacer,
        lambda r, s: resumen(r, s, "entradas"),
        f"con criterios oficiales · {sin_fuente} exámenes sin fuente de corrección",
    )
