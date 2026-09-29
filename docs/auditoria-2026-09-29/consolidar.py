"""Consolida las observaciones de esta auditoría; no vuelve a inferir su veracidad."""
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def read(p):
    return json.loads(p.read_text())


def write(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


figures = [
    ("FIG-01", "P1", ["184bfaad518f"], ["E1"], [2], "modelo", "La gráfica se sustituye por texto de otras preguntas."),
    ("FIG-02", "P1", ["1f06fc98f001"], ["E2", "E3"], [2], "modelo", "Gráficas incompletas: se corta su zona inferior y ejes."),
    ("FIG-03", "P1", ["fdd6ca513f80"], ["E5"], [7], "ajuste_pdf", "La pieza A2 se sustituye por la casilla de identificación del alumno."),
    ("FIG-04", "P1", ["61e34b1b42fa"], ["E4", "E5"], [2], "modelo_y_ajuste_pdf", "Tabla siderúrgica sustituida por tabla de electrodomésticos; segunda tabla reducida a última fila."),
    ("FIG-05", "P1", ["9c4cbc92103b"], ["E2", "E3"], [4], "modelo_y_recorte", "Jóvenes con móviles sustituidos por conejo; recorte del conejo casi vacío."),
    ("FIG-06", "P2", ["03364198c8fb"], ["E2"], [4], "modelo", "Primera de cuatro posiciones cortada casi por completo."),
    ("FIG-07", "P1", ["67eea232db63"], ["E2"], [3], "modelo", "Se pierde parte superior del contorno de Dibujo Técnico."),
    ("FIG-08", "P1", ["4a7c96ae2912", "3068d1110070"], [], [], "validacion_geometrica", "12 páginas de partituras descartadas por casi-pagina. Contraste visual de páginas representativas 5 y 7."),
    ("FIG-09", "P1", ["3068d1110070"], ["E2"], [4, 5, 6], "web", "Fallback de idioma muestra una de tres páginas publicadas; ejecución del cuerpo real de figurasDe, sin navegador."),
]
figure_findings = [dict(id=i, prioridad=p, documentos=d, estimulos=e, paginas=pg, causa=c,
                        estado="confirmado", descripcion=t) for i, p, d, e, pg, c, t in figures]
write(OUT / "figuras/hallazgos.json", figure_findings)
visual = []
for row in read(OUT / "figuras/contactos.json"):
    name = Path(row["archivo"]).name
    docid, stimulus = name.split("_")[:2]
    matches = [f["id"] for f in figure_findings if docid in f["documentos"] and stimulus in f["estimulos"]]
    visual.append({**row, "estado": "inspeccionada_en_hoja_por_agente", "hallazgos": matches,
                   "conformidad_semantica_certificada": False,
                   "alcance": "Criba visual de miniatura; contraste con PDF original solo en los casos documentados."})
write(OUT / "figuras/revision-visual.json", visual)

general = [
    {"id": "META-01", "documento": "09fa045004f2", "prioridad": "P1", "estado": "confirmado", "causa": "catalogo", "descripcion": "Examen CIUG Galicia catalogado como Comunidad Valenciana."},
    {"id": "META-02", "documento": "61e34b1b42fa", "prioridad": "P1", "estado": "confirmado", "causa": "catalogo", "descripcion": "Examen CIUG Galicia catalogado como Comunidad Valenciana."},
    {"id": "META-03", "documento": "cb9d8c2c12d7", "prioridad": "P1", "estado": "confirmado", "causa": "catalogo", "descripcion": "Literatura Universal catalogada como Lengua Castellana y Literatura II."},
    {"id": "PUB-01", "documento": None, "prioridad": "P1", "estado": "confirmado", "causa": "publicacion", "descripcion": "80 preguntas pierden su regla propia de elección; distinto de los 80 apartados fuera de pregunta."},
    {"id": "PUB-02", "documento": None, "prioridad": "P2", "estado": "limitacion_confirmada", "causa": "contrato_publicacion", "descripcion": "225 exámenes tienen instrucciones generales extraídas no publicadas; impacto variable según texto y PDF accesible."},
    {"id": "PUB-03", "documento": None, "prioridad": "P1", "estado": "confirmado", "causa": "jerarquia_y_publicacion", "descripcion": "86 entradas de corrección cuelgan de nodos no publicados: 82 r2 y 4 s1 de academia."},
    {"id": "FORM-01", "documento": "25fcf7208b8f", "prioridad": "P2", "estado": "confirmado", "causa": "latex", "descripcion": "Una fórmula s1 publicada no compila en KaTeX: texto con superíndice dentro de text. La otra fórmula inválida del corpus pertenece al histórico p4 (3ad09f75385c, sen)."},
]
write(OUT / "general/hallazgos.json", general)
manifest = read(OUT / "general/cabeceras/manifest.json")
for r in manifest:
    r.update(estado="inspeccionada_en_hoja_por_agente", metadatos_certificados=False,
             hallazgos=[g["id"] for g in general if g["id"].startswith("META") and g["documento"] == r["id"]])
write(OUT / "general/cabeceras/manifest.json", manifest)
summary_path = OUT / "general/resumen.json"
summary = read(summary_path)
summary["limitacion"] = "Inventario mecánico completo; no certifica semántica, completitud o matemática. Contrastes visuales y semánticos por agentes en carpetas hermanas; sin revisión docente humana."
write(summary_path, summary)

all_findings = []
for file in ["preguntas/hallazgos-confirmados.json", "rubricas/hallazgos.json", "soluciones/hallazgos.json", "figuras/hallazgos.json", "general/hallazgos.json"]:
    for item in read(OUT / file):
        all_findings.append({"informe_origen": file, **item})
write(OUT / "hallazgos.json", {"advertencia": "Índice de observaciones, no número de bugs independientes: hay solapamientos, limitaciones y procedencias pendientes de acreditar. No todos son errores de Luna.", "observaciones": all_findings})

rows = []
for file in sorted((ROOT / "pipeline/salida/gpt-6-luna__p5").glob("*.json")):
    r = read(file)
    if "documento" not in r:
        continue
    doc = r["documento"]
    findings = [f["id"] for f in all_findings if f.get("documento") == doc["id"] or doc["id"] in f.get("documentos", [])]
    rows.append({"documento": doc["id"], "region_catalogo": doc["region"], "asignatura_catalogo": doc["asignatura"],
                 "anio": doc["anio"], "estado": "con_observaciones" if findings else "sin_hallazgo_individual_no_certificado",
                 "hallazgos": ",".join(findings), "revision_semantica_completa": False,
                 "cobertura": "Inventario/estructura p5 y criba visual cabecera; alcance semántico por informe de área"})
with (OUT / "estado-examenes.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"{len(all_findings)} observaciones (solapadas); {len(rows)} exámenes; {len(visual)} imágenes; {len(manifest)} cabeceras")
