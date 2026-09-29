from pau.dominio.conservacion import comprobar_conservacion


def texto(valor):
    return [{"idioma": "es", "markdown": valor}]


def nodo(id, padre=None, tipo="pregunta", **cambios):
    base = {"id": id, "padre": padre, "tipo": tipo, "etiqueta": texto(id), "enunciado": texto(f"Enunciado {id}"),
            "puntos": 2.0, "eleccion": None, "estimulos": [], "sintetico": False}
    return {**base, **cambios}


def registro(*nodos, **resultado):
    return {"documento": {"id": "doc"}, "resultado": {"nodos": list(nodos), "estimulos": [], "instrucciones": [],
            "eleccion_raiz": None, **resultado}, "figuras": []}


def pregunta(id="n1", **cambios):
    base = {"id": f"doc:{id}", "etiqueta": {"es": id}, "enunciado": {"es": f"Enunciado {id}"},
            "puntos": 2.0, "regla": "", "reglaExamen": "", "contexto": [], "apartados": [],
            "instruccionesExamen": {}, "estimulos": [], "rubrica": None, "solucion": None,
            "criteriosGenerales": {}}
    return {**base, **cambios}


def reglas(hallazgos):
    assert all(h.grave for h in hallazgos)
    return {(h.regla, h.detalle) for h in hallazgos}


def test_conserva_una_pregunta_y_detecta_texto_alterado():
    origen = registro(nodo("n1"))
    assert comprobar_conservacion(origen, [pregunta()]) == []
    hallazgos = reglas(comprobar_conservacion(origen, [pregunta(enunciado={"es": "Otro"})]))
    assert any(r == "campo-alterado" and "n1" in d and "enunciado" in d for r, d in hallazgos)


def test_apartados_recursivos_omitidos_duplicados_y_desconocidos():
    origen = registro(nodo("n1"), nodo("n2", "n1", "apartado"), nodo("n3", "n2", "apartado"))
    a2 = {"_nodo": "n2", "etiqueta": {"es": "n2"}, "enunciado": {"es": "Enunciado n2"}, "puntos": 2.0,
          "estimulos": [], "regla": "", "rubrica": None, "solucion": None, "apartados": []}
    p = pregunta(apartados=[a2])
    assert ("nodo-omitido", "n3") in reglas(comprobar_conservacion(origen, [p]))
    duplicados = reglas(comprobar_conservacion(origen, [pregunta(apartados=[a2, a2])]))
    assert ("nodo-duplicado", "n2") in duplicados
    inventado = reglas(comprobar_conservacion(origen, [pregunta(apartados=[{**a2, "_nodo": "n99"}])]))
    assert ("nodo-desconocido", "n99") in inventado


def test_detecta_apartados_huerfanos_aunque_haya_preguntas_validas():
    origen = registro(nodo("n1"), *(nodo(f"a{i}", "bloque", "apartado") for i in range(24)), nodo("bloque", tipo="bloque", enunciado=[]))
    omitidos = {d for r, d in reglas(comprobar_conservacion(origen, [pregunta()])) if r == "nodo-omitido"}
    assert omitidos == {f"a{i}" for i in range(24)}


def test_reglas_instrucciones_y_contexto_respondible():
    eleccion = {"minimo": 1, "maximo": 1, "de": 2, "agregacion": "suma"}
    origen = registro(nodo("op", tipo="opcion", enunciado=texto("Lee esto"), eleccion=eleccion),
                      nodo("n1", "op", eleccion=eleccion),
                      instrucciones=texto("Responde solo una"), eleccion_raiz=eleccion)
    p = pregunta(contexto=[{"tipo": "opcion", "etiqueta": {"es": "op"}, "enunciado": {"es": "Lee esto"},
                            "regla": "elegir 1 de 2", "sintetico": False}],
                 regla="elegir 1 de 2", reglaExamen="elegir 1 de 2", instruccionesExamen={"es": "Responde solo una"})
    assert comprobar_conservacion(origen, [p]) == []
    roto = {k: v for k, v in p.items() if k not in {"regla", "instruccionesExamen"}}
    hallazgos = reglas(comprobar_conservacion(origen, [roto]))
    assert any(r == "campo-alterado" and "n1.regla" in d for r, d in hallazgos)
    assert any(r == "campo-alterado" and "n1.instruccionesExamen" in d for r, d in hallazgos)
    sin_contexto = reglas(comprobar_conservacion(origen, [pregunta(regla="elegir 1 de 2", reglaExamen="elegir 1 de 2", instruccionesExamen={"es": "Responde solo una"})]))
    assert any("op" in d for _, d in sin_contexto)


def test_rubrica_y_solucion_se_conservan_por_nodo():
    origen = registro(nodo("n1"), nodo("n2", "n1", "apartado"))
    rubrica = {"resultado": {"contiene_criterios": True, "generales": texto("Claridad"), "entradas": [
        {"nodo": "n2", "puntos": 2.0, "criterios": texto("Cálculo"), "desglose": [], "respuesta": texto("x=1"), "paginas": []},
        {"nodo": "n99", "puntos": None, "criterios": texto("Sobran"), "desglose": [], "respuesta": [], "paginas": []},
    ]}}
    a2 = {"_nodo": "n2", "etiqueta": {"es": "n2"}, "enunciado": {"es": "Enunciado n2"}, "puntos": 2.0,
          "estimulos": [], "regla": "", "rubrica": {"puntos": 2.0, "criterios": {"es": "Cálculo"}, "desglose": [], "paginas": {}},
          "solucion": {"texto": {"es": "x=1"}}, "apartados": []}
    p = pregunta(apartados=[a2], criteriosGenerales={"es": "Claridad"})
    soluciones = {"n2": {"texto": {"es": "x=1"}}, "n98": {"texto": {"es": "extra"}}}
    hallazgos = reglas(comprobar_conservacion(origen, [p], rubrica, soluciones))
    assert ("rubrica-sin-nodo", "n99") in hallazgos
    assert ("solucion-sin-nodo", "n98") in hallazgos
    alterada = reglas(comprobar_conservacion(origen, [pregunta(apartados=[{**a2, "rubrica": None, "solucion": None}])], rubrica, soluciones))
    assert any("n2.rubrica" in d for _, d in alterada)
    assert any("n2.solucion" in d for _, d in alterada)


def test_estimulos_y_recortes_utilizados():
    estimulo = {"id": "E1", "tipo": "figura", "descripcion": "Circuito", "contenido": [], "recortes": [{"idioma": "es"}]}
    origen = registro(nodo("n1", estimulos=["E1"]), estimulos=[estimulo])
    origen["figuras"] = [{"estimulo": "E1", "idioma": "es", "archivo": "recorte.png"}]
    e = {"id": "E1", "tipo": "figura", "descripcion": "Circuito", "contenido": {},
         "figuras": [{"src": "figuras/recorte.png", "idioma": "es"}]}
    assert comprobar_conservacion(origen, [pregunta(estimulos=[e])]) == []
    alterado = reglas(comprobar_conservacion(origen, [pregunta(estimulos=[{**e, "descripcion": "Otro", "figuras": []}])]))
    assert any("E1.descripcion" in d for _, d in alterado)
    assert any("E1.figuras" in d for _, d in alterado)
    sin_recorte = registro(nodo("n1", estimulos=["E1"]), estimulos=[estimulo])
    assert any(r == "figura-sin-imagen" for r, _ in reglas(comprobar_conservacion(sin_recorte, [pregunta(estimulos=[{**e, "figuras": []}])])))
    sin_recorte["figuras"] = [{"estimulo": "E1", "idioma": "es", "problemas": ["fuera-de-rango"]}]
    assert any(r == "recorte-con-problemas" for r, _ in reglas(comprobar_conservacion(sin_recorte, [pregunta(estimulos=[{**e, "figuras": []}])])))
    origen["figuras"][0]["problemas"] = ["imagen-incompleta"]
    assert any(r == "recorte-con-problemas" and "imagen-incompleta" in d for r, d in reglas(comprobar_conservacion(origen, [pregunta(estimulos=[e])])))


def test_grupo_vacio_no_exige_contexto_pero_grupo_con_regla_si():
    vacio = nodo("grupo", tipo="bloque", etiqueta=[], enunciado=[], puntos=None)
    origen = registro(vacio, nodo("n1", "grupo"))
    assert comprobar_conservacion(origen, [pregunta()]) == []
    vacio["eleccion"] = {"minimo": 1, "maximo": 1, "de": 2, "agregacion": "suma"}
    assert any(r == "contexto-omitido" and d == "grupo" for r, d in reglas(comprobar_conservacion(origen, [pregunta()])))


def test_rotulo_impreso_de_grupo_exige_contexto():
    grupo = nodo("grupo", tipo="bloque", etiqueta=texto("Grupo I"), enunciado=[], puntos=None)
    origen = registro(grupo, nodo("n1", "grupo"))
    hallazgos = reglas(comprobar_conservacion(origen, [pregunta()]))
    assert any("grupo" in d for r, d in hallazgos if r in {"contexto-alterado", "contexto-omitido"})


def test_rubrica_en_ancestro_de_contexto_no_se_considera_conservada():
    origen = registro(nodo("grupo", tipo="bloque", enunciado=texto("Grupo")), nodo("n1", "grupo"))
    rubrica = {"resultado": {"contiene_criterios": True, "generales": [], "entradas": [
        {"nodo": "grupo", "puntos": None, "criterios": texto("Criterio de grupo"), "desglose": [], "respuesta": [], "paginas": []},
    ]}}
    p = pregunta(contexto=[{"tipo": "bloque", "etiqueta": {"es": "grupo"}, "enunciado": {"es": "Grupo"},
                            "regla": "", "sintetico": False}])
    assert ("rubrica-sin-nodo", "grupo") in reglas(comprobar_conservacion(origen, [p], rubrica))


def test_estimulo_extraido_sin_referencia_se_revisa():
    estimulo = {"id": "E1", "tipo": "figura", "descripcion": "Mapa", "contenido": [], "recortes": []}
    origen = registro(nodo("n1"), estimulos=[estimulo])
    assert ("estimulo-sin-referencia", "E1") in reglas(comprobar_conservacion(origen, [pregunta()]))


def test_recorte_ausente_en_un_idioma_no_queda_oculto_por_otro():
    estimulo = {"id": "E1", "tipo": "figura", "descripcion": "Mapa bilingüe", "contenido": [],
                "recortes": [{"idioma": "es"}, {"idioma": "eu"}]}
    origen = registro(nodo("n1", estimulos=["E1"]), estimulos=[estimulo])
    origen["figuras"] = [{"estimulo": "E1", "idioma": "es", "archivo": "mapa_es.png"}]
    publicado = {"id": "E1", "tipo": "figura", "descripcion": "Mapa bilingüe", "contenido": {},
                 "figuras": [{"src": "figuras/mapa_es.png", "idioma": "es"}]}
    assert ("figura-sin-imagen", "E1.figuras.eu") in reglas(comprobar_conservacion(origen, [pregunta(estimulos=[publicado])]))


def test_literal_de_regla_no_se_pierde_aunque_string_sea_correcto():
    eleccion = {"minimo": 1, "maximo": 1, "de": 2, "agregacion": "suma", "literal": texto("Responde una; si haces ambas, solo cuenta la primera")}
    origen = registro(nodo("grupo", tipo="bloque", enunciado=texto("Elige"), eleccion=eleccion),
                      nodo("n1", "grupo", eleccion=eleccion), nodo("a1", "n1", "apartado", eleccion=eleccion),
                      eleccion_raiz=eleccion)
    apartado = {"_nodo": "a1", "etiqueta": {"es": "a1"}, "enunciado": {"es": "Enunciado a1"},
                "puntos": 2.0, "estimulos": [], "regla": "elegir 1 de 2", "rubrica": None, "solucion": None, "apartados": []}
    p = pregunta(regla="elegir 1 de 2", reglaExamen="elegir 1 de 2", apartados=[apartado],
                 contexto=[{"tipo": "bloque", "etiqueta": {"es": "grupo"}, "enunciado": {"es": "Elige"},
                            "regla": "elegir 1 de 2", "sintetico": False}])
    hallazgos = reglas(comprobar_conservacion(origen, [p]))
    for detalle in ("grupo.contexto.literalRegla", "n1.literalRegla", "a1.literalRegla", "n1.literalReglaExamen"):
        assert ("campo-alterado", detalle) in hallazgos


def test_pueden_omitirse_algunos_grupos_vacios_del_contexto():
    g1 = nodo("g1", tipo="bloque", etiqueta=[], enunciado=[], puntos=None)
    g2 = nodo("g2", "g1", "opcion", etiqueta=[], enunciado=[], puntos=None)
    g3 = nodo("g3", "g2", "bloque", etiqueta=texto("Responde"), enunciado=texto("Responde"), puntos=None)
    origen = registro(g1, g2, g3, nodo("n1", "g3"))
    p = pregunta(contexto=[{"tipo": "bloque", "etiqueta": {}, "enunciado": {}, "regla": "", "sintetico": False},
                           {"tipo": "bloque", "etiqueta": {"es": "Responde"}, "enunciado": {"es": "Responde"}, "regla": "", "sintetico": False}])
    assert comprobar_conservacion(origen, [p]) == []


def test_rubrica_duplicada_no_desaparece_en_el_mapa_publicado():
    origen = registro(nodo("n1"))
    entrada = {"nodo": "n1", "puntos": 2.0, "criterios": texto("Cálculo"), "desglose": [], "respuesta": [], "paginas": []}
    rubrica = {"resultado": {"contiene_criterios": True, "generales": [], "entradas": [entrada, {**entrada}]}}
    p = pregunta(rubrica={"puntos": 2.0, "criterios": {"es": "Cálculo"}, "desglose": [], "paginas": {}})
    assert ("rubrica-duplicada", "n1") in reglas(comprobar_conservacion(origen, [p], rubrica))


def test_recorte_ausente_en_segunda_pagina_del_mismo_idioma():
    estimulo = {"id": "E1", "tipo": "figura", "descripcion": "Gráfico partido", "contenido": [],
                "recortes": [{"idioma": "es", "pagina": 1}, {"idioma": "es", "pagina": 2}]}
    origen = registro(nodo("n1", estimulos=["E1"]), estimulos=[estimulo])
    origen["figuras"] = [{"estimulo": "E1", "idioma": "es", "pagina": 1, "archivo": "grafico_1.png"}]
    publicado = {"id": "E1", "tipo": "figura", "descripcion": "Gráfico partido", "contenido": {},
                 "figuras": [{"src": "figuras/grafico_1.png", "idioma": "es"}]}
    assert ("figura-sin-imagen", "E1.figuras.es.pagina-2") in reglas(comprobar_conservacion(origen, [pregunta(estimulos=[publicado])]))
