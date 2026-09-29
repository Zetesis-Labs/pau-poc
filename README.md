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

Los fallos pendientes detectados en la revisión del POC están registrados en
[docs/revision-2026-09-29.md](docs/revision-2026-09-29.md).
La auditoría de preguntas, soluciones, rúbricas, figuras y publicación está en
[docs/auditoria-2026-09-29/README.md](docs/auditoria-2026-09-29/README.md), con evidencias e inventarios por registro.
Los nuevos prompts candidatos y los controles añadidos están en
[docs/prompts-extraccion.md](docs/prompts-extraccion.md).
El control local que bloquea publicaciones con pérdidas se describe en
[docs/verificacion-banco.md](docs/verificacion-banco.md).

```bash
# pipeline (Python 3.12+, uv)
cd pipeline
uv sync
uv run pau --help
uv run pau verificar gpt-6-luna__p5  # informe local, sin IA
uv run pau publicar gpt-6-luna__p5   # regenera ../datos/ solo si supera los controles

# web (Node 22, pnpm)
cd web
pnpm install
pnpm dev          # http://localhost:3100
pnpm test && pnpm typecheck && pnpm lint
```

La vista de preguntas tiene dos columnas (lista y detalle); en móvil se abre el detalle a pantalla
completa. El botón **Filtros**, junto al buscador, abre un modal con selección provisional y recuentos:
**Ver preguntas** aplica los cambios y **Cancelar** los descarta. Los documentos originales están al
final del detalle, en acordeones de **Examen**, **Criterios** y **Soluciones**, y se cargan al abrirlos.
Los enlaces de rúbrica y solución abren el PDF correspondiente en su página.

El tema usa **Sistema** por defecto y responde en vivo a `prefers-color-scheme`. **Claro** y **Oscuro**
permiten fijarlo manualmente; volver a Sistema elimina la preferencia guardada.

La extracción necesita `OPENAI_API_KEY` en el entorno o en `.env` (ignorado por git).

## Despliegue

`.github/workflows/pages.yml` pasa lint, tipos y tests de las dos partes y, en `main`, construye la web con
`BASE_PATH=/pau-poc/` (prerender estático de TanStack Start) y la publica en GitHub Pages.
