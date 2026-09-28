from pau.dominio.publicacion import pdfs_referenciados, publicar


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




def test_se_publican_los_anexos_sueltos_publicos_descargados_y_todo_lo_enlazado_se_copia():
    examenes = {
        "generado": "2026-09-28", "fuentes": {},
        "documentos": [
            {"id": "a", "tipo": "examen", "url": "https://a", "archivo": "pdfs/madrid/a.pdf", "bytes": 10},
            {"id": "sol", "tipo": "solucion", "url": "https://me/sol.pdf", "archivo": "pdfs/madrid/sol.pdf", "bytes": 5},
            {"id": "crit", "tipo": "criterios", "url": "https://gva/crit.pdf", "archivo": "pdfs/cv/crit.pdf", "bytes": 5},
            {"id": "priv", "tipo": "solucion", "url": "https://ll/priv.pdf", "archivo": "pdfs/cv/priv.pdf", "bytes": 5},
            {"id": "web", "tipo": "solucion", "url": "https://web/sol", "archivo": "pdfs/cv/web.html", "bytes": 5},
            {"id": "b", "tipo": "examen", "url": "https://b", "archivo": "pdfs/madrid/b.pdf", "bytes": 10},
            {"id": "sol-b", "tipo": "solucion", "url": "https://me/sol-b.pdf", "archivo": "pdfs/madrid/sol-b.pdf", "bytes": 5},
        ],
    }
    base = {"origen": "academia", "fuente": "mundoestudiante", "acceso": "publico", "coincidencia": "exacta"}
    incrustado = {**base, "tipo": "criterios", "origen": "oficial", "fuente": "uc3m", "incrustado": {"pagina": 3}}
    suelto = {**base, "tipo": "solucion", "id": "sol", "url": "https://me/sol.pdf"}
    criterios = {**base, "tipo": "criterios", "origen": "oficial", "fuente": "llibreta", "id": "crit", "url": "https://gva/crit.pdf"}
    privado = {**base, "tipo": "solucion", "fuente": "llibreta", "acceso": "privado", "id": "priv", "url": "https://ll/priv.pdf"}
    sin_pdf = {**base, "tipo": "solucion", "id": "web", "url": "https://web/sol"}
    preguntas = [{
        "id": "a:n1", "examen": {"id": "a", "pdf": "pdfs/a.pdf"}, "_archivo": "pdfs/madrid/a.pdf", "estimulos": [],
        "solucion": {"texto": {"es": "x"}, "origen": "academia", "fuente": "mundoestudiante", "incrustado": False, "url": "https://me/sol.pdf", "pdf": "pdfs/sol.pdf", "paginas": {"es": 2}},
        "fuenteRubrica": {"tipo": "criterios", "incrustado": False, "url": "https://gva/crit.pdf", "pdf": "pdfs/crit.pdf"},
    }]
    de_b = {**suelto, "id": "sol-b", "url": "https://me/sol-b.pdf"}
    p = publicar(examenes, preguntas, "run", {"a": [incrustado, suelto, criterios, privado, sin_pdf], "b": [de_b]})
    anexos = {a.get("id", "incrustado"): a for a in p.preguntas["preguntas"][0]["examen"]["anexos"]}
    assert anexos["sol"]["pdf"] == "pdfs/sol.pdf" and anexos["crit"]["pdf"] == "pdfs/crit.pdf"
    assert not any("pdf" in anexos[k] for k in ("incrustado", "priv", "web"))
    assert p.catalogo["documentos"][0]["anexos"] == p.preguntas["preguntas"][0]["examen"]["anexos"]
    assert p.catalogo["documentos"][5]["anexos"] == [de_b]
    assert p.pdfs == {"pdfs/a.pdf": "pdfs/madrid/a.pdf", "pdfs/sol.pdf": "pdfs/madrid/sol.pdf", "pdfs/crit.pdf": "pdfs/cv/crit.pdf"}
    assert pdfs_referenciados([p.catalogo, p.preguntas]) == set(p.pdfs)
