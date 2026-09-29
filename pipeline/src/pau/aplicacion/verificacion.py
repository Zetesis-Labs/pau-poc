"""Control local de conservación antes de reemplazar el banco publicado."""

import hashlib
import json
from collections import Counter
from dataclasses import asdict

from pydantic import ValidationError

from pau.aplicacion.banco import RUBRICAS, SOLUCIONES
from pau.aplicacion.rutas import Rutas
from pau.dominio.banco import preguntas_de
from pau.dominio.conservacion import comprobar_conservacion
from pau.dominio.esquema import ExamenExtraido
from pau.dominio.recuperacion import recuperar_respuestas
from pau.dominio.soluciones import soluciones_por_nodo
from pau.dominio.validar import Hallazgo, contenido, estructura, paginas

ESTRUCTURA_INSEGURA = {"id-duplicado", "padre-inexistente", "ciclo"}


def _leer(ruta, huellas: dict) -> dict:
    contenido = ruta.read_bytes()
    huellas[str(ruta.name)] = hashlib.sha256(contenido).hexdigest()
    return json.loads(contenido)


def _correccion(ruta, huellas: dict, hallazgos: list[Hallazgo], etapa: str) -> dict | None:
    if not ruta.exists():
        return None
    contenido = ruta.read_bytes()
    huellas[etapa] = hashlib.sha256(contenido).hexdigest()
    try:
        registro = json.loads(contenido)
    except (json.JSONDecodeError, UnicodeDecodeError):
        hallazgos.append(Hallazgo("correccion-invalida", True, etapa))
        return None
    if not isinstance(registro, dict) or "resultado" not in registro:
        hallazgos.append(Hallazgo("correccion-fallida", True, etapa))
        return None
    if etapa.startswith("solucion"):
        cuentas = Counter(e["nodo"] for e in registro["resultado"].get("entradas", []))
        for nodo, cantidad in cuentas.items():
            if cantidad > 1:
                hallazgos.append(Hallazgo("solucion-duplicada", True, f"{etapa}: {nodo}, {cantidad} entradas"))
    return registro


def _fuentes(registro: dict, correcciones: list[dict | None], rutas: Rutas, hallazgos: list[Hallazgo]) -> None:
    archivos = [registro["documento"].get("archivo")]
    archivos += [c.get("fuente", {}).get("archivo") for c in correcciones if c and c.get("fuente")]
    for archivo in dict.fromkeys(archivos):
        if not archivo or not (rutas.data / archivo).is_file():
            hallazgos.append(Hallazgo("pdf-ausente", True, str(archivo)))


def _exclusiones(rubrica: dict | None, oficial: dict | None, academia: dict | None) -> list[dict]:
    excluidos = []
    for etapa, registro in (("rubrica", rubrica), ("solucion-oficial", oficial), ("solucion-academia", academia)):
        if registro is None:
            excluidos.append({"etapa": etapa, "motivo": "sin_resultado_disponible"})
    respondidos = set(soluciones_por_nodo(oficial, None))
    if academia:
        excluidos += [
            {"etapa": "solucion-academia", "nodo": e["nodo"], "motivo": "se_conserva_la_solucion_oficial_del_mismo_nodo"}
            for e in academia["resultado"].get("entradas", []) if e.get("respuesta") and e["nodo"] in respondidos
        ]
    return excluidos


def _examinar(registro: dict, base, rutas: Rutas, rubricas: str, soluciones: str, huellas: dict) -> tuple[list[dict], list[Hallazgo], list[dict]]:
    doc_id = registro["documento"]["id"]
    examen = ExamenExtraido(**registro["resultado"])
    hallazgos = estructura(examen)
    if any(h.regla in ESTRUCTURA_INSEGURA for h in hallazgos):
        return [], hallazgos, []
    hallazgos += contenido(examen) + paginas(examen)
    rubrica = _correccion(base / "rubricas" / rubricas / f"{doc_id}.json", huellas, hallazgos, "rubrica")
    oficial = _correccion(base / "soluciones" / soluciones / "oficial" / f"{doc_id}.json", huellas, hallazgos, "solucion-oficial")
    academia = _correccion(base / "soluciones" / soluciones / "academia" / f"{doc_id}.json", huellas, hallazgos, "solucion-academia")
    _fuentes(registro, [rubrica, oficial, academia], rutas, hallazgos)
    por_nodo = soluciones_por_nodo(oficial, academia)
    por_nodo, exclusiones_respuestas = recuperar_respuestas(registro, rubrica, por_nodo)
    preguntas = preguntas_de(registro, rubrica, por_nodo)
    hallazgos += comprobar_conservacion(registro, preguntas, rubrica, por_nodo)
    for nombre in sorted({f["src"].removeprefix("figuras/") for p in preguntas for e in p["estimulos"] for f in e["figuras"]}):
        if not (base / "figuras" / nombre).is_file():
            hallazgos.append(Hallazgo("figura-ausente", True, nombre))
    return preguntas, hallazgos, _exclusiones(rubrica, oficial, academia) + exclusiones_respuestas


def _cobertura(preguntas: list[dict]) -> dict[str, int]:
    cuentas = {
        "preguntas": len(preguntas), "apartados": 0, "rubricas": 0,
        "criterios_generales": sum(bool(p.get("criteriosGenerales")) for p in preguntas),
        "fuentes_rubrica": sum(bool(p.get("fuenteRubrica")) for p in preguntas),
        "soluciones": 0, "soluciones_oficiales": 0,
    }
    pendientes = list(preguntas)
    while pendientes:
        nodo = pendientes.pop()
        apartados = nodo.get("apartados", [])
        cuentas["apartados"] += len(apartados)
        cuentas["rubricas"] += bool(nodo.get("rubrica"))
        cuentas["soluciones"] += bool(nodo.get("solucion"))
        cuentas["soluciones_oficiales"] += bool(nodo.get("solucion") and nodo["solucion"].get("origen") == "oficial")
        pendientes.extend(apartados)
    return cuentas


def _comparar_anterior(rutas: Rutas, documentos: list[dict]) -> tuple[list[dict], str | None]:
    anterior = rutas.datos / "preguntas.json"
    if not anterior.exists():
        return [], None
    contenido = anterior.read_bytes()
    huella = hashlib.sha256(contenido).hexdigest()
    hallazgos = []
    try:
        banco = json.loads(contenido)
        por_examen = {}
        for p in banco["preguntas"]:
            por_examen.setdefault(p["examen"]["id"], []).append(p)
        actuales = {d["documento"]: d for d in documentos}
        for doc_id, preguntas in por_examen.items():
            if doc_id not in actuales:
                hallazgos.append(asdict(Hallazgo("examen-publicado-ausente", True, doc_id)))
                continue
            actual = actuales[doc_id]
            for campo, cantidad in _cobertura(preguntas).items():
                nueva = actual["cobertura"][campo]
                if nueva < cantidad:
                    actual["hallazgos"].append(asdict(Hallazgo("cobertura-reducida", True, f"{campo}: {cantidad} publicados, {nueva} propuestos")))
                    actual["estado"] = "pendiente_revision"
                    for p in actual["preguntas"]:
                        p["estado"] = "pendiente_revision"
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, AttributeError):
        hallazgos.append(asdict(Hallazgo("banco-anterior-invalido", True, "No se puede comprobar la cobertura publicada")))
    return hallazgos, huella


def verificar(ejecucion: str, rutas: Rutas, rubricas: str = RUBRICAS, soluciones: str = SOLUCIONES) -> dict:
    """Genera un informe sin API ni escritura en el corpus; aprobarlo no certifica el PDF."""
    base = rutas.ejecucion(ejecucion)
    documentos, excluidos = [], []
    for archivo in sorted(base.glob("*.json")):
        if archivo.name == "preguntas.json":
            continue
        huellas, preguntas, hallazgos, exclusiones = {}, [], [], []
        doc_id = archivo.stem
        try:
            registro = _leer(archivo, huellas)
            if not isinstance(registro, dict) or "resultado" not in registro:
                hallazgos = [Hallazgo("extraccion-fallida", True, archivo.name)]
            elif registro["resultado"].get("es_examen") is False:
                excluidos.append({"documento": doc_id, "motivo": "extraccion_declara_no_examen", "huellas": huellas})
                continue
            else:
                doc_id = registro["documento"]["id"]
                preguntas, hallazgos, exclusiones = _examinar(registro, base, rutas, rubricas, soluciones, huellas)
                if doc_id != archivo.stem:
                    hallazgos.append(Hallazgo("identidad-registro-incompatible", True, f"{archivo.name}: documento {doc_id}"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, KeyError, TypeError, ValueError, AttributeError) as error:
            hallazgos.append(Hallazgo("registro-invalido", True, f"{archivo.name}: {type(error).__name__}"))
        estado = "pendiente_revision" if any(h.grave for h in hallazgos) else "controles_superados"
        documentos.append({
            "documento": doc_id, "estado": estado, "huellas": huellas,
            "hallazgos": [asdict(h) for h in hallazgos],
            "preguntas": [{"id": p["id"], "estado": estado} for p in preguntas],
            "cobertura": _cobertura(preguntas), "exclusiones": exclusiones,
        })
    generales, banco_anterior = _comparar_anterior(rutas, documentos)
    if not documentos:
        generales.append(asdict(Hallazgo("sin-examenes", True, "No hay exámenes comprobables en la ejecución")))
    pendientes = sum(d["estado"] == "pendiente_revision" for d in documentos)
    return {
        "version": 1, "ejecucion": ejecucion, "rubricas": rubricas, "soluciones": soluciones,
        "estado": "pendiente_revision" if pendientes or generales else "controles_superados",
        "resumen": {"examenes": len(documentos), "pendientes_revision": pendientes, "controles_superados": len(documentos) - pendientes},
        "documentos": documentos, "exclusiones": excluidos,
        "hallazgos": generales, "banco_anterior_sha256": banco_anterior,
        "alcance": "Conservación y estructura del banco; no certifica exhaustividad frente al PDF ni corrección académica. El estado se propaga a las preguntas del examen.",
    }


def guardar(informe: dict, rutas: Rutas):
    destino = rutas.ejecucion(informe["ejecucion"]) / "verificacion" / "informe.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n")
    return destino


class PublicacionBloqueada(ValueError):
    """El banco anterior se conserva porque la propuesta pierde contenido o no se puede comprobar."""


def exigir_conservacion(ejecucion: str, rutas: Rutas, rubricas: str = RUBRICAS, soluciones: str = SOLUCIONES) -> dict:
    informe = verificar(ejecucion, rutas, rubricas, soluciones)
    destino = guardar(informe, rutas)
    if informe["estado"] != "controles_superados":
        raise PublicacionBloqueada(f"Publicación bloqueada; se conserva datos/. Revisa {destino}")
    return informe
