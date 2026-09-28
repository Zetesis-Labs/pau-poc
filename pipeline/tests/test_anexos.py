from pau.dominio.anexos import (
    Incrustado,
    acceso,
    encaje,
    huerfanos,
    incrustado_por_extraccion,
    incrustado_por_texto,
    origen,
    vincular,
)


def doc(id: str, tipo: str = "examen", variante: str = "", fuente: str = "uc3m", **extra) -> dict:
    base = {
        "id": id, "region": "Madrid", "asignatura": "Química", "anio": 2024, "convocatoria": "ordinaria",
        "tipo": tipo, "variante": variante, "fuente": fuente, "url": f"https://origen/{id}", "titulo": id, "bytes": 1,
    }
    return {**base, **extra}


def test_criterios_siempre_oficiales_y_soluciones_segun_la_fuente():
    assert origen("llibreta", "criterios") == "oficial"
    assert origen("ehu", "solucion") == "oficial"
    assert origen("uc3m", "solucion") == "oficial"
    assert origen("mundoestudiante", "solucion") == "academia"
    assert origen("llibreta", "solucion") == "academia"
    assert origen("selectividad.academy", "solucion") == "academia"


def test_acceso_distingue_privado_roto_y_publico():
    assert acceso(doc("a")) == "publico"
    assert acceso(doc("a", error="privado (requiere cuenta de Google con acceso)")) == "privado"
    assert acceso(doc("a", error="HTTPStatusError: 404")) == "roto"


def test_encaje_por_variante():
    assert encaje("Opción A", "Opción A") == "exacta"
    assert encaje("", "") == "exacta"
    assert encaje("coincidencias", "coincidencias") == "exacta"
    assert encaje("", "Opción B") == "por_clave"
    assert encaje("Opción A", "") == "por_clave"
    assert encaje("Opción A", "Opción B") is None
    assert encaje("", "soluciones") == "exacta"
    assert encaje("coincidencias", "criterios") == "por_clave"


def test_vincular_por_clave_y_variante_sin_mezclar_examenes():
    documentos = [
        doc("exA", variante="Opción A"),
        doc("exB", variante="Opción B"),
        doc("solA", "solucion", "Opción A", fuente="ehu"),
        doc("solB", "solucion", "Opción B", fuente="ehu"),
        doc("crit", "criterios", fuente="llibreta"),
        doc("otro-anio", "solucion", anio=2023),
    ]
    anexos = vincular(documentos, {})
    assert [a["id"] for a in anexos["exA"]] == ["crit", "solA"]
    assert [a["id"] for a in anexos["exB"]] == ["crit", "solB"]
    assert anexos["exA"][0] == {
        "id": "crit", "tipo": "criterios", "origen": "oficial", "fuente": "llibreta", "acceso": "publico",
        "coincidencia": "por_clave", "url": "https://origen/crit", "titulo": "crit",
    }


def test_vincular_pone_primero_lo_incrustado_y_lo_oficial():
    documentos = [
        doc("ex"),
        doc("sol-academia", "solucion", fuente="mundoestudiante"),
        doc("sol-privada", "solucion", fuente="llibreta", error="privado (requiere cuenta)"),
    ]
    anexos = vincular(documentos, {"ex": Incrustado("criterios", 5)})["ex"]
    assert anexos[0] == {
        "tipo": "criterios", "origen": "oficial", "fuente": "uc3m", "acceso": "publico",
        "coincidencia": "exacta", "incrustado": {"pagina": 5},
    }
    assert [a.get("id") for a in anexos[1:]] == ["sol-academia", "sol-privada"]
    assert anexos[2]["acceso"] == "privado"


def test_vincular_ignora_documentos_que_no_son_examenes_ni_anexos():
    documentos = [doc("ex"), doc("video", "video"), doc("sol", "solucion", fuente="mundoestudiante")]
    anexos = vincular(documentos, {})
    assert set(anexos) == {"ex"}


def test_huerfanos_son_anexos_sin_examen_con_su_clave():
    documentos = [doc("ex"), doc("sol", "solucion"), doc("suelto", "criterios", asignatura="Criterios Generales")]
    assert [d["id"] for d in huerfanos(documentos)] == ["suelto"]


def test_incrustado_por_extraccion_es_la_primera_pagina_no_vacia_tras_el_enunciado():
    seis = ["portada", "p2", "p3", "criterios", "más", "más"]
    assert incrustado_por_extraccion(["portada", "criterios", "soluciones"], [2, 3], seis) == Incrustado("criterios", 4)
    assert incrustado_por_extraccion(["soluciones"], [1, 2], ["a", "b", "sol"]) == Incrustado("solucion", 3)
    assert incrustado_por_extraccion(["criterios"], [1, 3], ["a", "", "b", " \n", "criterios"]) == Incrustado("criterios", 5)
    assert incrustado_por_extraccion(["instrucciones"], [1], ["a", "b", "c"]) is None
    assert incrustado_por_extraccion(["criterios"], [1, 2, 3], ["a", "b", "c"]) is None
    assert incrustado_por_extraccion(["criterios"], [1], ["a", "", ""]) is None
    assert incrustado_por_extraccion(["criterios"], [1, 2], ["", "", ""]) == Incrustado("criterios", 3)


def test_incrustado_por_texto_detecta_criterios_y_soluciones_en_castellano_valenciano_y_euskera():
    assert incrustado_por_texto(["Pregunta 1", "CRITERIOS ESPECÍFICOS DE CORRECCIÓN Y CALIFICACIÓN"]) == Incrustado("criterios", 2)
    assert incrustado_por_texto(["Enunciat", "CRITERIS ESPECÍFICS DE CORRECCIÓ"]) == Incrustado("criterios", 2)
    assert incrustado_por_texto(["Galdera", "ZUZENTZEKO ETA KALIFIKATZEKO IRIZPIDEAK"]) == Incrustado("criterios", 2)
    assert incrustado_por_texto(["Ejercicio 1", "Ejercicio 2", "SOLUCIONES\nEjercicio 1"]) == Incrustado("solucion", 3)
    assert incrustado_por_texto(["Ariketa", "EBAZPENAK"]) == Incrustado("solucion", 2)


def test_incrustado_por_texto_no_confunde_instrucciones_con_criterios():
    assert incrustado_por_texto(["CRITERIOS DE CALIFICACIÓN: cada pregunta vale 2 puntos", "Pregunta 2"]) is None
    assert incrustado_por_texto(["Indique la solución de la ecuación", "Pregunta 2"]) is None
