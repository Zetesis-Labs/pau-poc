import pymupdf
import pytest
from conftest import examen

from pau.adaptadores.pdf_pymupdf import LectorPymupdf
from pau.aplicacion.recortar import recortar
from pau.dominio.esquema import Estimulo, Recorte


@pytest.fixture
def pdf(tmp_path):
    documento = pymupdf.open()
    pagina = documento.new_page(width=600, height=800)
    pagina.insert_text((72, 100), "Pregunta 1. Observa el circuito de la figura", fontsize=11)
    pagina.draw_rect(pymupdf.Rect(150, 300, 450, 500), color=(0, 0, 0), fill=(0.2, 0.4, 0.8))
    pagina.insert_text((260, 515), "Figura 1", fontsize=9)
    ruta = tmp_path / "examen.pdf"
    documento.save(ruta)
    return ruta


def test_geometria_y_busqueda(pdf):
    with LectorPymupdf().abrir(pdf) as documento:
        assert documento.paginas == 1
        assert documento.rect(1).alto == 800
        [encontrado] = documento.buscar(1, "Observa el circuito")
        assert 85 < encontrado.y1 < 105
        geometria = documento.geometria(1)
        assert any(abs(c.x0 - 150) < 2 and abs(c.y1 - 500) < 2 for c in geometria.dibujos)
        assert any("Figura 1" in b.texto for b in geometria.bloques)
        assert documento.caracteres_por_pagina() > 40


def test_recortar_ajusta_al_dibujo_y_guarda_png(pdf, tmp_path):
    estimulo = Estimulo(
        id="E1", tipo="figura", paginas=[], descripcion="circuito", contenido=[],
        recortes=[Recorte(idioma="es", pagina=1, x0=0.2, y0=0.33, x1=0.7, y1=0.6)],
    )
    [figura] = recortar(LectorPymupdf(), pdf, examen(estimulos=[estimulo]), tmp_path / "figuras", "doc")
    assert figura["metodo"] == "pdf" and figura["problemas"] == []
    assert (tmp_path / "figuras" / "doc_E1_es_1.png").read_bytes().startswith(b"\x89PNG")
    assert figura["alto"] > figura["ancho"] * 0.6
