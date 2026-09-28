from pau.dominio.banco import (
    apariciones,
    desambiguar,
    fin_de_contenido,
    franjas,
    inicio,
    preguntas_de,
    primeras_apariciones,
    regla,
    sin_campos_internos,
    texto_plano,
    unidades,
    variantes,
)
from pau.dominio.geometria import Bloque, Caja

ALTO = 800


def fila(y: float) -> Caja:
    return Caja(50, y, 500, y + 10)


def test_desambiguar_elige_la_aparicion_seguida_de_su_primer_apartado():
    indice, real = fila(100), fila(400)
    assert desambiguar([indice, real], [fila(430)], ALTO) == [real]
    assert desambiguar([indice, real], [], ALTO) == [real]
    assert desambiguar([real], [fila(10)], ALTO) == [real]


def test_inicio_sube_a_la_etiqueta_si_esta_justo_encima():
    assert inicio([fila(400)], [fila(380)], ALTO) == 380 / ALTO
    assert inicio([fila(400)], [fila(100)], ALTO) == 400 / ALTO
    assert inicio([], [fila(100), fila(200)], ALTO) == 200 / ALTO
    assert inicio([], [], ALTO) is None


def test_apariciones_acorta_la_busqueda_hasta_encontrar():
    buscadas = []

    def buscar(t: str) -> list[Caja]:
        buscadas.append(t)
        return [fila(1)] if t == "uno dos dos" or t == "uno dos tres" else []

    assert apariciones(buscar, "uno dos tres cuatro cinco seis siete") == [fila(1)]
    assert buscadas == ["uno dos tres cuatro cinco seis", "uno dos tres cuatro", "uno dos tres"]
    assert apariciones(buscar, "uno dos", minimo=3) == []


def test_franjas_terminan_en_la_siguiente_pregunta_o_al_final_del_contenido():
    assert franjas([0.1, 0.4, 0.402], 0.9) == [0.4, 0.9, 0.9]
    assert franjas([0.95], 0.9) == [1.0]


def test_fin_de_contenido_ignora_numeros_de_pagina():
    bloques = [Bloque(Caja(0, 100, 10, 600), "texto"), Bloque(Caja(0, 780, 10, 790), "2")]
    assert fin_de_contenido(bloques, ALTO) == 600 / ALTO + 0.01


def test_regla_legible():
    assert regla(None) == ""
    assert regla({"minimo": 2, "maximo": 2, "de": 4, "agregacion": "suma"}) == "elegir 2 de 4"
    assert regla({"minimo": None, "maximo": 3, "de": None, "agregacion": "media"}) == "elegir 0–3 de ? (nota media)"


def _nodo(id, padre=None, tipo="pregunta", orden=1, estimulos=()):
    return {
        "id": id, "padre": padre, "tipo": tipo, "orden": orden, "etiqueta": [{"idioma": "es", "markdown": id}],
        "enunciado": [{"idioma": "es", "markdown": f"Enunciado de {id} con varias palabras"}], "puntos": 1.0,
        "eleccion": None, "estimulos": list(estimulos), "paginas": [{"idioma": "es", "pagina": 1}], "sintetico": False,
    }


def test_unidades_son_las_preguntas_mas_externas_o_las_opciones_hoja():
    nodos = [_nodo("p1"), _nodo("p2", padre="p1", tipo="pregunta"), _nodo("a", padre="p1", tipo="apartado")]
    por_id = {n["id"]: n for n in nodos}
    assert [n["id"] for n in unidades(nodos, por_id)] == ["p1"]
    opciones = [_nodo("A", tipo="opcion"), _nodo("B", tipo="opcion", orden=2), _nodo("a", padre="A", tipo="apartado")]
    assert [n["id"] for n in unidades(opciones, {n["id"]: n for n in opciones})] == ["A", "B"]


def test_preguntas_de_un_registro_siguen_el_contrato():
    registro = {
        "documento": {
            "id": "doc1", "region": "Madrid", "asignatura": "Física", "anio": 2024, "convocatoria": "ordinaria",
            "tipo": "examen", "fuente": "uc3m", "url": "https://x", "archivo": "pdfs/madrid/fisica/x.pdf",
        },
        "resultado": {
            "idiomas": ["es"], "eleccion_raiz": None,
            "estimulos": [{"id": "E1", "tipo": "figura", "descripcion": "Un circuito", "contenido": []}],
            "nodos": [_nodo("n1", estimulos=["E1"]), _nodo("n2", padre="n1", tipo="apartado")],
        },
        "figuras": [{"estimulo": "E1", "idioma": "es", "archivo": "doc1_E1_es_1.png"}, {"estimulo": "E1", "idioma": "es", "problemas": ["fuera-de-rango"]}],
    }
    [p] = preguntas_de(registro)
    assert p["id"] == "doc1:n1"
    assert p["examen"]["pdf"] == "pdfs/doc1.pdf" and "archivo" not in p["examen"]
    assert p["estimulos"][0]["figuras"] == [{"src": "figuras/doc1_E1_es_1.png", "idioma": "es"}]
    assert p["apartados"][0]["enunciado"] == {"es": "Enunciado de n2 con varias palabras"}
    assert not any(k.startswith("_") for k in sin_campos_internos(p))


def test_texto_plano_conserva_formulas_triviales_y_quita_las_complejas():
    assert texto_plano("Analiza y comenta la imagen $1$ ($4$ puntos).") == "Analiza y comenta la imagen 1 (4 puntos)."
    assert texto_plano("Vale $2{,}5$ y $x$ pero no $\\\\frac{1}{2}$ ni $x^2$ **aquí**") == "Vale 2,5 y x pero no ni aquí"
    assert texto_plano("Calcula ( $\\\\int f$ ): el área") == "Calcula el área"


def test_apariciones_ignora_la_puntuacion_final_de_la_ventana():
    pdf = "Analiza y comenta la imagen 1 (4 puntos). Las imágenes 2 y 3"

    def buscar(t: str) -> list[Caja]:
        return [fila(1)] if t in pdf else []

    assert apariciones(buscar, "Analiza y comenta la imagen 1. Las imágenes") == [fila(1)]


def test_dos_preguntas_con_el_mismo_comienzo_no_comparten_ancla():
    lineas = {"Analiza y comenta la imagen 1 (4 puntos).": fila(200), "Analiza y comenta la imagen 4 (4 puntos).": fila(300)}

    def buscar(t: str) -> list[Caja]:
        return [caja for linea, caja in lineas.items() if t in linea]

    primera = apariciones(buscar, texto_plano("Analiza y comenta la imagen $1$. Las imágenes $2$ y $3$"))
    segunda = apariciones(buscar, texto_plano("Analiza y comenta la imagen $4$. La imagen $5$"))
    assert primera == [fila(200)] and segunda == [fila(300)]


def test_variantes_prueban_decimal_con_punto_y_sin_formulas():
    assert variantes("SEGUNDA PREGUNTA. ($2{,}5$ puntos)") == [
        "SEGUNDA PREGUNTA. (2,5 puntos)", "SEGUNDA PREGUNTA. (2.5 puntos)", "SEGUNDA PREGUNTA. ( puntos)",
    ]
    pdf = "SEGUNDA PREGUNTA. (2.5 puntos)"
    assert primeras_apariciones(lambda t: [fila(5)] if t in pdf else [], variantes("SEGUNDA PREGUNTA. ($2{,}5$ puntos)")) == [fila(5)]


def test_preguntas_de_llevan_la_rubrica_de_cada_nodo_y_su_procedencia():
    registro = {
        "documento": {
            "id": "doc1", "region": "Madrid", "asignatura": "Física", "anio": 2024, "convocatoria": "ordinaria",
            "tipo": "examen", "fuente": "uc3m", "url": "https://x", "archivo": "pdfs/madrid/fisica/x.pdf",
        },
        "resultado": {
            "idiomas": ["es"], "eleccion_raiz": None, "estimulos": [],
            "nodos": [_nodo("n1"), _nodo("n2", padre="n1", tipo="apartado"), _nodo("n3", padre="n1", tipo="apartado")],
        },
    }
    rubrica = {
        "fuente": {"archivo": "pdfs/madrid/fisica/x.pdf", "desde": 5, "anexo": {"tipo": "criterios", "incrustado": {"pagina": 5}}},
        "resultado": {
            "contiene_criterios": True, "generales": [{"idioma": "es", "markdown": "Se valora la claridad"}],
            "entradas": [{
                "nodo": "n2", "puntos": 1.0, "criterios": [{"idioma": "es", "markdown": "Planteamiento"}], "desglose": [],
                "respuesta": [{"idioma": "es", "markdown": "$x=2$"}], "paginas": [{"idioma": "es", "pagina": 6}],
            }],
        },
    }
    solucion = {"texto": {"es": "b = 3"}, "origen": "academia", "fuente": "mundoestudiante", "incrustado": False, "url": "u", "paginas": {"es": 1}}
    [p] = preguntas_de(registro, rubrica, {"n3": solucion})
    assert p["rubrica"] is None and p["solucion"] is None
    assert p["apartados"][0]["rubrica"] == {"puntos": 1.0, "criterios": {"es": "Planteamiento"}, "desglose": [], "paginas": {"es": 6}}
    assert p["apartados"][1]["solucion"] == solucion
    assert p["apartados"][1]["rubrica"] is None
    assert p["criteriosGenerales"] == {"es": "Se valora la claridad"}
    assert p["fuenteRubrica"] == {"tipo": "criterios", "incrustado": True}
    [sin] = preguntas_de(registro)
    assert sin["rubrica"] is None and sin["criteriosGenerales"] == {} and sin["fuenteRubrica"] is None


def test_la_fuente_suelta_de_la_rubrica_enlaza_a_su_origen():
    registro = {
        "documento": {
            "id": "doc1", "region": "Comunidad Valenciana", "asignatura": "Química", "anio": 2023, "convocatoria": "ordinaria",
            "tipo": "examen", "fuente": "umh", "url": "https://x", "archivo": "pdfs/x.pdf",
        },
        "resultado": {"idiomas": ["es"], "eleccion_raiz": None, "estimulos": [], "nodos": [_nodo("n1")]},
    }
    rubrica = {
        "fuente": {"archivo": "pdfs/c.pdf", "desde": 1, "anexo": {"tipo": "criterios", "id": "c", "url": "https://gva/c.pdf", "titulo": "Criterios"}},
        "resultado": {"contiene_criterios": True, "generales": [], "entradas": []},
    }
    [p] = preguntas_de(registro, rubrica)
    assert p["fuenteRubrica"] == {"tipo": "criterios", "incrustado": False, "url": "https://gva/c.pdf"}
