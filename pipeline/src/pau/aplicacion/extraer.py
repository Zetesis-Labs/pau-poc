"""Extrae las preguntas de un lote de exámenes y deja un registro por examen en la ejecución."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

from pau.aplicacion.recortar import recortar
from pau.aplicacion.rutas import Rutas
from pau.dominio.esquema import VERSION, ExamenExtraido
from pau.dominio.geometria import hallazgos_de_recortes
from pau.dominio.normalizar import normalizar
from pau.dominio.validar import validar
from pau.puertos import ComprobadorKatex, Extractor, LectorPdf

CAMPOS_DOCUMENTO = ("id", "region", "asignatura", "anio", "convocatoria", "tipo", "fuente", "url", "archivo", "paginas", "estrato")


@dataclass(frozen=True)
class Parametros:
    modelo: str
    prompt: str
    esfuerzo: str

    @property
    def ejecucion(self) -> str:
        return f"{self.modelo}__{self.prompt}"


def contexto(documento: dict) -> str:
    return f"Examen de {documento['asignatura']} · {documento['region']} · {documento['anio']} · convocatoria {documento['convocatoria']}."


def revisar(examen: ExamenExtraido, figuras: list[dict], comprobar_katex: ComprobadorKatex) -> list[dict]:
    return [asdict(h) for h in validar(examen, comprobar_katex)] + hallazgos_de_recortes(figuras, examen)


def extraer_documento(documento: dict, parametros: Parametros, rutas: Rutas, extractor: Extractor, lector: LectorPdf, comprobar_katex: ComprobadorKatex) -> dict:
    inicio = time.monotonic()
    registro = {
        "documento": {k: documento[k] for k in CAMPOS_DOCUMENTO if k in documento},
        "modelo": parametros.modelo,
        "esfuerzo": parametros.esfuerzo,
        "esquema": VERSION,
        "prompt": parametros.prompt,
    }
    pdf = rutas.data / documento["archivo"]
    try:
        extraccion = extractor.extraer(
            pdf.read_bytes(), Path(documento["archivo"]).name, contexto(documento),
            (rutas.prompts / f"{parametros.prompt}.md").read_text(), parametros.modelo, parametros.esfuerzo,
        )
    except Exception as error:
        return {**registro, "error": f"{type(error).__name__}: {error}"[:500], "segundos": round(time.monotonic() - inicio, 1)}
    registro.update(segundos=round(time.monotonic() - inicio, 1), uso=extraccion.uso, estado=extraccion.estado, respuesta=extraccion.id)
    if extraccion.examen is None:
        return {**registro, "error": f"sin salida parseada (estado {extraccion.estado}, {extraccion.detalle})"}
    examen, cambios = normalizar(extraccion.examen)
    registro["normalizaciones"] = cambios
    registro["resultado"] = examen.model_dump()
    registro["figuras"] = recortar(lector, pdf, examen, rutas.ejecucion(parametros.ejecucion) / "figuras", documento["id"])
    registro["hallazgos"] = revisar(examen, registro["figuras"], comprobar_katex)
    return registro


def linea(registro: dict) -> str:
    d = registro["documento"]
    if "error" in registro:
        estado = "✗ " + registro["error"][:150]
    else:
        graves = sum(h["grave"] for h in registro["hallazgos"])
        estado = f"✓ {len(registro['resultado']['nodos'])} nodos · {graves} graves · {len(registro['resultado']['incidencias'])} incidencias"
    return f"{d['asignatura'][:30]:<30} {d['anio']} {d['region'][:10]:<10} {registro.get('segundos', 0):>6}s {estado}"


def extraer_lote(documentos: list[dict], parametros: Parametros, rutas: Rutas, extractor: Extractor, lector: LectorPdf, comprobar_katex: ComprobadorKatex, hilos: int, rehacer: bool) -> None:
    destino = rutas.ejecucion(parametros.ejecucion)
    destino.mkdir(parents=True, exist_ok=True)
    pendientes = [d for d in documentos if rehacer or not (destino / f"{d['id']}.json").exists()]
    print(f"{len(pendientes)} pendientes de {len(documentos)}", flush=True)
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        futuros = {pool.submit(extraer_documento, d, parametros, rutas, extractor, lector, comprobar_katex): d for d in pendientes}
        for futuro in as_completed(futuros):
            registro = futuro.result()
            (destino / f"{futuros[futuro]['id']}.json").write_text(json.dumps(registro, ensure_ascii=False, indent=1))
            print(linea(registro), flush=True)


def rehacer_recortes(ejecucion: str, rutas: Rutas, lector: LectorPdf) -> int:
    """Vuelve a recortar una ejecución con el código actual, sin llamar al modelo."""
    carpeta = rutas.ejecucion(ejecucion)
    for figura in (carpeta / "figuras").glob("*.png"):
        figura.unlink()
    rehechos = 0
    for ruta in sorted(carpeta.glob("*.json")):
        registro = json.loads(ruta.read_text())
        if "resultado" not in registro:
            continue
        examen = ExamenExtraido(**registro["resultado"])
        registro["figuras"] = recortar(lector, rutas.data / registro["documento"]["archivo"], examen, carpeta / "figuras", registro["documento"]["id"])
        registro["hallazgos"] = [h for h in registro["hallazgos"] if not h["regla"].startswith("recorte-") and h["regla"] != "figura-sin-recorte"]
        registro["hallazgos"] += hallazgos_de_recortes(registro["figuras"], examen)
        ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=1))
        rehechos += 1
    return rehechos
