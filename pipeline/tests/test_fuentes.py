import json

from pau.dominio.fuentes import academy, ehu, llibreta, mundoestudiante, uc3m, umh


def test_uc3m_toma_convocatoria_de_la_cabecera_de_columna():
    html = """<div class="contCentral"><table>
      <thead><tr><th>Materia</th><th>Ordinaria 2023</th><th>Extraordinaria 2023</th></tr></thead>
      <tr><td>Química</td>
          <td><a href="https://drive.google.com/file/d/A/view">Examen</a></td>
          <td><a href="/docs/criterios.pdf">Criterios</a></td></tr>
    </table></div>"""
    documentos = uc3m.parse_materia(html, "https://www.uc3m.es/ss/Satellite/evau/es/TextoMixta/1/", "Química")
    assert [(d.convocatoria, d.tipo, d.anio) for d in documentos] == [("ordinaria", "examen", 2023), ("extraordinaria", "criterios", 2023)]
    assert all(d.asignatura == "Química" for d in documentos)


def test_uc3m_indice_sin_duplicados():
    html = '<div class="contCentral"><a href="/TextoMixta/1">Física</a><a href="/TextoMixta/1">Física</a><a href="/TextoMixta/2">Química</a></div>'
    assert [t for t, _ in uc3m.parse_indice(html)] == ["Física", "Química"]


def test_mundoestudiante_usa_la_materia_de_la_columna_y_la_opcion_del_fichero():
    html = """<h3>Junio 2019</h3><div class="gb-block-layout-column-inner"><p>Física</p>
      <a href="/wp/Fisica-Madrid-opcion_A.pdf">Examen</a><a href="/wp/Fisica-Madrid-soluciones.pdf">Soluciones</a></div>"""
    documentos = mundoestudiante.parse(html)
    assert [(d.asignatura, d.anio, d.convocatoria, d.tipo, d.variante) for d in documentos] == [
        ("Física", 2019, "ordinaria", "examen", "Opción A"),
        ("Física", 2019, "ordinaria", "solucion", ""),
    ]


def test_llibreta_lee_anio_del_panel_y_tipo_de_la_clase():
    html = """<div data-year-panel="2022"><div class="ll-exam-call-box"><h4>Convocatoria ordinaria</h4>
      <a class="ll-btn--exam" href="/e.pdf">Examen</a><a class="ll-btn--sol" href="/s.pdf">Solución</a>
      <a href="https://youtube.com/watch?v=1">Vídeo</a></div></div>"""
    documentos = llibreta.parse_materia(html, llibreta.INDICE + "historia-del-arte/")
    assert [(d.anio, d.convocatoria, d.tipo) for d in documentos] == [(2022, "ordinaria", "examen"), (2022, "ordinaria", "solucion"), (2022, "ordinaria", "video")]
    assert documentos[0].asignatura == "Historia del Arte"


def test_umh_recoge_pdfs_y_videos_sin_repetir():
    html = """<h1>Química 2021</h1><div id="left-area">
      <a href="/f/examen.pdf">Examen</a><a href="/f/examen.pdf">Examen otra vez</a><a href="/f/criterios.pdf">Criterios</a>
      <iframe src="https://www.youtube.com/embed/abc?rel=0" title="Resolución"></iframe></div>"""
    documentos = umh.parse_convocatoria(html, umh.BASE + "quimica/julio-21/", "Química", "Julio")
    assert [(d.tipo, d.url.rsplit("/", 1)[-1]) for d in documentos] == [("examen", "examen.pdf"), ("criterios", "criterios.pdf"), ("video", "abc")]
    assert {d.anio for d in documentos} == {2021}


def test_ehu_formato_listado_parte_materia_y_convocatoria():
    html = """<div class="information-detail"><h2>Ohiko deialdia</h2><ul>
      <li><a class="bullet-pdf" href="/documents/1/fisica.pdf"><span>pdf</span><span>Física - Convocatoria ordinaria</span></a></li>
      <li><a href="/otra/cosa">no</a></li></ul></div>"""
    documentos = ehu.parse_pagina(html, ehu.INDICE + "/2024")
    assert [(d.asignatura, d.convocatoria, d.tipo, d.anio) for d in documentos] == [("Física", "ordinaria", "examen", 2024)]


def test_academy_filtra_regiones_y_arma_url_del_almacen():
    filas = [
        {"ccaa": "pais-vasco", "asignatura": "matematicas-ii", "year": 2024, "convocatoria": "ordinaria", "storage_path": "pais-vasco/2024/ordinaria/matematicas-ii/examen.pdf"},
        {"ccaa": "madrid", "asignatura": "fisica", "year": 2024, "convocatoria": "ordinaria", "storage_path": "madrid/2024/ordinaria/fisica/examen.pdf"},
    ]
    documentos = academy.parse(json.dumps(filas))
    assert len(documentos) == 1
    assert documentos[0].url == academy.ALMACEN + filas[0]["storage_path"]
    assert documentos[0].asignatura == "Matemáticas II"
