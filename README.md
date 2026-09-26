# pau-poc

Prueba de concepto de un banco de preguntas de la PAU (Madrid, Comunidad Valenciana y País Vasco): se rastrean
los exámenes publicados en seis fuentes, un modelo extrae de cada PDF sus preguntas y apartados en un esquema
común (Markdown + LaTeX, puntos, reglas de elección, figuras recortadas y versiones lingüísticas) y una web
permite consultarlas junto al PDF original, resaltando la pregunta en su página.

```
pipeline/   Python: rastreo, descarga, extracción con el modelo, recortes, banco y publicación
datos/      conjunto publicado (lo único del corpus que se versiona); contrato en docs/datos.md
web/        TanStack Start + React + Tailwind: banco de preguntas y catálogo, desplegada en GitHub Pages
docs/       contrato de datos y notas
```

## Arquitectura

Las dos partes siguen *functional core, imperative shell* con puertos y adaptadores:

- **Núcleo** (`pipeline/src/pau/dominio`, `web/src/dominio`): funciones puras, sin red, disco ni librerías de
  E/S. Aquí vive todo lo que decide: parseo de las fuentes, esquema, normalización y validación de la extracción,
  geometría de los recortes, anclaje de preguntas, facetas, filtros, estado de la URL, franja del PDF.
- **Puertos** (`pipeline/src/pau/puertos.py`, `web/src/puertos`): interfaces de lo que el núcleo necesita del
  mundo (web, modelo, lector de PDF, validador KaTeX, fuente de datos).
- **Adaptadores** (`pipeline/src/pau/adaptadores`, `web/src/adaptadores`): httpx, OpenAI, PyMuPDF, Node/KaTeX,
  `fetch` de estáticos y PDF.js. Se inyectan (en la web, por el contexto del router).

## Qué se publica

Solo los PDF de los exámenes **procesados** (los que tienen preguntas en `datos/preguntas.json`), sus figuras
recortadas y el catálogo de metadatos. El resto del corpus (PDF crudos, caché HTML, salidas intermedias del
modelo) queda fuera del repositorio; el catálogo enlaza cada documento a su origen.

## Uso

```bash
# pipeline (Python 3.12+, uv)
cd pipeline
uv sync
uv run pau --help
uv run pau publicar gpt-6-luna__p5   # regenera ../datos/

# web (Node 22, pnpm)
cd web
pnpm install
pnpm dev          # http://localhost:3100
pnpm test && pnpm typecheck && pnpm lint
```

La extracción necesita `OPENAI_API_KEY` en el entorno o en `.env` (ignorado por git).

## Despliegue

`.github/workflows/pages.yml` pasa lint, tipos y tests de las dos partes y, en `main`, construye la web con
`BASE_PATH=/pau-poc/` (prerender estático de TanStack Start) y la publica en GitHub Pages.
