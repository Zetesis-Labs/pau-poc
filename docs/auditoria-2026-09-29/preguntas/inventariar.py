"""Inventario reproducible, solo lectura, de las extracciones p4/p5.

Ejecutar desde la raíz con pipeline/.venv/bin/python docs/auditoria-2026-09-29/preguntas/inventariar.py.
No llama a servicios ni modifica las extracciones originales.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUNS = {v: ROOT / "pipeline/salida" / f"gpt-6-luna__{v}" for v in ("p4", "p5")}


def fold(value: str) -> str:
    value = re.sub(r"\$+|\\(?:mathrm|operatorname|ce|text|mathbf|frac|sqrt|left|right)\b", " ", value)
    value = value.replace("{,}", ",")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", value.lower())).strip()


def texts(items: list[dict]) -> list[str]:
    return [x.get("markdown", "") for x in items if x.get("markdown")]


def node_text(node: dict) -> str:
    return " ".join(texts(node.get("enunciado", [])))


def pdf_texts(path: Path) -> list[str]:
    with pymupdf.open(path) as doc:
        return [page.get_text(sort=True) for page in doc]


def analyze(version: str) -> tuple[dict[str, dict], list[dict]]:
    results = {}
    suspects = []
    for path in sorted(RUNS[version].glob("*.json")):
        if path.name == "preguntas.json":
            continue
        data = json.loads(path.read_text())
        result = data.get("resultado") or {}
        nodes = result.get("nodos") or []
        stimuli = result.get("estimulos") or []
        doc = data["documento"]
        pdf = ROOT / "data" / doc["archivo"]
        row = {
            "version": version,
            "documento": path.stem,
            "region": doc.get("region"),
            "asignatura": doc.get("asignatura"),
            "anio": doc.get("anio"),
            "convocatoria": doc.get("convocatoria"),
            "fuente": doc.get("fuente"),
            "pdf": str(pdf.relative_to(ROOT)),
            "pdf_existe": pdf.is_file(),
            "es_examen": result.get("es_examen"),
            "paginas_pdf": doc.get("paginas"),
            "paginas_enunciado": result.get("paginas_enunciado", []),
            "idiomas": result.get("idiomas", []),
            "nodos": len(nodes),
            "preguntas": sum(n.get("tipo") == "pregunta" for n in nodes),
            "apartados": sum(n.get("tipo") == "apartado" for n in nodes),
            "estimulos": len(stimuli),
            "incidencias": len(result.get("incidencias") or []),
            "hallazgos_graves": [h for h in data.get("hallazgos", []) if h.get("grave")],
            "normalizaciones": data.get("normalizaciones"),
        }
        results[path.stem] = row
        by_id = {n.get("id"): n for n in nodes}
        orders = defaultdict(list)
        for n in nodes:
            orders[n.get("padre")].append(n.get("orden"))
            if n.get("padre") is not None and n.get("padre") not in by_id:
                suspects.append({"version": version, "documento": path.stem, "tipo": "padre_inexistente", "nodo": n.get("id")})
            if n.get("tipo") == "pregunta" and n.get("padre") in by_id and by_id[n["padre"]].get("tipo") == "pregunta":
                suspects.append({"version": version, "documento": path.stem, "tipo": "pregunta_dentro_pregunta", "nodo": n.get("id")})
            pages = {x.get("pagina") for x in n.get("paginas", [])}
            if any(not isinstance(p, int) or p < 1 or p > (doc.get("paginas") or 0) for p in pages):
                suspects.append({"version": version, "documento": path.stem, "tipo": "pagina_fuera_pdf", "nodo": n.get("id"), "paginas": sorted(pages, key=str)})
            if n.get("tipo") == "pregunta" and not node_text(n) and not n.get("estimulos") and not any(x.get("padre") == n.get("id") for x in nodes):
                suspects.append({"version": version, "documento": path.stem, "tipo": "pregunta_vacia", "nodo": n.get("id")})
            if n.get("tipo") == "apartado" and n.get("padre") not in by_id:
                suspects.append({"version": version, "documento": path.stem, "tipo": "apartado_sin_padre", "nodo": n.get("id")})
            if n.get("tipo") == "apartado" and n.get("padre") in by_id and by_id[n["padre"]].get("tipo") not in ("pregunta", "apartado"):
                suspects.append({"version": version, "documento": path.stem, "tipo": "apartado_fuera_pregunta", "nodo": n.get("id"), "padre": n.get("padre"), "tipo_padre": by_id[n["padre"]].get("tipo")})
        for parent, seq in orders.items():
            if len(seq) != len(set(seq)):
                suspects.append({"version": version, "documento": path.stem, "tipo": "orden_duplicado", "padre": parent, "ordenes": seq})
        if not pdf.is_file():
            continue
        try:
            pages_text = pdf_texts(pdf)
        except Exception as exc:
            suspects.append({"version": version, "documento": path.stem, "tipo": "pdf_ilegible", "error": str(exc)})
            continue
        row["paginas_pdf_leidas"] = len(pages_text)
        row["caracteres_texto_pdf"] = sum(len(p) for p in pages_text)
        row["paginas_sin_capa_texto"] = [i + 1 for i, p in enumerate(pages_text) if len(p.strip()) < 30]
        page_words = [set(fold(p).split()) for p in pages_text]
        for n in nodes:
            if n.get("tipo") not in ("pregunta", "apartado"):
                continue
            for t in n.get("enunciado", []):
                words = set(w for w in fold(t.get("markdown", "")).split() if len(w) >= 5)
                if len(words) < 6:
                    continue
                stated = [x["pagina"] - 1 for x in n.get("paginas", []) if x.get("idioma") == t.get("idioma") and isinstance(x.get("pagina"), int)]
                nearby = set(i for p in stated for i in range(max(0, p - 1), min(len(pages_text), p + 2)))
                if not nearby:
                    nearby = set(range(len(pages_text)))
                score = max((len(words & page_words[i]) / len(words) for i in nearby), default=0)
                if score < 0.25:
                    suspects.append({"version": version, "documento": path.stem, "tipo": "baja_similitud_lexica", "nodo": n.get("id"), "idioma": t.get("idioma"), "pagina": stated, "similitud": round(score, 3), "texto": t.get("markdown", "")[:280]})
        for stim in stimuli:
            if stim.get("tipo") in ("texto", "tabla") and not stim.get("contenido"):
                suspects.append({"version": version, "documento": path.stem, "tipo": "estimulo_textual_vacio", "estimulo": stim.get("id")})
    return results, suspects


def main() -> None:
    all_rows = {}
    all_suspects = []
    for version in RUNS:
        rows, suspects = analyze(version)
        all_rows[version] = rows
        all_suspects.extend(suspects)
    shared = set(all_rows["p4"]) & set(all_rows["p5"])
    regressions = []
    for doc in sorted(shared):
        a, b = all_rows["p4"][doc], all_rows["p5"][doc]
        delta = {field: [a[field], b[field]] for field in ("nodos", "preguntas", "apartados", "estimulos", "idiomas", "paginas_enunciado", "es_examen") if a[field] != b[field]}
        if delta:
            regressions.append({"documento": doc, "cambios": delta})
    inventory = {"resumen": {v: {"documentos": len(rows), "nodos": sum(r["nodos"] for r in rows.values()), "preguntas": sum(r["preguntas"] for r in rows.values()), "pdfs_presentes": sum(r["pdf_existe"] for r in rows.values()), "pdfs_sin_capa_texto": sum(r.get("caracteres_texto_pdf", 0) < 100 for r in rows.values()), "graves": sum(len(r["hallazgos_graves"]) for r in rows.values())} for v, rows in all_rows.items()}, "documentos": all_rows, "regresiones_candidatas": regressions}
    (OUT / "inventario.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    (OUT / "candidatos.json").write_text(json.dumps(all_suspects, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"resumen": inventory["resumen"], "regresiones_candidatas": len(regressions), "candidatos": dict(Counter(s["tipo"] for s in all_suspects))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
