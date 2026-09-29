"""Reproduce el resumen local y comprueba que los registros auditados siguen intactos."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from pau.aplicacion.rutas import Rutas
from pau.aplicacion.verificacion import guardar, verificar

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = Path(__file__).resolve().parent
informe = verificar("gpt-6-luna__p5", Rutas(RAIZ))
guardar(informe, Rutas(RAIZ))
reglas = Counter(h["regla"] for d in informe["documentos"] for h in d["hallazgos"])
campos = Counter(h["detalle"].split(".", 1)[-1] for d in informe["documentos"] for h in d["hallazgos"] if h["regla"] == "campo-alterado")
inventario = list(csv.DictReader((RAIZ / "docs/auditoria-2026-09-29/general/inventario.csv").open()))
modificados = [r["archivo"] for r in inventario if hashlib.sha256((RAIZ / r["archivo"]).read_bytes()).hexdigest() != r["sha256"]]
resumen = {
    "ejecucion": informe["ejecucion"], "resumen": informe["resumen"],
    "hallazgos_generales": informe["hallazgos"], "hallazgos_por_regla": dict(reglas),
    "campos_alterados": dict(campos), "banco_anterior_sha256": informe["banco_anterior_sha256"],
    "registros_originales_comprobados": len(inventario), "registros_originales_modificados": modificados,
    "alcance": informe["alcance"],
}
(DESTINO / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
with (DESTINO / "estado-examenes.csv").open("w", newline="") as archivo:
    salida = csv.writer(archivo)
    salida.writerow(["documento", "estado", "hallazgos_graves", "hallazgos_leves", "reglas"])
    for d in informe["documentos"]:
        salida.writerow([d["documento"], d["estado"], sum(h["grave"] for h in d["hallazgos"]), sum(not h["grave"] for h in d["hallazgos"]), "|".join(sorted({h["regla"] for h in d["hallazgos"]}))])
print(json.dumps(resumen, ensure_ascii=False))
