"""Resumen agregado y detalle de una ejecución de extracción."""

from collections import Counter, defaultdict
from statistics import median


def resumen(registros: list[dict]) -> dict:
    ok = [r for r in registros if "resultado" in r]
    examenes = [r for r in ok if r["resultado"]["es_examen"]]
    graves = Counter(h["regla"] for r in ok for h in r["hallazgos"] if h["grave"])
    leves = Counter(h["regla"] for r in ok for h in r["hallazgos"] if not h["grave"])
    limpios = [r for r in examenes if not any(h["grave"] for h in r["hallazgos"])]
    por_estrato: dict[str, list[dict]] = defaultdict(list)
    for r in ok:
        por_estrato[r["documento"]["estrato"].split(" · ")[0]].append(r)
    return {
        "total": len(registros),
        "errores_api": [(r["documento"]["asignatura"], r["error"][:120]) for r in registros if "error" in r],
        "no_es_examen": len(ok) - len(examenes),
        "sin_hallazgos_graves": len(limpios),
        "graves": graves.most_common(),
        "leves": leves.most_common(),
        "con_incidencias": sum(bool(r["resultado"]["incidencias"]) for r in ok),
        "incidencias": sum(len(r["resultado"]["incidencias"]) for r in ok),
        "nodos": sum(len(r["resultado"]["nodos"]) for r in ok),
        "preguntas": sum(n["tipo"] == "pregunta" for r in ok for n in r["resultado"]["nodos"]),
        "bilingues": sum(len(r["resultado"]["idiomas"]) > 1 for r in ok),
        "segundos_mediana": median(r["segundos"] for r in ok) if ok else 0,
        "tokens_entrada": sum(r["uso"]["input_tokens"] for r in ok),
        "tokens_salida": sum(r["uso"]["output_tokens"] for r in ok),
        "tokens_razonamiento": sum(r["uso"]["output_tokens_details"]["reasoning_tokens"] for r in ok),
        "por_estrato": {
            e: f"{sum(not any(h['grave'] for h in r['hallazgos']) for r in rs)}/{len(rs)} limpios"
            for e, rs in sorted(por_estrato.items())
        },
    }


def detalle(registros: list[dict]) -> list[str]:
    lineas = []
    for r in registros:
        d = r["documento"]
        cabecera = f"{d['region']} · {d['asignatura']} · {d['anio']} {d['convocatoria']} ({d['fuente']}, {d['paginas']} p.)"
        if "error" in r:
            lineas.append(f"✗ {cabecera}\n    error: {r['error'][:200]}")
            continue
        graves = [h for h in r["hallazgos"] if h["grave"]]
        marca = "✓" if not graves else "!"
        res = r["resultado"]
        lineas.append(f"{marca} {cabecera} — {len(res['nodos'])} nodos, idiomas {','.join(res['idiomas'])}, {r['segundos']}s")
        lineas += [f"    grave: {h['regla']} {h['detalle']}" for h in graves]
        lineas += [f"    incidencia: {i}" for i in res["incidencias"]]
    return lineas
