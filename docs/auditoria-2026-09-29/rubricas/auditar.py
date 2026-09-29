"""Inventario reproducible de rúbricas; solo lee corpus y PDF originales."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "pipeline/salida/gpt-6-luna__p5"

ESTADOS = {
    "070c3795d83c": "error_confirmado",
    "9c4cbc92103b": "error_confirmado",
    "3c134e1125e6": "pagina_criterio_incorrecta",
    "cdd0f4f759e1": "pagina_criterio_incorrecta",
    "5091bd5d23ad": "fuente_con_pregunta_distinta",
    "ab690a84e30c": "baremo_fuente_difiere_examen",
    "4a7c96ae2912": "contradiccion_en_pdf",
    "6649ce9eecb2": "procedencia_oficial_no_acreditada",
    "b996e7795739": "procedencia_oficial_no_acreditada",
    "17445f0ab770": "solo_criterios_generales",
    "1f06fc98f001": "solo_criterios_generales",
    "6a2a804ce68f": "solo_criterios_generales",
    "3068d1110070": "sin_criterios_en_fuente",
    "c159097f9120": "sin_criterios_en_fuente",
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", texto))


def palabras(textos: list[dict]) -> str:
    return " ".join(t.get("markdown", "") for t in textos)


def ngramas(texto: str, n: int = 4) -> set[tuple[str, ...]]:
    tokens = normalizar(texto).split()
    return set(zip(*(tokens[i:] for i in range(n))))


def solape(texto: str, fuente: str) -> float | None:
    muestras = ngramas(texto)
    if not muestras:
        return None
    return round(len(muestras & ngramas(fuente)) / len(muestras), 3)


def hijo_de(nodo: str, ancestro: str, padres: dict[str, str | None]) -> bool:
    actual = nodo
    while actual:
        if actual == ancestro:
            return True
        actual = padres.get(actual)
    return False


def revisar(ruta: Path) -> tuple[dict, list[dict]]:
    registro = json.loads(ruta.read_text())
    examen = json.loads((BASE / f"{registro['documento']}.json").read_text())
    nodos = {n["id"]: n for n in examen["resultado"]["nodos"]}
    padres = {n["id"]: n["padre"] for n in nodos.values()}
    resultado = registro["resultado"]
    anexo = registro["fuente"]["anexo"]
    pdf_id = anexo.get("id", registro["documento"])
    pdf = ROOT / "data" / registro["fuente"]["archivo"]
    copia = ROOT / "datos/pdfs" / f"{pdf_id}.pdf"
    hash_fuente = hashlib.sha256(pdf.read_bytes()).hexdigest()
    hash_copia = hashlib.sha256(copia.read_bytes()).hexdigest() if copia.exists() else None
    documento = pymupdf.open(pdf)
    paginas = [p.get_text(sort=True) for p in documento]
    desde = registro["fuente"]["desde"]
    entradas = resultado["entradas"]
    ids = [e["nodo"] for e in entradas]
    puntos = [n["id"] for n in nodos.values() if n["puntos"] is not None]
    cubiertos = [n for n in puntos if any(hijo_de(n, x, padres) or hijo_de(x, n, padres) for x in ids if x in nodos)]
    detalles = []
    for numero, e in enumerate(entradas, start=1):
        pagina = e["paginas"]
        texto = palabras(e["criterios"]) + " " + " ".join(palabras(t["descripcion"]) for t in e["desglose"])
        respuesta = palabras(e["respuesta"])
        paginas_validas = all(1 <= p["pagina"] <= len(paginas) and p["pagina"] >= desde for p in pagina)
        fuente_paginas = " ".join(paginas[p["pagina"] - 1] for p in pagina if 1 <= p["pagina"] <= len(paginas))
        total_desglose = sum(t["puntos"] for t in e["desglose"])
        nodo = nodos.get(e["nodo"])
        detalles.append({
            "version": ruta.parent.name,
            "documento": registro["documento"],
            "entrada": numero,
            "nodo": e["nodo"],
            "nodo_valido": nodo is not None,
            "etiqueta": palabras(nodo["etiqueta"]) if nodo else "",
            "puntos_criterios": e["puntos"],
            "puntos_enunciado": nodo["puntos"] if nodo else None,
            "desglose_total": round(total_desglose, 3) if e["desglose"] else None,
            "desglose_no_suma": bool(e["desglose"] and e["puntos"] is not None and abs(total_desglose - e["puntos"]) > .01),
            "idiomas_criterios": sorted({x["idioma"] for x in e["criterios"]}),
            "idiomas_respuesta": sorted({x["idioma"] for x in e["respuesta"]}),
            "paginas": pagina,
            "paginas_validas": paginas_validas,
            "criterio_solape_pagina": solape(texto, fuente_paginas),
            "criterio_solape_pdf": solape(texto, " ".join(paginas[desde - 1:])),
            "respuesta_solape_pdf": solape(respuesta, " ".join(paginas[desde - 1:])),
            "respuesta_solape_pagina": solape(respuesta, fuente_paginas),
            "texto_criterio": texto.strip(),
            "texto_respuesta": respuesta.strip(),
        })
    anexado = registro["fuente"]["anexo"]
    fila = {
        "version": ruta.parent.name,
        "documento": registro["documento"],
        "materia": examen["documento"]["asignatura"],
        "region": examen["documento"]["region"],
        "anio": examen["documento"]["anio"],
        "convocatoria": examen["documento"]["convocatoria"],
        "pdf_fuente": str(pdf.relative_to(ROOT)),
        "pdf_publicado": str(copia.relative_to(ROOT)) if copia.exists() else None,
        "sha256_fuente": hash_fuente,
        "sha256_publicado": hash_copia,
        "pdf_identico_al_publicado": hash_fuente == hash_copia,
        "pdf_paginas": len(paginas),
        "desde": desde,
        "anexo_tipo": anexado["tipo"],
        "anexo_id": anexado.get("id"),
        "contiene_criterios": resultado["contiene_criterios"],
        "nodos_examen": len(nodos),
        "nodos_puntuados": len(puntos),
        "nodos_puntuados_cubiertos_por_jerarquia": len(cubiertos),
        "entradas": len(entradas),
        "nodos_distintos": len(set(ids)),
        "nodos_inexistentes": sorted(set(ids) - set(nodos)),
        "nodos_duplicados": sorted(x for x, c in Counter(ids).items() if c > 1),
        "generales": len(resultado["generales"]),
        "generales_solape_pdf": solape(palabras(resultado["generales"]), " ".join(paginas[desde - 1:])),
        "idiomas_declarados": resultado["idiomas"],
        "respuestas_en_rubrica": sum(bool(e["respuesta"]) for e in entradas),
        "paginas_invalidas": sum(not d["paginas_validas"] for d in detalles),
        "desgloses_no_suman": sum(d["desglose_no_suma"] for d in detalles),
        "sin_correspondencia": resultado["sin_correspondencia"],
        "incidencias": resultado["incidencias"],
        "hallazgos_automaticos": registro.get("hallazgos", []),
        "revision_semantica": ESTADOS.get(registro["documento"], "sin_alerta_en_cotejo_sistematico"),
    }
    documento.close()
    return fila, detalles


def main() -> None:
    filas, entradas = [], []
    for ruta in sorted((BASE / "rubricas").glob("*/*.json")):
        fila, detalle = revisar(ruta)
        filas.append(fila)
        entradas.extend(detalle)
    (HERE / "registros.json").write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n")
    (HERE / "entradas.json").write_text(json.dumps(entradas, ensure_ascii=False, indent=2) + "\n")
    with (HERE / "registros.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)
    tabla = [
        "# Estado por registro",
        "",
        "Las cifras indican entradas asociadas / nodos puntuados cubiertos / nodos puntuados del árbol. "
        "La cobertura por jerarquía no demuestra fidelidad semántica. "
        "`sin_alerta_en_cotejo_sistematico` significa que no saltó una discrepancia verificable en los controles; "
        "no equivale a certificación humana de cada frase.",
        "",
        "| Versión | Examen | Materia | Entradas | Cobertura | Generales | Respuestas | Estado |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for fila in filas:
        tabla.append(
            f"| {fila['version'].split('__')[-1]} | `{fila['documento']}` | {fila['materia']} | "
            f"{fila['entradas']} | {fila['nodos_puntuados_cubiertos_por_jerarquia']}/{fila['nodos_puntuados']} | "
            f"{fila['generales']} | {fila['respuestas_en_rubrica']} | {fila['revision_semantica']} |"
        )
    (HERE / "tabla-registros.md").write_text("\n".join(tabla) + "\n")
    print(f"{len(filas)} registros, {len(entradas)} entradas")


if __name__ == "__main__":
    main()
