import random

from pau.dominio.catalogo import Respuesta, deduplicar, evaluar_descarga
from pau.dominio.documento import Documento
from pau.dominio.lote import clave_examen, elegir, epoca


def _candidato(i: int, region: str, anio: int, asignatura: str, texto: int = 2000) -> dict:
    return {"id": str(i), "region": region, "anio": anio, "asignatura": asignatura, "convocatoria": "ordinaria", "tipo": "examen", "texto_por_pagina": texto}


def test_epoca():
    assert [epoca(None), epoca(2019), epoca(2020), epoca(2024), epoca(2025)] == ["hasta-2019", "hasta-2019", "2020-2024", "2020-2024", "pau-2025"]


def test_elegir_reparte_por_celdas_sin_repetir_examen_e_incluye_escaneados():
    candidatos = [_candidato(i, r, a, s) for i, (r, a, s) in enumerate(
        (r, a, s) for r in ("Madrid", "País Vasco") for a in (2018, 2022, 2025) for s in ("Física", "Química", "Arte")
    )]
    candidatos.append(_candidato(99, "Madrid", 2018, "Latín II", texto=50))
    lote = elegir(candidatos, 10, 1, random.Random(1))
    assert len(lote) == 10
    assert len({clave_examen(d) for d in lote}) == 10
    assert lote[0]["estrato"] == "especial · escaneado"
    assert {(d["region"], epoca(d["anio"])) for d in lote[1:7]} == {(r, e) for r in ("Madrid", "País Vasco") for e in ("hasta-2019", "2020-2024", "pau-2025")}


def test_deduplicar_por_fuente_y_url():
    a = Documento("Madrid", "uc3m", "p", "Física", 2024, "ordinaria", "examen", "https://x.pdf", "t")
    b = Documento("Madrid", "uc3m", "q", "Física", 2024, "ordinaria", "examen", "https://x.pdf", "otro")
    assert deduplicar([a, b]) == [a]


def test_evaluar_descarga():
    assert evaluar_descarga(Respuesta(200, "https://x", b"%PDF-1.7", "application/pdf")) == (".pdf", None)
    assert evaluar_descarga(Respuesta(403, "https://drive.google.com/x", b"", "text/html"))[1].startswith("privado")
    assert evaluar_descarga(Respuesta(200, "https://x", b"<html>", "text/html")) == (None, "formato no reconocido (text/html)")
    assert evaluar_descarga(Respuesta(404, "https://x", b"", "text/html"))[0] is None
