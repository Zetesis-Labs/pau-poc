"""Extrae la respuesta de cada nodo de los exámenes procesados: primero de la fuente oficial y luego, para lo que falte, de la academia."""

import json
import time
from dataclasses import asdict
from pathlib import Path

from pau.aplicacion.anexos import anexos_de
from pau.aplicacion.banco import registros
from pau.aplicacion.extraer import Parametros
from pau.aplicacion.pasadas import ejecutar, resumen
from pau.aplicacion.rubricas import contexto_rubrica
from pau.aplicacion.rutas import Rutas
from pau.dominio.esquema import ExamenExtraido
from pau.dominio.soluciones import (
    VERSION_SOLUCIONES,
    FuenteSolucion,
    OrigenSolucion,
    SolucionExtraida,
    fuente_de_solucion,
    normalizar_soluciones,
    sin_respuesta,
    validar_soluciones,
)
from pau.puertos import ComprobadorKatex, Extractor, LectorPdf


def carpeta(rutas: Rutas, ejecucion: str, parametros: Parametros, origen: OrigenSolucion) -> Path:
    return rutas.ejecucion(ejecucion) / "soluciones" / parametros.ejecucion / origen


def extraer_solucion(
    registro: dict, fuente: FuenteSolucion, parametros: Parametros, rutas: Rutas,
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
        "esquema": VERSION_SOLUCIONES,
    }
    try:
        respuesta = extractor.estructurar(
            lector.paginas_desde(rutas.data / fuente.archivo, fuente.desde), Path(fuente.archivo).name,
            contexto_rubrica(registro, examen), (rutas.prompts / f"{parametros.prompt}.md").read_text(),
            parametros.modelo, parametros.esfuerzo, SolucionExtraida,
        )
    except Exception as error:
        return {**salida, "error": f"{type(error).__name__}: {error}"[:500], "segundos": round(time.monotonic() - inicio, 1)}
    salida.update(segundos=round(time.monotonic() - inicio, 1), uso=respuesta.uso, estado=respuesta.estado)
    if respuesta.resultado is None:
        return {**salida, "error": f"sin salida parseada (estado {respuesta.estado}, {respuesta.detalle})"}
    solucion = normalizar_soluciones(respuesta.resultado, fuente.desde)
    salida["resultado"] = solucion.model_dump()
    salida["hallazgos"] = [asdict(h) for h in validar_soluciones(solucion, examen, comprobar_katex)]
    return salida


def respondidos(ruta: Path) -> set[str] | None:
    """Nodos con respuesta en un registro de soluciones ya hecho, o None si no existe o falló."""
    if not ruta.exists():
        return None
    salida = json.loads(ruta.read_text())
    if "resultado" not in salida or not salida["resultado"]["contiene_soluciones"]:
        return set()
    return {e["nodo"] for e in salida["resultado"]["entradas"] if e["respuesta"]}


def tareas(
    ejecucion: str, parametros: Parametros, origen: OrigenSolucion, rutas: Rutas, lector: LectorPdf,
) -> tuple[list[tuple[dict, FuenteSolucion]], int]:
    """Exámenes con fuente de ese origen. La academia solo se consulta si lo oficial deja preguntas sin respuesta."""
    documentos = json.loads(rutas.examenes.read_text())["documentos"]
    por_id = {d["id"]: d for d in documentos}
    procesados = registros(rutas.ejecucion(ejecucion))
    anexos = anexos_de(documentos, procesados, rutas, lector)
    oficiales = carpeta(rutas, ejecucion, parametros, "oficial")
    lista, sin_fuente = [], 0
    for r in procesados:
        doc_id = r["documento"]["id"]
        if origen == "academia":
            hechos = respondidos(oficiales / f"{doc_id}.json") or set()
            if not sin_respuesta(ExamenExtraido(**r["resultado"]), hechos):
                continue
        fuente = fuente_de_solucion(por_id[doc_id], anexos.get(doc_id, []), por_id, origen)
        if fuente:
            lista.append((r, fuente))
        else:
            sin_fuente += 1
    return lista, sin_fuente


def extraer_soluciones(
    ejecucion: str, parametros: Parametros, origen: OrigenSolucion, rutas: Rutas, extractor: Extractor, lector: LectorPdf,
    comprobar_katex: ComprobadorKatex, hilos: int, rehacer: bool, ids: list[str] | None = None, limite: int | None = None,
) -> None:
    lista, sin_fuente = tareas(ejecucion, parametros, origen, rutas, lector)
    if ids:
        lista = [(r, f) for r, f in lista if r["documento"]["id"] in ids]
    ejecutar(
        lista[:limite],
        lambda r, f: extraer_solucion(r, f, parametros, rutas, extractor, lector, comprobar_katex),
        carpeta(rutas, ejecucion, parametros, origen), hilos, rehacer,
        lambda r, s: resumen(r, s, "entradas"),
        f"con solución {origen} · {sin_fuente} exámenes que la necesitan y no la tienen",
    )
