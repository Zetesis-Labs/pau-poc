"""Compara cada nodo exportado, incluidos apartados, con las fases de extracción."""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def texts(entries):
    return {t["idioma"]: t["markdown"] for t in entries}


def main():
    run = ROOT / "pipeline/salida/gpt-6-luna__p5"
    published = read(ROOT / "datos/preguntas.json")["preguntas"]
    nodes = {}
    mismatches = []
    allrecords = {}
    for q in published:
        docid, nid = q["id"].split(":")
        if docid not in allrecords:
            allrecords[docid] = read(run / (docid + ".json"))
        r = allrecords[docid]
        tree = defaultdict(list)
        for n in r["resultado"]["nodos"]:
            tree[n["padre"]].append(n)
        for children in tree.values():
            children.sort(key=lambda n: n["orden"])
        def mapnode(nid, pub):
            nodes[(docid, nid)] = pub
            raw = next(n for n in r["resultado"]["nodos"] if n["id"] == nid)
            for key in ("etiqueta", "enunciado"):
                if pub[key] != texts(raw[key]):
                    mismatches.append({"documento": docid, "nodo": nid, "campo": key})
            if len(tree[nid]) != len(pub["apartados"]):
                mismatches.append({"documento": docid, "nodo": nid, "campo": "cantidad-apartados"})
            for rawchild, child in zip(tree[nid], pub["apartados"]):
                mapnode(rawchild["id"], child)
        mapnode(nid, q)
    answers, rubrics = [], []
    for path in sorted((run / "rubricas/gpt-6-luna__r2").glob("*.json")):
        r = read(path)
        for e in r.get("resultado", {}).get("entradas", []):
            pub = nodes.get((path.stem, e["nodo"]))
            rubric = pub.get("rubrica") if pub else None
            rubrics.append({"documento": path.stem, "nodo": e["nodo"], "nodo_publicado": pub is not None, "rubrica_publicada": rubric is not None})
            if not e.get("respuesta"):
                continue
            solution = pub.get("solucion") if pub else None
            answers.append({"documento": path.stem, "nodo": e["nodo"], "idiomas": list(texts(e["respuesta"])), "nodo_publicado": pub is not None, "solucion_publicada": solution is not None, "texto_r2_igual_a_solucion": bool(solution and solution["texto"] == texts(e["respuesta"])), "pregunta_raiz_publicada": bool(pub and "examen" in pub)})
    overview = {
        "nodos_mapeados": len(nodes), "discrepancias_texto_entre_nodo_y_publicacion": len(mismatches),
        "entradas_r2": len(rubrics), "rubricas_en_nodo_no_publicado": sum(not r["nodo_publicado"] for r in rubrics),
        "entradas_r2_con_respuesta": len(answers),
        "respuestas_r2_en_nodo_no_publicado": sum(not a["nodo_publicado"] for a in answers),
        "respuestas_r2_en_nodo_publicado_sin_solucion": sum(a["nodo_publicado"] and not a["solucion_publicada"] for a in answers),
        "respuestas_r2_en_nodo_publicado_con_solucion": sum(a["nodo_publicado"] and a["solucion_publicada"] for a in answers),
        "solucion_identica_respuesta_r2": sum(a["texto_r2_igual_a_solucion"] for a in answers),
        "advertencia": "Las respuestas r2 no se certifican correctas: hay que contrastarlas con fuente antes de reutilizarlas.",
    }
    for filename, result in [("respuestas-r2-publicacion.json", answers), ("rubricas-publicacion.json", rubrics), ("discrepancias-publicacion.json", mismatches), ("resumen-publicacion.json", overview)]:
        (OUT / filename).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(overview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
