import json

import pymupdf
import pytest
from conftest import examen, nodo, texto

from pau.aplicacion.rutas import Rutas
from pau.aplicacion.verificacion import PublicacionBloqueada
from pau.cli import parser


def guardar(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido))


@pytest.fixture
def rutas(tmp_path):
    rutas = Rutas(tmp_path)
    pdf = rutas.data / "pdfs/ex.pdf"
    pdf.parent.mkdir(parents=True)
    with pymupdf.open() as documento:
        documento.new_page().insert_text((72, 100), "Enunciado de prueba")
        documento.save(pdf)
    doc = {
        "id": "ex", "region": "Madrid", "asignatura": "Matemáticas II", "anio": 2026, "convocatoria": "modelo",
        "tipo": "modelo", "fuente": "uc3m", "url": "https://example.org/ex.pdf", "archivo": "pdfs/ex.pdf", "bytes": pdf.stat().st_size,
    }
    guardar(rutas.examenes, {"generado": "2026-09-29", "fuentes": {}, "documentos": [doc]})
    base = rutas.ejecucion("gpt-6-luna__p6")
    guardar(base / "ex.json", {"documento": doc, "resultado": examen(nodo("n1", puntos=10)).model_dump(), "figuras": []})
    anexo = {"tipo": "criterios", "origen": "oficial", "fuente": "uc3m", "incrustado": {"pagina": 1}}
    fuente = {"archivo": "pdfs/ex.pdf", "desde": 1, "anexo": anexo}
    for rubrica, solucion, marca in [("r2", "s1", "anterior"), ("r3", "s2", "nueva")]:
        entrada_rubrica = {
            "nodo": "n1", "puntos": 10, "criterios": [t.model_dump() for t in texto(f"Rúbrica {marca}")],
            "desglose": [], "respuesta": [], "paginas": [{"idioma": "es", "pagina": 1}],
        }
        guardar(base / "rubricas" / f"gpt-6-luna__{rubrica}" / "ex.json", {
            "fuente": fuente, "resultado": {"contiene_criterios": True, "entradas": [entrada_rubrica], "generales": []},
        })
        for origen in ("oficial", "academia"):
            guardar(base / "soluciones" / f"gpt-6-luna__{solucion}" / origen / "ex.json", {
                "fuente": {**fuente, "anexo": {**anexo, "origen": origen}},
                "resultado": {"contiene_soluciones": True, "entradas": [{
                    "nodo": "n1", "respuesta": [t.model_dump() for t in texto(f"Solución {marca} {origen}")],
                    "paginas": [{"idioma": "es", "pagina": 1}],
                }]},
            })
    return rutas


@pytest.mark.parametrize("orden", ["banco", "publicar"])
@pytest.mark.parametrize("explicitas", [True, False])
def test_la_cli_usa_las_versiones_elegidas_y_conserva_los_valores_anteriores(rutas, orden, explicitas):
    argumentos = [orden, "gpt-6-luna__p6"]
    if explicitas:
        argumentos += ["--rubricas", "gpt-6-luna__r3", "--soluciones", "gpt-6-luna__s2"]
    args = parser().parse_args(argumentos)
    args.accion(args, rutas)
    destino = rutas.datos if orden == "publicar" else rutas.ejecucion(args.ejecucion)
    [pregunta] = json.loads((destino / "preguntas.json").read_text())["preguntas"]
    marca = "nueva" if explicitas else "anterior"
    assert pregunta["rubrica"]["criterios"] == {"es": f"Rúbrica {marca}"}
    assert pregunta["solucion"]["texto"] == {"es": f"Solución {marca} oficial"}


def test_una_solucion_negativa_nueva_no_recupera_silenciosamente_la_version_antigua(rutas):
    base = rutas.ejecucion("gpt-6-luna__p6")
    for origen in ("oficial", "academia"):
        guardar(base / "soluciones/gpt-6-luna__s2" / origen / "ex.json", {"resultado": {"contiene_soluciones": False}})
    args = parser().parse_args(["banco", "gpt-6-luna__p6", "--soluciones", "gpt-6-luna__s2"])
    args.accion(args, rutas)
    [pregunta] = json.loads((base / "preguntas.json").read_text())["preguntas"]
    assert pregunta["solucion"] is None


def test_publicar_con_perdidas_deja_intacto_el_banco_anterior_y_guarda_el_motivo(rutas):
    previo = rutas.datos / "preguntas.json"
    guardar(previo, {"preguntas": [], "contenido": "publicación anterior"})
    original = previo.read_bytes()
    ruta = rutas.ejecucion("gpt-6-luna__p6") / "ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"]["instrucciones"] = [t.model_dump() for t in texto("Responda solo dos preguntas")]
    guardar(ruta, registro)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    assert previo.read_bytes() == original
    informe = json.loads((ruta.parent / "verificacion/informe.json").read_text())
    assert informe["estado"] == "pendiente_revision"
    assert informe["documentos"][0]["hallazgos"]


def test_verificar_detecta_un_ciclo_sin_recorrerlo_ni_modificar_datos(rutas):
    ruta = rutas.ejecucion("gpt-6-luna__p6") / "ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"]["nodos"][0]["padre"] = "n1"
    guardar(ruta, registro)
    args = parser().parse_args(["verificar", "gpt-6-luna__p6"])
    with pytest.raises(SystemExit) as salida:
        args.accion(args, rutas)
    assert salida.value.code == 1
    informe = json.loads((ruta.parent / "verificacion/informe.json").read_text())
    assert "ciclo" in {h["regla"] for h in informe["documentos"][0]["hallazgos"]}
    assert not rutas.datos.exists()


def test_la_publicacion_no_filtra_identificadores_internos_de_apartados(rutas):
    ruta = rutas.ejecucion("gpt-6-luna__p6") / "ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"] = examen(
        nodo("n1", puntos=10), nodo("n2", padre="n1", tipo="apartado"), nodo("n3", padre="n2", tipo="apartado"),
    ).model_dump()
    guardar(ruta, registro)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    publicado = (rutas.datos / "preguntas.json").read_text()
    assert '"_nodo"' not in publicado
    [pregunta] = json.loads(publicado)["preguntas"]
    assert pregunta["apartados"][0]["apartados"][0]["enunciado"] == {"es": "Enunciado de prueba"}


@pytest.mark.parametrize("fallo", ["sin-resultados", "json-roto", "correccion-rota", "pdf-ausente"])
def test_publicacion_incomprobable_no_reemplaza_el_destino(rutas, fallo):
    base = rutas.ejecucion("gpt-6-luna__p6")
    guardar(rutas.datos / "preguntas.json", {"preguntas": [], "anterior": True})
    if fallo == "sin-resultados":
        ejecucion = "ejecucion-inexistente"
    else:
        ejecucion = "gpt-6-luna__p6"
        if fallo == "json-roto":
            (base / "ex.json").write_text("{")
        elif fallo == "correccion-rota":
            (base / "rubricas/gpt-6-luna__r2/ex.json").write_text("{")
        elif fallo == "pdf-ausente":
            registro = json.loads((base / "ex.json").read_text())
            registro["documento"]["archivo"] = "pdfs/ausente.pdf"
            guardar(base / "ex.json", registro)
    args = parser().parse_args(["publicar", ejecucion])
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    assert json.loads((rutas.datos / "preguntas.json").read_text()) == {"preguntas": [], "anterior": True}


def test_un_fallo_al_copiar_el_pdf_conserva_el_banco_anterior(rutas, monkeypatch):
    import shutil

    guardar(rutas.datos / "preguntas.json", {"preguntas": [], "anterior": True})

    def disco_lleno(origen, destino):
        raise OSError("disco lleno")

    monkeypatch.setattr(shutil, "copyfile", disco_lleno)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    with pytest.raises(OSError, match="disco lleno"):
        args.accion(args, rutas)
    assert json.loads((rutas.datos / "preguntas.json").read_text()) == {"preguntas": [], "anterior": True}


def test_un_fallo_al_sustituir_el_directorio_restaura_el_banco_anterior(rutas, monkeypatch):
    from pathlib import Path

    guardar(rutas.datos / "preguntas.json", {"preguntas": [], "anterior": True})
    renombrar = Path.rename

    def fallo_al_instalar(origen, destino):
        if origen.name == "datos" and origen.parent.name.startswith(".pau-publicacion-"):
            raise OSError("fallo al instalar")
        return renombrar(origen, destino)

    monkeypatch.setattr(Path, "rename", fallo_al_instalar)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    with pytest.raises(OSError, match="fallo al instalar"):
        args.accion(args, rutas)
    assert json.loads((rutas.datos / "preguntas.json").read_text()) == {"preguntas": [], "anterior": True}


@pytest.mark.parametrize("perdida", ["examen", "rubrica", "solucion-oficial"])
def test_desaparecer_un_archivo_no_borra_cobertura_ya_publicada(rutas, perdida):
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    previo = (rutas.datos / "preguntas.json").read_bytes()
    base = rutas.ejecucion("gpt-6-luna__p6")
    if perdida == "examen":
        registro = json.loads((base / "ex.json").read_text())
        registro["documento"]["id"] = "otro"
        guardar(base / "otro.json", registro)
        (base / "ex.json").unlink()
    elif perdida == "rubrica":
        (base / "rubricas/gpt-6-luna__r2/ex.json").unlink()
    else:
        (base / "soluciones/gpt-6-luna__s1/oficial/ex.json").unlink()
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    assert (rutas.datos / "preguntas.json").read_bytes() == previo


def test_identidad_repetida_en_dos_archivos_no_produce_preguntas_duplicadas(rutas):
    base = rutas.ejecucion("gpt-6-luna__p6")
    guardar(base / "otra-copia.json", json.loads((base / "ex.json").read_text()))
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    assert not rutas.datos.exists()


def test_una_solucion_duplicada_no_desaparece_en_el_mapa_por_nodo(rutas):
    base = rutas.ejecucion("gpt-6-luna__p6")
    ruta = base / "soluciones/gpt-6-luna__s1/oficial/ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"]["entradas"].append({**registro["resultado"]["entradas"][0], "respuesta": [t.model_dump() for t in texto("Otra respuesta")]})
    guardar(ruta, registro)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    informe = json.loads((base / "verificacion/informe.json").read_text())
    assert "solucion-duplicada" in {h["regla"] for h in informe["documentos"][0]["hallazgos"]}


def test_las_exclusiones_de_respuestas_tienen_motivo_explicito(rutas):
    base = rutas.ejecucion("gpt-6-luna__p6")
    ruta = base / "rubricas/gpt-6-luna__r2/ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"]["entradas"][0]["respuesta"] = [t.model_dump() for t in texto("Respuesta en criterios")]
    guardar(ruta, registro)
    args = parser().parse_args(["verificar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    informe = json.loads((base / "verificacion/informe.json").read_text())
    motivos = {e["motivo"] for e in informe["documentos"][0]["exclusiones"]}
    assert motivos == {"solucion-existente", "se_conserva_la_solucion_oficial_del_mismo_nodo"}


def test_publicar_recupera_respuesta_de_criterios_con_procedencia_y_verificacion(rutas):
    base = rutas.ejecucion("gpt-6-luna__p6")
    for origen in ("oficial", "academia"):
        (base / "soluciones/gpt-6-luna__s1" / origen / "ex.json").unlink()
    ruta = base / "rubricas/gpt-6-luna__r2/ex.json"
    registro = json.loads(ruta.read_text())
    registro["documento"] = "ex"
    registro["fuente"]["anexo"]["acceso"] = "publico"
    registro["resultado"]["entradas"][0]["respuesta"] = [t.model_dump() for t in texto("Respuesta literal en criterios")]
    guardar(ruta, registro)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    [pregunta] = json.loads((rutas.datos / "preguntas.json").read_text())["preguntas"]
    assert pregunta["solucion"] == {
        "texto": {"es": "Respuesta literal en criterios"}, "origen": "oficial", "fuente": "uc3m",
        "incrustado": True, "paginas": {"es": 1}, "extraccion": "rubrica",
    }
    informe = json.loads((base / "verificacion/informe.json").read_text())
    assert informe["documentos"][0]["cobertura"]["soluciones"] == 1
    assert not any(e["etapa"] == "respuesta-rubrica" for e in informe["documentos"][0]["exclusiones"])


def test_republicar_sin_perdidas_supera_la_comparacion_con_el_banco_anterior(rutas):
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    anterior = (rutas.datos / "preguntas.json").read_bytes()
    args.accion(args, rutas)
    assert (rutas.datos / "preguntas.json").read_bytes() == anterior
    assert not list(rutas.raiz.glob(".pau-publicacion-*"))


def test_desaparecer_una_rubrica_solo_con_criterios_generales_bloquea_publicacion(rutas):
    ruta = rutas.ejecucion("gpt-6-luna__p6") / "rubricas/gpt-6-luna__r2/ex.json"
    registro = json.loads(ruta.read_text())
    registro["resultado"]["entradas"] = []
    registro["resultado"]["generales"] = [t.model_dump() for t in texto("Se valorará la precisión")]
    guardar(ruta, registro)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    anterior = (rutas.datos / "preguntas.json").read_bytes()
    ruta.unlink()
    with pytest.raises(PublicacionBloqueada):
        args.accion(args, rutas)
    assert (rutas.datos / "preguntas.json").read_bytes() == anterior


def test_fallo_al_limpiar_respaldo_informa_y_conserva_la_publicacion_instalada(rutas, monkeypatch, capsys):
    import shutil

    guardar(rutas.datos / "preguntas.json", {"preguntas": [], "anterior": True})
    borrar = shutil.rmtree

    def fallo_solo_en_respaldo(ruta, *args, **kwargs):
        if str(ruta).endswith("-anterior"):
            raise OSError("respaldo ocupado")
        return borrar(ruta, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", fallo_solo_en_respaldo)
    args = parser().parse_args(["publicar", "gpt-6-luna__p6"])
    args.accion(args, rutas)
    assert len(json.loads((rutas.datos / "preguntas.json").read_text())["preguntas"]) == 1
    [respaldo] = list(rutas.raiz.glob(".pau-publicacion-*-anterior"))
    assert json.loads((respaldo / "preguntas.json").read_text())["anterior"] is True
    assert "no se pudo retirar el respaldo" in capsys.readouterr().err
