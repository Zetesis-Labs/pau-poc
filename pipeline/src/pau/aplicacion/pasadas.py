"""Ejecuta una pasada del modelo sobre varios exámenes en paralelo y guarda un registro por examen."""

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def resumen(registro: dict, salida: dict, entradas: str) -> str:
    d = registro["documento"]
    if "error" in salida:
        estado = "✗ " + salida["error"][:150]
    else:
        graves = sum(h["grave"] for h in salida["hallazgos"])
        leves = ",".join(sorted({h["regla"] for h in salida["hallazgos"] if not h["grave"]})) or "-"
        estado = f"✓ {len(salida['resultado'][entradas])} entradas · {graves} graves · leves {leves}"
    return f"{d['asignatura'][:30]:<30} {d['anio']} {d['region'][:10]:<10} {salida.get('segundos', 0):>6}s {estado}"


def ejecutar[F](
    tareas: list[tuple[dict, F]], procesar: Callable[[dict, F], dict], destino: Path, hilos: int, rehacer: bool,
    describir: Callable[[dict, dict], str], cabecera: str,
) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    pendientes = [(r, f) for r, f in tareas if rehacer or not (destino / f"{r['documento']['id']}.json").exists()]
    print(f"{len(pendientes)} pendientes de {len(tareas)} {cabecera}", flush=True)
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        futuros = {pool.submit(procesar, r, f): r for r, f in pendientes}
        for futuro in as_completed(futuros):
            registro, salida = futuros[futuro], futuro.result()
            (destino / f"{registro['documento']['id']}.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))
            print(describir(registro, salida), flush=True)
