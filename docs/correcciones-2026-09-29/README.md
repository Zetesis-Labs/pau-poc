# Correcciones de HTML, variantes y reglas de elección

Aplicadas localmente el 29 de septiembre de 2026, sin nuevas llamadas de IA ni despliegue.

- **PAU-REV-01:** DOMPurify sanea el HTML después de Markdown, KaTeX y resaltado. Sin DOM compatible se presenta texto escapado. Regresiones de eventos, enlaces ejecutables, SVG/MathML maliciosos, formularios y SSR; pruebas de conservación de tablas, MathML, raíces SVG, química y resaltado. Decisión y fuentes en [saneado-html.md](../saneado-html.md).
- **PAU-REV-03:** el parser reconoce opción D. El emparejamiento recupera esa variante de la URL cuando recibe metadatos antiguos vacíos. La reparación elimina exactamente `e880b6f47a91` → `2337676aef2a` del catálogo y las 11 fichas del examen; no había respuestas extraídas de ese solucionario en esas preguntas. El documento sigue disponible por sí mismo en el catálogo y no se borran PDFs.
- **PAU-REV-04:** `preguntas_de` publica `regla` y el `literalRegla` bilingüe de la elección propia. El detalle los presenta antes del enunciado y apartados, también cuando no hay enunciado. Reparadas 80 preguntas; 79 disponen de literal original. Caso comprobado: `cdd0f4f759e1:n2`, «Defina DOS de los conceptos siguientes», castellano y valenciano.

## Reparación acotada del conjunto existente

`aplicar.py` es una excepción de mantenimiento local para estos dos fallos de datos,
autorizados en la sesión. No llama a `pau publicar` ni pretende regenerar el banco
completo con sus problemas todavía pendientes. El control normal de publicación
permanece sin cambios y sigue bloqueando nuevas publicaciones con pérdidas.

El plan cerrado `plan.json` registra los 80 IDs exactos y las huellas SHA-256 de entrada
y salida de ambos JSON. El script solo admite esos archivos y esos resultados;
contrasta además que todos los campos ajenos al alcance queden intactos. No sirve
como mecanismo general para eludir los controles. Repetirlo sobre la salida revisada
es una operación sin cambios. Si otra edición ha alterado los archivos, se detiene.

Desde la raíz del repo:

```bash
pipeline/.venv/bin/python docs/correcciones-2026-09-29/aplicar.py
pipeline/.venv/bin/python docs/correcciones-2026-09-29/aplicar.py --aplicar
```

`resultado.json` conserva la evidencia de la ejecución original. Se mantienen los
2.697 IDs de pregunta y 4.633 documentos; las extracciones originales no se modifican.
Las instrucciones generales y los literales de contexto todavía omitidos quedan
fuera de estos tres puntos y continúan pendientes en los controles de conservación.

## Validación

- 139 pruebas del pipeline con el entorno Python local y Node 22; 96 pruebas web en contenedor.
- Ruff, Biome, tipos y build web pasan en contenedor; prerender de ambas rutas correcto.
- Navegador: ficha real `cdd0f4f759e1:n2` conserva instrucción y selección 2 de 4 en castellano y valenciano.
- Revisión de estándares y de requisitos sin hallazgos pendientes tras acotar el plan y su recuperación.
