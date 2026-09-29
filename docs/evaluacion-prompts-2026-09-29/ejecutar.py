"""Ejecuta, una por invocación, las cinco comparaciones autorizadas.

Reutiliza el mismo registro de preguntas o fuente de corrección de la pasada
anterior. Nunca sobrescribe un resultado existente y desactiva los reintentos
del cliente de OpenAI.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "pipeline" / "src"))

from pau.adaptadores.extractor_openai import ExtractorOpenAI  # noqa: E402
from pau.adaptadores.katex_node import comprobar_katex  # noqa: E402
from pau.adaptadores.pdf_pymupdf import LectorPymupdf  # noqa: E402
from pau.aplicacion.extraer import Parametros, extraer_documento  # noqa: E402
from pau.aplicacion.rubricas import extraer_rubrica  # noqa: E402
from pau.aplicacion.rutas import Rutas  # noqa: E402
from pau.aplicacion.soluciones import extraer_solucion  # noqa: E402
from pau.dominio.rubrica import FuenteRubrica  # noqa: E402
from pau.dominio.soluciones import FuenteSolucion  # noqa: E402

BASE = Path("pipeline/salida/gpt-6-luna__p5")
CASOS = {
    "p6-fda": ("preguntas", BASE / "fda5ea13b6c5.json", Path("pipeline/salida/gpt-6-luna__p6/fda5ea13b6c5.json"), "p6"),
    "p6-0b7": ("preguntas", BASE / "0b7e227a5499.json", Path("pipeline/salida/gpt-6-luna__p6/0b7e227a5499.json"), "p6"),
    "r3-070": ("rubrica", BASE / "rubricas/gpt-6-luna__r2/070c3795d83c.json", BASE / "rubricas/gpt-6-luna__r3/070c3795d83c.json", "r3"),
    "s2-25f": ("solucion", BASE / "soluciones/gpt-6-luna__s1/academia/25fcf7208b8f.json", BASE / "soluciones/gpt-6-luna__s2/academia/25fcf7208b8f.json", "s2"),
    "s2-1bc": ("solucion", BASE / "soluciones/gpt-6-luna__s1/oficial/1bc800a06e3b.json", BASE / "soluciones/gpt-6-luna__s2/oficial/1bc800a06e3b.json", "s2"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("caso", choices=CASOS)
    args = parser.parse_args()
    tipo, anterior, destino, prompt = CASOS[args.caso]
    anterior, destino = RAIZ / anterior, RAIZ / destino
    if destino.exists():
        raise SystemExit(f"Ya existe: {destino}")
    load_dotenv(RAIZ / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Falta OPENAI_API_KEY; no se ejecuta la extracción")

    previo = json.loads(anterior.read_text())
    rutas = Rutas(RAIZ)
    parametros = Parametros("gpt-6-luna", prompt, "high")
    extractor = ExtractorOpenAI(reintentos=0)
    lector = LectorPymupdf()
    if tipo == "preguntas":
        resultado = extraer_documento(previo["documento"], parametros, rutas, extractor, lector, comprobar_katex)
    else:
        registro = json.loads((RAIZ / BASE / f"{previo['documento']}.json").read_text())
        fuente = (FuenteRubrica if tipo == "rubrica" else FuenteSolucion)(**previo["fuente"])
        funcion = extraer_rubrica if tipo == "rubrica" else extraer_solucion
        resultado = funcion(registro, fuente, parametros, rutas, extractor, lector, comprobar_katex)

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    print(json.dumps({
        "caso": args.caso,
        "destino": str(destino.relative_to(RAIZ)),
        "estado": resultado.get("estado"),
        "error": resultado.get("error"),
        "uso": resultado.get("uso"),
        "segundos": resultado.get("segundos"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
