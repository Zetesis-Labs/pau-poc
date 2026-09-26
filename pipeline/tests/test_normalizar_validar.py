from conftest import examen, nodo, regla, texto

from pau.dominio.normalizar import inferir_reglas, normalizar, normalizar_markdown
from pau.dominio.validar import validar


def sin_errores(formulas: list[dict]) -> list[None]:
    return [None] * len(formulas)


def reglas(hallazgos, graves=True) -> set[str]:
    return {h.regla for h in hallazgos if h.grave == graves}


def test_normaliza_grados_y_trigonometria_solo_dentro_de_formulas():
    assert normalizar_markdown("A 25 ºC, el ángulo $30º$ y $\\sen x$") == "A 25 °C, el ángulo $30^{\\circ}$ y $\\operatorname{sen} x$"
    assert normalizar_markdown("sen sin barra y 3º puesto") == "sen sin barra y 3º puesto"


def test_infiere_elegir_una_entre_opciones_sin_regla():
    ex, notas = inferir_reglas(examen(nodo("a", tipo="opcion", orden=1), nodo("b", tipo="opcion", orden=2)))
    assert ex.eleccion_raiz.maximo == 1 and ex.eleccion_raiz.de == 2
    assert len(notas) == 1 and ex.incidencias == notas


def test_normalizar_cuenta_cambios():
    _, cambios = normalizar(examen(nodo("n1", enunciado="$90º$")))
    assert cambios == 1


def test_validar_examen_correcto_sin_graves():
    ex = examen(nodo("n1", puntos=5), nodo("n2", orden=2, puntos=5))
    assert reglas(validar(ex, sin_errores)) == set()


def test_validar_detecta_estructura_rota():
    ex = examen(nodo("n1"), nodo("n1", orden=2), nodo("n3", padre="nx", orden=3))
    assert {"id-duplicado", "padre-inexistente"} <= reglas(validar(ex, sin_errores))


def test_validar_pregunta_dentro_de_pregunta_y_enunciado_vacio():
    ex = examen(nodo("n1"), nodo("n2", padre="n1", enunciado=""))
    assert {"pregunta-dentro-de-pregunta", "enunciado-vacio"} <= reglas(validar(ex, sin_errores))


def test_validar_puntos_y_media_implicita():
    descuadre = examen(nodo("n1", puntos=3), nodo("n2", orden=2, puntos=3))
    assert "total-distinto" in reglas(validar(descuadre, sin_errores))
    media = examen(nodo("n1", puntos=10), nodo("n2", orden=2, puntos=10), nodo("n3", orden=3, puntos=10), eleccion_raiz=regla(2, 2, 3))
    hallazgos = validar(media, sin_errores)
    assert "total-distinto" not in reglas(hallazgos) and "media-implicita" in reglas(hallazgos, graves=False)


def test_validar_katex_inyectado():
    ex = examen(nodo("n1", enunciado="$\\frac{1}{2}$ y $\\mal$", puntos=10))
    hallazgos = validar(ex, lambda fs: [None if "frac" in f["tex"] else "Undefined control sequence" for f in fs])
    assert [h.detalle for h in hallazgos if h.regla == "latex-invalido"] == ["\\mal — Undefined control sequence"]


def test_validar_no_examen():
    assert reglas(validar(examen(es_examen=False), sin_errores)) == {"no-es-examen"}


def test_version_linguistica_incompleta_es_leve():
    bilingue = nodo("n1", puntos=10)
    bilingue = bilingue.model_copy(update={"enunciado": texto("Hola") + texto("Kaixo", "eu")})
    ex = examen(bilingue, nodo("n2", orden=2), idiomas=["es", "eu"])
    assert "version-linguistica-incompleta" in reglas(validar(ex, sin_errores), graves=False)
