"""Auditoría local de inventario, integridad y publicación. No modifica las fuentes.

Ejecutar desde cualquier directorio con pipeline/.venv/bin/python este_fichero.
Los checks automáticos no certifican fidelidad semántica al PDF.
"""
import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FORMULA = re.compile(r"\$\$([\s\S]+?)\$\$|(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$", re.S)


def read(p):
    return json.loads(p.read_text())


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def table(name, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def walk(value, path=""):
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")


def main():
    inventory, issues, figures, losses, formulas = [], [], [], [], []
    pdfs, pdfhashes = {}, defaultdict(list)
    current = {}
    for run in sorted((ROOT / "pipeline/salida").iterdir()):
        for path in sorted(run.rglob("*.json")):
            if path.name == "preguntas.json":
                continue
            r = read(path)
            stage = str(path.parent.relative_to(run))
            if "documento" not in r:
                issues.append({"archivo": str(path.relative_to(ROOT)), "tipo": "registro-desconocido"})
                continue
            doc = r["documento"] if isinstance(r["documento"], dict) else {"id": r["documento"]}
            docid = doc["id"]
            result = r.get("resultado", {})
            source = r.get("fuente", {}).get("archivo", doc.get("archivo"))
            fullsource = ROOT / "data" / source if source else None
            pdferror = None
            if source not in pdfs and fullsource and fullsource.exists():
                try:
                    with pymupdf.open(fullsource) as pdf:
                        pdfs[source] = {"paginas": len(pdf), "caracteres_por_pagina": [len(p.get_text().strip()) for p in pdf]}
                    pdfhashes[hashlib.sha256(fullsource.read_bytes()).hexdigest()].append(source)
                except Exception as e:
                    pdferror = str(e)
            elif not fullsource or not fullsource.exists():
                pdferror = "no existe el PDF fuente"
            pages = pdfs.get(source, {}).get("paginas", 0)
            row = {
                "run": run.name, "fase": stage, "id": docid,
                "archivo": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "fuente": source, "pdf_paginas": pages, "pdf_error": pdferror,
                "modelo": r.get("modelo"), "prompt": r.get("prompt"), "estado": r.get("estado"),
                "respuesta_id_disponible": bool(r.get("respuesta")), "error": r.get("error"),
                "resultado_disponible": "resultado" in r,
                "contenido": result.get("es_examen", result.get("contiene_criterios", result.get("contiene_soluciones"))),
                "nodos": len(result.get("nodos", [])), "entradas": len(result.get("entradas", [])),
                "estimulos": len(result.get("estimulos", [])), "incidencias": len(result.get("incidencias", [])),
                "sin_correspondencia": len(result.get("sin_correspondencia", [])),
                "graves_guardados": sum(h.get("grave", False) for h in r.get("hallazgos", [])),
                "leves_guardados": sum(not h.get("grave", False) for h in r.get("hallazgos", [])),
                "revision_semantica_completa": False,
            }
            inventory.append(row)
            prefix = {"run": run.name, "fase": stage, "id": docid}
            if pdferror:
                issues.append({**prefix, "tipo": "pdf-error", "detalle": pdferror})
            for field, val in walk(result):
                if isinstance(val, dict) and "pagina" in val and isinstance(val["pagina"], int):
                    if not 1 <= val["pagina"] <= pages:
                        issues.append({**prefix, "tipo": "pagina-fuera-pdf", "campo": field, "valor": val})
                if isinstance(val, list) and field.endswith("paginas_enunciado"):
                    for n in val:
                        if not 1 <= n <= pages:
                            issues.append({**prefix, "tipo": "pagina-enunciado-fuera-pdf", "valor": n})
                if isinstance(val, str) and (field.endswith("markdown") or field.endswith("descripcion")):
                    for m in FORMULA.finditer(val):
                        formulas.append({**prefix, "campo": field, "tex": (m.group(1) or m.group(2)).strip(), "bloque": m.group(1) is not None})
            for f in r.get("figuras", []):
                figures.append({**prefix, **f, "existe": bool(f.get("archivo") and (run / "figuras" / f["archivo"]).exists())})
            if stage == "." and run.name.endswith("__p5"):
                current[docid] = r
    published = read(ROOT / "datos/preguntas.json")["preguntas"]
    catalogue = read(ROOT / "datos/catalogo.json")["documentos"]
    pubbyid = {q["id"]: q for q in published}
    pubdocs = {q["examen"]["id"] for q in published}
    for docid, r in current.items():
        nodes = r["resultado"]["nodos"]
        represented = set()
        children = defaultdict(list)
        for n in nodes:
            children[n["padre"]].append(n["id"])
        def descendants(n):
            yield n
            for c in children[n]:
                yield from descendants(c)
        for n in nodes:
            q = pubbyid.get(docid + ":" + n["id"])
            if q:
                represented.update(descendants(n["id"]))
                if n.get("eleccion"):
                    losses.append({"tipo": "regla-propia-pregunta-omitida", "id": docid, "nodo": n["id"], "eleccion": n["eleccion"]})
        if r["resultado"].get("instrucciones"):
            losses.append({"tipo": "instrucciones-generales-no-publicadas", "id": docid, "cantidad": len(r["resultado"]["instrucciones"])})
        for stage, subdir in [("rubrica", "rubricas/gpt-6-luna__r2"), ("solucion-oficial", "soluciones/gpt-6-luna__s1/oficial"), ("solucion-academia", "soluciones/gpt-6-luna__s1/academia")]:
            path = ROOT / "pipeline/salida/gpt-6-luna__p5" / subdir / (docid + ".json")
            if not path.exists():
                continue
            correction = read(path)
            for entry in correction.get("resultado", {}).get("entradas", []):
                if entry["nodo"] not in represented:
                    losses.append({"tipo": "entrada-en-nodo-no-publicado", "fase": stage, "id": docid, "nodo": entry["nodo"], "entrada": entry})
    asset_errors = []
    for where, val in walk([published, catalogue]):
        if isinstance(val, dict):
            for key in ("pdf", "src"):
                if isinstance(val.get(key), str) and not (ROOT / "datos" / val[key]).is_file():
                    asset_errors.append({"campo": where + "." + key, "ruta": val[key]})
    coverage = []
    for docid, r in current.items():
        qs = [q for q in published if q["examen"]["id"] == docid]
        allnodes = [v for _, v in walk(qs) if isinstance(v, dict) and "apartados" in v and "enunciado" in v]
        coverage.append({"id": docid, **{k: r["documento"].get(k) for k in ("asignatura", "region", "anio", "convocatoria")}, "preguntas_publicadas": len(qs), "nodos_publicados": len(allnodes), "nodos_con_rubrica": sum(bool(n.get("rubrica")) for n in allnodes), "nodos_con_solucion": sum(bool(n.get("solucion")) for n in allnodes), "preguntas_con_ancla": sum(any(a.get("y0") is not None for a in q.get("anclas", {}).values()) for q in qs)})
    katex_errors = []
    node = Path("/opt/homebrew/opt/node@22/bin/node")
    executable = str(node) if node.exists() else shutil.which("node")
    if executable:
        proc = subprocess.run([executable, str(ROOT / "pipeline/src/pau/adaptadores/katex_check.js")], input=json.dumps(formulas), text=True, capture_output=True, check=True)
        for f, error in zip(formulas, json.loads(proc.stdout), strict=True):
            if error:
                katex_errors.append({**f, "error": error})
    summary = {
        "registros": len(inventory), "por_run_fase": dict(Counter(r["run"] + "/" + r["fase"] for r in inventory)),
        "pdfs_fuente_unicos_por_ruta": len(pdfs), "paginas_fuente": sum(p["paginas"] for p in pdfs.values()),
        "paginas_sin_capa_texto_suficiente_menos_40_caracteres": sum(n < 40 for p in pdfs.values() for n in p["caracteres_por_pagina"]),
        "errores_integridad": len(issues), "figuras_registradas": len(figures),
        "publicado": {"documentos_catalogo": len(catalogue), "examenes": len(pubdocs), "preguntas": len(published), "referencias_rotas": len(asset_errors), "figuras_png": len(list((ROOT / 'datos/figuras').glob('*.png')))},
        "perdidas_o_limitaciones_publicacion": dict(Counter(x["tipo"] for x in losses)),
        "formulas_comprobadas": len(formulas), "errores_katex": len(katex_errors),
        "limitacion": "Inventario y comprobaciones mecánicas de todos los registros; no certifica semántica, completitud o matemática. Contrastes visuales y semánticos por agentes en carpetas hermanas; sin revisión docente humana.",
    }
    for name, rows in [("inventario", inventory), ("integridad", issues), ("figuras", figures), ("perdidas-publicacion", losses), ("cobertura", coverage), ("errores-katex", katex_errors)]:
        write(name + ".json", rows)
        table(name + ".csv", rows)
    write("pdfs.json", pdfs)
    write("pdfs-duplicados.json", {h: ps for h, ps in pdfhashes.items() if len(ps) > 1})
    write("referencias-rotas.json", asset_errors)
    write("resumen.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
