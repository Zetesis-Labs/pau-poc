"""Punto de entrada: compone los adaptadores con los casos de uso."""

import argparse
import json
import random
import sys
from dataclasses import fields

from dotenv import load_dotenv

from pau.aplicacion.rutas import Rutas, rutas_por_defecto

EJECUCION = "gpt-6-luna__p5"
SEMILLA = 20260926


def _rastrear(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.web_httpx import WebHttpx
    from pau.aplicacion.rastrear import catalogo, descargas_previas, rastrear

    documentos = rastrear(WebHttpx(rutas.cache_html, sin_red=args.sin_red), args.fuentes)
    salida = catalogo(documentos, args.fuentes, descargas_previas(rutas.examenes))
    destino = args.salida or rutas.examenes
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print(f"{len(salida['documentos'])} documentos → {destino}")


def _descargar(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.web_httpx import WebHttpx
    from pau.aplicacion.descargar import descargar_todo
    from pau.dominio.catalogo import registro
    from pau.dominio.documento import Documento

    catalogo = json.loads(rutas.examenes.read_text())
    campos = {f.name for f in fields(Documento)}
    documentos = [Documento(**{k: v for k, v in d.items() if k in campos}) for d in catalogo["documentos"]]
    descargas = descargar_todo(documentos, WebHttpx(rutas.cache_html), rutas.data, args.hilos_por_host)
    catalogo["documentos"] = [registro(d, descargas) for d in documentos]
    rutas.examenes.write_text(json.dumps(catalogo, ensure_ascii=False, indent=1))
    fallos = sum("error" in r for r in descargas.values())
    print(f"{len(descargas) - fallos} en disco, {fallos} fallos")


def _medidos(rutas: Rutas, excluir: set[tuple] = frozenset(), max_paginas: int | None = None) -> list[dict]:
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.dominio.lote import MAX_PAGINAS, clave_examen, es_candidato, medible

    lector, vistos, medidos = LectorPymupdf(), set(), []
    for d in json.loads(rutas.examenes.read_text())["documentos"]:
        clave = clave_examen(d)
        if not es_candidato(d) or clave in excluir or clave in vistos:
            continue
        with lector.abrir(rutas.data / d["archivo"]) as pdf:
            paginas, texto = pdf.paginas, pdf.caracteres_por_pagina()
        if medible(paginas, max_paginas or MAX_PAGINAS):
            vistos.add(clave)
            medidos.append({**d, "paginas": paginas, "texto_por_pagina": texto})
    return medidos


def _lote(args: argparse.Namespace, rutas: Rutas) -> None:
    from collections import Counter

    from pau.dominio.lote import clave_examen, elegir, lote_piloto, muestra

    azar = random.Random(SEMILLA)
    procesados = {clave_examen(json.loads(r.read_text())["documento"]) for r in rutas.salida.glob("*/*.json") if r.name != "preguntas.json"}
    if args.muestra:
        lote = muestra(_medidos(rutas), azar)
    elif args.asignaturas:
        medidos = _medidos(rutas, procesados, args.max_paginas)
        lote = lote_piloto(medidos, set(args.regiones), set(args.asignaturas), procesados)
        todos = lote_piloto(_medidos(rutas, procesados, 10_000), set(args.regiones), set(args.asignaturas), procesados)
        print(f"{len(todos) - len(lote)} exámenes excluidos por pasar de {args.max_paginas} páginas")
        for (region, asignatura), n in sorted(Counter((d["region"], d["asignatura"]) for d in lote).items()):
            print(f"  {region} · {asignatura}: {n}")
    else:
        lote = elegir(_medidos(rutas, procesados), args.total, args.escaneados, azar)
    destino = rutas.lotes / f"{args.nombre}.json"
    destino.write_text(json.dumps(lote, ensure_ascii=False, indent=1))
    print(f"{len(lote)} exámenes ({sum(d['paginas'] for d in lote)} páginas) → {destino}")


def _extraer(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.extractor_openai import ExtractorOpenAI
    from pau.adaptadores.katex_node import comprobar_katex
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.extraer import Parametros, extraer_lote

    load_dotenv(rutas.raiz / ".env")
    documentos = json.loads((rutas.lotes / f"{args.lote}.json").read_text())
    if args.ids:
        documentos = [d for d in documentos if d["id"] in args.ids]
    documentos = documentos[: args.limite]
    parametros = Parametros(args.modelo, args.prompt, args.esfuerzo)
    extraer_lote(documentos, parametros, rutas, ExtractorOpenAI(), LectorPymupdf(), comprobar_katex, args.hilos, args.rehacer)


def _recortar(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.extraer import rehacer_recortes

    print(f"recortes rehechos en {rehacer_recortes(args.ejecucion, rutas, LectorPymupdf())} exámenes de {args.ejecucion}")


def _banco(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.banco import ancladas, construir
    from pau.dominio.banco import sin_campos_internos

    preguntas = construir(args.ejecucion, rutas, LectorPymupdf())
    destino = rutas.ejecucion(args.ejecucion) / "preguntas.json"
    destino.write_text(json.dumps({"ejecucion": args.ejecucion, "preguntas": [sin_campos_internos(p) for p in preguntas]}, ensure_ascii=False))
    examenes = len({p["examen"]["id"] for p in preguntas})
    print(f"{len(preguntas)} preguntas de {examenes} exámenes · {ancladas(preguntas)} ancladas a su posición en el PDF → {destino}")


def _publicar(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.publicar import publicar

    r = publicar(args.ejecucion, rutas, LectorPymupdf())
    tamanos = " · ".join(f"{n} {b / 1e6:.1f} MB" for n, b in r.bytes.items())
    print(f"{r.documentos} documentos en el catálogo, {r.procesados} procesados · {r.preguntas} preguntas · {r.figuras} figuras · {r.pdfs} PDFs → {rutas.datos}")
    print(tamanos)


def _rubricas(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.extractor_openai import ExtractorOpenAI
    from pau.adaptadores.katex_node import comprobar_katex
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.extraer import Parametros
    from pau.aplicacion.rubricas import extraer_rubricas

    load_dotenv(rutas.raiz / ".env")
    parametros = Parametros(args.modelo, args.prompt, args.esfuerzo)
    extraer_rubricas(
        args.ejecucion, parametros, rutas, ExtractorOpenAI(), LectorPymupdf(), comprobar_katex,
        args.hilos, args.rehacer, args.ids, args.limite,
    )


def _soluciones(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.adaptadores.extractor_openai import ExtractorOpenAI
    from pau.adaptadores.katex_node import comprobar_katex
    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.extraer import Parametros
    from pau.aplicacion.soluciones import extraer_soluciones

    load_dotenv(rutas.raiz / ".env")
    parametros = Parametros(args.modelo, args.prompt, args.esfuerzo)
    extraer_soluciones(
        args.ejecucion, parametros, args.origen, rutas, ExtractorOpenAI(), LectorPymupdf(), comprobar_katex,
        args.hilos, args.rehacer, args.ids, args.limite,
    )


def _anexos(args: argparse.Namespace, rutas: Rutas) -> None:
    from collections import Counter

    from pau.adaptadores.pdf_pymupdf import LectorPymupdf
    from pau.aplicacion.anexos import detectar_incrustados, incrustados_guardados
    from pau.dominio.anexos import huerfanos, vincular

    d = detectar_incrustados(rutas, LectorPymupdf())
    print(f"{d.revisados} PDF de examen revisados · {d.con_correccion} con la corrección dentro · {len(d.ilegibles)} ilegibles → {rutas.incrustados}")
    for linea in d.ilegibles:
        print(f"  ilegible {linea}")
    documentos = json.loads(rutas.examenes.read_text())["documentos"]
    vinculos = vincular(documentos, incrustados_guardados(rutas))
    examenes = [x for x in documentos if x["tipo"] in ("examen", "modelo")]
    cobertura = Counter()
    for x in examenes:
        anexos = vinculos.get(x["id"], [])
        oficial = any(a["origen"] == "oficial" and a["acceso"] == "publico" for a in anexos)
        cobertura[(x["region"], "oficial" if oficial else "solo academia" if anexos else "sin corrección")] += 1
    for region in sorted({x["region"] for x in examenes}):
        print(f"  {region}: " + " · ".join(f"{c} {cobertura[(region, c)]}" for c in ("oficial", "solo academia", "sin corrección")))
    sueltos = huerfanos(documentos)
    print(f"{len(sueltos)} criterios o soluciones sin examen al que vincularse")
    for h in sueltos:
        print(f"  {h['region']} · {h['asignatura']} · {h['anio']} · {h['convocatoria']} · {h['tipo']} · {h['variante'] or '-'} · {h['id']}")


def _informe(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.dominio.informe import detalle, resumen

    lista = [json.loads(r.read_text()) for r in sorted(rutas.ejecucion(args.ejecucion).glob("*.json")) if r.name != "preguntas.json"]
    print(json.dumps(resumen(lista), ensure_ascii=False, indent=1))
    print("\n".join(detalle(lista)))


def _comparar(args: argparse.Namespace, rutas: Rutas) -> None:
    from pau.dominio.comparacion import metricas, similitud

    referencia = {p.stem: json.loads(p.read_text()) for p in rutas.ejecucion(args.referencia).glob("*.json") if p.name != "preguntas.json"}
    ejecuciones = sorted(p.name for p in rutas.salida.iterdir() if p.is_dir())
    for doc_id, ref in sorted(referencia.items(), key=lambda kv: kv[1]["documento"]["asignatura"]):
        d = ref["documento"]
        print(f"\n{d['asignatura']} · {d['region']} · {d['anio']}")
        for ejecucion in ejecuciones:
            ruta = rutas.ejecucion(ejecucion) / f"{doc_id}.json"
            if not ruta.exists():
                continue
            registro = json.loads(ruta.read_text())
            if "error" in registro:
                print(f"  {ejecucion:<18} ERROR {registro['error'][:100]}")
                continue
            m = metricas(registro)
            cobertura, texto = similitud(ref, registro) if ejecucion != args.referencia else (1.0, 1.0)
            print(
                f"  {ejecucion:<18} preg {m['preguntas']:>2} apart {m['apartados']:>2} ptos {m['con_puntos']:>2} reglas {m['reglas']} "
                f"fórm {m['formulas']:>3} idiomas {m['idiomas']:<6} | nodos≈ref {cobertura:>4.0%} texto≈ref {texto:>4.0%} "
                f"| graves {','.join(m['graves']) or '-':<16} incid {m['incidencias']}"
            )


def parser() -> argparse.ArgumentParser:
    from pathlib import Path

    from pau.aplicacion.rastrear import FUENTES

    p = argparse.ArgumentParser(prog="pau", description="Rastreo, extracción y publicación de exámenes de la PAU")
    sub = p.add_subparsers(dest="orden", required=True)

    s = sub.add_parser("rastrear", help="recorre las fuentes y escribe el catálogo (data/examenes.json)")
    s.add_argument("--fuentes", nargs="*", default=list(FUENTES), choices=list(FUENTES))
    s.add_argument("--sin-red", action="store_true", help="usar solo la caché de HTML")
    s.add_argument("--salida", type=Path, help="escribir el catálogo en otra ruta")
    s.set_defaults(accion=_rastrear)

    s = sub.add_parser("descargar", help="descarga los documentos del catálogo a data/pdfs")
    s.add_argument("--hilos-por-host", type=int, default=3)
    s.set_defaults(accion=_descargar)

    s = sub.add_parser("lote", help="elige exámenes nuevos para extraer")
    s.add_argument("--total", type=int, default=100)
    s.add_argument("--escaneados", type=int, default=8)
    s.add_argument("--asignaturas", nargs="*", help="lote de piloto: todos los exámenes pendientes de estas asignaturas")
    s.add_argument("--regiones", nargs="*", default=["Madrid", "Comunidad Valenciana"])
    s.add_argument("--max-paginas", type=int, default=40)
    s.add_argument("--muestra", action="store_true", help="muestra inicial estratificada en vez de un lote de nuevos")
    s.add_argument("--nombre", default="lote-100")
    s.set_defaults(accion=_lote)

    s = sub.add_parser("extraer", help="extrae las preguntas de un lote con el modelo")
    s.add_argument("--modelo", default="gpt-6-luna")
    s.add_argument("--prompt", default="p5")
    s.add_argument("--esfuerzo", default="high")
    s.add_argument("--lote", default="lote-58")
    s.add_argument("--ids", nargs="*")
    s.add_argument("--limite", type=int)
    s.add_argument("--hilos", type=int, default=6)
    s.add_argument("--rehacer", action="store_true")
    s.set_defaults(accion=_extraer)

    for nombre, accion, ayuda in (
        ("recortar", _recortar, "rehace los recortes de figuras de una ejecución"),
        ("banco", _banco, "construye y ancla el banco de preguntas de una ejecución"),
        ("publicar", _publicar, "escribe datos/ para la web"),
        ("informe", _informe, "resume los hallazgos de una ejecución"),
    ):
        s = sub.add_parser(nombre, help=ayuda)
        s.add_argument("ejecucion", nargs="?", default=EJECUCION)
        s.set_defaults(accion=accion)

    s = sub.add_parser("rubricas", help="extrae la rúbrica de corrección de los exámenes procesados con criterios oficiales")
    s.add_argument("ejecucion", nargs="?", default=EJECUCION)
    s.add_argument("--modelo", default="gpt-6-luna")
    s.add_argument("--prompt", default="r2")
    s.add_argument("--esfuerzo", default="high")
    s.add_argument("--hilos", type=int, default=6)
    s.add_argument("--ids", nargs="*")
    s.add_argument("--limite", type=int)
    s.add_argument("--rehacer", action="store_true")
    s.set_defaults(accion=_rubricas)

    s = sub.add_parser("soluciones", help="extrae la respuesta de cada nodo: --origen oficial primero y luego academia para lo que falte")
    s.add_argument("ejecucion", nargs="?", default=EJECUCION)
    s.add_argument("--origen", choices=["oficial", "academia"], default="oficial")
    s.add_argument("--modelo", default="gpt-6-luna")
    s.add_argument("--prompt", default="s1")
    s.add_argument("--esfuerzo", default="high")
    s.add_argument("--hilos", type=int, default=6)
    s.add_argument("--ids", nargs="*")
    s.add_argument("--limite", type=int)
    s.add_argument("--rehacer", action="store_true")
    s.set_defaults(accion=_soluciones)

    s = sub.add_parser("anexos", help="localiza la corrección dentro de los PDF de examen y resume qué examen tiene cuál")
    s.set_defaults(accion=_anexos)

    s = sub.add_parser("comparar", help="compara todas las ejecuciones con una de referencia")
    s.add_argument("--referencia", default="gpt-5.6-sol__p1")
    s.set_defaults(accion=_comparar)
    return p


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    try:
        args.accion(args, rutas_por_defecto())
    except BrokenPipeError:
        sys.exit(0)
