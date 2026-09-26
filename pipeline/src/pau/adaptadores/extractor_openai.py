"""Extractor sobre la Responses API de OpenAI con salida estructurada."""

import base64

from openai import OpenAI

from pau.dominio.esquema import ExamenExtraido
from pau.puertos import Extraccion

MAX_TOKENS_SALIDA = 100_000


class ExtractorOpenAI:
    def __init__(self, timeout: float = 900, reintentos: int = 3):
        self._cliente = OpenAI(timeout=timeout, max_retries=reintentos)

    def extraer(self, pdf: bytes, nombre: str, contexto: str, instrucciones: str, modelo: str, esfuerzo: str) -> Extraccion:
        respuesta = self._cliente.responses.parse(
            model=modelo,
            instructions=instrucciones,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_file", "filename": nombre, "file_data": "data:application/pdf;base64," + base64.b64encode(pdf).decode()},
                    {"type": "input_text", "text": contexto},
                ],
            }],
            text_format=ExamenExtraido,
            reasoning={"effort": esfuerzo},
            max_output_tokens=MAX_TOKENS_SALIDA,
        )
        return Extraccion(
            examen=respuesta.output_parsed,
            uso=respuesta.usage.model_dump() if respuesta.usage else None,
            estado=respuesta.status,
            detalle=str(respuesta.incomplete_details),
        )
