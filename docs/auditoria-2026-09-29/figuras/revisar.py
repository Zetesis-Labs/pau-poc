"""Inventario geométrico y hojas de contacto; no modifica las extracciones."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import pymupdf

from pau.adaptadores.pdf_pymupdf import LectorPymupdf
from pau.dominio.esquema import ExamenExtraido
from pau.dominio.geometria import paginas_con_recortes, planificar_recortes

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main():
    run = ROOT / "pipeline/salida/gpt-6-luna__p5"
    rows, hashes = [], defaultdict(list)
    for file in sorted(run.glob("*.json")):
        r = json.loads(file.read_text())
        if "resultado" not in r:
            continue
        examen = ExamenExtraido(**r["resultado"])
        with LectorPymupdf().abrir(ROOT / "data" / r["documento"]["archivo"]) as pdf:
            pages = {n: pdf.geometria(n) for n in paginas_con_recortes(examen) if 1 <= n <= pdf.paginas}
        for p in planificar_recortes(examen, pages):
            imagefile = f"{file.stem}_{p.estimulo}_{p.idioma}_{p.numero}.png"
            saved = next((f for f in r.get("figuras", []) if f.get("archivo") == imagefile), {})
            original = next(e for e in examen.estimulos if e.id == p.estimulo).recortes[p.numero - 1]
            row = {"documento": file.stem, "asignatura": r["documento"]["asignatura"], "estimulo": p.estimulo, "pagina": p.pagina, "idioma": p.idioma, "archivo": imagefile, "publicado": (ROOT / "datos/figuras" / imagefile).exists(), "metodo_guardado": saved.get("metodo"), "metodo_recalculado": p.metodo, "problemas": list(p.problemas), "caja_modelo_fraccion": [original.x0, original.y0, original.x1, original.y1], "caja_recalculada_puntos_pdf": list(p.caja.tupla()) if p.caja else None, "revision_visual": "hoja-contacto" if (ROOT / "datos/figuras" / imagefile).exists() else "sin-imagen-publicada"}
            rows.append(row)
            if row["publicado"]:
                hashes[hashlib.sha256((ROOT / "datos/figuras" / imagefile).read_bytes()).hexdigest()].append(imagefile)
    (OUT / "geometria.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    (OUT / "duplicados-exactos.json").write_text(json.dumps({k: v for k, v in hashes.items() if len(v) > 1}, ensure_ascii=False, indent=2))
    files = sorted((ROOT / "datos/figuras").glob("*.png"))
    manifest = []
    for start in range(0, len(files), 20):
        doc = pymupdf.open()
        page = doc.new_page(width=1400, height=1250)
        for i, p in enumerate(files[start:start + 20]):
            x, y = (i % 4) * 350, (i // 4) * 250
            page.insert_text((x + 5, y + 14), p.name, fontsize=9)
            page.insert_image(pymupdf.Rect(x + 5, y + 23, x + 345, y + 245), filename=str(p), keep_proportion=True)
            manifest.append({"hoja": start // 20 + 1, "posicion": i + 1, "archivo": str(p.relative_to(ROOT))})
        page.get_pixmap().save(OUT / f"contacto-{start // 20 + 1:02}.png")
    (OUT / "contactos.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"{len(rows)} planes; {len(files)} imágenes publicadas; {len(hashes)} hashes")


if __name__ == "__main__":
    main()
