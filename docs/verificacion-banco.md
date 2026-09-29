# Conservación antes de publicar

`pau verificar` comprueba la extracción y el banco propuesto sin llamadas a IA. `pau publicar` ejecuta el mismo control antes de sustituir `datos/`. Cualquier hallazgo grave bloquea toda la publicación y conserva la anterior; no publica parcialmente los exámenes aprobados.

Desde `pipeline/`:

```bash
uv run pau verificar gpt-6-luna__p5
uv run pau verificar gpt-6-luna__p5 --rubricas gpt-6-luna__r3 --soluciones gpt-6-luna__s2
```

El informe queda en `pipeline/salida/<ejecucion>/verificacion/informe.json`. El comando sale con código 1 si hay pendientes. Incluye versiones, huellas SHA-256 de registros y banco anterior, cobertura por examen, hallazgos y exclusiones. Sus estados son `controles_superados` y `pendiente_revision`; el estado del examen se propaga a sus preguntas dentro del informe. No se modifica el contrato público ni la web.

## Qué comprueba

- Estructura: padres, ciclos, ids repetidos, apartados bajo preguntas, reglas de elección y contenido básico.
- Conservación entre extracción y banco: preguntas, apartados, contexto, etiquetas, textos, puntos, instrucciones, reglas y sus literales, estímulos, rúbricas y soluciones seleccionadas.
- Figuras: archivos, idiomas, páginas de recortes y problemas ya registrados. Comprueba que estén representadas todas las páginas, sin certificar que la imagen sea el objeto correcto.
- Existencia de PDF y correcciones legibles; entradas duplicadas de rúbricas/soluciones e identidad de cada registro.
- Frente al banco publicado: desaparición de exámenes y reducción de cantidades de preguntas, apartados, rúbricas, criterios generales, fuentes de rúbrica, soluciones y soluciones oficiales. Una reorganización legítima también puede exigir revisión. Comparar cantidades no detecta toda sustitución incorrecta con el mismo número de elementos.

Las respuestas presentes solo en la extracción de rúbricas se recuperan cuando superan
el [filtro de identidad, procedencia y referencias](recuperacion-respuestas-2026-09-29/README.md).
Las restantes quedan registradas como exclusiones con motivo concreto. También queda
explícito cuándo una solución oficial desplaza la de academia y cuándo falta una etapa.
No se considera que todos los exámenes deban tener una corrección disponible; sí se
bloquea perder cobertura que ya estaba publicada.

El control exige la estructura actual incluso para extracciones antiguas: los documentos sin nodos de pregunta quedan pendientes aunque el constructor anterior pudiera aprovechar opciones terminales.

## Sustitución y recuperación

Tras superar el control, la publicación se construye y copia en un directorio temporal. Solo entonces se mueve el banco anterior a un respaldo y se instala el nuevo. Si falla la instalación, se intenta restaurar el anterior; el respaldo queda fuera del temporal para no borrarlo si también falla la restauración. Si únicamente falla la limpieza del respaldo después de instalar, se informa por stderr y se conserva esa copia.

No es una transacción frente a apagados ni una protección contra publicaciones simultáneas. Las pruebas cubren rechazos, errores de copia, errores de instalación, recuperación y limpieza del respaldo.

## Barrido del corpus existente

Sobre 266 exámenes p5: **19 con controles superados y 247 pendientes**. Se guardan el [resumen](verificacion-2026-09-29/resumen.json), el [estado por examen](verificacion-2026-09-29/estado-examenes.csv) y el [script reproducible](verificacion-2026-09-29/resumir.py).

Predominan pérdidas del constructor: instrucciones generales y literales de elección no llegan al banco, además de 80 reglas propias de preguntas. Las incidencias se contabilizan por uso: una instrucción perdida puede señalarse en varias preguntas. No representan miles de fallos independientes del modelo ni una tasa de precisión. El nuevo bloqueo hace visibles esas pérdidas; corregirlas y adaptar su presentación sigue pendiente.

Las 431 extracciones auditadas conservan sus huellas originales y `datos/` no se ha regenerado. Un examen sin alertas sigue necesitando cotejo académico: estos controles no detectan una raíz mal transcrita, un anexo de otra variante con rutas válidas ni contenido omitido tanto por la extracción como por su inventario. La [evaluación de prompts](prompts-extraccion.md) es una comprobación distinta.

## Reparación local de los datos existentes

La corrección autorizada de PAU-REV-03/04 del 29 de septiembre de 2026 usa un
[script específico y un plan cerrado](correcciones-2026-09-29/README.md), no una nueva
publicación completa. Solo acepta las huellas conocidas de los dos JSON y produce
las huellas revisadas: 80 reglas propias, 79 literales, una variante y la retirada
de un vínculo incorrecto en el catálogo y sus 11 fichas. No puede añadir exámenes,
cambiar respuestas ni publicar una nueva extracción. Esta excepción de mantenimiento
no desactiva `exigir_conservacion`, no añade `--force` y no declara superados los
controles pendientes. Una regeneración completa sigue pasando por `pau publicar`.

La recuperación posterior de respuestas r2 tiene un [plan independiente](recuperacion-respuestas-2026-09-29/README.md):
añade únicamente soluciones a nodos existentes, conserva las soluciones previas y
coteja PDF/páginas. Tampoco permite publicar un banco completo con pérdidas pendientes.
