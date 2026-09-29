# Prompts candidatos después de la auditoría

Se añaden `p6`, `r3` y `s2` para comparar con `p5`, `r2` y `s1`. Las versiones anteriores y los valores por defecto se conservan hasta evaluar las nuevas contra los PDF. La versión del prompt es independiente de la del esquema: siguen vigentes los contratos de preguntas `v3`, rúbricas `r1` y soluciones `s1`.

La primera evaluación autorizada de cinco casos está en
[evaluacion-prompts-2026-09-29/README.md](evaluacion-prompts-2026-09-29/README.md).
Hay mejoras en los fallos elegidos, pero también una omisión de un paso intermedio
en el control positivo; las versiones siguen siendo candidatas.

## Cambios principales

| Prompt | Cambio | Límite |
| --- | --- | --- |
| [p6](../pipeline/prompts/p6.md) | Inventariar preguntas, alternativas y apartados por página antes de construir el árbol; cerrar cada elemento como nodo o incidencia; verificar padres y cardinalidad de elección. | El inventario es una instrucción de trabajo, no un campo guardado ni una comprobación independiente de exhaustividad. |
| [r3](../pipeline/prompts/r3.md) | Usar `desglose` solo para partidas acumulables. Conservar bandas, escalas y tarifas literalmente en `criterios`, sin transformarlas en sumandos. Referenciar el inicio por idioma. | Las escalas todavía no tienen un tipo estructurado propio; se conserva su texto completo. |
| [s2](../pipeline/prompts/s2.md) | Registrar toda respuesta sin nodo con etiqueta, página y motivo; comprobar visualmente antes de atribuir erratas al original; referenciar el comienzo de la respuesta por idioma. | Una pregunta ausente del árbol no se reconstruye desde las soluciones. Se registra la falta de correspondencia. |

Los tres incluyen instrucciones condicionales para fórmulas y manuscritos: cotejar raíces, exponentes, subíndices, barras de complemento/fracción, signos, decimales y unidades con la imagen. Las lecturas inciertas quedan como incidencias, sin corregir por plausibilidad matemática.

P6 refuerza correspondencia, integridad y secuencia de los recortes. R3/S2 conservan el marcador de figura y las notas textuales, y registran qué figura requiere consultar el original; no intentan sustituir un árbol sintáctico por etiquetas sueltas. El contrato de soluciones sigue sin admitir imágenes. Estas ramas están en los propios prompts, activadas por el contenido: no hay un clasificador ni selección automática por asignatura.

Las contradicciones entre cabecera y catálogo se anotan, manteniendo la comprobación de correspondencia por contenido. Los prompts no corrigen metadatos ni pueden recuperar páginas que el pipeline no les envía.

## Controles deterministas añadidos

- `apartado-fuera-de-pregunta`: grave si un apartado es raíz o depende de un bloque/opción, en lugar de pregunta/apartado.
- `eleccion-hijos-distintos`: grave si `de` no coincide con el número de hijos directos, también en la raíz y en nodos sin hijos.
- `eleccion-imposible` se comprueba aunque el examen no tenga puntuaciones.

Sobre los 266 resultados p5 existentes, los dos controles nuevos detectan **80 apartados mal anidados y 15 discrepancias de cardinalidad**. Entre ellas están las pérdidas auditadas de `fda5ea13b6c5`, `0b7e227a5499`, `ed03ea4e6cf8`, `42576f6f84fc` y `a25ae1a53c4f`. El barrido se hizo en memoria: no reescribe los registros ni sus hallazgos antiguos.

Son hallazgos graves para revisión; **el comando de publicación bloquea por ellos** mediante el nuevo [control de conservación](verificacion-banco.md). No demuestran que se haya recuperado contenido ni detectan una omisión si también desaparece la evidencia de cuántas alternativas había.

## Cómo comparar las versiones

Los comandos siguientes se ejecutan desde `pipeline/`. `extraer`, `rubricas` y `soluciones` llaman a la API y generan costes. Son una propuesta de evaluación ampliada; la evaluación autorizada inicial se limita a cinco casos y se registra en `docs/evaluacion-prompts-2026-09-29/`. Los lotes son locales e ignorados por Git; estos nombres corresponden al corpus auditado.

```bash
# Preguntas: jerarquía, alternativas y material gráfico.
uv run pau extraer --prompt p6 --lote lote-58 --ids fda5ea13b6c5 ed03ea4e6cf8 070c3795d83c 9c4cbc92103b 4a7c96ae2912 3068d1110070
uv run pau extraer --prompt p6 --lote piloto --ids 0b7e227a5499 42576f6f84fc a25ae1a53c4f 1bc800a06e3b

# Rúbricas/soluciones: mantener el árbol p5 permite aislar el cambio de prompt.
uv run pau rubricas gpt-6-luna__p5 --prompt r3 --ids 070c3795d83c 9c4cbc92103b
uv run pau soluciones gpt-6-luna__p5 --prompt s2 --origen oficial --ids 0b7e227a5499 184bfaad518f 1bc800a06e3b
uv run pau soluciones gpt-6-luna__p5 --prompt s2 --origen academia --ids 25fcf7208b8f

# Construye un banco intermedio usando exactamente las versiones elegidas.
uv run pau banco gpt-6-luna__p5 --rubricas gpt-6-luna__r3 --soluciones gpt-6-luna__s2
```

`banco` y `publicar` aceptan ahora `--rubricas modelo__prompt` y `--soluciones modelo__prompt`. Seleccionan subdirectorios de la ejecución de preguntas indicada, sin recuperar silenciosamente una versión anterior. Sin esas opciones se conservan `gpt-6-luna__r2` y `gpt-6-luna__s1`.

Un banco de comparación con r3/s2 parciales tendrá huecos en los documentos no extraídos con esas versiones. El comando `banco` solo escribe el agregado dentro de `pipeline/salida/`; `publicar` reemplaza `datos/` y debe reservarse para el conjunto que se decida publicar después de evaluarlo. Las etapas r3/s2 extraídas bajo p5 no pueden copiarse bajo p6: los ids y la estructura pueden cambiar. Para evaluar la cadena completa hay que extraerlas otra vez sobre el árbol p6.

## Criterios de evaluación sobre los casos reales

| Caso | Resultado que hay que comprobar contra el PDF |
| --- | --- |
| `fda5ea13b6c5` | 24 apartados bajo sus seis preguntas; ninguno omitido al construir el banco. |
| `0b7e227a5499` | P6 conserva 4.2 a/b. S2 sobre el árbol p5 incompleto registra las dos respuestas sin nodo; sobre p6 debe asociarlas a los nuevos nodos. |
| `ed03ea4e6cf8`, `42576f6f84fc`, `a25ae1a53c4f` | Las alternativas quedan dentro de la regla correcta y B.2 está representada. |
| `070c3795d83c` | Las bandas se conservan íntegras en criterios, con `desglose` vacío. |
| `9c4cbc92103b` | Ningún enunciado francés se presenta como criterio español/francés inventado; cada referencia corresponde a su idioma. |
| `184bfaad518f` | Barra de complemento conservada, sin acusar falsamente al original. Las soluciones A seguirán sin llegar mientras la entrada comience en p. 6: es un bloqueo del pipeline documentado, no un criterio para atribuir fallo a s2. |
| `25fcf7208b8f` | Raíz cuarta y decimal exactos, conservación de pasos y erratas realmente presentes; comparación visual de todas las páginas manuscritas. |
| `1bc800a06e3b` | Control de regresión: conservar resultados, casos y complementos que ya estaban bien. |
| `4a7c96ae2912`, `3068d1110070` | P6 mantiene todas las páginas de partituras; el rechazo por tamaño y el fallback de idioma siguen siendo problemas de código pendientes. |

Estos casos están seleccionados por fallos conocidos y no estiman una tasa general de precisión. Antes de cambiar valores por defecto, ampliar con ejemplos correctos de cada tipo y comprobar fuente→extracción→banco. Los tests locales verifican estructura y selección de versiones; no certifican que Luna siga mejor el nuevo prompt.

## Validación de la implementación

La suite del pipeline pasa con **136 tests**. Incluye regresiones de apartados mal anidados, alternativas ausentes incluso sin puntuaciones, apartados válidos anidados y selección de versiones desde la CLI hasta el banco/publicación en directorios temporales. También verifica que una solución negativa s2 no recupera automáticamente una respuesta s1, la conservación del contenido y la recuperación ante errores al publicar.

Los controles se han ejecutado sobre las salidas existentes sin IA. La comparación semántica de los cinco casos se documenta por separado; no representa una tasa general de fiabilidad. Los originales y `datos/` se conservan. No se ha ejecutado build; un subagente ejecutó Ruff en el host, fuera del procedimiento del workspace, y no se considera validación de entrega.
