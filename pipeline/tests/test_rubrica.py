from conftest import examen, nodo, texto

from pau.dominio.esquema import Pagina
from pau.dominio.rubrica import (
    EntradaRubrica,
    FuenteRubrica,
    RubricaExtraida,
    Tramo,
    arbol_para_el_modelo,
    fuente_de_rubrica,
    normalizar_rubrica,
    paginas_originales,
    rubricas_por_nodo,
    validar_rubrica,
)


def entrada(nodo_id: str, puntos: float | None = None, desglose: list[tuple[str, float]] = (), respuesta: str = "") -> EntradaRubrica:
    return EntradaRubrica(
        nodo=nodo_id, puntos=puntos, criterios=texto(f"Criterios de {nodo_id}"),
        desglose=[Tramo(descripcion=texto(d), puntos=p) for d, p in desglose],
        respuesta=texto(respuesta) if respuesta else [], paginas=[Pagina(idioma="es", pagina=2)],
    )


def rubrica(*entradas: EntradaRubrica, **extra) -> RubricaExtraida:
    base = dict(contiene_criterios=True, idiomas=["es"], generales=[], entradas=list(entradas), sin_correspondencia=[], incidencias=[])
    return RubricaExtraida(**{**base, **extra})


EXAMEN = examen(
    nodo("n1", puntos=2.5, enunciado="Pregunta con dos apartados"),
    nodo("n2", padre="n1", tipo="apartado", puntos=1.5, orden=1, etiqueta="a)"),
    nodo("n3", padre="n1", tipo="apartado", puntos=1.0, orden=2, etiqueta="b)"),
    nodo("n4", puntos=2.0, orden=2),
)

EXAMEN_DOC = {"id": "ex", "archivo": "pdfs/madrid/ex.pdf", "fuente": "uc3m"}


def anexo(**campos) -> dict:
    base = {"tipo": "criterios", "contenido": ["criterios"], "origen": "oficial", "fuente": "llibreta", "acceso": "publico", "coincidencia": "exacta"}
    return {**base, **campos}


def test_fuente_prefiere_la_correccion_incrustada_en_el_mismo_pdf():
    anexos = [anexo(fuente="uc3m", incrustado={"pagina": 6}), anexo(id="c1", url="u")]
    documentos = {"c1": {"id": "c1", "archivo": "pdfs/c1.pdf", "bytes": 10}}
    assert fuente_de_rubrica(EXAMEN_DOC, anexos, documentos) == FuenteRubrica(archivo="pdfs/madrid/ex.pdf", desde=6, anexo=anexos[0])


def test_fuente_suelta_oficial_descargada_y_con_la_variante_exacta_antes():
    anexos = [anexo(id="por-clave", coincidencia="por_clave"), anexo(id="exacta")]
    documentos = {i: {"id": i, "archivo": f"pdfs/{i}.pdf", "bytes": 1} for i in ("por-clave", "exacta")}
    assert fuente_de_rubrica(EXAMEN_DOC, anexos, documentos).archivo == "pdfs/exacta.pdf"


def test_fuente_nunca_de_academia_ni_privada_ni_sin_descargar_ni_imagen():
    documentos = {
        "academia": {"id": "academia", "archivo": "pdfs/a.pdf", "bytes": 1},
        "privada": {"id": "privada", "archivo": "pdfs/p.pdf"},
        "imagen": {"id": "imagen", "archivo": "pdfs/i.jpg", "bytes": 1},
    }
    anexos = [
        anexo(id="academia", tipo="solucion", contenido=["solucion"], origen="academia", fuente="mundoestudiante"),
        anexo(id="privada", acceso="privado"),
        anexo(id="imagen"),
    ]
    assert fuente_de_rubrica(EXAMEN_DOC, anexos, documentos) is None


def test_una_solucion_oficial_suelta_sirve_si_no_hay_criterios():
    anexos = [anexo(id="sol", tipo="solucion", contenido=["solucion"], fuente="ehu")]
    documentos = {"sol": {"id": "sol", "archivo": "pdfs/sol.pdf", "bytes": 1}}
    assert fuente_de_rubrica(EXAMEN_DOC, anexos, documentos) == FuenteRubrica(archivo="pdfs/sol.pdf", desde=1, anexo=anexos[0])


def test_arbol_para_el_modelo_lista_cada_nodo_con_su_padre_etiqueta_puntos_y_enunciado_recortado():
    largo = examen(nodo("n1", puntos=2.0, enunciado="x" * 500), nodo("n2", padre="n1", tipo="apartado", etiqueta="a)"))
    lineas = arbol_para_el_modelo(largo).splitlines()
    assert lineas[0] == "id | padre | tipo | etiqueta | puntos | enunciado"
    assert lineas[1].startswith("n1 | - | pregunta | 1 | 2.0 | xxx")
    assert len(lineas[1]) < 260
    assert lineas[2].startswith("n2 | n1 | apartado | a) | - | ")


def test_paginas_originales_desplaza_las_del_recorte_enviado():
    r = rubrica(entrada("n1"))
    assert paginas_originales(r, desde=6).entradas[0].paginas == [Pagina(idioma="es", pagina=7)]
    assert paginas_originales(r, desde=1) == r


def test_validar_rubrica_coherente_no_da_hallazgos():
    r = rubrica(
        entrada("n1", 2.5), entrada("n2", 1.5, [("Planteamiento", 0.5), ("Resultado", 1.0)]), entrada("n3", 1.0), entrada("n4", 2.0),
    )
    assert validar_rubrica(r, EXAMEN, lambda formulas: [None] * len(formulas)) == []


def test_validar_rubrica_detecta_nodos_inventados_puntos_distintos_desglose_y_huecos():
    r = rubrica(entrada("n9", 1.0), entrada("n2", 2.0, [("Algo", 0.5)]), entrada("n2", 2.0))
    hallazgos = {(h.regla, h.grave) for h in validar_rubrica(r, EXAMEN, lambda formulas: [None] * len(formulas))}
    assert ("nodo-inexistente", True) in hallazgos
    assert ("nodo-repetido", False) in hallazgos
    assert ("puntos-distintos", False) in hallazgos
    assert ("desglose-no-suma", False) in hallazgos
    assert ("nodos-sin-rubrica", False) in hallazgos


def test_validar_rubrica_marca_la_falta_de_criterios_y_el_latex_invalido():
    vacia = rubrica(contiene_criterios=False)
    assert [h.regla for h in validar_rubrica(vacia, EXAMEN, lambda f: [])] == ["sin-criterios"]
    mala = rubrica(entrada("n4", 2.0, respuesta="$\\frac{1$"))
    reglas = [h.regla for h in validar_rubrica(mala, EXAMEN, lambda formulas: ["error" if "frac" in f["tex"] else None for f in formulas])]
    assert "latex-invalido" in reglas


def test_rubricas_por_nodo_da_los_campos_publicables_por_idioma():
    r = rubrica(entrada("n2", 1.5, [("Planteamiento", 0.5)], respuesta="$x = 2$"), generales=texto("Se valora la claridad"))
    por_nodo, generales = rubricas_por_nodo(r.model_dump())
    assert generales == {"es": "Se valora la claridad"}
    assert por_nodo["n2"] == {
        "puntos": 1.5,
        "criterios": {"es": "Criterios de n2"},
        "desglose": [{"descripcion": {"es": "Planteamiento"}, "puntos": 0.5}],
        "paginas": {"es": 2},
    }


def test_normalizar_rubrica_quita_secuencias_de_control_y_arregla_la_tipografia():
    sucia = rubrica(
        EntradaRubrica(
            nodo="n1", puntos=1.0, criterios=texto("Se obtiene $\x1b[0m\\ce{Cl2}$ a $25º C$\x07"),
            desglose=[Tramo(descripcion=texto("\x1b[1mPlanteamiento"), puntos=1.0)], respuesta=[], paginas=[],
        ),
        generales=texto("Ortografía\x1b[0m"),
    )
    limpia = normalizar_rubrica(sucia)
    assert limpia.entradas[0].criterios[0].markdown == "Se obtiene $\\ce{Cl2}$ a $25^{\\circ} C$"
    assert limpia.entradas[0].desglose[0].descripcion[0].markdown == "Planteamiento"
    assert limpia.generales[0].markdown == "Ortografía"
