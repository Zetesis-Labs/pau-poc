from conftest import examen, nodo, texto

from pau.dominio.esquema import Pagina
from pau.dominio.soluciones import (
    EntradaSolucion,
    FuenteSolucion,
    SolucionExtraida,
    fuente_de_solucion,
    sin_respuesta,
    soluciones_por_nodo,
    validar_soluciones,
)

EXAMEN = examen(
    nodo("n1", puntos=2.5),
    nodo("n2", padre="n1", tipo="apartado", orden=1, etiqueta="a)"),
    nodo("n3", padre="n1", tipo="apartado", orden=2, etiqueta="b)"),
    nodo("n4", orden=2),
    nodo("b1", tipo="bloque", orden=3, enunciado=""),
)
EXAMEN_DOC = {"id": "ex", "archivo": "pdfs/madrid/ex.pdf", "fuente": "uc3m", "url": "https://uc3m/ex"}


def anexo(**campos) -> dict:
    base = {"tipo": "solucion", "contenido": ["solucion"], "origen": "oficial", "fuente": "ehu", "acceso": "publico", "coincidencia": "exacta"}
    return {**base, **campos}


def documentos(*ids: str) -> dict:
    return {i: {"id": i, "archivo": f"pdfs/{i}.pdf", "bytes": 1} for i in ids}


def entrada(nodo_id: str, respuesta: str = "Respuesta", pagina: int = 3) -> EntradaSolucion:
    return EntradaSolucion(nodo=nodo_id, respuesta=texto(respuesta), paginas=[Pagina(idioma="es", pagina=pagina)])


def solucion(*entradas: EntradaSolucion, **extra) -> SolucionExtraida:
    return SolucionExtraida(**{**dict(contiene_soluciones=True, idiomas=["es"], entradas=list(entradas), sin_correspondencia=[], incidencias=[]), **extra})


def test_la_fuente_oficial_prefiere_lo_incrustado_y_luego_solucionario_antes_que_criterios():
    anexos = [anexo(id="crit", tipo="criterios", contenido=["criterios"]), anexo(id="sol"), anexo(tipo="criterios", contenido=["criterios", "solucion"], fuente="uc3m", incrustado={"pagina": 5})]
    assert fuente_de_solucion(EXAMEN_DOC, anexos, documentos("crit", "sol"), "oficial") == FuenteSolucion("pdfs/madrid/ex.pdf", 5, anexos[2])
    sin_incrustado = anexos[:2]
    assert fuente_de_solucion(EXAMEN_DOC, sin_incrustado, documentos("crit", "sol"), "oficial").anexo["id"] == "sol"


def test_la_fuente_de_academia_solo_toma_soluciones_de_academia_accesibles_y_descargadas():
    anexos = [
        anexo(id="oficial"),
        anexo(id="privada", origen="academia", fuente="llibreta", acceso="privado"),
        anexo(id="por-clave", origen="academia", fuente="mundoestudiante", coincidencia="por_clave"),
        anexo(id="exacta", origen="academia", fuente="mundoestudiante"),
    ]
    elegida = fuente_de_solucion(EXAMEN_DOC, anexos, documentos("oficial", "privada", "por-clave", "exacta"), "academia")
    assert elegida == FuenteSolucion("pdfs/exacta.pdf", 1, anexos[3])
    assert fuente_de_solucion(EXAMEN_DOC, anexos[:2], documentos("oficial", "privada"), "academia") is None


def test_sin_respuesta_son_las_hojas_respondibles_sin_entrada_propia_ni_de_un_antepasado():
    assert sin_respuesta(EXAMEN, set()) == ["n2", "n3", "n4"]
    assert sin_respuesta(EXAMEN, {"n1"}) == ["n4"]
    assert sin_respuesta(EXAMEN, {"n2", "n4"}) == ["n3"]


def test_validar_soluciones():
    assert validar_soluciones(solucion(entrada("n1"), entrada("n4")), EXAMEN, lambda f: [None] * len(f)) == []
    reglas = {(h.regla, h.grave) for h in validar_soluciones(solucion(entrada("n9"), entrada("n2"), entrada("n2")), EXAMEN, lambda f: [None] * len(f))}
    assert reglas == {("nodo-inexistente", True), ("nodo-repetido", False), ("nodos-sin-respuesta", False)}
    assert [h.regla for h in validar_soluciones(solucion(contiene_soluciones=False), EXAMEN, lambda f: [])] == ["sin-soluciones"]
    mala = solucion(entrada("n1", "$\\frac{1$"), entrada("n4"))
    assert [h.regla for h in validar_soluciones(mala, EXAMEN, lambda f: ["error" if "frac" in x["tex"] else None for x in f])] == ["latex-invalido"]


def _registro(sol: SolucionExtraida, fuente: FuenteSolucion) -> dict:
    return {"resultado": sol.model_dump(), "fuente": {"archivo": fuente.archivo, "desde": fuente.desde, "anexo": fuente.anexo}}


def test_soluciones_por_nodo_da_la_oficial_y_completa_con_la_de_academia():
    oficial = _registro(solucion(entrada("n2", "Oficial a", 6)), FuenteSolucion("pdfs/ex.pdf", 5, anexo(fuente="uc3m", incrustado={"pagina": 5})))
    academia = _registro(
        solucion(entrada("n2", "Academia a"), entrada("n3", "Academia b", 2)),
        FuenteSolucion("pdfs/me.pdf", 1, anexo(id="me", origen="academia", fuente="mundoestudiante", url="https://me/sol.pdf")),
    )
    por_nodo = soluciones_por_nodo(oficial, academia)
    assert por_nodo["n2"] == {"texto": {"es": "Oficial a"}, "origen": "oficial", "fuente": "uc3m", "incrustado": True, "paginas": {"es": 6}}
    assert por_nodo["n3"] == {
        "texto": {"es": "Academia b"}, "origen": "academia", "fuente": "mundoestudiante", "incrustado": False,
        "url": "https://me/sol.pdf", "paginas": {"es": 2},
    }
    assert soluciones_por_nodo(None, None) == {}


def test_soluciones_por_nodo_ignora_documentos_sin_soluciones_y_respuestas_vacias():
    vacia = _registro(solucion(contiene_soluciones=False), FuenteSolucion("pdfs/x.pdf", 1, anexo(id="x", url="u")))
    hueca = _registro(solucion(EntradaSolucion(nodo="n4", respuesta=[], paginas=[])), FuenteSolucion("pdfs/y.pdf", 1, anexo(id="y", url="u")))
    assert soluciones_por_nodo(vacia, hueca) == {}
