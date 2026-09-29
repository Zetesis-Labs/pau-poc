from pau.dominio.recuperacion import recuperar_respuestas


def examen(*nodos):
    return {"documento": {"id": "ex", "archivo": "pdfs/ex.pdf"}, "resultado": {"nodos": list(nodos)}}


def nodo(id, padre=None, tipo="pregunta"):
    return {"id": id, "padre": padre, "tipo": tipo}


def entrada(id="n1", respuesta=None, paginas=None):
    return {
        "nodo": id,
        "respuesta": respuesta if respuesta is not None else [{"idioma": "es", "markdown": "Respuesta literal"}],
        "paginas": paginas if paginas is not None else [{"idioma": "es", "pagina": 3}],
    }


def rubrica(*entradas, documento="ex", anexo=None, archivo="pdfs/crit.pdf", desde=1, contiene=True):
    anexo = anexo if anexo is not None else {"id": "crit", "url": "https://ejemplo/crit", "acceso": "publico", "origen": "oficial", "fuente": "ehu", "coincidencia": "exacta"}
    return {"documento": documento, "fuente": {"archivo": archivo, "desde": desde, "anexo": anexo}, "resultado": {"contiene_criterios": contiene, "entradas": list(entradas)}}


def motivos(exclusiones):
    assert all(e["etapa"] == "respuesta-rubrica" and "nodo" in e for e in exclusiones)
    return [e["motivo"] for e in exclusiones]


def test_recupera_respuesta_literal_con_procedencia_y_preserva_soluciones():
    previa = {"n0": {"texto": {"es": "Previa"}}}
    recuperadas, exclusiones = recuperar_respuestas(examen(nodo("n0"), nodo("n1")), rubrica(entrada()), previa)
    assert recuperadas == {
        "n0": previa["n0"],
        "n1": {
            "texto": {"es": "Respuesta literal"},
            "origen": "oficial", "fuente": "ehu", "incrustado": False,
            "url": "https://ejemplo/crit", "pdf": "pdfs/crit.pdf",
            "paginas": {"es": 3}, "extraccion": "rubrica",
        },
    }
    assert exclusiones == []
    assert previa == {"n0": {"texto": {"es": "Previa"}}}


def test_solucion_existente_y_ancestro_tienen_prioridad():
    previa = {"n1": {"texto": {"es": "Existente"}}}
    res, excl = recuperar_respuestas(examen(nodo("n1"), nodo("n2", "n1", "apartado")), rubrica(entrada("n1"), entrada("n2")), previa)
    assert res == previa
    assert motivos(excl) == ["solucion-existente", "ancestro-con-solucion"]


def test_solo_identidad_exacto_y_fuente_publica_con_origen_admitido():
    base = examen(nodo("n1"))
    anexo = {"id": "crit", "url": "u", "acceso": "publico", "origen": "oficial", "fuente": "ehu", "coincidencia": "exacta"}
    for cambio, motivo in [
        ({"documento": "otro"}, "documento-distinto"),
        ({"anexo": {**anexo, "acceso": "privado"}}, "fuente-no-publica"),
        ({"anexo": {**anexo, "origen": "otro"}}, "origen-no-admitido"),
        ({"anexo": {**anexo, "coincidencia": "parcial"}}, "coincidencia-no-exacta"),
    ]:
        res, excl = recuperar_respuestas(base, rubrica(entrada(), **cambio), {})
        assert res == {}
        assert motivos(excl) == [motivo]


def test_no_recupera_fuente_incompleta_ni_incrustado_de_otro_archivo():
    for r, motivo in [
        (rubrica(entrada(), anexo={"acceso": "publico", "origen": "oficial", "fuente": "ehu", "coincidencia": "exacta"}), "fuente-incompleta"),
        (rubrica(entrada(), anexo={"acceso": "publico", "origen": "oficial", "fuente": "ehu", "incrustado": {"pagina": 3}}, archivo="pdfs/otro.pdf"), "incrustado-ajeno"),
    ]:
        assert motivos(recuperar_respuestas(examen(nodo("n1")), r, {})[1]) == [motivo]


def test_incrustado_propio_no_necesita_coincidencia_y_respeta_desde():
    a = {"acceso": "publico", "origen": "oficial", "fuente": "ehu", "incrustado": {"pagina": 3}}
    r = rubrica(entrada(), anexo=a, archivo="pdfs/ex.pdf", desde=3)
    res, excl = recuperar_respuestas(examen(nodo("n1")), r, {})
    assert res["n1"] == {"texto": {"es": "Respuesta literal"}, "origen": "oficial", "fuente": "ehu", "incrustado": True, "paginas": {"es": 3}, "extraccion": "rubrica"}
    assert excl == []


def test_rechaza_respuesta_vacia_idiomas_duplicados_y_paginas_invalidas():
    casos = [
        (entrada(respuesta=[{"idioma": "es", "markdown": "  "}]), "respuesta-vacia"),
        (entrada(respuesta=[{"idioma": "es", "markdown": "A"}, {"idioma": "es", "markdown": "B"}]), "idioma-repetido"),
        (entrada(paginas=[{"idioma": "eu", "pagina": 3}]), "idiomas-paginas-distintos"),
        (entrada(paginas=[{"idioma": "es", "pagina": 2}]), "pagina-fuera-de-fuente"),
    ]
    for e, motivo in casos:
        res, excl = recuperar_respuestas(examen(nodo("n1")), rubrica(e, desde=3), {})
        assert res == {}
        assert motivos(excl) == [motivo]


def test_ignora_criterios_sin_respuesta_y_sin_rubrica():
    ex = examen(nodo("n1"))
    previa = {"n1": {"texto": {"es": "Anterior"}}}
    assert recuperar_respuestas(ex, None, previa) == (previa, [])
    assert recuperar_respuestas(ex, rubrica(entrada(respuesta=[])), {}) == ({}, [])


def test_paginas_de_criterios_pueden_tener_idiomas_sin_respuesta():
    paginas = [{"idioma": "es", "pagina": 3}, {"idioma": "eu", "pagina": 4}]
    res, excl = recuperar_respuestas(
        examen(nodo("n1")), rubrica(entrada(paginas=paginas)), {}
    )
    assert res["n1"]["paginas"] == {"es": 3}
    assert excl == []


def test_duplicados_bloquean_nodo_y_nodos_ausentes_o_no_respondibles_se_excluyen():
    r = rubrica(entrada("n1"), entrada("n1"), entrada("n2"), entrada("n3"))
    res, excl = recuperar_respuestas(examen(nodo("n1"), nodo("n3", tipo="bloque")), r, {})
    assert res == {}
    assert motivos(excl) == ["nodo-repetido", "nodo-repetido", "nodo-inexistente", "tipo-no-respondible"]


def test_exclusiones_documentadas_y_rubrica_sin_criterios():
    for doc, fuente_id, node, motivo in [
        ("ex", "c4afc8d9c75a", "n1", "origen-no-acreditado"),
        ("ex", "361720afddf5", "n1", "origen-no-acreditado"),
        ("5091bd5d23ad", "crit", "n1", "correspondencia-parcial"),
        ("ab690a84e30c", "crit", "n1", "baremo-distinto"),
        ("9c4cbc92103b", "crit", "n21", "idioma-pagina-incorrectos"),
        ("3c134e1125e6", "crit", "n9", "pagina-incorrecta"),
        ("cdd0f4f759e1", "crit", "n9", "pagina-incorrecta"),
    ]:
        ex = examen(nodo(node))
        ex["documento"]["id"] = doc
        r = rubrica(entrada(node), documento=doc)
        r["fuente"]["anexo"]["id"] = fuente_id
        assert motivos(recuperar_respuestas(ex, r, {})[1]) == [motivo]
    assert motivos(recuperar_respuestas(examen(nodo("n1")), rubrica(entrada(), contiene=False), {})[1]) == ["sin-criterios"]


def test_exclusion_de_pagina_afecta_solo_al_nodo_y_conserva_otras_definiciones():
    ex = examen(nodo("n9"), nodo("n10", tipo="apartado"))
    ex["documento"]["id"] = "cdd0f4f759e1"
    recuperadas, exclusiones = recuperar_respuestas(ex, rubrica(entrada("n9"), entrada("n10"), documento="cdd0f4f759e1"), {})
    assert set(recuperadas) == {"n10"}
    assert [(e["nodo"], e["motivo"]) for e in exclusiones] == [("n9", "pagina-incorrecta")]
