"""Reparación acotada del banco existente; no sustituye el control de publicación completa."""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote

from pau.aplicacion.banco import registros
from pau.dominio.anexos import vincular
from pau.dominio.banco import preguntas_de
from pau.dominio.fuentes.mundoestudiante import variante_de

RAIZ = Path(__file__).resolve().parents[2]


def huella(contenido):
    return hashlib.sha256(contenido).hexdigest()


def preparar():
    rutas = [RAIZ / "datos" / n for n in ("catalogo.json", "preguntas.json")]
    originales = [r.read_bytes() for r in rutas]
    plan = json.loads((Path(__file__).parent / "plan.json").read_text())
    for ruta, original in zip(rutas, originales, strict=True):
        if huella(original) not in plan["archivos"][ruta.name].values():
            raise ValueError(f"El archivo no coincide con el plan revisado: {ruta.name}")
    catalogo, banco = [json.loads(b) for b in originales]
    antes_catalogo, antes_banco = copy.deepcopy(catalogo), copy.deepcopy(banco)
    variantes = []
    for doc in catalogo["documentos"]:
        if doc["fuente"] != "mundoestudiante" or doc.get("variante"):
            continue
        nombre = unquote(doc["url"]).rsplit("/", 1)[-1].replace("+", " ")
        variante = variante_de("", nombre)
        if variante:
            doc["variante"] = variante
            variantes.append(doc["id"])
    validos = {doc_id: {a["id"] for a in anexos} for doc_id, anexos in vincular(catalogo["documentos"], {}).items()}
    retirados = set()

    def conservar_anexos(examen):
        if "anexos" not in examen:
            return
        conservados = []
        for anexo in examen["anexos"]:
            if "incrustado" in anexo or anexo.get("id") in validos.get(examen["id"], set()):
                conservados.append(anexo)
            else:
                retirados.add((examen["id"], anexo["id"]))
        examen["anexos"] = conservados

    for doc in catalogo["documentos"]:
        conservar_anexos(doc)
    fuentes = registros(RAIZ / "pipeline" / "salida" / banco["ejecucion"])
    esperadas = {p["id"]: p for r in fuentes for p in preguntas_de(r)}
    cambios_regla = []
    for pregunta in banco["preguntas"]:
        conservar_anexos(pregunta["examen"])
        esperada = esperadas[pregunta["id"]]
        if esperada.get("regla"):
            if any(pregunta.get(k) != esperada.get(k) for k in ("regla", "literalRegla")):
                cambios_regla.append(pregunta["id"])
            pregunta["regla"] = esperada["regla"]
            if "literalRegla" in esperada:
                pregunta["literalRegla"] = esperada["literalRegla"]

    # La lista permitida fija el alcance de esta reparación y evita ampliaciones accidentales.
    if set(variantes) - {"2337676aef2a"} or retirados - {("e880b6f47a91", "2337676aef2a")}:
        raise ValueError("Cambios de anexos fuera del alcance revisado")
    if cambios_regla and set(cambios_regla) != set(plan["reglas_recuperadas"]):
        raise ValueError("Los IDs de las reglas no coinciden con el plan revisado")
    for anterior, nueva in zip(antes_banco["preguntas"], banco["preguntas"], strict=True):
        comparable = copy.deepcopy(nueva)
        comparable["examen"]["anexos"] = anterior["examen"]["anexos"]
        for campo in ("regla", "literalRegla"):
            if campo in anterior:
                comparable[campo] = anterior[campo]
            else:
                comparable.pop(campo, None)
        if comparable != anterior:
            raise ValueError(f"Contenido de pregunta alterado fuera de alcance: {anterior['id']}")
    for anterior, nuevo in zip(antes_catalogo["documentos"], catalogo["documentos"], strict=True):
        comparable = copy.deepcopy(nuevo)
        for campo in ("variante", "anexos"):
            if campo in anterior:
                comparable[campo] = anterior[campo]
            else:
                comparable.pop(campo, None)
        if comparable != anterior:
            raise ValueError(f"Documento alterado fuera de alcance: {anterior['id']}")
    nuevos = [json.dumps(valor, ensure_ascii=False).encode() for valor in (catalogo, banco)]
    for ruta, nuevo in zip(rutas, nuevos, strict=True):
        if huella(nuevo) != plan["archivos"][ruta.name]["despues"]:
            raise ValueError(f"El resultado no coincide con el plan revisado: {ruta.name}")
    resumen = {
        "preguntas": len(banco["preguntas"]), "documentos": len(catalogo["documentos"]),
        "variantes_corregidas": variantes, "vinculos_retirados": sorted(retirados),
        "reglas_recuperadas": cambios_regla,
        "archivos": {r.name: {"antes": huella(a), "despues": huella(n)} for r, a, n in zip(rutas, originales, nuevos, strict=True)},
    }
    return rutas, originales, nuevos, resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    rutas, originales, nuevos, resumen = preparar()
    if args.aplicar and originales != nuevos:
        with TemporaryDirectory(prefix="pau-reparacion-") as temporal:
            for ruta, original in zip(rutas, originales, strict=True):
                (Path(temporal) / ruta.name).write_bytes(original)
            reemplazados = []
            try:
                for ruta, original, nuevo in zip(rutas, originales, nuevos, strict=True):
                    if ruta.read_bytes() != original:
                        raise ValueError(f"El archivo cambió durante la reparación: {ruta.name}")
                    provisional = ruta.with_suffix(".reparacion.tmp")
                    provisional.write_bytes(nuevo)
                    os.replace(provisional, ruta)
                    reemplazados.append((ruta, original, nuevo))
            except Exception:
                for ruta, original, nuevo in reversed(reemplazados):
                    if ruta.read_bytes() == nuevo:
                        provisional = ruta.with_suffix(".reparacion.tmp")
                        provisional.write_bytes(original)
                        os.replace(provisional, ruta)
                raise
        (Path(__file__).parent / "resultado.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
