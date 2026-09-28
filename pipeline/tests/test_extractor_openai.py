from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel

from pau.adaptadores import extractor_openai
from pau.adaptadores.extractor_openai import ExtractorOpenAI

SRC = Path(__file__).parent.parent / "src"


class Formato(BaseModel):
    valor: int


class ClienteFalso:
    def __init__(self, **_):
        self.llamadas = []
        self.responses = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs):
        self.llamadas.append(kwargs)
        return SimpleNamespace(id="resp_1", output_parsed=Formato(valor=1), usage=None, status="completed", incomplete_details=None)


def test_ninguna_peticion_se_guarda_en_openai(monkeypatch):
    monkeypatch.setattr(extractor_openai, "OpenAI", ClienteFalso)
    extractor = ExtractorOpenAI()
    salida = extractor.estructurar(b"%PDF", "x.pdf", "contexto", "instrucciones", "gpt-6-luna", "high", Formato)
    assert extractor._cliente.llamadas[0]["store"] is False
    assert salida.id == "resp_1"


def test_solo_el_adaptador_llama_a_openai():
    llamadores = {p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py") if "responses." in p.read_text() or "import OpenAI" in p.read_text()}
    assert llamadores == {"pau/adaptadores/extractor_openai.py"}
