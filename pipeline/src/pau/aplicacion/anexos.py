"""Localiza la corrección que viene dentro de los PDF de examen y vincula cada examen con sus anexos."""

import json
from collections.abc import Iterable
from dataclasses import dataclass

from pau.aplicacion.rutas import Rutas
from pau.dominio.anexos import TIPOS_EXAMEN, Incrustado, combinar, incrustado_por_extraccion, incrustado_por_texto, vincular
from pau.puertos import LectorPdf


@dataclass(frozen=True)
class Deteccion:
    revisados: int
    con_correccion: int
    ilegibles: list[str]


def _pdfs_de_examen(documentos: list[dict]) -> Iterable[dict]:
    return (d for d in documentos if d["tipo"] in TIPOS_EXAMEN and d.get("bytes") and d.get("archivo", "").endswith(".pdf"))


def detectar_incrustados(rutas: Rutas, lector: LectorPdf) -> Deteccion:
    """Recorre los PDF de examen descargados y guarda en data/incrustados.json dónde empieza su corrección."""
    documentos = json.loads(rutas.examenes.read_text())["documentos"]
    encontrados: dict[str, dict] = {}
    revisados, ilegibles = 0, []
    for d in _pdfs_de_examen(documentos):
        revisados += 1
        try:
            with lector.abrir(rutas.data / d["archivo"]) as pdf:
                incrustado = incrustado_por_texto([pdf.texto(n) for n in range(1, pdf.paginas + 1)])
        except Exception as error:
            ilegibles.append(f"{d['id']}: {error}")
            continue
        if incrustado:
            encontrados[d["id"]] = {"contenido": list(incrustado.contenido), "pagina": incrustado.pagina}
    rutas.incrustados.write_text(json.dumps(encontrados, ensure_ascii=False, indent=1))
    return Deteccion(revisados, len(encontrados), ilegibles)


def incrustados_guardados(rutas: Rutas) -> dict[str, Incrustado]:
    if not rutas.incrustados.exists():
        return {}
    return {k: Incrustado(tuple(v["contenido"]), v["pagina"]) for k, v in json.loads(rutas.incrustados.read_text()).items()}


def incrustados_de_extraccion(registros: list[dict], textos: dict[str, list[str]]) -> dict[str, Incrustado]:
    """En los exámenes procesados el modelo sabe dónde acaba el enunciado; sirve cuando el texto no trae un título reconocible."""
    salida = {}
    for r in registros:
        doc_id, resultado = r["documento"]["id"], r["resultado"]
        incrustado = incrustado_por_extraccion(resultado["otro_contenido"], resultado["paginas_enunciado"], textos.get(doc_id, []))
        if incrustado:
            salida[doc_id] = incrustado
    return salida


def anexos_de(documentos: list[dict], registros: list[dict], rutas: Rutas, lector: LectorPdf) -> dict[str, list[dict]]:
    textos = {}
    for r in registros:
        with lector.abrir(rutas.data / r["documento"]["archivo"]) as pdf:
            textos[r["documento"]["id"]] = [pdf.texto(n) for n in range(1, pdf.paginas + 1)]
    return vincular(documentos, combinar(incrustados_guardados(rutas), incrustados_de_extraccion(registros, textos)))
