"""Comprobación de fórmulas con el KaTeX real (Node), el mismo motor que renderiza la web."""

import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).with_name("katex_check.js")


def comprobar_katex(formulas: list[dict]) -> list[str | None]:
    if not formulas:
        return []
    salida = subprocess.run(["node", str(SCRIPT)], input=json.dumps(formulas), capture_output=True, text=True, check=True)
    return json.loads(salida.stdout)
