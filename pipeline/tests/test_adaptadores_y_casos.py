import shutil

import pytest

from pau.adaptadores.katex_node import comprobar_katex
from pau.aplicacion.rastrear import catalogo, rastrear
from pau.dominio.fuentes import mundoestudiante


@pytest.mark.skipif(shutil.which("node") is None, reason="sin Node")
def test_katex_real_distingue_formulas_validas():
    errores = comprobar_katex([{"tex": "\\ce{H2O -> H2 + O2}", "bloque": False}, {"tex": "\\sen x", "bloque": False}])
    assert errores[0] is None and "sen" in errores[1]


class WebFalsa:
    def __init__(self, paginas: dict[str, str]):
        self.paginas = paginas

    def texto(self, url: str) -> str:
        return self.paginas[url]

    def descargar(self, url: str):
        raise NotImplementedError


def test_rastrear_compone_fuentes_y_deduplica():
    html = '<h3>Junio 2024</h3><a href="/a.pdf">Examen Física</a><a href="/a.pdf">Examen Física</a>'
    documentos = rastrear(WebFalsa({mundoestudiante.PAGINA: html}), [mundoestudiante.FUENTE])
    assert len(documentos) == 1
    salida = catalogo(documentos, [mundoestudiante.FUENTE], {documentos[0].id: {"bytes": 5, "archivo": "pdfs/x.pdf"}})
    assert salida["fuentes"] == {"mundoestudiante": {"region": "Madrid", "url": mundoestudiante.PAGINA}}
    assert salida["documentos"][0]["bytes"] == 5
