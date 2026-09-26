# pipeline

Rastrea las fuentes de exámenes de la PAU, descarga los PDF, extrae las preguntas con un modelo de visión y publica `datos/`, el conjunto que consume la web (contrato en `../docs/datos.md`).

## Arquitectura

Núcleo funcional con cáscara imperativa, y puertos y adaptadores entre ambos:

```
src/pau/
  dominio/       núcleo puro: sin red, sin disco, sin PDF, sin modelo
    documento.py   clasificación de documentos (asignatura, convocatoria, año, formato)
    fuentes/       un parser HTML → Documento por fuente
    catalogo.py    deduplicado y decisiones de la descarga
    esquema.py     contrato de extracción (pydantic) que se pide al modelo
    normalizar.py  correcciones tipográficas sin ambigüedad
    validar.py     validaciones deterministas (KaTeX llega inyectado)
    geometria.py   Caja y ajuste de los recortes de figuras a la geometría real del PDF
    banco.py       aplanado en preguntas y franja de cada pregunta en su página
    lote.py        selección estratificada de exámenes
    publicacion.py qué sale a datos/
    informe.py, comparacion.py
  puertos.py     Web, Extractor, LectorPdf/DocumentoPdf, ComprobadorKatex
  adaptadores/   httpx (+ caché HTML), OpenAI Responses, PyMuPDF, KaTeX en Node
  aplicacion/    casos de uso que componen núcleo y puertos
  cli.py         compone los adaptadores reales
```

El núcleo recibe datos (geometría de página, funciones de búsqueda) y devuelve decisiones; los casos de uso hacen el I/O.

## Uso

```bash
uv sync && npm install          # Node solo para validar fórmulas con KaTeX
uv run pau rastrear             # data/examenes.json (--sin-red usa solo data/cache/html)
uv run pau descargar            # data/pdfs/…
uv run pau lote --total 100     # lotes/lote-100.json con exámenes aún no extraídos
uv run pau extraer --lote lote-58 --modelo gpt-6-luna --prompt p5   # salida/gpt-6-luna__p5/
uv run pau recortar gpt-6-luna__p5   # rehace los recortes sin llamar al modelo
uv run pau informe gpt-6-luna__p5    # hallazgos graves y leves
uv run pau banco gpt-6-luna__p5      # salida/<ejecución>/preguntas.json
uv run pau publicar gpt-6-luna__p5   # ../datos/
uv run pytest && uv run ruff check
```

`extraer` lee `OPENAI_API_KEY` del entorno o de `../.env`. `PAU_RAIZ` cambia la raíz del repo.

## Datos

- `data/` (sin versionar): catálogo, PDF crudos y caché HTML.
- `pipeline/salida/<modelo>__<prompt>/` (sin versionar): un JSON por examen con el resultado, las figuras, los hallazgos y el uso de tokens.
- `pipeline/prompts/`: versiones del prompt de extracción (p5 es la vigente).
- `pipeline/lotes/`: los lotes de exámenes extraídos.
- `datos/` (versionado): solo lo publicado. Los PDF que no se han procesado no salen nunca de `data/`.
