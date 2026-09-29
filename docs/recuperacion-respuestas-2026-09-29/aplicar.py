"""Recupera solo soluciones en el banco existente, con entradas y salida fijadas en plan.json."""

import argparse
import copy
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import pymupdf
from pau.dominio.recuperacion import recuperar_respuestas

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = Path(__file__).resolve().parent


def huella(contenido):
    return hashlib.sha256(contenido).hexdigest()


def preparar(raiz=RAIZ):
    original = (raiz / "datos/preguntas.json").read_bytes()
    banco = json.loads(original)
    base = raiz / "pipeline/salida" / banco["ejecucion"]
    por_examen = defaultdict(list)
    for pregunta in banco["preguntas"]:
        por_examen[pregunta["examen"]["id"]].append(pregunta)
    entradas, cambios, exclusiones = {}, [], []

    def leer(ruta):
        contenido = ruta.read_bytes()
        entradas[str(ruta.relative_to(raiz))] = huella(contenido)
        return json.loads(contenido)

    for doc_id, preguntas in por_examen.items():
        ruta = base / "rubricas/gpt-6-luna__r2" / f"{doc_id}.json"
        if not ruta.exists():
            continue
        rubrica = leer(ruta)
        registro = leer(base / f"{doc_id}.json")
        nodos = {n["id"]: n for n in registro["resultado"]["nodos"]}
        hijos = defaultdict(list)
        for n in nodos.values():
            hijos[n["padre"]].append(n)
        for hermanos in hijos.values():
            hermanos.sort(key=lambda n: n["orden"])
        publicados, propietarios = {}, {}

        def mapear(nid, publicado, propietario, publicados=publicados, propietarios=propietarios, nodos=nodos, hijos=hijos, doc_id=doc_id):
            if nid in publicados:
                raise ValueError(f"Nodo publicado duplicado: {doc_id}:{nid}")
            nodo = nodos[nid]
            for campo in ("etiqueta", "enunciado"):
                esperado = {t["idioma"]: t["markdown"] for t in nodo[campo]}
                if publicado[campo] != esperado:
                    raise ValueError(f"No coincide {campo}: {doc_id}:{nid}")
            publicados[nid], propietarios[nid] = publicado, propietario
            for hijo, apartado in zip(hijos[nid], publicado["apartados"], strict=True):
                mapear(hijo["id"], apartado, propietario)

        for pregunta in preguntas:
            mapear(pregunta["id"].split(":")[1], pregunta, pregunta["id"])
        existentes = {nid: n["solucion"] for nid, n in publicados.items() if n.get("solucion")}
        soluciones, excluidos = recuperar_respuestas(registro, rubrica, existentes)
        exclusiones += [{"documento": doc_id, **e} for e in excluidos]
        nuevas = {nid: s for nid, s in soluciones.items() if nid not in existentes}
        for nid in set(nuevas) - publicados.keys():
            exclusiones.append({"documento": doc_id, "nodo": nid, "motivo": "nodo_no_publicado"})
        nuevas = {nid: s for nid, s in nuevas.items() if nid in publicados}
        if not nuevas:
            continue
        fuente = raiz / "data" / rubrica["fuente"]["archivo"]
        contenido = fuente.read_bytes()
        entradas[str(fuente.relative_to(raiz))] = huella(contenido)
        with pymupdf.open(stream=contenido, filetype="pdf") as pdf:
            paginas = len(pdf)
        for nid, solucion in nuevas.items():
            publicado = raiz / "datos" / (f"pdfs/{doc_id}.pdf" if solucion["incrustado"] else solucion["pdf"])
            copia = publicado.read_bytes()
            entradas[str(publicado.relative_to(raiz))] = huella(copia)
            if copia != contenido or any(not 1 <= p <= paginas for p in solucion["paginas"].values()):
                raise ValueError(f"PDF o página de origen no coincide: {doc_id}:{nid}")
            anterior = copy.deepcopy(publicados[nid])
            publicados[nid]["solucion"] = solucion
            comparable = {**publicados[nid], "solucion": anterior.get("solucion")}
            if comparable != anterior:
                raise ValueError(f"Cambio fuera de solución: {doc_id}:{nid}")
            cambios.append({"id": f"{doc_id}:{nid}", "pregunta": propietarios[nid], "solucion_sha256": huella(json.dumps(solucion, sort_keys=True).encode())})
    nuevo = json.dumps(banco, ensure_ascii=False).encode()
    resumen = {
        "respuestas": len(cambios), "preguntas": len({c["pregunta"] for c in cambios}),
        "examenes": len({c["id"].split(":")[0] for c in cambios}),
        "motivos_exclusion": dict(Counter(e["motivo"] for e in exclusiones)),
    }
    return original, nuevo, {"antes": huella(original), "despues": huella(nuevo), "entradas": entradas, "cambios": cambios, "exclusiones": exclusiones, "resumen": resumen}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    plan = json.loads((CARPETA / "plan.json").read_text())
    destino = RAIZ / "datos/preguntas.json"
    actual = destino.read_bytes()
    if huella(actual) == plan["despues"]:
        print(json.dumps({"estado": "ya_aplicado", **plan["resumen"]}, ensure_ascii=False))
        return
    if huella(actual) != plan["antes"]:
        raise ValueError("El banco no coincide con la entrada del plan revisado")
    original, nuevo, comprobado = preparar()
    if comprobado != plan:
        raise ValueError("Las fuentes, los IDs o el resultado no coinciden con el plan revisado")
    if args.aplicar:
        temporal = None
        try:
            with NamedTemporaryFile(dir=destino.parent, prefix=".respuestas-", delete=False) as archivo:
                temporal = Path(archivo.name)
                archivo.write(nuevo)
            if destino.read_bytes() != original:
                raise ValueError("El banco cambió durante la reparación")
            os.replace(temporal, destino)
        finally:
            if temporal:
                temporal.unlink(missing_ok=True)
        (CARPETA / "resultado.json").write_text(json.dumps({"antes": plan["antes"], "despues": plan["despues"], **plan["resumen"]}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"estado": "aplicado" if args.aplicar else "simulacion", **plan["resumen"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
