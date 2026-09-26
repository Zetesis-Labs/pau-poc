"""Recorta de la página las figuras que el modelo ha localizado."""

from pathlib import Path

from pau.dominio.esquema import ExamenExtraido
from pau.dominio.geometria import en_blanco, nombre_figura, paginas_con_recortes, planificar_recortes
from pau.puertos import LectorPdf

DPI = 200


def recortar(lector: LectorPdf, pdf: Path, examen: ExamenExtraido, destino: Path, prefijo: str) -> list[dict]:
    destino.mkdir(parents=True, exist_ok=True)
    figuras = []
    with lector.abrir(pdf) as documento:
        paginas = {n: documento.geometria(n) for n in paginas_con_recortes(examen) if 1 <= n <= documento.paginas}
        for plan in planificar_recortes(examen, paginas):
            entrada = {"estimulo": plan.estimulo, "idioma": plan.idioma, "pagina": plan.pagina, "problemas": list(plan.problemas)}
            if plan.caja is not None:
                entrada["metodo"] = plan.metodo
                imagen = documento.renderizar(plan.pagina, plan.caja, DPI)
                if en_blanco(imagen.grises):
                    entrada["problemas"].append("en-blanco")
                archivo = destino / nombre_figura(prefijo, plan)
                archivo.write_bytes(imagen.png)
                entrada.update(archivo=archivo.name, ancho=imagen.ancho, alto=imagen.alto)
            figuras.append(entrada)
    return figuras
