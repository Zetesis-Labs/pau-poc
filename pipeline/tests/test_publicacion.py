from pau.dominio.publicacion import publicar


def test_publicacion_solo_incluye_pdfs_procesados_y_ninguna_ruta_local():
    examenes = {
        "generado": "2026-09-26", "fuentes": {"uc3m": {"region": "Madrid", "url": "u"}},
        "documentos": [
            {"id": "a", "region": "Madrid", "tipo": "examen", "url": "https://a", "archivo": "pdfs/madrid/a.pdf", "bytes": 10},
            {"id": "b", "region": "Madrid", "tipo": "examen", "url": "https://b", "archivo": "pdfs/madrid/b.pdf", "bytes": 20},
            {"id": "c", "region": "Madrid", "tipo": "examen", "url": "https://c", "archivo": "pdfs/madrid/c.pdf", "error": "privado"},
        ],
    }
    preguntas = [{
        "id": "a:n1", "examen": {"id": "a", "pdf": "pdfs/a.pdf"}, "_archivo": "pdfs/madrid/a.pdf", "_ancla": {},
        "estimulos": [{"figuras": [{"src": "figuras/a_E1_es_1.png", "idioma": "es"}]}],
    }]
    anexo = {"tipo": "criterios", "origen": "oficial", "fuente": "uc3m", "acceso": "publico", "coincidencia": "exacta", "incrustado": {"pagina": 3}}
    p = publicar(examenes, preguntas, "run", {"a": [anexo]})
    documentos = {d["id"]: d for d in p.catalogo["documentos"]}
    assert documentos["a"]["procesado"] and documentos["a"]["pdf"] == "pdfs/a.pdf"
    assert not documentos["b"]["procesado"] and "pdf" not in documentos["b"]
    assert documentos["a"]["anexos"] == [anexo] and "anexos" not in documentos["b"]
    assert documentos["c"]["error"] == "privado"
    assert not any("archivo" in d for d in documentos.values())
    assert p.pdfs == {"pdfs/a.pdf": "pdfs/madrid/a.pdf"}
    assert p.figuras == ["a_E1_es_1.png"]
    assert p.preguntas == {"ejecucion": "run", "preguntas": [{"id": "a:n1", "examen": {"id": "a", "pdf": "pdfs/a.pdf", "anexos": [anexo]}, "estimulos": preguntas[0]["estimulos"]}]}
