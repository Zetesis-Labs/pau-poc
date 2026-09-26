from pau.dominio.documento import Documento, anio_de, asignatura_canonica, convocatoria_de, formato, ruta_local, url_descarga


def test_formato_por_url():
    assert formato("https://www.youtube.com/watch?v=x") == "youtube"
    assert formato("https://drive.google.com/drive/folders/abc") == "carpeta"
    assert formato("https://drive.google.com/file/d/abc/view") == "drive"
    assert formato("https://docs.google.com/document/d/abc/edit") == "gdoc"
    assert formato("https://ejemplo.es/pagina/") == "web"
    assert formato("https://ejemplo.es/examen.pdf") == "pdf"


def test_url_descarga_de_drive_y_gdoc():
    assert url_descarga("https://drive.google.com/file/d/AbC_1-2/view") == "https://drive.usercontent.google.com/download?id=AbC_1-2&export=download&confirm=t"
    assert url_descarga("https://docs.google.com/document/d/XyZ/edit") == "https://docs.google.com/document/d/XyZ/export?format=pdf"
    assert url_descarga("https://www.youtube.com/watch?v=x") is None


def test_asignatura_canonica_resuelve_variantes_y_lenguas():
    assert asignatura_canonica("Matemáticas Aplicadas a las CC.SS. II") == "Matemáticas Aplicadas a las CCSS II"
    assert asignatura_canonica("MATEMÁTICAS II") == "Matemáticas II"
    assert asignatura_canonica("Kimika") == "Química"
    assert asignatura_canonica("Espainiako Historia") == "Historia de España"
    assert asignatura_canonica("materia rara") == "Materia Rara"


def test_convocatoria_de_texto():
    assert convocatoria_de("Convocatoria extraordinaria 2023") == "extraordinaria"
    assert convocatoria_de("Ohiko deialdia") == "ordinaria"
    assert convocatoria_de("Julio 2020") == "ordinaria"
    assert convocatoria_de("Julio 2021") == "extraordinaria"
    assert convocatoria_de("Modelo 2025") == "modelo"
    assert convocatoria_de("sin pistas") == "otra"


def test_anio_de_curso_escolar_es_el_del_examen():
    assert anio_de("Curso 2022-23") == 2023
    assert anio_de("Junio 2019") == 2019
    assert anio_de("nada") is None


def test_id_estable_y_ruta_local():
    d = Documento("Madrid", "uc3m", "p", "Química", 2024, "ordinaria", "examen", "https://x/y.pdf", "t")
    assert d.id == Documento("Madrid", "uc3m", "otra", "Física", 2020, "modelo", "modelo", "https://x/y.pdf", "u").id
    assert ruta_local(d) == f"pdfs/madrid/quimica/2024-ordinaria-examen-uc3m-{d.id}.pdf"
