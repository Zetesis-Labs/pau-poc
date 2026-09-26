from conftest import examen

from pau.dominio.esquema import Estimulo, Recorte
from pau.dominio.geometria import (
    Bloque,
    Caja,
    GeometriaPagina,
    ajustar,
    candidatos,
    en_blanco,
    es_etiqueta,
    fusionar_contiguos,
    planificar_recortes,
    problemas,
    rectangulo,
)

PAGINA = Caja(0, 0, 600, 800)


def recorte(x0, y0, x1, y1, pagina=1, idioma="es") -> Recorte:
    return Recorte(idioma=idioma, pagina=pagina, x0=x0, y0=y0, x1=x1, y1=y1)


def test_caja_interseccion_union_y_area():
    a, b = Caja(0, 0, 10, 10), Caja(5, 5, 20, 20)
    assert (a & b) == Caja(5, 5, 10, 10)
    assert (a | b) == Caja(0, 0, 20, 20)
    assert (a & Caja(30, 30, 40, 40)).area == 0
    assert not a.intersecta(Caja(10, 0, 20, 10))


def test_problemas_de_un_recorte():
    assert problemas(recorte(0.1, 0.1, 0.5, 0.5)) == []
    assert problemas(recorte(-0.1, 0.1, 0.5, 0.5)) == ["fuera-de-rango"]
    assert problemas(recorte(0.5, 0.1, 0.1, 0.5)) == ["invertido"]
    assert problemas(recorte(0.1, 0.1, 0.12, 0.12)) == ["diminuto"]
    assert problemas(recorte(0, 0, 1, 0.95)) == ["casi-pagina"]


def test_rectangulo_pasa_de_fracciones_a_puntos():
    assert rectangulo(recorte(0.5, 0.25, 1, 0.5), PAGINA) == Caja(300, 200, 600, 400)


def test_candidatos_fusiona_piezas_contiguas_y_descarta_tamanos_extremos():
    trazos = [Caja(100, 100, 200, 200), Caja(201, 100, 300, 200), Caja(0, 0, 5, 5)]
    assert candidatos([], trazos, PAGINA) == [Caja(100, 100, 300, 200)]
    assert candidatos([Caja(0, 0, 600, 800)], [], PAGINA) == []
    assert fusionar_contiguos([Caja(0, 0, 10, 10), Caja(50, 50, 60, 60)]) == [Caja(0, 0, 10, 10), Caja(50, 50, 60, 60)]


def test_ajustar_se_engancha_a_la_figura_real_y_suma_sus_rotulos():
    figura = Caja(100, 300, 400, 500)
    rotulo = Bloque(Caja(200, 505, 260, 515), "Figura 1")
    parrafo = Bloque(Caja(100, 510, 500, 560), "Un párrafo largo que no es un rótulo de la figura, sino texto del enunciado")
    caja, metodo = ajustar(Caja(90, 250, 390, 450), [figura], [rotulo, parrafo], PAGINA)
    assert metodo == "pdf"
    assert caja == Caja(96, 296, 404, 519)


def test_ajustar_sin_geometria_amplia_la_caja_del_modelo():
    caja, metodo = ajustar(Caja(100, 100, 200, 200), [], [], PAGINA)
    assert metodo == "modelo"
    assert caja == Caja(84, 84, 216, 216)


def test_ajustar_no_invade_la_figura_de_otro_estimulo():
    compartida, aproximado = Caja(100, 100, 500, 400), Caja(100, 100, 400, 350)
    assert ajustar(aproximado, [compartida], [], PAGINA)[1] == "pdf"
    assert ajustar(aproximado, [compartida], [], PAGINA, ajenas=[Caja(300, 250, 500, 400)])[1] == "modelo"


def test_etiquetas_excluyen_numeros_de_pagina_y_bloques_vacios():
    assert es_etiqueta(Bloque(Caja(10, 100, 50, 110), "a)"), PAGINA)
    assert not es_etiqueta(Bloque(Caja(290, 780, 310, 795), "3"), PAGINA)
    assert not es_etiqueta(Bloque(Caja(10, 100, 50, 110), "  "), PAGINA)


def test_en_blanco():
    assert en_blanco(bytes([255] * 100))
    assert not en_blanco(bytes([0, 255] * 50))


def test_planificar_descarta_duplicados_y_marca_paginas_inexistentes():
    figura = Caja(100, 300, 400, 500)
    geometria = {1: GeometriaPagina(PAGINA, imagenes=[figura])}
    estimulo = Estimulo(
        id="E1", tipo="figura", paginas=[], descripcion="", contenido=[],
        recortes=[recorte(0.15, 0.36, 0.65, 0.61), recorte(0.16, 0.37, 0.66, 0.62, idioma="va"), recorte(0.1, 0.1, 0.5, 0.5, pagina=3)],
    )
    plan = planificar_recortes(examen(estimulos=[estimulo]), geometria)
    assert [(p.numero, p.problemas, p.metodo) for p in plan] == [(1, (), "pdf"), (3, ("pagina-inexistente",), None)]
